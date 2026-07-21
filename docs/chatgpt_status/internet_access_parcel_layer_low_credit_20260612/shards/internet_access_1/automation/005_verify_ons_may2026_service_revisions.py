#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path

REQUIRED = {
    "hosted_table": {"period": "2026-05", "data_last_edit": "2026-06-04"},
    "centroid_feature_layer": {"period": "2026-05", "data_last_edit": "2026-06-16"},
    "nspl_lookup": {"period": "2026-05"},
}

def parse_iso(value: str) -> date:
    return date.fromisoformat(value)

def verify(payload: dict) -> dict:
    errors = []
    for key, expected in REQUIRED.items():
        source = payload.get(key)
        if not isinstance(source, dict):
            errors.append(f"missing:{key}")
            continue
        for field, value in expected.items():
            if source.get(field) != value:
                errors.append(f"{key}.{field}:{source.get(field)!r}!={value!r}")
    stale = payload.get("stale_live_layer") or {}
    if stale.get("period") != "2026-02" or stale.get("promotion_allowed") is not False:
        errors.append("stale_live_layer_not_fail_closed")
    if not errors and parse_iso(payload["hosted_table"]["data_last_edit"]) > parse_iso(payload["centroid_feature_layer"]["data_last_edit"]):
        errors.append("hosted_table_edit_after_centroid_layer")
    return {
        "status": "PASS" if not errors else "FAIL",
        "checks_total": 8,
        "checks_passed": 8 - len(errors),
        "checks_failed": len(errors),
        "errors": errors,
        "promotion_decision": {
            "hosted_table": "PRIMARY_METADATA_API",
            "centroid_feature_layer": "PRIMARY_CENTROID_LAYER",
            "nspl_lookup": "PROMOTE_GEOGRAPHY_CROSSCHECK_ONLY",
            "stale_live_layer": "DIAGNOSTIC_ONLY"
        },
        "broadband_values_allowed": False,
        "final_ready": False
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = verify(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    raise SystemExit(0 if result["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
