#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

MAX_POINT_CAP = 65

def validate_candidate(c: dict) -> None:
    cid = str(c.get("candidate_id") or "")
    eligible = str(c.get("eligibility") or "").startswith("eligible")
    point = str(c.get("official_point_wkt") or "")
    geometry_empty = c.get("official_geometry_field_empty") is True
    role = str(c.get("geometry_role") or "")
    cap = float(c.get("parcel_match_confidence_cap") or 0)
    if not geometry_empty or not point.startswith("POINT ("):
        raise ValueError(f"{cid}: point-only evidence not proven")
    if "point_only" not in role or "boundary" not in role:
        raise ValueError(f"{cid}: point-only role missing")
    if c.get("canonical_row_no") is not None or c.get("canonical_parcel_id") is not None:
        raise ValueError(f"{cid}: parcel promotion forbidden before exact crosswalk")
    if c.get("future_growth_score") is not None or c.get("future_growth_confidence") not in (0, None):
        raise ValueError(f"{cid}: score promotion forbidden")
    if eligible and not (0 < cap <= MAX_POINT_CAP):
        raise ValueError(f"{cid}: eligible point cap must be 1..{MAX_POINT_CAP}")
    if not eligible and cap != 0:
        raise ValueError(f"{cid}: excluded/held point cap must be zero")

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--wave",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    payload=json.loads(a.wave.read_text(encoding="utf-8"))
    for c in payload.get("candidates") or []: validate_candidate(c)
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,"validated_candidates":len(payload.get("candidates") or []),"max_point_confidence_cap":MAX_POINT_CAP,"all_passed":True,"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
