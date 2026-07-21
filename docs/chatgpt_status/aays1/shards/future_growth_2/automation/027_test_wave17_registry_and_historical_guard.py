#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from copy import deepcopy
from pathlib import Path

def load(path: Path):
    spec=importlib.util.spec_from_file_location("guard",path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--guard",type=Path,required=True); parser.add_argument("--wave",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    guard=load(args.guard); payload=json.loads(args.wave.read_text(encoding="utf-8")); candidates=payload["candidates"]; checks=[]
    def check(name,fn,expected=None):
        try:
            fn(); passed=expected is None; detail="" if passed else "expected error not raised"
        except Exception as exc:
            passed=expected is not None and expected in str(exc); detail=f"{type(exc).__name__}: {exc}"
        checks.append({"check":name,"passed":passed,"detail":detail})
    check("candidate_count_6",lambda: (_ for _ in ()).throw(AssertionError()) if len(candidates)!=6 else None)
    check("eligible_count_3",lambda: (_ for _ in ()).throw(AssertionError()) if sum(str(c["eligibility"]).startswith("eligible") for c in candidates)!=3 else None)
    check("historical_count_3",lambda: (_ for _ in ()).throw(AssertionError()) if sum(str(c["eligibility"]).startswith("excluded_historical") for c in candidates)!=3 else None)
    check("unique_ids",lambda: (_ for _ in ()).throw(AssertionError()) if len({c["candidate_id"] for c in candidates})!=6 else None)
    check("unique_entities",lambda: (_ for _ in ()).throw(AssertionError()) if len({c["source_entity"] for c in candidates})!=6 else None)
    check("unique_references",lambda: (_ for _ in ()).throw(AssertionError()) if len({c["source_reference"] for c in candidates})!=6 else None)
    check("authoritative_all",lambda: (_ for _ in ()).throw(AssertionError()) if any(c["source_quality"]!="authoritative" for c in candidates) else None)
    check("eligible_blank_end",lambda: (_ for _ in ()).throw(AssertionError()) if any(c.get("end_date") for c in candidates[:3]) else None)
    check("historical_end_present",lambda: (_ for _ in ()).throw(AssertionError()) if any(not c.get("end_date") for c in candidates[3:]) else None)
    check("eligible_caps_65",lambda: (_ for _ in ()).throw(AssertionError()) if any(c["parcel_match_confidence_cap"]!=65 for c in candidates[:3]) else None)
    check("historical_caps_zero",lambda: (_ for _ in ()).throw(AssertionError()) if any(c["parcel_match_confidence_cap"]!=0 for c in candidates[3:]) else None)
    check("product_fields_null",lambda: (_ for _ in ()).throw(AssertionError()) if any(c.get("canonical_row_no") is not None or c.get("canonical_parcel_id") is not None or c.get("future_growth_score") is not None or c.get("future_growth_confidence") not in (0,None) for c in candidates) else None)
    result=guard.validate(payload)
    check("guard_flags_three",lambda: (_ for _ in ()).throw(AssertionError(result)) if result["flagged_count"]!=3 else None)
    check("guard_exact_ids",lambda: (_ for _ in ()).throw(AssertionError(result)) if result["flagged_candidates"]!=["FG2-W17-004","FG2-W17-005","FG2-W17-006"] else None)
    def run(candidate): return guard.validate({"slot_id":"future_growth_2","candidates":[candidate]})
    base=deepcopy(candidates[3]); base["eligibility"]="eligible_bad"; check("ended_eligible_rejected",lambda:run(base),"must be excluded_historical")
    base=deepcopy(candidates[3]); base["parcel_match_confidence_cap"]=65; check("ended_cap_rejected",lambda:run(base),"zero parcel confidence")
    base=deepcopy(candidates[3]); base["canonical_row_no"]=30762; check("ended_row_promotion_rejected",lambda:run(base),"parcel promotion forbidden")
    base=deepcopy(candidates[3]); base["canonical_parcel_id"]="x"; check("ended_parcel_promotion_rejected",lambda:run(base),"parcel promotion forbidden")
    base=deepcopy(candidates[3]); base["future_growth_score"]=50; check("ended_score_rejected",lambda:run(base),"score promotion forbidden")
    base=deepcopy(candidates[3]); base["future_growth_confidence"]=60; check("ended_confidence_rejected",lambda:run(base),"score promotion forbidden")
    check("current_not_flagged",lambda:run(deepcopy(candidates[0])))
    check("wrong_slot_rejected",lambda:guard.validate({"slot_id":"other","candidates":[candidates[0]]}),"wrong slot_id")
    output={"schema_version":1,"slot_id":"future_growth_2","executed":True,"test_type":"wave17_registry_and_historical_end_date_guard","checks_passed":sum(c["passed"] for c in checks),"checks_total":len(checks),"all_passed":all(c["passed"] for c in checks),"checks":checks,"historical_flagged":result["flagged_candidates"],"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(output)); return 0 if output["all_passed"] else 1
if __name__=="__main__": raise SystemExit(main())
