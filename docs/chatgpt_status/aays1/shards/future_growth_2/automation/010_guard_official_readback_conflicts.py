#!/usr/bin/env python3
"""Fail closed when official readbacks disagree on identity-critical/currentness fields."""
from __future__ import annotations
import argparse, json
from pathlib import Path

CONFLICT_FIELDS = ("source_entity", "source_reference", "entry_date", "start_date", "end_date")

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    rows = payload.get("candidates", [])
    out = []
    for row in rows:
        evidence = row.get("official_readbacks", [])
        conflicts = {}
        for field in CONFLICT_FIELDS:
            vals = {str(x.get(field)) for x in evidence if x.get(field) not in (None, "")}
            if len(vals) > 1:
                conflicts[field] = sorted(vals)
        promoted = row.get("eligibility", "").startswith("eligible")
        if conflicts and promoted:
            raise SystemExit(f"conflicting official readbacks cannot be eligible: {row.get('candidate_id')} {conflicts}")
        if conflicts:
            row["eligibility"] = "held_official_readback_conflict"
            row["canonical_row_no"] = None
            row["canonical_parcel_id"] = None
            row["future_growth_score"] = None
            row["future_growth_confidence"] = 0
        out.append({"candidate_id":row.get("candidate_id"),"conflicts":conflicts,"eligibility":row.get("eligibility")})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"results":out}, indent=2), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
