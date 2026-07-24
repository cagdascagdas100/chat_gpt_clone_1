#!/usr/bin/env python3
"""Static contract tests for the revision 8 single-runner pipeline."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

SLOT_ID = "internet_access_3"
EXPECTED_SCRIPTS = [
    "007_worker_contract_tests.py", "009_hmlr_geometry_contract_tests.py", "011_revision6_contract_tests.py",
    "015_corrected_migration_contract_tests.py", "019_revision7_pipeline_manifest_tests.py",
    "021_ons_uprn_arcgis_release_discovery_tests.py", "023_stratified_candidate_sampler_tests.py",
    "026_exact_manifest_binding_tests.py", "028_revision8_pipeline_manifest_tests.py",
    "012_official_source_access_preflight.py", "016_official_uprn_relation_preflight.py",
    "020_ons_uprn_arcgis_release_discovery.py", "014_migrate_existing_semantics_corrected.py",
    "022_stratified_candidate_sampler.py", "018_prepared_candidate_preview.py",
    "006_normalize_legacy_unable30_semantics.py", "004_ofcom_2026_full_schema_audit.py",
    "024_stratified_ofcom_onspd_adapter.py", "025_hmlr_exact_stratified_manifest_audit.py"
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/023_revision8_pipeline_manifest_tests_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "docs").exists() and (item / "england_map_web").exists():
            return item
    raise FileNotFoundError("repository root not found")


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    args = parse_args()
    repo = root(args.repo_root)
    pipeline = Path(__file__).resolve().parent / "027_full_pipeline_revision8_entry.py"
    source = pipeline.read_text(encoding="utf-8")
    tests: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        tests.append({"name": name, "passed": bool(condition), "detail": detail})

    missing_refs = [name for name in EXPECTED_SCRIPTS if name not in source]
    missing_files = [name for name in EXPECTED_SCRIPTS if not (pipeline.parent / name).exists()]
    check("ALL_WORKER_REFERENCES_PRESENT", not missing_refs, repr(missing_refs))
    check("ALL_WORKER_FILES_EXIST", not missing_files, repr(missing_files))
    check("SAMPLE_SIZE_384", "SAMPLE_SIZE = 384" in source, "sample target")
    check("TEST_TARGET_84", "CONTRACT_TESTS = 84" in source, "declared test count")
    check("SOURCE_CHECK_TARGET_13", "SOURCE_CHECKS = 13" in source, "source checks")
    check("OFcom_ONSPD_95_PERCENT_GATES", source.count('"--minimum-match-ratio", "0.95"') == 2, "two 95 percent gates")
    check("HMLR_90_PERCENT_GATE", '"--minimum-match-ratio", "0.90"' in source, "HMLR gate")
    check("PREVIEW_AND_TARGET_24", '"--preview-size", "24"' in source and '"transparent_target_rows_published": 24' in source, "24 examples")
    check("EXACT_STRATIFIED_ADAPTERS_USED", source.count("024_stratified_ofcom_onspd_adapter.py") == 2 and "025_hmlr_exact_stratified_manifest_audit.py" in source, "exact manifest adapters")
    check("SAFETY_FLAGS_PRESENT", all(token in source for token in ['"fake_data": False', '"db_write": False', '"migration": False', '"production_deploy": False', '"final_ready": False']), "safety flags")
    failures = [item for item in tests if not item["passed"]]
    summary = {"schema_version": 1, "slot_id": SLOT_ID, "state": "passed" if not failures else "failed", "tests_expected": 10, "tests_executed": len(tests), "tests_passed": len(tests) - len(failures), "tests_failed": len(failures), "tests": tests, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    atomic_json(repo / args.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
