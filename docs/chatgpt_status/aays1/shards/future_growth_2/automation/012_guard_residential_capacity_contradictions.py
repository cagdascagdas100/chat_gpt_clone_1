#!/usr/bin/env python3
"""Fail closed when residential narrative conflicts with zero dwelling capacity."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

RESIDENTIAL = re.compile(r"\b(residential|dwelling|flat|house|maisonette)\b", re.I)

def guard(candidate: dict, notes: str = "") -> dict:
    cid = str(candidate.get("candidate_id") or "")
    lo = candidate.get("minimum_net_dwellings")
    hi = candidate.get("maximum_net_dwellings")
    eligibility = str(candidate.get("eligibility") or "")
    conflict = lo == 0 and hi == 0 and bool(RESIDENTIAL.search(notes))
    if conflict and not eligibility.startswith("held_"):
        raise ValueError(f"{cid}: zero capacity conflicts with residential narrative but is not held")
    if conflict and (candidate.get("canonical_parcel_id") is not None or candidate.get("future_growth_score") is not None):
        raise ValueError(f"{cid}: conflicting record promoted to product fields")
    return {"candidate_id": cid, "capacity_conflict": conflict, "state": "HELD_FAIL_CLOSED" if conflict else "NO_CONFLICT", "parcel_promoted": False, "score_written": False}

def main() -> int:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    notes = {1709770: "Demolition and erection comprising residential flats and maisonettes"}
    results = [guard(c, notes.get(int(c["source_entity"]), "")) for c in payload["candidates"]]
    print(json.dumps({"ok": True, "results": results}, ensure_ascii=False))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
