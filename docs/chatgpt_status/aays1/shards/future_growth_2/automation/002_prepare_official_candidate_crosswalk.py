#!/usr/bin/env python3
"""Prepare diagnostic-only candidate-to-canonical distance evidence.

Nearest points are never promoted to parcel matches. A product row requires a current
parcel polygon intersection or an official identity crosswalk outside this script.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

EARTH_RADIUS_M = 6371008.8


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            for key in ("row_no", "parcel_id", "hmlr_inspire_id", "longitude", "latitude"):
                if row.get(key) in (None, ""):
                    raise ValueError(f"line {line_number} missing {key}")
            rows.append(row)
    if not rows:
        raise ValueError("canonical shard is empty")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-shard-jsonl", type=Path, required=True)
    parser.add_argument("--candidate-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    shard = load_jsonl(args.canonical_shard_jsonl.resolve())
    candidate_payload = json.loads(args.candidate_json.resolve().read_text(encoding="utf-8"))
    candidates = candidate_payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidate file lacks candidates array")

    diagnostics: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("canonical_row_no") is not None or candidate.get("canonical_parcel_id") is not None:
            raise ValueError("candidate already contains a parcel assignment")
        if candidate.get("future_growth_score") is not None or candidate.get("future_growth_confidence") not in (0, None):
            raise ValueError("candidate already contains a product score/confidence")
        if not str(candidate.get("candidate_eligibility") or "").startswith("ELIGIBLE"):
            diagnostics.append({
                "candidate_id": candidate.get("candidate_id"),
                "state": "SKIPPED_NOT_ELIGIBLE",
                "canonical_row_no": None,
                "canonical_parcel_id": None,
                "future_growth_score": None,
                "future_growth_confidence": 0
            })
            continue
        lon, lat = candidate.get("longitude"), candidate.get("latitude")
        if lon is None or lat is None:
            diagnostics.append({
                "candidate_id": candidate.get("candidate_id"),
                "state": "BLOCKED_SOURCE_GEOMETRY_MISSING",
                "canonical_row_no": None,
                "canonical_parcel_id": None,
                "future_growth_score": None,
                "future_growth_confidence": 0
            })
            continue
        nearest = min(
            shard,
            key=lambda row: haversine_m(float(lon), float(lat), float(row["longitude"]), float(row["latitude"]))
        )
        distance = haversine_m(
            float(lon), float(lat), float(nearest["longitude"]), float(nearest["latitude"])
        )
        diagnostics.append({
            "candidate_id": candidate.get("candidate_id"),
            "state": "DIAGNOSTIC_ONLY_REQUIRES_CURRENT_PARCEL_POLYGON_INTERSECTION_OR_OFFICIAL_IDENTITY",
            "nearest_diagnostic_row_no": nearest["row_no"],
            "nearest_diagnostic_parcel_id": nearest["parcel_id"],
            "nearest_distance_m": round(distance, 3),
            "canonical_row_no": None,
            "canonical_parcel_id": None,
            "future_growth_score": None,
            "future_growth_confidence": 0,
            "nearest_point_promotion_used": False
        })

    output = {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "semantics": "DIAGNOSTIC_ONLY_NO_PARCEL_PROMOTION",
        "candidate_count": len(candidates),
        "diagnostics": diagnostics,
        "actual_parcel_matches": 0,
        "actual_business_data_rows_written": 0,
        "nearest_point_promotion_used": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "diagnostics": len(diagnostics), "matches": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
