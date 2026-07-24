#!/usr/bin/env python3
"""Run existing pipeline 015 and then fail-closed runtime bundle validation 019."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
SLOT_ID = "internet_access_3"
AUTOMATION_RELATIVE = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/automation")
PIPELINE = "015_materialize_exact_blobs_and_run_targeted_slot3.py"
VALIDATOR = "019_runtime_bundle_gate.py"
def build_pipeline_command(args: argparse.Namespace, repo_root: Path, work_root: Path) -> list[str]:
    command = [sys.executable,str(repo_root / AUTOMATION_RELATIVE / PIPELINE),"--repo-root",str(repo_root),"--git-ref",args.git_ref,"--work-root",str(work_root),"--download-retries",str(args.download_retries),"--download-timeout-seconds",str(args.download_timeout_seconds)]
    if args.ofcom_zip: command.extend(["--ofcom-zip", str(args.ofcom_zip.resolve())])
    if args.ofcom_url: command.extend(["--ofcom-url", args.ofcom_url])
    return command
def build_validation_command(repo_root: Path, work_root: Path) -> list[str]:
    return [sys.executable,str(repo_root / AUTOMATION_RELATIVE / VALIDATOR),"--candidate-manifest",str(work_root / "candidate_outputs/internet_access_3_candidate_manifest_latest.json"),"--candidates-jsonl",str(work_root / "candidate_outputs/internet_access_3_candidates_latest.jsonl"),"--slice-manifest",str(work_root / "slot_inputs/internet_access_3_stream_slice_manifest_latest.json"),"--output",str(work_root / "internet_access_3_runtime_bundle_validation_latest.json")]
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", required=True, type=Path); parser.add_argument("--work-root", type=Path); parser.add_argument("--git-ref", default="HEAD"); parser.add_argument("--ofcom-zip", type=Path); parser.add_argument("--ofcom-url"); parser.add_argument("--download-retries", type=int, default=4); parser.add_argument("--download-timeout-seconds", type=int, default=600); parser.add_argument("--validate-existing-only", action="store_true"); return parser.parse_args()
def main() -> int:
    args = parse_args(); repo_root = args.repo_root.resolve(); work_root = (args.work_root or (repo_root / "outputs/internet_access_3_verified_run")).resolve(); output_path = work_root / "internet_access_3_validated_runner_bundle_latest.json"
    state: dict[str, Any] = {"schema_version":1,"slot_id":SLOT_ID,"started_at":datetime.now(timezone.utc).isoformat(),"validate_existing_only":args.validate_existing_only,"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    work_root.mkdir(parents=True, exist_ok=True)
    try:
        for name in (PIPELINE, VALIDATOR):
            path = repo_root / AUTOMATION_RELATIVE / name
            if not path.is_file(): raise RuntimeError(f"required automation missing: {path}")
        if not args.validate_existing_only:
            pipeline_command = build_pipeline_command(args, repo_root, work_root); state["pipeline_command"] = pipeline_command; pipeline = subprocess.run(pipeline_command, capture_output=True, text=True, check=False); state["pipeline_returncode"] = pipeline.returncode; state["pipeline_stdout_tail"] = pipeline.stdout[-8000:]; state["pipeline_stderr_tail"] = pipeline.stderr[-8000:]
            if pipeline.returncode != 0: raise RuntimeError(f"pipeline 015 blocked with return code {pipeline.returncode}")
        else: state["pipeline_state"] = "SKIPPED_VALIDATE_EXISTING_ONLY"
        validation_command = build_validation_command(repo_root, work_root); state["validation_command"] = validation_command; validation = subprocess.run(validation_command, capture_output=True, text=True, check=False); state["validation_returncode"] = validation.returncode; state["validation_stdout_tail"] = validation.stdout[-8000:]; state["validation_stderr_tail"] = validation.stderr[-8000:]
        if validation.returncode != 0: raise RuntimeError(f"runtime bundle validation blocked with return code {validation.returncode}")
        validation_path = work_root / "internet_access_3_runtime_bundle_validation_latest.json"; value = json.loads(validation_path.read_text(encoding="utf-8"))
        if value.get("state") != "PASS_VALIDATED_RUNTIME_BUNDLE_REVIEW_ONLY": raise RuntimeError("runtime validation state mismatch")
        state["state"] = "COMPLETE_RUNTIME_BUNDLE_VALIDATED_REVIEW_ONLY"; state["counts"] = value["counts"]; state["hashes"] = value["hashes"]; state["samples"] = value.get("samples", []); output_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"); print(json.dumps({k:v for k,v in state.items() if not k.endswith("_tail")}, sort_keys=True)); return 0
    except Exception as exc:
        state["state"] = "BLOCKED_RUNTIME_BUNDLE_WRAPPER_GATE"; state["error"] = f"{type(exc).__name__}: {exc}"; output_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"); print(state["error"], file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
