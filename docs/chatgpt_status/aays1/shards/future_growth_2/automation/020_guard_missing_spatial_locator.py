#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def validate_candidate(c:dict)->None:
    cid=str(c.get("candidate_id") or "")
    geometry_empty=c.get("official_geometry_field_empty") is True
    point=str(c.get("official_point_wkt") or "").strip()
    missing=geometry_empty and not point
    if not missing:
        return
    eligibility=str(c.get("eligibility") or "")
    if not (eligibility.startswith("held") or eligibility.startswith("excluded")):
        raise ValueError(f"{cid}: missing spatial locator must be held or excluded")
    if c.get("missing_spatial_locator") is not True:
        raise ValueError(f"{cid}: missing spatial locator flag required")
    if not str(c.get("missing_spatial_locator_evidence") or "").strip():
        raise ValueError(f"{cid}: missing spatial locator evidence required")
    if float(c.get("parcel_match_confidence_cap") or 0) != 0:
        raise ValueError(f"{cid}: missing spatial locator cap must be zero")
    if c.get("canonical_row_no") is not None or c.get("canonical_parcel_id") is not None:
        raise ValueError(f"{cid}: parcel promotion forbidden without spatial locator")
    if c.get("future_growth_score") is not None or c.get("future_growth_confidence") not in (0,None):
        raise ValueError(f"{cid}: score promotion forbidden without spatial locator")

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--wave",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    payload=json.loads(a.wave.read_text(encoding="utf-8")); missing=[]
    for c in payload.get("candidates") or []:
        validate_candidate(c)
        if c.get("official_geometry_field_empty") is True and not str(c.get("official_point_wkt") or "").strip(): missing.append(c.get("candidate_id"))
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,"missing_spatial_locator_candidates":missing,"missing_spatial_locator_count":len(missing),"all_passed":True,"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8"); return 0
if __name__=="__main__": raise SystemExit(main())
