#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path

def compact(postcode: str) -> str:
    return "".join(postcode.upper().split())

def distance_m(a: dict, b: dict) -> float:
    r = 6371008.8
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = math.radians(b["lat"] - a["lat"])
    dl = math.radians(b["lon"] - a["lon"])
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return r * 2 * math.atan2(math.sqrt(x), math.sqrt(1-x))

def classify(max_current_delta_m: float, archival_conflict_m: float | None) -> str:
    if archival_conflict_m is not None and archival_conflict_m > 250:
        return "CURRENT_CONSENSUS_WITH_ARCHIVAL_CONFLICT_FAIL_CLOSED"
    if max_current_delta_m <= 5:
        return "CURRENT_DUAL_SOURCE_STRONG"
    if max_current_delta_m <= 25:
        return "CURRENT_DUAL_SOURCE_SUPPORTED"
    return "CURRENT_SOURCE_CONFLICT_FAIL_CLOSED"

def audit(payload: dict) -> dict:
    rows = []
    for item in payload["postcodes"]:
        current = item["current_sources"]
        deltas = [
            distance_m(current[i], current[j])
            for i in range(len(current))
            for j in range(i + 1, len(current))
        ]
        max_delta = max(deltas) if deltas else 0.0
        archival = item.get("archival_source")
        archival_delta = None
        if archival:
            archival_delta = distance_m(current[0], archival)
        rows.append({
            "postcode": compact(item["postcode"]),
            "current_source_count": len(current),
            "max_current_source_delta_m": round(max_delta, 1),
            "archival_conflict_distance_m": None if archival_delta is None else round(archival_delta, 1),
            "state": classify(max_delta, archival_delta),
            "broadband_value_allowed": False,
        })
    return {
        "schema_version": 1,
        "slot_id": "internet_access_1",
        "rows": rows,
        "postcodes_checked": len(rows),
        "current_consensus_rows": sum(r["max_current_source_delta_m"] <= 5 for r in rows),
        "stable_without_archival_conflict": sum(r["state"] == "CURRENT_DUAL_SOURCE_STRONG" for r in rows),
        "archival_conflict_rows": sum("ARCHIVAL_CONFLICT" in r["state"] for r in rows),
        "internet_accuracy_upgraded_rows": 0,
        "business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args()
    result=audit(json.loads(a.input.read_text(encoding="utf-8")))
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
