#!/usr/bin/env python3
"""Validate parcel_89's two-output-area hierarchy bridge without selecting a postcode."""
from __future__ import annotations
import json
import sys
from pathlib import Path

SLOT_ID = "internet_access_1"
EXPECTED_SHARED = {
    "ward_code": "E05014070",
    "lad_code": "E09000002",
    "lsoa_code": "E01000103",
    "msoa_code": "E02000015",
    "constituency_code": "E14001189",
    "country_code": "E92000001",
}


def main() -> int:
    source = Path(sys.argv[1])
    payload = json.loads(source.read_text(encoding="utf-8"))
    candidates = payload["candidates"]
    reps = payload["output_area_representatives"]
    checks = {
        "slot_id": payload.get("slot_id") == SLOT_ID,
        "parcel_89": payload.get("parcel_id") == "parcel_89",
        "nine_candidates": len(candidates) == 9,
        "two_output_areas": set(reps) == {"E00000534", "E00000536"},
        "cluster_counts": {oa: sum(row["output_area"] == oa for row in candidates) for oa in reps} == {"E00000534": 3, "E00000536": 6},
        "rank_sequence": [row["rank"] for row in candidates] == list(range(1, 10)),
        "distance_sorted": [row["distance_m"] for row in candidates] == sorted(row["distance_m"] for row in candidates),
        "nearest_two_different_oa": candidates[0]["output_area"] != candidates[1]["output_area"],
        "nearest_gap_6_8m": round(candidates[1]["distance_m"] - candidates[0]["distance_m"], 1) == 6.8,
        "top_three_span_12_4m": round(candidates[2]["distance_m"] - candidates[0]["distance_m"], 1) == 12.4,
        "representatives": reps["E00000536"]["postcode"] == "RM10 9XJ" and reps["E00000534"]["postcode"] == "RM10 9YR",
        "representative_period": all(row["last_updated"] == "May 2026" for row in reps.values()),
    }
    for key, value in EXPECTED_SHARED.items():
        checks[f"shared_{key}"] = {row[key] for row in reps.values()} == {value}
    checks.update({
        "canonical_postcode_null": payload["decision"]["canonical_postcode"] is None,
        "accuracy_zero": payload["decision"]["internet_accuracy"] == "0/4",
        "broadband_forbidden": payload["decision"]["broadband_value_allowed"] is False,
        "official_rows_zero": payload["official_direct_rows_read"] == 0,
        "business_rows_zero": payload["business_rows_written"] == 0,
        "migration_false": payload["migration_applied"] is False,
        "db_write_false": payload["db_write"] is False,
        "production_deploy_false": payload["production_deploy"] is False,
        "final_ready_false": payload["final_ready"] is False,
        "oa_membership_secondary_only": payload["source_role"] == "SECONDARY_OGL_GEOGRAPHY_CROSSCHECK_ONLY",
        "no_accuracy_upgrade": payload["accuracy_upgraded_rows"] == 0,
    })
    failed = [name for name, passed in checks.items() if not passed]
    result = {"slot_id": SLOT_ID, "status": "PASS" if not failed else "FAIL", "checks_passed": len(checks) - len(failed), "checks_failed": len(failed), "checks_total": len(checks), "failed": failed}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
