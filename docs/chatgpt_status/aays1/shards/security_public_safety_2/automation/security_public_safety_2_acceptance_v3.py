from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
START = 30762
END = 31061
EXPECTED_ROWS = 300
REQUIRED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
BASE_PATH = Path(__file__).resolve().parent / "security_public_safety_2_acceptance_v2.py"


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("security_slot2_acceptance_v2", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"BASE_ACCEPTANCE_IMPORT_FAILED:{BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def validate_payload(payload: dict[str, Any], html_text: str) -> dict[str, bool]:
    rows = payload.get("rows") or []
    guard = payload.get("canonical_guard") or {}
    exact_blob = guard.get("pass") is True and guard.get("observed_blob_sha") == REQUIRED_BLOB_SHA
    expected_ids = [f"parcel_{number}" for number in range(START, END + 1)]
    observed_ids = [str(row.get("parcel_id") or "") for row in rows]

    accuracy_4_evidence = True
    accuracy_ge_3_api = True
    for row in rows:
        score = _as_int(row.get("accuracy_score_4"))
        api_ok = row.get("official_api_http_status") == 200 and bool(row.get("official_api_sha256"))
        iod_ok = row.get("iod25_v2_join_pass") is True or row.get("iod25_crime_score") not in (None, "")
        mps_ok = row.get("mps_lsoa_join_pass") is True
        if score >= 3 and not api_ok:
            accuracy_ge_3_api = False
        if score == 4 and not (exact_blob and api_ok and iod_ok and mps_ok):
            accuracy_4_evidence = False

    checks = {
        "payload_slot_id_exact": payload.get("slot_id") == SLOT_ID,
        "payload_final_ready_false": payload.get("final_ready") is False,
        "payload_fake_data_false": payload.get("fake_data") is False,
        "payload_business_rows_zero": _as_int(payload.get("actual_business_rows_written")) == 0,
        "payload_area_level_proxy": payload.get("output_semantics") == "AREA_LEVEL_PROXY",
        "payload_rows_300": len(rows) == EXPECTED_ROWS,
        "payload_canonical_rows_300": _as_int(payload.get("canonical_rows")) == EXPECTED_ROWS,
        "payload_unique_parcel_ids_300": len(set(observed_ids)) == EXPECTED_ROWS,
        "payload_exact_contiguous_id_range": observed_ids == expected_ids,
        "payload_no_missing_canonical_status": all(
            row.get("candidate_status") != "CANONICAL_FEATURE_NOT_FOUND" for row in rows
        ),
        "payload_all_area_level_proxy": all(
            row.get("output_semantics") == "AREA_LEVEL_PROXY" for row in rows
        ),
        "payload_no_parcel_measurement": all(
            row.get("parcel_measurement") is False for row in rows
        ),
        "payload_exact_blob_verified": exact_blob,
        "payload_json_csv_geojson_parity": bool((payload.get("artifacts") or {}).get("parity_pass")),
        "payload_accuracy_ge_3_has_api_sha": accuracy_ge_3_api,
        "payload_accuracy_4_has_all_evidence": accuracy_4_evidence,
        "html_slot_id_exact": f'data-slot-id="{SLOT_ID}"' in html_text,
        "html_visible_rows_300": 'data-visible-row-count="300"' in html_text,
        "html_final_ready_false": 'data-final-ready="false"' in html_text,
        "html_table_present": "<table" in html_text and "<tbody" in html_text,
    }
    return checks


def run(args: argparse.Namespace) -> dict[str, Any]:
    base = load_base()
    base_result = base.run(args)

    html_result = base.fetch(args.html_url)
    json_result = base.fetch(args.json_url)
    payload: dict[str, Any] = {}
    parse_error = None
    if json_result.get("http_status") == 200:
        try:
            payload = json.loads(json_result["body"].decode("utf-8-sig"))
        except Exception as exc:
            parse_error = f"JSON_PARSE:{type(exc).__name__}:{exc}"

    html_text = html_result.get("body", b"").decode("utf-8", errors="replace")
    invariant_checks = validate_payload(payload, html_text) if payload else {
        "payload_parseable": False
    }

    checks = dict(base_result.get("checks") or {})
    checks.update(invariant_checks)
    passed = sum(bool(value) for value in checks.values())
    output = dict(base_result)
    output.update({
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "acceptance_gate_version": 3,
        "payload_parse_error": parse_error,
        "invariant_checks": invariant_checks,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "all_checks_pass": passed == len(checks),
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    })
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html-url", required=True)
    parser.add_argument("--json-url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--browser-url")
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({
        "slot_id": SLOT_ID,
        "passed": result["passed"],
        "total": result["total"],
        "all_checks_pass": result["all_checks_pass"],
        "final_ready": False,
    }))
