from __future__ import annotations

import argparse
import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check(condition: bool, name: str, detail: str, results: list[dict[str, Any]]) -> None:
    results.append({"name": name, "pass": bool(condition), "detail": detail})


def run(repo: Path) -> dict[str, Any]:
    root = repo / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_2/automation"
    pipeline_path = root / "gas_emissions_2_runtime_pipeline.py"
    carrier_path = root / "gas_emissions_2_runtime_pipeline_v5_1.ps1"
    results: list[dict[str, Any]] = []

    check(pipeline_path.is_file(), "pipeline_exists", str(pipeline_path), results)
    check(carrier_path.is_file(), "carrier_exists", str(carrier_path), results)
    pipeline = pipeline_path.read_text(encoding="utf-8") if pipeline_path.is_file() else ""
    carrier = carrier_path.read_text(encoding="utf-8") if carrier_path.is_file() else ""

    try:
        ast.parse(pipeline)
        syntax_ok = True
        syntax_detail = "ast.parse PASS"
    except Exception as exc:
        syntax_ok = False
        syntax_detail = f"{type(exc).__name__}:{exc}"
    check(syntax_ok, "python_syntax", syntax_detail, results)

    required_python_tokens = [
        'SLOT_ID = "gas_emissions_2"',
        'TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"',
        "LOCAL_RUNTIME_PASS_AWAITING_PUBLISHER_COMMIT_READBACK",
        "completion_forbidden_without_remote_commit_readback",
        "window.__gasEmissions2RuntimeEvidenceReady === true",
        "window.__gasEmissions2RuntimeEvidence",
        '"remote_readback": "0"',
        '"browser_acceptance_after": 66',
        '"final_ready": False',
        '"fake_data": False',
        '"db_write": False',
        '"migration": False',
        '"production_deploy": False',
    ]
    for token in required_python_tokens:
        check(token in pipeline, "pipeline_token", token, results)

    required_ps_tokens = [
        "SLOT_ID=$expectedSlot",
        "SINGLE_SHARED_RUNNER_ONLY=true",
        "NEW_RUNNER=false",
        "PARALLEL_RUNNER=false",
        "DIRECT_PUSH=false",
        "DB_WRITE=false",
        "MIGRATION=false",
        "PRODUCTION_DEPLOY=false",
        "FINAL_READY=false",
        "--slot-id $expectedSlot",
        "--target-branch $expectedBranch",
    ]
    for token in required_ps_tokens:
        check(token in carrier, "carrier_token", token, results)

    check("git push" not in pipeline.lower() and "git push" not in carrier.lower(), "no_direct_push_command", "git push absent", results)
    check("..\\..\\..\\..\\..\\.." in carrier, "repo_root_fallback_six_levels", "six parent traversals to repository root", results)
    check("new runner" not in pipeline.lower(), "no_new_runner_instruction", "no new runner text", results)
    check(re.search(r"EXPECTED_CHECKS\s*=\s*21", pipeline) is not None, "expected_checks_21", "EXPECTED_CHECKS=21", results)
    check(re.search(r"EXPECTED_METADATA_LOCAL\s*=\s*8", pipeline) is not None, "expected_local_metadata_8", "EXPECTED_METADATA_LOCAL=8", results)
    check(re.search(r"EXPECTED_METADATA_FINAL\s*=\s*9", pipeline) is not None, "expected_final_metadata_9", "EXPECTED_METADATA_FINAL=9", results)

    passed = sum(1 for item in results if item["pass"])
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "validation_scope": "LOCAL_STATIC_CARRIER_SELFTEST",
        "checks": results,
        "passed": passed,
        "total": len(results),
        "all_checks_pass": passed == len(results),
        "runtime_executed": False,
        "browser_acceptance_changed": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    payload = run(Path(args.repo_root).resolve())
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"slot_id": SLOT_ID, "passed": payload["passed"], "total": payload["total"], "all_checks_pass": payload["all_checks_pass"], "final_ready": False}))
    raise SystemExit(0 if payload["all_checks_pass"] else 1)
