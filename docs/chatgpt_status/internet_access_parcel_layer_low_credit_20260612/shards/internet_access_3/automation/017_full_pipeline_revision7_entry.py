#!/usr/bin/env python3
"""Fourteen-step single-runner pipeline for internet_access_3 revision 7."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SLOT_ID = "internet_access_3"
TASK_ID = "aays1-internet-access-3-revision7-uprn-relation-gates-20260722"
SAMPLE_SIZE = 320
CONTRACT_TESTS = 42
SOURCE_PREFLIGHTS = 11


def root() -> Path:
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "england_map_web").exists() and (item / "docs").exists():
            return item
    raise FileNotFoundError("repository root not found")


def run(repo: Path, script: Path, name: str, extra: list[str] | None = None) -> dict:
    command = [sys.executable, str(script), "--repo-root", str(repo), *(extra or [])]
    completed = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
    return {"name": name, "script": str(script.relative_to(repo)), "command": command, "exit_code": completed.returncode, "stdout_tail": completed.stdout[-12000:], "stderr_tail": completed.stderr[-12000:]}


def blocked(state: str, steps: list[dict], next_step: str) -> int:
    exit_code = int(steps[-1]["exit_code"])
    print(json.dumps({"schema_version": 3, "task_id": TASK_ID, "slot_id": SLOT_ID, "state": state, "steps": steps, "sample_size_target": SAMPLE_SIZE, "contract_tests_target": CONTRACT_TESTS, "official_sources_preflight_target": SOURCE_PREFLIGHTS, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "first_unverified_step_after_run": next_step}, ensure_ascii=False, indent=2))
    return exit_code


def main() -> int:
    repo = root()
    automation = Path(__file__).resolve().parent
    plan = [
        ("019_revision7_pipeline_manifest_tests.py", "REVISION7_PIPELINE_MANIFEST_TESTS_8", [], "revision7_manifest_tests_blocked", "REPAIR_REVISION7_PIPELINE_MANIFEST"),
        ("007_worker_contract_tests.py", "BASE_WORKER_CONTRACT_TESTS_6", [], "base_tests_blocked", "REPAIR_BASE_WORKER_TESTS"),
        ("009_hmlr_geometry_contract_tests.py", "HMLR_GEOMETRY_CONTRACT_TESTS_8", [], "hmlr_geometry_tests_blocked", "REPAIR_HMLR_GEOMETRY_TESTS"),
        ("011_revision6_contract_tests.py", "REVISION6_GUARD_CONTRACT_TESTS_12", [], "revision6_tests_blocked", "REPAIR_REVISION6_GUARDS"),
        ("015_corrected_migration_contract_tests.py", "CORRECTED_MIGRATION_CONTRACT_TESTS_8", [], "migration_semantic_tests_blocked", "REPAIR_CORRECTED_MIGRATION_SEMANTICS"),
        ("012_official_source_access_preflight.py", "BASE_OFFICIAL_SOURCE_ACCESS_PREFLIGHT_5", [], "base_source_preflight_blocked", "REPAIR_BASE_OFFICIAL_SOURCE_ACCESS"),
        ("016_official_uprn_relation_preflight.py", "OFFICIAL_UPRN_RELATION_PREFLIGHT_6", [], "uprn_relation_preflight_blocked", "REPAIR_UPRN_PRODUCT_PORTAL_LICENCE_OR_HMLR_ACCESS"),
        ("014_migrate_existing_semantics_corrected.py", "MIGRATE_EXISTING_ROWS_WITH_CORRECT_UNABLE30_SEMANTICS", [], "migration_blocked", "REPAIR_MIGRATION_VALIDATION_OR_SEMANTIC_CONFLICTS"),
        ("018_prepared_candidate_preview.py", "PUBLISH_16_PREPARED_CANDIDATE_PREVIEW_ROWS", ["--preview-size", "16"], "candidate_preview_blocked", "REPAIR_PREVIEW_ELIGIBLE_PROXY_ROWS"),
        ("006_normalize_legacy_unable30_semantics.py", "IDEMPOTENT_UNABLE30_SEMANTIC_SAFETY_NET", [], "semantic_safety_net_blocked", "REPAIR_UNABLE30_SEMANTIC_CONFLICTS"),
        ("004_ofcom_2026_full_schema_audit.py", "OFcom_ALL_121_FILES_FULL_AUDIT", [], "ofcom_full_audit_blocked", "REPAIR_OFcom_ARCHIVE_SCHEMA_OR_ROW_COUNT"),
        ("002_ofcom_2026_sample_revalidation.py", "OFcom_320_EXACT_POSTCODE_SAMPLE", ["--sample-size", str(SAMPLE_SIZE)], "ofcom_sample_blocked", "REPAIR_OFcom_SAMPLE_MATCHES"),
        ("005_onspd_2026_centroid_crosscheck.py", "ONSPD_320_EXACT_POSTCODE_CENTROID_CROSSCHECK", ["--sample-size", str(SAMPLE_SIZE)], "onspd_blocked", "REPAIR_ONSPD_SERVICE_OR_MATCHES"),
        ("010_hmlr_revision6_guarded_entry.py", "HMLR_320_GUARDED_POLYGON_CROSSCHECK_90_PERCENT", ["--sample-size", str(SAMPLE_SIZE), "--max-authorities", "12", "--minimum-match-ratio", "0.90"], "hmlr_guard_blocked", "REPAIR_HMLR_LINKS_HYDRATION_OR_90_PERCENT_MATCH_RATIO"),
    ]
    steps: list[dict] = []
    for filename, name, extra, state, next_step in plan:
        result = run(repo, automation / filename, name, extra)
        steps.append(result)
        if int(result["exit_code"]) != 0:
            return blocked(state, steps, next_step)
    summary = {"schema_version": 3, "task_id": TASK_ID, "slot_id": SLOT_ID, "state": "pipeline_passed", "steps": steps, "sample_size_target": SAMPLE_SIZE, "prepared_candidate_preview_target": 16, "contract_tests_target": CONTRACT_TESTS, "official_sources_preflight_target": SOURCE_PREFLIGHTS, "ofcom_member_count_target": 121, "ofcom_total_rows_target": 1741096, "hmlr_minimum_match_ratio": 0.90, "hmlr_minimum_matches_required": 288, "parcel_relations_promoted": 0, "confidence_uplifts": 0, "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "first_unverified_step_after_run": "HYDRATE_CURRENT_OS_OPEN_UPRN_AND_ONSUD_OR_NSUL_RELEASES_THEN_REQUIRE_EXACT_UPRN_POSTCODE_RELATION"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"task_id": TASK_ID, "slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
