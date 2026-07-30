#!/usr/bin/env python3
"""Prepare an atomic, history-bound serial-publisher manifest for Strict12 outputs.

The seven accepted files are cross-bound through the local acceptance and execution
records. All inputs must remain hash-stable while the manifest is built. This stage
never pushes or changes numeric values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

EXPECTED_ROWS = list(range(61540, 61552))
BRANCH = "codex/aays-single-runner-v5-20260706"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
CONTRACT = "EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

STRICT_BASE = Path("docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/027_batch130_prepare12_strict_chain")
ACCEPT_BASE = Path("docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/029_batch131_strict12_acceptance")
FILES = {
    "proj": STRICT_BASE / "00_proj_ostn15_gate.json",
    "measurements": STRICT_BASE / "measurement/official_measurements.json",
    "verified_json": STRICT_BASE / "measurement/verified_examples.json",
    "verified_geojson": STRICT_BASE / "measurement/verified_examples.geojson",
    "strict_acceptance": STRICT_BASE / "batch130_strict12_acceptance.json",
    "local_acceptance": ACCEPT_BASE / "batch131_strict12_local_acceptance.json",
    "acceptance_execution": ACCEPT_BASE / "batch131_strict12_acceptance_execution.json",
}


def _load_bytes(path: Path) -> tuple[bytes, dict[str, Any]]:
    data = path.read_bytes()
    if not data:
        raise ValueError(f"empty JSON file: {path}")
    value = json.loads(data.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data, value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return bool(SHA256_RE.fullmatch(str(value or "").strip().lower()))


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        staged = Path(temp_name)
        if staged.stat().st_size <= 0:
            raise ValueError("staged publish manifest is empty")
        os.replace(staged, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def build(repo: Path, output: Path, pre_publish_origin_head: str) -> dict[str, Any]:
    pre_head = pre_publish_origin_head.strip().lower()
    if not SHA1_RE.fullmatch(pre_head):
        raise ValueError("pre-publish origin HEAD must be a 40-character Git SHA-1")
    repo = repo.resolve()
    resolved = {name: (repo / rel).resolve() for name, rel in FILES.items()}
    for name, path in resolved.items():
        try:
            path.relative_to(repo)
        except ValueError as exc:
            raise ValueError(f"accepted path escapes repository: {name}") from exc
        if not path.is_file():
            raise FileNotFoundError(path)

    initial: dict[str, bytes] = {}
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in resolved.items():
        initial[name], payloads[name] = _load_bytes(path)

    acceptance = payloads["local_acceptance"]
    execution = payloads["acceptance_execution"]
    if int(acceptance.get("schema_version") or 0) < 3:
        raise ValueError("local acceptance schema is older than v3")
    if acceptance.get("local_acceptance_passed") is not True:
        raise ValueError("Batch131 local acceptance has not passed")
    if acceptance.get("inputs_hash_stable") is not True or acceptance.get("atomic_acceptance_materialization") is not True:
        raise ValueError("local acceptance lacks hash-stability or atomicity proof")
    if acceptance.get("measurement_contract_version") != CONTRACT or acceptance.get("same_point_crosscheck_required") is not True:
        raise ValueError("local acceptance same-point contract mismatch")
    if acceptance.get("remote_github_readback_required") is not True:
        raise ValueError("remote GitHub readback gate is disabled")
    if [int(v) for v in acceptance.get("expected_rows") or []] != EXPECTED_ROWS:
        raise ValueError("local acceptance rows are not exactly 61540..61551")
    prior_hashes = acceptance.get("file_sha256")
    if not isinstance(prior_hashes, dict):
        raise ValueError("local acceptance file hashes are missing")

    if int(execution.get("schema_version") or 0) < 6:
        raise ValueError("acceptance execution schema is older than v6")
    if execution.get("local_acceptance_passed") is not True:
        raise ValueError("acceptance execution did not pass")
    if execution.get("local_acceptance_inputs_hash_stable") is not True:
        raise ValueError("acceptance execution lacks stable-input proof")
    if execution.get("local_acceptance_atomic_materialization") is not True:
        raise ValueError("acceptance execution lacks atomic local-acceptance proof")
    if execution.get("atomic_execution_materialization") is not True:
        raise ValueError("acceptance execution was not atomically materialized")
    if execution.get("measurement_contract_version") != CONTRACT or execution.get("same_point_crosscheck_required") is not True:
        raise ValueError("acceptance execution same-point contract mismatch")
    if execution.get("remote_github_readback_required") is not True:
        raise ValueError("acceptance execution remote readback gate is disabled")
    local_acceptance_sha = _sha256(initial["local_acceptance"])
    if execution.get("local_acceptance_sha256") != local_acceptance_sha:
        raise ValueError("acceptance execution is not bound to local acceptance SHA-256")

    for name in ("proj", "measurements", "verified_json", "verified_geojson", "strict_acceptance"):
        expected = str(prior_hashes.get(name) or "").lower()
        actual = _sha256(initial[name])
        if not _valid_sha256(expected) or expected != actual:
            raise ValueError(f"local acceptance SHA-256 mismatch for {name}")
    if execution.get("strict_contract_sha256") != _sha256(initial["strict_acceptance"]):
        raise ValueError("acceptance execution strict-contract SHA-256 mismatch")

    records: list[dict[str, Any]] = []
    for name, relative in FILES.items():
        data = initial[name]
        records.append({
            "name": name,
            "relative_path": relative.as_posix(),
            "size_bytes": len(data),
            "sha256": _sha256(data),
            "git_blob_sha1": _git_blob_sha1(data),
        })
    if len({record["relative_path"] for record in records}) != 7:
        raise ValueError("publish manifest paths are not exactly seven unique files")

    final_bytes = {name: path.read_bytes() for name, path in resolved.items()}
    if initial != final_bytes:
        raise ValueError("accepted files changed while publish manifest was built")

    result = {
        "schema_version": 3,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "canonical_branch": BRANCH,
        "pre_publish_origin_head": pre_head,
        "pre_publish_origin_head_fresh_fetch_required": True,
        "expected_rows": EXPECTED_ROWS,
        "expected_verified_count": 12,
        "measurement_contract_version": CONTRACT,
        "same_point_crosscheck_required": True,
        "source_local_acceptance": FILES["local_acceptance"].as_posix(),
        "source_acceptance_execution": FILES["acceptance_execution"].as_posix(),
        "local_acceptance_sha256": local_acceptance_sha,
        "acceptance_execution_sha256": _sha256(initial["acceptance_execution"]),
        "inputs_hash_stable": True,
        "local_acceptance_execution_bound": True,
        "atomic_manifest_materialization": True,
        "ready_for_serial_publisher": True,
        "child_direct_push_forbidden": True,
        "new_task_forbidden": True,
        "same_task_id_required": True,
        "files": records,
        "remote_readback_contract": {
            "origin_fetch_required": True,
            "remote_commit_required": True,
            "pre_publish_origin_head_required": True,
            "pre_publish_head_must_be_ancestor_or_exact_already_published_state": True,
            "first_full_blob_materialization_commit_required_when_not_already_present": True,
            "local_sha256_must_match": True,
            "local_git_blob_sha1_must_match": True,
            "remote_git_blob_sha1_must_match": True,
            "manifest_sha256_stability_required": True,
            "all_files_required": True,
        },
        "numeric_values_changed": 0,
        "numeric_final_acceptance": "PENDING_REMOTE_HISTORY_BOUND_GITHUB_READBACK",
        "final_ready": False,
        "fake_data": False,
    }
    _write_atomic(output, result)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--pre-publish-origin-head", required=True)
    args = ap.parse_args(argv)
    result = build(args.repo_root, args.output, args.pre_publish_origin_head)
    print(json.dumps({"ok": True, "files": len(result["files"]), "pre_publish_origin_head": result["pre_publish_origin_head"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
