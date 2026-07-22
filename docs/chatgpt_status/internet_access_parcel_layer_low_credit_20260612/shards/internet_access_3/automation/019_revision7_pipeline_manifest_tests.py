#!/usr/bin/env python3
"""Static manifest tests for the revision 7 single-runner pipeline."""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path

SLOT_ID = "internet_access_3"
EXPECTED_SCRIPTS = [
    "007_worker_contract_tests.py",
    "009_hmlr_geometry_contract_tests.py",
    "011_revision6_contract_tests.py",
    "015_corrected_migration_contract_tests.py",
    "012_official_source_access_preflight.py",
    "016_official_uprn_relation_preflight.py",
    "014_migrate_existing_semantics_corrected.py",
    "018_prepared_candidate_preview.py",
    "006_normalize_legacy_unable30_semantics.py",
    "004_ofcom_2026_full_schema_audit.py",
    "002_ofcom_2026_sample_revalidation.py",
    "005_onspd_2026_centroid_crosscheck.py",
    "010_hmlr_revision6_guarded_entry.py",
]


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/014_revision7_pipeline_manifest_tests_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "england_map_web").exists() and (item / "docs").exists():
            return item
    raise FileNotFoundError("repository root not found")


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parsed = args()
    repo = root(parsed.repo_root)
    automation = Path(__file__).resolve().parent
    pipeline = automation / "017_full_pipeline_revision7_entry.py"
    text = pipeline.read_text(encoding="utf-8")
    tests = []

    def check(name: str, condition: bool, detail: str) -> None:
        tests.append({"name": name, "passed": bool(condition), "detail": detail})

    missing = [name for name in EXPECTED_SCRIPTS if not (automation / name).exists()]
    check("ALL_REFERENCED_WORKERS_EXIST", not missing, str(missing))
    absent_from_plan = [name for name in EXPECTED_SCRIPTS if name not in text]
    check("ALL_WORKERS_REFERENCED_BY_PIPELINE", not absent_from_plan, str(absent_from_plan))
    check("SAMPLE_SIZE_320", "SAMPLE_SIZE = 320" in text, "320 target")
    check("CONTRACT_TEST_TARGET_42", "CONTRACT_TESTS = 42" in text, "6+8+12+8+8")
    check("SOURCE_PREFLIGHT_TARGET_11", "SOURCE_PREFLIGHTS = 11" in text, "5+6")
    check("HMLR_RATIO_90_PERCENT", '"--minimum-match-ratio", "0.90"' in text and '"hmlr_minimum_matches_required": 288' in text, "90 percent of 320")
    check("NO_PARALLEL_RUNNER_LANGUAGE", "parallel" not in text.lower() and "new_runner" not in text.lower(), "single sequential subprocess chain")
    check("SAFETY_FLAGS_FALSE", all(token in text for token in ['"final_ready": False', '"fake_data": False', '"db_write": False', '"migration": False', '"production_deploy": False']), "safety contract")

    failures = [item for item in tests if not item["passed"]]
    summary = {"schema_version": 1, "slot_id": SLOT_ID, "state": "passed" if not failures else "failed", "tests_expected": 8, "tests_executed": len(tests), "tests_passed": len(tests) - len(failures), "tests_failed": len(failures), "tests": tests, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    atomic_json(repo / parsed.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
