#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def validate_candidate(c: dict) -> None:
    cid=str(c.get("candidate_id") or "")
    ref=str(c.get("source_reference") or "")
    site_ref=str(c.get("official_site_plan_reference") or "")
    mismatch=bool(site_ref and ref and site_ref != ref)
    eligible=str(c.get("eligibility") or "").startswith("eligible")
    if mismatch and eligible:
        raise ValueError(f"{cid}: site-plan reference conflict must be held or excluded")
    if mismatch and not c.get("reference_conflict_evidence"):
        raise ValueError(f"{cid}: reference conflict evidence missing")
    if mismatch and (c.get("canonical_row_no") is not None or c.get("canonical_parcel_id") is not None):
        raise ValueError(f"{cid}: parcel promotion forbidden for reference conflict")
    if mismatch and (c.get("future_growth_score") is not None or c.get("future_growth_confidence") not in (0,None)):
        raise ValueError(f"{cid}: score promotion forbidden for reference conflict")
    if mismatch and float(c.get("parcel_match_confidence_cap") or 0) != 0:
        raise ValueError(f"{cid}: reference-conflict confidence cap must be zero")

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--wave",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    payload=json.loads(a.wave.read_text(encoding="utf-8")); candidates=payload.get("candidates") or []
    for c in candidates: validate_candidate(c)
    conflicts=sum(bool(c.get("official_site_plan_reference") and c.get("official_site_plan_reference") != c.get("source_reference")) for c in candidates)
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,"validated_candidates":len(candidates),"reference_conflicts_held_or_excluded":conflicts,"all_passed":True,"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8"); return 0
if __name__=="__main__": raise SystemExit(main())
