#!/usr/bin/env python3
"""Batch 116 top-level strict runner entry.

Runs the explicit PROJ OSTN15/no-ballpark/only-best gate first, then the
four-candidate official HMLR+EA+OS measurement chain. Existing single runner
only; no queue submission or second runner is created.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(stage: str, command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "stage": stage,
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-16000:],
        "stderr": proc.stderr[-16000:],
    }


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    proj_script = script_dir / "027_verify_batch116_proj_ostn15_gate.py"
    chain_script = script_dir / "026_execute_batch116_four_candidate_full_chain.py"
    for path in (proj_script, chain_script):
        if not path.is_file():
            raise FileNotFoundError(path)
    candidate_manifest = args.candidate_manifest.resolve()
    if not candidate_manifest.is_file():
        raise FileNotFoundError(candidate_manifest)

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    stages: list[dict[str, Any]] = []
    proj_output = out / "00_proj_ostn15_gate.json"
    chain_output_dir = out / "01_four_candidate_chain"
    execution_path = out / "batch116_strict_execution.json"

    proj_cmd = [
        sys.executable, str(proj_script),
        "--output", str(proj_output),
        "--enable-network",
    ]
    stages.append(_run("PROJ_OSTN15_NO_BALLPARK_ONLY_BEST", proj_cmd, script_dir))
    status = "BLOCKED_PROJ_OSTN15_NO_BALLPARK_ONLY_BEST"

    if stages[-1]["exit_code"] == 0:
        chain_cmd = [
            sys.executable, str(chain_script),
            "--candidate-manifest", str(candidate_manifest),
            "--output-dir", str(chain_output_dir),
            "--timeout", str(args.timeout),
        ]
        stages.append(_run("FOUR_CANDIDATE_OFFICIAL_FULL_CHAIN", chain_cmd, script_dir))
        status = "BLOCKED_FOUR_CANDIDATE_OFFICIAL_FULL_CHAIN"
        if stages[-1]["exit_code"] == 0:
            child_execution = chain_output_dir / "batch116_four_candidate_execution.json"
            if child_execution.is_file():
                child = json.loads(child_execution.read_text(encoding="utf-8-sig"))
                if child.get("status") == "FOUR_HARDENED_CANDIDATES_OFFICIAL_MEASURED_AND_PUBLISHED" and int(child.get("published_count") or 0) == 4:
                    status = "FOUR_HARDENED_CANDIDATES_STRICT_PROJ_OFFICIAL_MEASURED_AND_PUBLISHED"

    success = status == "FOUR_HARDENED_CANDIDATES_STRICT_PROJ_OFFICIAL_MEASURED_AND_PUBLISHED"
    execution = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "batch_id": 116,
        "status": status,
        "candidate_manifest": str(candidate_manifest),
        "stages": stages,
        "outputs": {
            "proj_gate": str(proj_output),
            "four_candidate_execution": str(chain_output_dir / "batch116_four_candidate_execution.json"),
            "verified_json": str(chain_output_dir / "05_verified_examples.json"),
            "verified_geojson": str(chain_output_dir / "05_verified_examples.geojson"),
        },
        "numeric_publish_allowed": success,
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
    _write(execution_path, execution)
    print(json.dumps({"ok": success, "status": status, "execution": str(execution_path)}))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
