from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).resolve().parent / "security_public_safety_2_acceptance_v3.py"


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("security_slot2_acceptance_v3", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("ACCEPTANCE_V3_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_payload(module: Any) -> dict[str, Any]:
    rows = []
    for number in range(module.START, module.END + 1):
        rows.append({
            "parcel_id": f"parcel_{number}",
            "candidate_status": "CANONICAL_API_IOD25_V2_MPS_LSOA_VERIFIED",
            "accuracy_score_4": 4,
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
            "official_api_http_status": 200,
            "official_api_sha256": "a" * 64,
            "iod25_v2_join_pass": True,
            "iod25_crime_score": "0.25",
            "mps_lsoa_join_pass": True,
        })
    return {
        "slot_id": module.SLOT_ID,
        "final_ready": False,
        "fake_data": False,
        "actual_business_rows_written": 0,
        "output_semantics": "AREA_LEVEL_PROXY",
        "canonical_rows": module.EXPECTED_ROWS,
        "canonical_guard": {
            "pass": True,
            "observed_blob_sha": module.REQUIRED_BLOB_SHA,
        },
        "artifacts": {"parity_pass": True},
        "rows": rows,
    }


def run() -> dict[str, Any]:
    module = load_module()
    html = (
        f'<body data-slot-id="{module.SLOT_ID}" '
        'data-visible-row-count="300" data-final-ready="false">'
        '<table><tbody></tbody></table></body>'
    )
    base = valid_payload(module)
    cases = []

    positive = module.validate_payload(base, html)
    cases.append({"name": "positive_fixture_all_invariants", "pass": all(positive.values())})

    mutations = [
        ("wrong_slot_rejected", lambda p: p.__setitem__("slot_id", "wrong_slot"), "payload_slot_id_exact"),
        ("fake_data_rejected", lambda p: p.__setitem__("fake_data", True), "payload_fake_data_false"),
        ("business_write_rejected", lambda p: p.__setitem__("actual_business_rows_written", 1), "payload_business_rows_zero"),
        ("canonical_299_rejected", lambda p: p.__setitem__("canonical_rows", 299), "payload_canonical_rows_300"),
        ("duplicate_id_rejected", lambda p: p["rows"][1].__setitem__("parcel_id", p["rows"][0]["parcel_id"]), "payload_unique_parcel_ids_300"),
        ("non_contiguous_range_rejected", lambda p: p["rows"][0].__setitem__("parcel_id", "parcel_99999"), "payload_exact_contiguous_id_range"),
        ("missing_canonical_rejected", lambda p: p["rows"][0].__setitem__("candidate_status", "CANONICAL_FEATURE_NOT_FOUND"), "payload_no_missing_canonical_status"),
        ("parcel_measurement_rejected", lambda p: p["rows"][0].__setitem__("parcel_measurement", True), "payload_no_parcel_measurement"),
        ("wrong_blob_rejected", lambda p: p["canonical_guard"].__setitem__("observed_blob_sha", "0" * 40), "payload_exact_blob_verified"),
        ("accuracy3_without_api_rejected", lambda p: (p["rows"][0].__setitem__("accuracy_score_4", 3), p["rows"][0].__setitem__("official_api_http_status", None)), "payload_accuracy_ge_3_has_api_sha"),
        ("accuracy4_without_iod_rejected", lambda p: (p["rows"][0].__setitem__("iod25_v2_join_pass", False), p["rows"][0].__setitem__("iod25_crime_score", None)), "payload_accuracy_4_has_all_evidence"),
        ("accuracy4_without_mps_rejected", lambda p: p["rows"][0].__setitem__("mps_lsoa_join_pass", False), "payload_accuracy_4_has_all_evidence"),
        ("html_wrong_row_count_rejected", None, "html_visible_rows_300"),
    ]
    for name, mutate, expected_false in mutations:
        payload = copy.deepcopy(base)
        candidate_html = html
        if mutate is not None:
            mutate(payload)
        else:
            candidate_html = html.replace('data-visible-row-count="300"', 'data-visible-row-count="299"')
        checks = module.validate_payload(payload, candidate_html)
        cases.append({
            "name": name,
            "expected_false_check": expected_false,
            "pass": checks.get(expected_false) is False,
        })

    passed = sum(case["pass"] for case in cases)
    return {
        "schema_version": 1,
        "slot_id": module.SLOT_ID,
        "test_type": "ACCEPTANCE_V3_NEGATIVE_INVARIANT_MATRIX",
        "cases": cases,
        "passed": passed,
        "total": len(cases),
        "pass": passed == len(cases),
        "synthetic_fixture_is_business_data": False,
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
