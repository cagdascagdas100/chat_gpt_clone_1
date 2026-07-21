#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("019_verify_single_run_provenance.py")
spec = importlib.util.spec_from_file_location("provenance", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import provenance verifier")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.EXPECTED_ROWS = 4
module.EXPECTED_OFcom_FILES = 4
module.EXPECTED_OFcom_ROWS = 4
module.MIN_ZIP_BYTES = 4

passed: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    passed.append(name)


def expect_fail(name: str, fn, text: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if text not in str(exc):
            raise AssertionError(f"{name}: {exc}")
        passed.append(name)
    else:
        raise AssertionError(name)


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    work = root / "work"
    web = root / "web"
    canonical_source = root / "canonical.geojson"
    legacy_source = root / "legacy.geojson"
    canonical_slice = work / "slot_inputs/internet_access_2_canonical_slice_latest.geojson"
    legacy_slice = work / "slot_inputs/internet_access_2_legacy_slice_latest.geojson"
    extraction_manifest = work / "candidate_outputs/internet_access_2_extraction_manifest_latest.json"
    candidates = work / "candidate_outputs/internet_access_2_candidates_latest.jsonl"
    readback_path = web / "runner_readback_latest.json"
    examples_path = web / "verified_examples_latest.json"
    bundle_path = web / "runner_bundle_audit_latest.json"

    for path, text in (
        (canonical_source, '{"source":"canonical"}\n'),
        (legacy_source, '{"source":"legacy"}\n'),
        (canonical_slice, '{"slice":"canonical"}\n'),
        (legacy_slice, '{"slice":"legacy"}\n'),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    v2 = {
        "source": "Ofcom Connected Nations Spring 2026 fixed broadband coverage",
        "source_snapshot": "2026-01",
        "source_revision": "v2-r2",
        "source_revision_date": "2026-07-07",
        "status": "PASS_OFFICIAL_V2_R2_CORRECTION_AND_SEMANTICS_VALIDATED",
        "file_count": 4, "row_count": 4, "unique_postcode_count": 4,
        "actual_business_data_rows_written": 0, "final_ready": False,
    }
    dump(work / "internet_access_2_ofcom_v2_validation_latest.json", v2)

    slice_manifest = {
        "slot_id": "internet_access_2",
        "row_partition": {"start": 1, "end": 4, "expected": 4},
        "canonical": {
            "source_sha256": sha(canonical_source), "output_sha256": sha(canonical_slice),
            "rows": 4, "unique_row_numbers": 4, "unique_parcel_ids": 4,
        },
        "legacy_internet": {
            "source_sha256": sha(legacy_source), "output_sha256": sha(legacy_slice),
            "rows": 2, "unique_row_numbers": 2, "unique_parcel_ids": 2,
        },
        "actual_business_data_rows_written": 0, "scores_written": 0,
        "db_write": False, "migration": False, "production_deploy": False, "final_ready": False,
    }
    dump(work / "slot_inputs/internet_access_2_stream_slice_manifest_latest.json", slice_manifest)

    extraction = {
        "slot_id": "internet_access_2", "canonical_rows": 4,
        "direct_current_r2_matches": 2,
        "legacy_current_r2_matches_pending_spatial_qa": 1,
        "no_data_rows": 1,
        "canonical_source_sha256": sha(canonical_slice),
        "legacy_internet_source_sha256": sha(legacy_slice),
        "actual_business_data_rows_written": 0, "scores_written": 0,
        "db_write": False, "migration": False, "production_deploy": False, "final_ready": False,
    }
    dump(extraction_manifest, extraction)
    candidates.parent.mkdir(parents=True, exist_ok=True)
    candidates.write_text('{"row":1}\n{"row":2}\n{"row":3}\n{"row":4}\n', encoding="utf-8")

    counts = {
        "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW": 2,
        "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA": 1,
        "NO_DATA": 1,
    }
    readback = {
        "slot_id": "internet_access_2", "canonical_rows": 4,
        "status_counts": counts, "visible_example_rows": 3,
        "manifest_sha256": sha(extraction_manifest), "rows_jsonl_sha256": sha(candidates),
        "actual_business_data_rows_written": 0, "scores_written": 0,
        "db_write": False, "migration": False, "production_deploy": False, "final_ready": False,
    }
    dump(readback_path, readback)
    examples = {
        "slot_id": "internet_access_2",
        "rows": [{"canonical_row_no": 1}, {"canonical_row_no": 2}, {"canonical_row_no": 3}],
        "actual_business_data_rows_written": 0, "final_ready": False,
    }
    dump(examples_path, examples)
    bundle = {
        "slot_id": "internet_access_2", "canonical_rows": 4,
        "status_counts": counts, "visible_example_rows": 3,
        "runner_readback_file_sha256": sha(readback_path),
        "verified_examples_file_sha256": sha(examples_path),
        "source_manifest_sha256": sha(extraction_manifest),
        "source_rows_jsonl_sha256": sha(candidates),
        "actual_business_data_rows_written": 0, "scores_written": 0,
        "db_write": False, "migration": False, "production_deploy": False, "final_ready": False,
    }
    dump(bundle_path, bundle)
    diagnostics = {
        "slot_id": "internet_access_2", "state": "COMPLETE_REVIEW_OUTPUT_READY",
        "zip_sha256": "a" * 64, "zip_bytes": 4, "r1_file_count": 0, "r2_file_count": 4,
        "actual_business_data_rows_written": 0, "scores_written": 0,
        "db_write": False, "migration": False, "production_deploy": False, "final_ready": False,
    }
    dump(work / "internet_access_2_network_and_execution_diagnostics_latest.json", diagnostics)

    output = web / "runner_provenance_audit_latest.json"
    report = module.audit(work, web, output)
    check("valid_status", report["status"] == "PASS_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY")
    check("exact_rows", report["canonical_rows"] == 4)
    check("exact_ofcom_files", report["ofcom_r2_file_count"] == 4)
    check("exact_ofcom_rows", report["ofcom_postcode_rows"] == 4)
    check("status_counts", sum(report["status_counts"].values()) == 4)
    check("visible_examples", report["visible_example_rows"] == 3)
    check("chain_sha", len(report["provenance_chain_sha256"]) == 64)
    check("audit_written", output.is_file())
    check("no_business_write", report["actual_business_data_rows_written"] == 0)
    check("not_final", report["final_ready"] is False)

    bad_diag = dict(diagnostics); bad_diag["state"] = "BLOCKED_DNS"
    dump(work / "internet_access_2_network_and_execution_diagnostics_latest.json", bad_diag)
    expect_fail("incomplete_diagnostics_rejected", lambda: module.audit(work, web), "not terminal")
    dump(work / "internet_access_2_network_and_execution_diagnostics_latest.json", diagnostics)

    bad_slice = json.loads(json.dumps(slice_manifest))
    bad_slice["canonical"]["output_sha256"] = "b" * 64
    dump(work / "slot_inputs/internet_access_2_stream_slice_manifest_latest.json", bad_slice)
    expect_fail("canonical_chain_rejected", lambda: module.audit(work, web), "canonical slice/extraction")
    dump(work / "slot_inputs/internet_access_2_stream_slice_manifest_latest.json", slice_manifest)

    bad_extraction = dict(extraction); bad_extraction["no_data_rows"] = 2
    dump(extraction_manifest, bad_extraction)
    expect_fail("status_total_rejected", lambda: module.audit(work, web), "status counts")
    dump(extraction_manifest, extraction)

    bad_readback = dict(readback); bad_readback["manifest_sha256"] = "c" * 64
    dump(readback_path, bad_readback)
    expect_fail("manifest_hash_rejected", lambda: module.audit(work, web), "manifest/readback")
    dump(readback_path, readback)

    bad_bundle = dict(bundle); bad_bundle["runner_readback_file_sha256"] = "d" * 64
    dump(bundle_path, bad_bundle)
    expect_fail("readback_bundle_hash_rejected", lambda: module.audit(work, web), "readback/bundle-audit")
    dump(bundle_path, bundle)

    bad_examples = dict(examples); bad_examples["rows"] = examples["rows"][:2]
    dump(examples_path, bad_examples)
    bundle2 = dict(bundle); bundle2["verified_examples_file_sha256"] = sha(examples_path)
    dump(bundle_path, bundle2)
    expect_fail("visible_count_rejected", lambda: module.audit(work, web), "visible count")
    dump(examples_path, examples); dump(bundle_path, bundle)

    bad_v2 = dict(v2); bad_v2["unique_postcode_count"] = 3
    dump(work / "internet_access_2_ofcom_v2_validation_latest.json", bad_v2)
    expect_fail("v2_unique_count_rejected", lambda: module.audit(work, web), "postcode row/unique")
    dump(work / "internet_access_2_ofcom_v2_validation_latest.json", v2)

    bad_v2_revision = dict(v2); bad_v2_revision["source_revision_date"] = "2026-07-06"
    dump(work / "internet_access_2_ofcom_v2_validation_latest.json", bad_v2_revision)
    expect_fail("v2_revision_rejected", lambda: module.audit(work, web), "source identity/revision")
    dump(work / "internet_access_2_ofcom_v2_validation_latest.json", v2)

    bad_diag = dict(diagnostics); bad_diag["zip_sha256"] = "UPPER"
    dump(work / "internet_access_2_network_and_execution_diagnostics_latest.json", bad_diag)
    expect_fail("zip_hash_format_rejected", lambda: module.audit(work, web), "not a lowercase SHA-256")
    dump(work / "internet_access_2_network_and_execution_diagnostics_latest.json", diagnostics)

    bad_bundle = dict(bundle); bad_bundle["actual_business_data_rows_written"] = 1
    dump(bundle_path, bad_bundle)
    expect_fail("business_write_rejected", lambda: module.audit(work, web), "business rows")
    dump(bundle_path, bundle)

print(json.dumps({
    "status": "PASS",
    "tests_passed": len(passed),
    "tests_total": 20,
    "test_names": passed,
    "actual_business_data_rows_written": 0,
    "final_ready": False,
}, sort_keys=True))
