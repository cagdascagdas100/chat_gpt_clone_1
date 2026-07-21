#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

LAPSED = re.compile(r"\blapsed\b", re.I)
NEGATED = re.compile(r"\b(?:not|never|has\s+not|have\s+not|is\s+not)\s+lapsed\b", re.I)

def notes_indicate_lapsed(text: str) -> bool:
    value = str(text or "").strip()
    return bool(LAPSED.search(value)) and not bool(NEGATED.search(value))

def validate_candidate(candidate: dict) -> bool:
    cid = str(candidate.get("candidate_id") or "").strip()
    notes = str(candidate.get("official_notes") or candidate.get("notes") or "").strip()
    end_date = str(candidate.get("end_date") or "").strip()
    flagged = not end_date and notes_indicate_lapsed(notes)
    if not flagged:
        return False
    eligibility = str(candidate.get("eligibility") or "")
    if not (eligibility.startswith("held_blank_end_lapsed_note") or eligibility.startswith("excluded_")):
        raise ValueError(f"{cid}: blank-end lapsed-note conflict must be held or excluded")
    if not str(candidate.get("lapsed_evidence") or "").strip():
        raise ValueError(f"{cid}: lapsed-note evidence missing")
    if float(candidate.get("parcel_match_confidence_cap") or 0) != 0:
        raise ValueError(f"{cid}: lapsed-note conflict must have zero parcel confidence cap")
    if candidate.get("canonical_row_no") is not None or candidate.get("canonical_parcel_id") is not None:
        raise ValueError(f"{cid}: parcel promotion forbidden for lapsed-note conflict")
    if candidate.get("future_growth_score") is not None or candidate.get("future_growth_confidence") not in (0, None):
        raise ValueError(f"{cid}: score promotion forbidden for lapsed-note conflict")
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
    p=argparse.ArgumentParser(); p.add_argument("--wave",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    out=validate(json.loads(a.wave.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out)); return 0
if __name__=="__main__": raise SystemExit(main())
