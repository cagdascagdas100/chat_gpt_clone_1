#!/usr/bin/env python3
"""Single-runner entrypoint for internet_access_3 migration and official-source validation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SLOT_ID = "internet_access_3"
TASK_ID = "aays1-internet-access-3-migrate-ofcom-onspd-validation-20260722"
SAMPLE_SIZE = 96


def find_repo_root() -> Path:
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found")


def run_step(repo_root: Path, script: Path, name: str, extra_args: list[str] | None = None) -> dict[str, object]:
    command = [sys.executable, str(script), "--repo-root", str(repo_root), *(extra_args or [])]
    completed = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "name": name,
        "script": str(script.relative_to(repo_root)),
        "command": command,
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-12000:],
        "stderr_tail": completed.stderr[-12000:],
    }


def blocked_summary(state: str, steps: list[dict[str, object]], exit_code: int, next_step: str) -> int:
    summary = {
        "schema_version": 3,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "state": state,
        "steps": steps,
        "sample_size_target": SAMPLE_SIZE,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": next_step,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return exit_code


def run_required(
    repo_root: Path,
    automation_root: Path,
    steps: list[dict[str, object]],
    filename: str,
    name: str,
    blocked_state: str,
    next_step: str,
    extra_args: list[str] | None = None,
) -> int | None:
    result = run_step(repo_root, automation_root / filename, name, extra_args)
    steps.append(result)
    exit_code = int(result["exit_code"])
    if exit_code != 0:
        return blocked_summary(blocked_state, steps, exit_code, next_step)
    return None


def main() -> int:
    repo_root = find_repo_root()
    automation_root = Path(__file__).resolve().parent
    steps: list[dict[str, object]] = []

    required_steps = [
        (
            "007_worker_contract_tests.py",
            "WORKER_CONTRACT_TESTS",
            "worker_contract_tests_blocked",
            "REPAIR_WORKER_CONTRACT_TEST_FAILURES",
            None,
        ),
        (
            "001_migrate_existing_and_close_no_data.py",
            "MIGRATE_EXISTING_ROWS_AND_CLOSE_NO_DATA",
            "migration_blocked",
            "REPAIR_MIGRATION_VALIDATION_BLOCKERS",
            None,
        ),
        (
            "006_normalize_legacy_unable30_semantics.py",
            "NORMALIZE_LEGACY_UNABLE30_SEMANTICS",
            "legacy_semantic_normalization_blocked",
            "REPAIR_LEGACY_UNABLE30_SEMANTIC_CONFLICTS",
            None,
        ),
        (
            "004_ofcom_2026_full_schema_audit.py",
            "OFcom_2026_ALL_121_POSTCODE_FILES_SCHEMA_AND_ROW_AUDIT",
            "official_schema_audit_blocked",
            "REPAIR_OFFICIAL_ARCHIVE_MEMBER_HEADER_OR_ROW_COUNT_BLOCKER",
            None,
        ),
        (
            "002_ofcom_2026_sample_revalidation.py",
            "OFcom_2026_EXACT_POSTCODE_96_ROW_SAMPLE_REVALIDATION",
            "sample_revalidation_blocked",
            "REPAIR_OFFICIAL_SOURCE_DOWNLOAD_OR_SAMPLE_SCHEMA_BLOCKER",
            ["--sample-size", str(SAMPLE_SIZE)],
        ),
        (
            "005_onspd_2026_centroid_crosscheck.py",
            "ONSPD_MAY_2026_EXACT_POSTCODE_AND_CENTROID_96_ROW_CROSSCHECK",
            "onspd_centroid_crosscheck_blocked",
            "REPAIR_ONSPD_SERVICE_SCHEMA_OR_QUERY_BLOCKER",
            ["--sample-size", str(SAMPLE_SIZE)],
        ),
    ]

    for filename, name, state, next_step, extra_args in required_steps:
        blocked = run_required(
            repo_root, automation_root, steps, filename, name, state, next_step, extra_args
        )
        if blocked is not None:
            return blocked

    summary = {
        "schema_version": 3,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "state": "pipeline_passed",
        "steps": steps,
        "sample_size_target": SAMPLE_SIZE,
        "official_postcode_member_count_target": 121,
        "official_postcode_total_rows_target": 1_741_096,
        "onspd_snapshot": "2026-05",
        "parcel_relations_promoted": 0,
        "confidence_uplifts": 0,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": (
            "ESTABLISH_INDEPENDENT_PARCEL_TO_UPRN_OR_ADDRESS_RELATION_OR_RETAIN_POSTCODE_PROXY"
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({
            "task_id": TASK_ID,
            "slot_id": SLOT_ID,
            "state": "exception",
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
