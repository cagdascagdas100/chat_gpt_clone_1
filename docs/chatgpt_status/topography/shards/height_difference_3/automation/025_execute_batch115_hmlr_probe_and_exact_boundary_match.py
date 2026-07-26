#!/usr/bin/env python3
"""Execute Batch 115 HMLR Lambeth source probe and strict exact-ID boundary match.

Existing single runner only. No elevation sampling or candidate promotion occurs.
The wrapper fails closed unless all four hardened rows are found in exactly one
HMLR CadastralParcel feature and the existing matcher chooses an EXACT_OFFICIAL_ID
method for every row.
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


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-12000:],
        "stderr": proc.stderr[-12000:],
    }


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    probe_script = script_dir / "024_probe_current_lambeth_hmlr_exact_ids.py"
    matcher_script = script_dir / "008_match_hmlr_inspire_gml.py"
    for script in (probe_script, matcher_script):
        if not script.is_file():
            raise FileNotFoundError(script)
    candidate_manifest = args.candidate_manifest.resolve()
    if not candidate_manifest.is_file():
        raise FileNotFoundError(candidate_manifest)

    out = args.output_dir.resolve()
    probe_out = out / "hmlr_probe"
    boundary_out = out / "hmlr_exact_boundaries.json"
    execution_out = out / "batch115_hmlr_probe_execution.json"
    stages: list[dict[str, Any]] = []

    probe_cmd = [
        sys.executable,
        str(probe_script),
        "--output-dir",
        str(probe_out),
        "--timeout",
        str(args.timeout),
    ]
    probe_result = _run(probe_cmd, script_dir)
    probe_result["stage"] = "CURRENT_HMLR_LAMBETH_DOWNLOAD_AND_EXACT_ID_PROBE"
    stages.append(probe_result)
    status = "BLOCKED_HMLR_LAMBETH_PROBE"

    strict_boundary_pass = False
    strict_checks: list[dict[str, Any]] = []
    if probe_result["exit_code"] == 0:
        vector_root = probe_out / "extracted"
        matcher_cmd = [
            sys.executable,
            str(matcher_script),
            "--starter-manifest",
            str(candidate_manifest),
            "--vector-root",
            str(vector_root),
            "--output",
            str(boundary_out),
        ]
        match_result = _run(matcher_cmd, script_dir)
        match_result["stage"] = "STRICT_EXISTING_HMLR_BOUNDARY_MATCH"
        stages.append(match_result)
        status = "BLOCKED_STRICT_HMLR_BOUNDARY_MATCH"
        if match_result["exit_code"] == 0 and boundary_out.is_file():
            payload = json.loads(boundary_out.read_text(encoding="utf-8-sig"))
            results = payload.get("results") or []
            for item in results:
                method = str(item.get("match_method") or "")
                exact_count = int(item.get("exact_match_count") or 0)
                passed = (
                    item.get("status") == "MATCHED"
                    and method.startswith("EXACT_OFFICIAL_ID")
                    and exact_count >= 1
                    and not bool(item.get("nearest_polygon_fill_used"))
                )
                strict_checks.append({
                    "row_no": item.get("row_no"),
                    "parcel_id": item.get("parcel_id"),
                    "status": item.get("status"),
                    "match_method": method,
                    "exact_match_count": exact_count,
                    "passed": passed,
                })
            strict_boundary_pass = len(strict_checks) == 4 and all(x["passed"] for x in strict_checks)
            status = "FOUR_HARDENED_CANDIDATES_EXACT_HMLR_BOUNDARIES_READY" if strict_boundary_pass else "BLOCKED_NON_EXACT_BOUNDARY_MATCH"

    execution = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "batch_id": 115,
        "status": status,
        "candidate_manifest": str(candidate_manifest),
        "stages": stages,
        "strict_boundary_checks": strict_checks,
        "strict_boundary_pass": strict_boundary_pass,
        "outputs": {
            "hmlr_probe_manifest": str(probe_out / "lambeth_hmlr_exact_id_probe.json"),
            "hmlr_exact_boundaries": str(boundary_out),
        },
        "next_step_only_if_pass": "EA_DTM1M_AND_TERRAIN50_TQ26_TQ27_MEASUREMENT_CHAIN",
        "candidate_promotion_allowed": False,
        "numeric_publish_allowed": False,
        "nearest_fill_forbidden": True,
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "final_ready": False,
        "fake_data": False,
    }
    _write(execution_out, execution)
    print(json.dumps({"ok": strict_boundary_pass, "status": status, "execution": str(execution_out)}))
    return 0 if strict_boundary_pass else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
