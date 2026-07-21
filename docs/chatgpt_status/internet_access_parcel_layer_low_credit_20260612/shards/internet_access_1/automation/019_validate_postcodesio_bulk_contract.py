#!/usr/bin/env python3
"""Fail-closed Postcodes.io bulk-response validator for internet_access_1.

The API is secondary ONSPD-derived corroboration only. It cannot create or
upgrade broadband values and never writes business data.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

POSTCODE_RE = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s\d[A-Z]{2}$")
FORBIDDEN_BROADBAND_KEYS = {
    "gigabit_available_pct",
    "ultrafast_or_100mbps_available_pct",
    "superfast_30mbps_available_pct",
    "unable_30mbps_pct",
    "broadband",
    "speed",
}
MAX_REFERENCE_DISTANCE_M = 25.0


def normalise_postcode(value: str) -> str:
    compact = "".join(str(value).upper().split())
    if len(compact) < 5:
        raise ValueError(f"invalid postcode: {value!r}")
    postcode = f"{compact[:-3]} {compact[-3:]}"
    if not POSTCODE_RE.fullmatch(postcode):
        raise ValueError(f"invalid postcode: {value!r}")
    return postcode


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_m = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def finite_number(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} is not numeric") from exc
    if not math.isfinite(result):
        raise RuntimeError(f"{name} is not finite")
    return result


def validate_manifest(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if manifest.get("slot_id") != "internet_access_1":
        raise RuntimeError("wrong slot_id")
    rows = manifest.get("rows")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("manifest rows must be a non-empty list")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        postcode = normalise_postcode(row.get("postcode"))
        if postcode in result:
            raise RuntimeError(f"duplicate manifest postcode: {postcode}")
        result[postcode] = {
            "postcode": postcode,
            "reference_lat": finite_number(row.get("reference_lat"), "reference_lat"),
            "reference_lon": finite_number(row.get("reference_lon"), "reference_lon"),
            "represented_rows": list(row.get("represented_rows") or []),
        }
    return result


def validate_bulk_response(
    manifest: dict[str, Any],
    payload: dict[str, Any],
    max_reference_distance_m: float = MAX_REFERENCE_DISTANCE_M,
) -> dict[str, Any]:
    expected = validate_manifest(manifest)
    if payload.get("status") != 200:
        raise RuntimeError("bulk response status must be 200")
    items = payload.get("result")
    if not isinstance(items, list):
        raise RuntimeError("bulk response result must be a list")

    seen: set[str] = set()
    output_rows: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise RuntimeError("bulk response item must be an object")
        query = normalise_postcode(item.get("query"))
        if query not in expected:
            raise RuntimeError(f"unexpected postcode query: {query}")
        if query in seen:
            raise RuntimeError(f"duplicate postcode query: {query}")
        seen.add(query)

        result = item.get("result")
        if not isinstance(result, dict):
            raise RuntimeError(f"missing postcode result: {query}")
        postcode = normalise_postcode(result.get("postcode"))
        if postcode != query:
            raise RuntimeError(f"query/result postcode mismatch: {query} != {postcode}")

        if FORBIDDEN_BROADBAND_KEYS.intersection(result):
            raise RuntimeError(f"broadband fields forbidden in secondary response: {query}")

        lat = finite_number(result.get("latitude"), "latitude")
        lon = finite_number(result.get("longitude"), "longitude")
        if not (49.0 <= lat <= 61.5 and -8.5 <= lon <= 2.5):
            raise RuntimeError(f"coordinate outside UK guardrail: {query}")

        if result.get("region") != "London":
            raise RuntimeError(f"non-London region: {query}")
        if result.get("admin_district") != "Barking and Dagenham":
            raise RuntimeError(f"unexpected admin district: {query}")
        codes = result.get("codes")
        if not isinstance(codes, dict):
            raise RuntimeError(f"missing codes object: {query}")
        if codes.get("admin_district") != "E09000002":
            raise RuntimeError(f"unexpected LAD code: {query}")

        reference = expected[query]
        delta = haversine_m(
            reference["reference_lon"], reference["reference_lat"], lon, lat
        )
        if delta > max_reference_distance_m:
            raise RuntimeError(
                f"secondary/reference centroid distance exceeds "
                f"{max_reference_distance_m:.1f}m: {query}={delta:.1f}m"
            )
        output_rows.append(
            {
                "postcode": query,
                "latitude": lat,
                "longitude": lon,
                "reference_delta_m": round(delta, 1),
                "admin_district_code": codes["admin_district"],
                "represented_rows": reference["represented_rows"],
                "source_role": "SECONDARY_ONSPD_DERIVED_GEOGRAPHY_CROSSCHECK_ONLY",
                "broadband_value_allowed": False,
            }
        )

    missing = sorted(set(expected) - seen)
    if missing:
        raise RuntimeError(f"missing requested postcode results: {missing}")
    output_rows.sort(key=lambda row: row["postcode"])
    return {
        "schema_version": 1,
        "slot_id": "internet_access_1",
        "source": "POSTCODES_IO_BULK_LOOKUP",
        "source_role": "SECONDARY_ONSPD_DERIVED_GEOGRAPHY_CROSSCHECK_ONLY",
        "rows": output_rows,
        "validated_rows": len(output_rows),
        "max_reference_distance_m": max_reference_distance_m,
        "official_rows_read": 0,
        "secondary_api_rows_read": len(output_rows),
        "internet_accuracy_upgraded_rows": 0,
        "broadband_values_written": 0,
        "business_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--max-reference-distance-m", type=float, default=MAX_REFERENCE_DISTANCE_M
    )
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    payload = json.loads(args.response.read_text(encoding="utf-8"))
    result = validate_bulk_response(
        manifest, payload, args.max_reference_distance_m
    )
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
