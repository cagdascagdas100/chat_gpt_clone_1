#!/usr/bin/env python3
"""Single-runner entrypoint for internet_access_3 migration plus official Ofcom sample revalidation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SLOT_ID = "internet_access_3"
TASK_ID = "aays1-internet-access-3-migrate-and-ofcom-2026-samples-20260722"


def find_repo_root() -> Path:
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found")


def run_step(repo_root: Path, script: Path, name: str) -> dict[str, object]:
    command = [sys.executable, str(script), "--repo-root", str(repo_root)]
    completed = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    result: dict[str, object] = {
        "name": name,
        "script": str(script.relative_to(repo_root)),
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-12000:],
        "stderr_tail": completed.stderr[-12000:],
    }
    return result


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
        summary = {
            "schema_version": 1,
            "task_id": TASK_ID,
            "slot_id": SLOT_ID,
            "state": "migration_blocked",
            "steps": steps,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return int(migration["exit_code"])

    revalidation = run_step(
        repo_root,
        automation_root / "002_ofcom_2026_sample_revalidation.py",
        "OFcom_2026_EXACT_POSTCODE_SAMPLE_REVALIDATION",
    )
    steps.append(revalidation)

    summary = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "state": "pipeline_passed" if int(revalidation["exit_code"]) == 0 else "sample_revalidation_blocked",
        "steps": steps,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": (
            "EXPAND_EXACT_POSTCODE_REVALIDATION_THEN_INDEPENDENTLY_VALIDATE_PARCEL_POSTCODE_RELATIONS"
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
