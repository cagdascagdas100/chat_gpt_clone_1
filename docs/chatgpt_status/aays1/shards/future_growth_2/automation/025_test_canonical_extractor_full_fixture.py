#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from copy import deepcopy
from pathlib import Path

def load(path):
    spec=importlib.util.spec_from_file_location("extractor",path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def feature(i):
    lon=-0.25+(i%1000)*0.0001; lat=51.3+(i%500)*0.0001
    return {"type":"Feature","geometry":{"type":"Point","coordinates":[lon,lat]},
            "properties":{"row_no":i,"parcel_id":f"parcel_{i}","hmlr_inspire_id":f"inspire_{i}",
                          "hmlr_row_id":str(i),"hmlr_area_m2":"100.0","hmlr_lon":lon,"hmlr_lat":lat,
                          "london_authority":"Fixture Authority"}}
def payload(n): return {"type":"FeatureCollection","features":[feature(i) for i in range(1,n+1)]}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--extractor",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    m=load(a.extractor); checks=[]
    def check(name,fn,expected=None):
        try: fn(); passed=expected is None; detail="" if passed else "expected error not raised"
        except Exception as exc: passed=expected is not None and expected in str(exc); detail=f"{type(exc).__name__}: {exc}"
        checks.append({"check":name,"passed":passed,"detail":detail})
    full=payload(92283)
    shard,audit=m.extract_rows(full,canonical_count=92283,row_start=30762,row_end=61522)
    check("full_canonical_92283_validated",lambda: (_ for _ in ()).throw(AssertionError(audit)) if audit["canonical_features_validated"]!=92283 else None)
    check("full_shard_30761_rows",lambda: (_ for _ in ()).throw(AssertionError(len(shard))) if len(shard)!=30761 else None)
    check("full_shard_first_last_identity",lambda: (_ for _ in ()).throw(AssertionError((shard[0]["row_no"],shard[-1]["row_no"]))) if (shard[0]["row_no"],shard[-1]["row_no"])!=(30762,61522) else None)
    check("full_explicit_identity_only",lambda: (_ for _ in ()).throw(AssertionError(audit)) if audit["row_order_inference_used"] or audit["nearest_fill_used"] else None)
    small=payload(3)
    c=deepcopy(small); c["features"][1]["properties"]["row_no"]=1; check("duplicate_row_rejected",lambda:m.extract_rows(c,canonical_count=3,row_start=1,row_end=3),"duplicate row_no")
    c=deepcopy(small); c["features"][1]["properties"]["parcel_id"]="parcel_1"; check("duplicate_parcel_rejected",lambda:m.extract_rows(c,canonical_count=3,row_start=1,row_end=3),"duplicate parcel_id")
    c=deepcopy(small); c["features"][1]["properties"]["hmlr_inspire_id"]="inspire_1"; check("duplicate_inspire_rejected",lambda:m.extract_rows(c,canonical_count=3,row_start=1,row_end=3),"duplicate hmlr_inspire_id")
    c=deepcopy(small); c["features"][2]["properties"]["row_no"]=4; check("registry_gap_rejected",lambda:m.extract_rows(c,canonical_count=3,row_start=1,row_end=3),"row registry mismatch")
    c=deepcopy(small); c["features"][0]["geometry"]["coordinates"][0]+=0.01; check("coordinate_disagreement_rejected",lambda:m.extract_rows(c,canonical_count=3,row_start=1,row_end=3),"coordinate fields disagree")
    c=deepcopy(small); c["features"][0]["geometry"]["type"]="Polygon"; check("non_point_rejected",lambda:m.extract_rows(c,canonical_count=3,row_start=1,row_end=3),"must have Point")
    c=deepcopy(small); c["features"][0]["properties"]["hmlr_lon"]="nan"; check("nonfinite_rejected",lambda:m.extract_rows(c,canonical_count=3,row_start=1,row_end=3),"non-finite")
    c=deepcopy(small); c["features"][0]["properties"]["hmlr_lon"]=10; c["features"][0]["geometry"]["coordinates"][0]=10; check("out_of_bounds_rejected",lambda:m.extract_rows(c,canonical_count=3,row_start=1,row_end=3),"outside Great Britain")
    check("invalid_range_rejected",lambda:m.extract_rows(small,canonical_count=3,row_start=3,row_end=2),"invalid shard range")
    check("wrong_feature_count_rejected",lambda:m.extract_rows(small,canonical_count=4,row_start=1,row_end=3),"expected 4 features")
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,
         "test_type":"canonical_extractor_full_92283_fixture_regression",
         "source_script_blob_sha":"ec41f120830483b1cb35df5d7b054a5fffaab743",
         "checks_passed":sum(x["passed"] for x in checks),"checks_total":len(checks),
         "all_passed":all(x["passed"] for x in checks),"checks":checks,
         "offline_canonical_features_exercised":92283,"offline_shard_rows_exercised":30761,
         "actual_canonical_shard_rows_exported":0,"canonical_parcel_matches":0,
         "future_growth_scores_produced":0,"actual_business_data_rows_written":0,
         "fixture_only_not_live_product":True,"final_ready":False,
         "fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out)); return 0 if out["all_passed"] else 1
if __name__=="__main__": raise SystemExit(main())
