#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path

def validate(payload:dict)->dict:
    rows=payload.get("examples") or []
    checks=[]
    def check(name,ok,actual=None): checks.append({"name":name,"pass":bool(ok),"actual":actual})
    check("exactly_8_examples",len(rows)==8,len(rows))
    ids=[r.get("parcel_id") for r in rows]; check("unique_parcel_ids",len(ids)==len(set(ids)),len(set(ids)))
    pcs=[r.get("postcode") for r in rows]; check("unique_postcodes",len(pcs)==len(set(pcs)),len(set(pcs)))
    check("all_accuracy_2_of_4",all(r.get("internet_accuracy")=="2/4" for r in rows))
    check("no_r2_refresh",all(r.get("r2_refreshed") is False for r in rows))
    check("numeric_coverage_fields",all(all(isinstance(r.get(k),(int,float)) and math.isfinite(float(r[k])) for k in ("gigabit_available_pct","ultrafast_or_100mbps_available_pct","superfast_30mbps_available_pct","unable_30mbps_pct")) for r in rows))
    classes={r.get("join_class") for r in rows}; check("all_join_classes_represented",{"STRONG","SUPPORTED","BORDERLINE","CONFLICT"}.issubset(classes),sorted(classes))
    bands={r.get("quality_band") for r in rows}; check("quality_band_diversity",{"Very High","Low","Very Low"}.issubset(bands),sorted(bands))
    check("conflict_has_candidate_distances",all("join_distance_candidates_m" in r for r in rows if r.get("join_class")=="CONFLICT"))
    check("no_business_write",payload.get("business_rows_written")==0)
    check("safety_flags",payload.get("fake_data") is False and payload.get("db_write") is False and payload.get("migration") is False and payload.get("production_deploy") is False)
    check("final_ready_false",payload.get("final_ready") is False)
    return {"schema_version":1,"slot_id":"internet_access_1","status":"PASS" if all(c["pass"] for c in checks) else "FAIL","checks_total":len(checks),"checks_passed":sum(c["pass"] for c in checks),"checks_failed":sum(not c["pass"] for c in checks),"checks":checks,"visible_examples":len(rows),"internet_accuracy_upgraded_rows":0,"business_rows_written":0,"fake_data":False,"final_ready":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    out=validate(json.loads(a.input.read_text(encoding="utf-8")));a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");raise SystemExit(0 if out["status"]=="PASS" else 1)
if __name__=="__main__":main()
