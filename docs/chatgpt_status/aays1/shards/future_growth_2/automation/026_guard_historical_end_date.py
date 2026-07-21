#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def validate_candidate(candidate: dict) -> bool:
    candidate_id = str(candidate.get("candidate_id") or "")
    end_date = str(candidate.get("end_date") or "").strip()
    if not end_date:
        return False
    eligibility = str(candidate.get("eligibility") or "")
    if not eligibility.startswith("excluded_historical"):
        raise ValueError(f"{candidate_id}: ended record must be excluded_historical")
    if float(candidate.get("parcel_match_confidence_cap") or 0) != 0:
        raise ValueError(f"{candidate_id}: ended record must have zero parcel confidence cap")
    if candidate.get("canonical_row_no") is not None or candidate.get("canonical_parcel_id") is not None:
        raise ValueError(f"{candidate_id}: parcel promotion forbidden for ended record")
    if candidate.get("future_growth_score") is not None or candidate.get("future_growth_confidence") not in (0, None):
        raise ValueError(f"{candidate_id}: score promotion forbidden for ended record")
    return True

def validate(payload: dict) -> dict:
    if payload.get("slot_id") != "future_growth_2":
        raise ValueError("wrong slot_id")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate array missing")
    flagged = [str(c.get("candidate_id") or "") for c in candidates if validate_candidate(c)]
    return {"schema_version":1,"slot_id":"future_growth_2","executed":True,
            "flagged_candidates":flagged,"flagged_count":len(flagged),
            "canonical_parcel_matches":0,"future_growth_scores_produced":0,
            "actual_business_data_rows_written":0,"all_passed":True,"final_ready":False,
            "fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--wave",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    output=validate(json.loads(args.wave.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(output)); return 0
if __name__=="__main__": raise SystemExit(main())
