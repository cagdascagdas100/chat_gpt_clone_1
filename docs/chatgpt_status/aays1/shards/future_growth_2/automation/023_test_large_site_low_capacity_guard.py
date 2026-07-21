#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from copy import deepcopy
from pathlib import Path

def load(path: Path):
    spec=importlib.util.spec_from_file_location("guard",path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--guard",type=Path,required=True)
    p.add_argument("--wave",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    mod=load(a.guard)
    payload=json.loads(a.wave.read_text(encoding="utf-8"))
    checks=[]
    def check(name, fn, expected_error=None):
        try:
            fn()
            passed=expected_error is None; detail="" if passed else "expected error not raised"
        except Exception as exc:
            passed=expected_error is not None and expected_error in str(exc)
            detail=f"{type(exc).__name__}: {exc}"
        checks.append({"check":name,"passed":passed,"detail":detail})
    flagged=mod.validate(payload)
    check("actual_wave_two_flagged",lambda: (_ for _ in ()).throw(AssertionError(flagged)) if flagged["flagged_count"]!=2 else None)
    check("actual_wave_exact_ids",lambda: (_ for _ in ()).throw(AssertionError(flagged)) if flagged["flagged_candidates"] != ["FG2-W16-005","FG2-W16-006"] else None)
    base=deepcopy(payload["candidates"][4])
    def run(c): return mod.validate({"slot_id":"future_growth_2","candidates":[c]})
    c=deepcopy(base); c["eligibility"]="eligible_bad"; check("eligible_anomaly_rejected",lambda:run(c),"must be held")
    c=deepcopy(base); c["capacity_anomaly_evidence"]=""; check("missing_evidence_rejected",lambda:run(c),"evidence missing")
    c=deepcopy(base); c["parcel_match_confidence_cap"]=65; check("nonzero_cap_rejected",lambda:run(c),"zero parcel confidence")
    c=deepcopy(base); c["canonical_row_no"]=30762; check("parcel_promotion_rejected",lambda:run(c),"parcel promotion forbidden")
    c=deepcopy(base); c["future_growth_score"]=80; check("score_promotion_rejected",lambda:run(c),"score promotion forbidden")
    c=deepcopy(base); c["hectares"]=4.99; c["eligibility"]="eligible_ok"; c["capacity_anomaly_evidence"]=""; check("below_area_threshold_not_flagged",lambda:run(c))
    c=deepcopy(base); c["maximum_net_dwellings"]=20; c["eligibility"]="eligible_ok"; c["capacity_anomaly_evidence"]=""; check("higher_capacity_not_flagged",lambda:run(c))
    c=deepcopy(base); c["maximum_net_dwellings"]=None; c["eligibility"]="eligible_ok"; c["capacity_anomaly_evidence"]=""; check("missing_capacity_not_flagged",lambda:run(c))
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,
      "test_type":"large_site_low_capacity_fail_closed_guard",
      "checks_passed":sum(x["passed"] for x in checks),"checks_total":len(checks),
      "all_passed":all(x["passed"] for x in checks),"checks":checks,
      "actual_wave_flagged_count":flagged["flagged_count"],
      "canonical_parcel_matches":0,"future_growth_scores_produced":0,
      "actual_business_data_rows_written":0,"final_ready":False,
      "fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out))
    return 0 if out["all_passed"] else 1
if __name__=="__main__": raise SystemExit(main())
