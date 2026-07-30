#!/usr/bin/env python3
"""Run the candidate-aware OSTN15 gate and four-candidate official chain.

The complete top-level output tree is staged and atomically published only when the
PROJ evidence and child official-chain execution are hash-bound to the same candidate
manifest. Failed reruns preserve the previous valid tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

EXPECTED_ROWS = [61536, 61537, 61538, 61539]
EXPECTED_CHILD_STATUS = "FOUR_HARDENED_CANDIDATES_OFFICIAL_SAME_POINT_MEASURED_AND_PUBLISHED"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}_", suffix=".json.tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _run(stage: str, command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "stage": stage,
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-16000:],
        "stderr": proc.stderr[-16000:],
    }


def _transactional_directory_swap(stage: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.parent / f".{target.name}.backup"
    if backup.exists():
        shutil.rmtree(backup)
    previous_moved = False
    published = False
    try:
        if target.exists():
            target.replace(backup)
            previous_moved = True
        try:
            stage.replace(target)
            published = True
        except Exception:
            if previous_moved and backup.exists():
                backup.replace(target)
                previous_moved = False
            raise
        if backup.exists():
            shutil.rmtree(backup)
            previous_moved = False
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if backup.exists():
            if previous_moved and not target.exists():
                backup.replace(target)
            else:
                shutil.rmtree(backup, ignore_errors=True)
        if not published and target.exists() and target.is_dir():
            pass


def _validate_candidate_manifest(path: Path) -> str:
    payload = _load(path)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidate manifest lacks candidates list")
    rows = [int(item.get("row_no")) for item in candidates]
    if rows != EXPECTED_ROWS or len(set(rows)) != len(rows):
        raise ValueError(f"candidate row set/order mismatch: {rows}")
    for item in candidates:
        row_no = int(item["row_no"])
        if not str(item.get("parcel_id") or "").strip():
            raise ValueError(f"candidate {row_no} lacks parcel_id")
        if not str(
            item.get("hmlr_inspire_id")
            or item.get("national_cadastral_reference")
            or item.get("parcel_registry_id")
            or ""
        ).strip():
            raise ValueError(f"candidate {row_no} lacks official INSPIRE identity")
    return _sha256(path)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--proj-script", type=Path)
    parser.add_argument("--chain-script", type=Path)
    args = parser.parse_args(argv)
    if args.timeout < 1 or args.timeout > 900:
        raise ValueError("timeout must be between 1 and 900 seconds")

    script_dir = Path(__file__).resolve().parent
    proj_script = (args.proj_script or script_dir / "027_verify_batch116_proj_ostn15_gate.py").resolve()
    chain_script = (args.chain_script or script_dir / "026_execute_batch116_four_candidate_full_chain.py").resolve()
    candidate_manifest = args.candidate_manifest.resolve()
    for label, path in (
        ("candidate manifest", candidate_manifest),
        ("PROJ gate script", proj_script),
        ("official chain script", chain_script),
    ):
        if not path.is_file() or path.stat().st_size <= 0:
            raise FileNotFoundError(f"{label} missing or empty: {path}")

    candidate_sha_before = _validate_candidate_manifest(candidate_manifest)
    dependency_hashes_before = {
        "proj_script": _sha256(proj_script),
        "chain_script": _sha256(chain_script),
    }

    target = args.output_dir.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=f".{target.name}_", suffix=".stage", dir=target.parent))
    stages: list[dict[str, Any]] = []
    try:
        proj_output = stage_root / "00_proj_ostn15_gate.json"
        child_output_dir = stage_root / "01_four_candidate_chain"

        proj_cmd = [
            sys.executable,
            str(proj_script),
            "--candidate-manifest",
            str(candidate_manifest),
            "--output",
            str(proj_output),
            "--enable-network",
            "--maximum-display-delta-m",
            "20.0",
        ]
        proj_result = _run("CANDIDATE_AWARE_PROJ_OSTN15_NO_BALLPARK_ONLY_BEST", proj_cmd, script_dir)
        stages.append(proj_result)
        if proj_result["exit_code"] != 0 or not proj_output.is_file():
            raise RuntimeError(f"PROJ gate failed: {proj_result['stderr'][-2400:]}")
        proj = _load(proj_output)
        if (
            int(proj.get("schema_version") or 0) < 2
            or proj.get("passed") is not True
            or [int(v) for v in (proj.get("candidate_rows") or [])] != EXPECTED_ROWS
            or proj.get("candidate_manifest_sha256") != candidate_sha_before
            or proj.get("candidate_manifest_hash_stable") is not True
            or proj.get("network_state_restored") is not True
            or proj.get("all_display_deltas_within_sanity_limit") is not True
            or proj.get("evidence_atomic_materialization") is not True
            or int(proj.get("measurement_values_written") or 0) != 0
        ):
            raise ValueError("candidate-aware PROJ gate contract mismatch")

        chain_cmd = [
            sys.executable,
            str(chain_script),
            "--candidate-manifest",
            str(candidate_manifest),
            "--output-dir",
            str(child_output_dir),
            "--timeout",
            str(args.timeout),
        ]
        chain_result = _run("FOUR_CANDIDATE_OFFICIAL_SAME_POINT_FULL_CHAIN", chain_cmd, script_dir)
        stages.append(chain_result)
        if chain_result["exit_code"] != 0:
            raise RuntimeError(f"four-candidate official chain failed: {chain_result['stderr'][-2400:]}")
        child_execution_path = child_output_dir / "batch116_four_candidate_execution.json"
        if not child_execution_path.is_file():
            raise FileNotFoundError(child_execution_path)
        child = _load(child_execution_path)
        if (
            int(child.get("schema_version") or 0) < 4
            or child.get("status") != EXPECTED_CHILD_STATUS
            or child.get("candidate_manifest_sha256") != candidate_sha_before
            or [int(v) for v in (child.get("expected_rows") or [])] != EXPECTED_ROWS
            or int(child.get("published_count") or 0) != 4
            or child.get("measurement_contract_version") != "EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2"
            or child.get("same_point_crosscheck_required") is not True
            or child.get("source_errors_forbid_promotion") is not True
            or child.get("transactional_output_tree") is not True
            or child.get("previous_valid_output_tree_preserved_on_failure") is not True
        ):
            raise ValueError("four-candidate child execution contract mismatch")

        candidate_sha_after = _sha256(candidate_manifest)
        dependency_hashes_after = {
            "proj_script": _sha256(proj_script),
            "chain_script": _sha256(chain_script),
        }
        if candidate_sha_after != candidate_sha_before:
            raise RuntimeError("candidate manifest changed during strict four-candidate chain")
        if dependency_hashes_after != dependency_hashes_before:
            raise RuntimeError("PROJ or official-chain script changed during execution")

        execution_path = stage_root / "batch116_strict_execution.json"
        execution = {
            "schema_version": 3,
            "slot_id": "height_difference_3",
            "batch_id": 116,
            "status": "FOUR_HARDENED_CANDIDATES_CANDIDATE_AWARE_PROJ_OFFICIAL_SAME_POINT_MEASURED_AND_PUBLISHED",
            "candidate_manifest": str(candidate_manifest),
            "candidate_manifest_sha256": candidate_sha_before,
            "candidate_input_hash_stable": True,
            "dependency_script_sha256": dependency_hashes_before,
            "dependency_script_hashes_stable": True,
            "expected_rows": EXPECTED_ROWS,
            "stages": stages,
            "output_hashes": {
                "proj_gate_sha256": _sha256(proj_output),
                "four_candidate_execution_sha256": _sha256(child_execution_path),
                "verified_json_sha256": _sha256(child_output_dir / "05_verified_examples.json"),
                "verified_geojson_sha256": _sha256(child_output_dir / "05_verified_examples.geojson"),
            },
            "outputs": {
                "proj_gate": "00_proj_ostn15_gate.json",
                "four_candidate_execution": "01_four_candidate_chain/batch116_four_candidate_execution.json",
                "verified_json": "01_four_candidate_chain/05_verified_examples.json",
                "verified_geojson": "01_four_candidate_chain/05_verified_examples.geojson",
            },
            "candidate_aware_proj_gate": True,
            "same_point_crosscheck_required": True,
            "source_errors_forbid_promotion": True,
            "transactional_output_tree": True,
            "previous_valid_output_tree_preserved_on_failure": True,
            "numeric_publish_allowed": True,
            "single_shared_runner_only": True,
            "new_runner_created": False,
            "parallel_runner_used": False,
            "queue_submission": False,
            "nearest_or_fuzzy_fill_forbidden": True,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        _atomic_json(execution_path, execution)
        _transactional_directory_swap(stage_root, target)
        stage_root = target
        print(
            json.dumps(
                {
                    "ok": True,
                    "status": execution["status"],
                    "candidate_manifest_sha256": candidate_sha_before,
                    "proj_gate_sha256": execution["output_hashes"]["proj_gate_sha256"],
                    "execution": str(target / "batch116_strict_execution.json"),
                }
            )
        )
        return 0
    finally:
        if stage_root.exists() and stage_root != target:
            shutil.rmtree(stage_root, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
