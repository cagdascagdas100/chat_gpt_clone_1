#!/usr/bin/env python3
"""Single-runner entrypoint for internet_access_3 migration and official-source validation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SLOT_ID = "internet_access_3"
TASK_ID = "aays1-internet-access-3-migrate-schema-audit-and-ofcom-2026-samples-20260722"
SAMPLE_SIZE = 48


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
        "schema_version": 2,
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


def main() -> int:
    repo_root = find_repo_root()
    automation_root = Path(__file__).resolve().parent
    steps: list[dict[str, object]] = []

    migration = run_step(
        repo_root,
        automation_root / "001_migrate_existing_and_close_no_data.py",
        "MIGRATE_EXISTING_ROWS_AND_CLOSE_NO_DATA",
    )
    steps.append(migration)
    if int(migration["exit_code"]) != 0:
        return blocked_summary(
            "migration_blocked",
            steps,
            int(migration["exit_code"]),
            "REPAIR_MIGRATION_VALIDATION_BLOCKERS",
        )

    schema_audit = run_step(
        repo_root,
        automation_root / "004_ofcom_2026_full_schema_audit.py",
        "OFcom_2026_ALL_121_POSTCODE_FILES_SCHEMA_AND_ROW_AUDIT",
    )
    steps.append(schema_audit)
    if int(schema_audit["exit_code"]) != 0:
        return blocked_summary(
            "official_schema_audit_blocked",
            steps,
            int(schema_audit["exit_code"]),
            "REPAIR_OFFICIAL_ARCHIVE_MEMBER_HEADER_OR_ROW_COUNT_BLOCKER",
        )

    revalidation = run_step(
        repo_root,
        automation_root / "002_ofcom_2026_sample_revalidation.py",
        "OFcom_2026_EXACT_POSTCODE_48_ROW_SAMPLE_REVALIDATION",
        ["--sample-size", str(SAMPLE_SIZE)],
    )
    steps.append(revalidation)

    summary = {
        "schema_version": 2,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "state": "pipeline_passed" if int(revalidation["exit_code"]) == 0 else "sample_revalidation_blocked",
        "steps": steps,
        "sample_size_target": SAMPLE_SIZE,
        "official_postcode_member_count_target": 121,
        "official_postcode_total_rows_target": 1_741_096,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": (
            "INDEPENDENTLY_VALIDATE_PARCEL_TO_POSTCODE_RELATIONS_THEN_EXPAND_OFFICIAL_SAMPLE"
            if int(revalidation["exit_code"]) == 0
            else "REPAIR_OFFICIAL_SOURCE_DOWNLOAD_OR_SAMPLE_SCHEMA_BLOCKER"
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return int(revalidation["exit_code"])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {
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
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        raise
