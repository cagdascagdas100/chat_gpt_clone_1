#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from copy import deepcopy
from pathlib import Path

def load(path: Path):
    spec=importlib.util.spec_from_file_location("guard",path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--guard",type=Path,required=True); p.add_argument("--wave",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    mod=load(a.guard); payload=json.loads(a.wave.read_text(encoding="utf-8")); checks=[]
    def check(name, fn, expected_error=None):
        try:
            fn(); passed=expected_error is None; detail="" if passed else "expected error not raised"
        except Exception as exc:
            passed=expected_error is not None and expected_error in str(exc); detail=f"{type(exc).__name__}: {exc}"
        checks.append({"check":name,"passed":passed,"detail":detail})
    candidates=payload["candidates"]
    check("candidate_count_6",lambda: (_ for _ in ()).throw(AssertionError()) if len(candidates)!=6 else None)
    check("eligible_count_3",lambda: (_ for _ in ()).throw(AssertionError()) if sum(str(c["eligibility"]).startswith("eligible") for c in candidates)!=3 else None)
    check("held_count_3",lambda: (_ for _ in ()).throw(AssertionError()) if sum(str(c["eligibility"]).startswith("held") for c in candidates)!=3 else None)
    check("unique_ids",lambda: (_ for _ in ()).throw(AssertionError()) if len({c["candidate_id"] for c in candidates})!=6 else None)
    check("unique_entities",lambda: (_ for _ in ()).throw(AssertionError()) if len({c["source_entity"] for c in candidates})!=6 else None)
    check("unique_references",lambda: (_ for _ in ()).throw(AssertionError()) if len({c["source_reference"] for c in candidates})!=6 else None)
    check("authoritative_all",lambda: (_ for _ in ()).throw(AssertionError()) if any(c["source_quality"]!="authoritative" for c in candidates) else None)
    check("blank_end_all",lambda: (_ for _ in ()).throw(AssertionError()) if any(c.get("end_date") for c in candidates) else None)
    check("point_all",lambda: (_ for _ in ()).throw(AssertionError()) if any(not str(c.get("official_point_wkt") or "").startswith("POINT") for c in candidates) else None)
    check("eligible_caps_65",lambda: (_ for _ in ()).throw(AssertionError()) if any(c["parcel_match_confidence_cap"]!=65 for c in candidates[:3]) else None)
    check("held_caps_zero",lambda: (_ for _ in ()).throw(AssertionError()) if any(c["parcel_match_confidence_cap"]!=0 for c in candidates[3:]) else None)
    check("product_fields_null",lambda: (_ for _ in ()).throw(AssertionError()) if any(c.get("canonical_row_no") is not None or c.get("canonical_parcel_id") is not None or c.get("future_growth_score") is not None or c.get("future_growth_confidence") not in (0,None) for c in candidates) else None)
    flagged=mod.validate(payload)
    check("guard_flags_three",lambda: (_ for _ in ()).throw(AssertionError(flagged)) if flagged["flagged_count"]!=3 else None)
    check("guard_exact_ids",lambda: (_ for _ in ()).throw(AssertionError(flagged)) if flagged["flagged_candidates"]! =["FG2-W18-004","FG2-W18-005","FG2-W18-006"] else None)
    base=deepcopy(candidates[3])
    def run(c): return mod.validate({"slot_id":"future_growth_2","candidates":[c]})
    c=deepcopy(base); c["eligibility"]="eligible_bad"; check("eligible_conflict_rejected",lambda:run(c),"must be held or excluded")
    c=deepcopy(base); c["lapsed_evidence"]=""; check("missing_evidence_rejected",lambda:run(c),"evidence missing")
    c=deepcopy(base); c["parcel_match_confidence_cap"]=65; check("nonzero_cap_rejected",lambda:run(c),"zero parcel confidence")
    c=deepcopy(base); c["canonical_row_no"]=30762; check("row_promotion_rejected",lambda:run(c),"parcel promotion forbidden")
    c=deepcopy(base); c["canonical_parcel_id"]="x"; check("parcel_promotion_rejected",lambda:run(c),"parcel promotion forbidden")
    c=deepcopy(base); c["future_growth_score"]=70; check("score_promotion_rejected",lambda:run(c),"score promotion forbidden")
    c=deepcopy(base); c["future_growth_confidence"]=70; check("confidence_promotion_rejected",lambda:run(c),"score promotion forbidden")
    c=deepcopy(base); c["official_notes"]="Permission remains valid"; c["eligibility"]="eligible_ok"; c["parcel_match_confidence_cap"]=65; c["lapsed_evidence"]=""; check("non_lapsed_note_not_flagged",lambda:run(c))
    c=deepcopy(base); c["official_notes"]="Permission has not lapsed"; c["eligibility"]="eligible_ok"; c["parcel_match_confidence_cap"]=65; c["lapsed_evidence"]=""; check("negated_lapsed_not_flagged",lambda:run(c))
    c=deepcopy(base); c["end_date"]="2024-01-01"; c["eligibility"]="excluded_historical_ended_record"; c["lapsed_evidence"]=""; check("explicit_end_delegated_to_historical_guard",lambda:run(c))
    check("wrong_slot_rejected",lambda:mod.validate({"slot_id":"other","candidates":[base]}),"wrong slot_id")
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,"test_type":"wave18_blank_end_lapsed_note_guard","checks_passed":sum(x["passed"] for x in checks),"checks_total":len(checks),"all_passed":all(x["passed"] for x in checks),"checks":checks,"actual_wave_flagged_count":flagged["flagged_count"],"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(out)); return 0 if out["all_passed"] else 1
if __name__=="__main__": raise SystemExit(main())
