#!/usr/bin/env python3
"""Fail-closed postcode-candidate ambiguity audit for internet_access_1.

Ranks postcode centroids by distance but never converts proximity into a
canonical parcel postcode. Promotion requires an explicit canonical join or
parcel/address containment evidence.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Any

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    values = (lat1, lon1, lat2, lon2)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("coordinates must be finite")
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    parcel = payload["parcel"]
    candidates = payload["postcode_candidates"]
    if not candidates:
        raise ValueError("at least one postcode candidate is required")
    seen: set[str] = set()
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        postcode = str(candidate["postcode"]).strip().upper()
        if not postcode or postcode in seen:
            raise ValueError("postcode candidates must be non-empty and unique")
        seen.add(postcode)
        distance = haversine_m(
            float(parcel["lat"]), float(parcel["lon"]),
            float(candidate["lat"]), float(candidate["lon"]),
        )
        ranked.append({**candidate, "postcode": postcode, "distance_m": round(distance, 1)})
    ranked.sort(key=lambda row: (row["distance_m"], row["postcode"]))
    gap = round(ranked[1]["distance_m"] - ranked[0]["distance_m"], 1) if len(ranked) > 1 else None
    return {
        "slot_id": payload.get("slot_id", "internet_access_1"),
        "parcel": parcel,
        "ranked_candidates": ranked,
        "nearest_distance_m": ranked[0]["distance_m"],
        "nearest_second_gap_m": gap,
        "canonical_postcode": None,
        "decision": "AMBIGUOUS_NEAREST_CENTROID_NOT_CANONICAL",
        "promotion_allowed": False,
        "internet_accuracy_upgrade_allowed": False,
        "required_next_evidence": [
            "exact canonical parcel-to-postcode record",
            "or authoritative address/parcel containment evidence",
        ],
        "fake_data": False,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.input_json.read_text(encoding="utf-8")))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
