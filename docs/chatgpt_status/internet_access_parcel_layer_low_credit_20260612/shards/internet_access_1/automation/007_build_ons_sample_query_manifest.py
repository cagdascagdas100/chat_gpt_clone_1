#!/usr/bin/env python3
"""Build a deterministic, preview-only ONSPD query manifest for sample postcodes."""
from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

ENDPOINT = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/ONSPD_Online_latest_Postcode_Centroids/FeatureServer/0/query"
OUT_FIELDS = ["PCDS", "DOTERM", "LAD25CD", "RGN25CD", "LAT", "LONG"]
PC_RE = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$")


def compact(value: str) -> str:
    return "".join(value.upper().split())


def spaced(value: str) -> str:
    value = compact(value)
    if not PC_RE.fullmatch(value):
        raise ValueError(f"invalid postcode {value!r}")
    return f"{value[:-3]} {value[-3:]}"


def build(sample_rows: list[dict]) -> dict:
    grouped = defaultdict(lambda: {"parcel_ids": [], "row_nos": []})
    for row in sample_rows:
        pc = spaced(str(row["postcode"]))
        grouped[pc]["parcel_ids"].append(row["parcel_id"])
        grouped[pc]["row_nos"].append(int(row["row_no"]))
    postcodes = sorted(grouped)
    where = "PCDS IN (" + ",".join("'" + p.replace("'", "''") + "'" for p in postcodes) + ")"
    params = {
        "where": where,
        "outFields": ",".join(OUT_FIELDS),
        "returnGeometry": "false",
        "f": "json",
        "resultRecordCount": str(max(50, len(postcodes))),
    }
    return {
        "schema_version": 1,
        "slot_id": "internet_access_1",
        "official_endpoint": ENDPOINT,
        "dataset_period": "2026-05",
        "required_fields": OUT_FIELDS,
        "query_parameters": params,
        "query_url": ENDPOINT + "?" + urllib.parse.urlencode(params),
        "unique_postcodes": len(postcodes),
        "sample_rows_represented": len(sample_rows),
        "query_examples": [
            {"postcode": pc, "parcel_ids": grouped[pc]["parcel_ids"], "row_nos": grouped[pc]["row_nos"], "official_row_state": "NOT_RETRIEVED"}
            for pc in postcodes
        ],
        "official_rows_read": 0,
        "internet_accuracy_upgraded_rows": 0,
        "business_rows_written": 0,
        "query_execution_state": "REQUEST_READY_EXECUTION_BLOCKED_RUNTIME_DNS_AND_WEB_PARAMETER_SAFETY",
        "fake_data": False,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.samples.read_text(encoding="utf-8"))
    rows = payload.get("sample_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("sample_rows missing or empty")
    result = build(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"unique_postcodes":result["unique_postcodes"],"sample_rows_represented":result["sample_rows_represented"],"official_rows_read":0}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED_FAIL_CLOSED","error":f"{type(exc).__name__}: {exc}","final_ready":False}), file=sys.stderr)
        raise
