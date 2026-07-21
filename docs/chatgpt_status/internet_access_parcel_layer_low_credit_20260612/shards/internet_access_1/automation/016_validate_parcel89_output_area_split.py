#!/usr/bin/env python3
"""Validate parcel_89 two-output-area ambiguity evidence fail-closed."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path

POSTCODE_RE=re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s\d[A-Z]{2}$")
def validate(payload:dict)->list[dict]:
    c=payload["ranked_candidates"]; s=payload["summary"]; clusters=payload["output_area_clusters"]
    checks=[]
    def add(name,ok): checks.append({"name":name,"pass":bool(ok)})
    add("slot_id",payload.get("slot_id")=="internet_access_1")
    add("parcel_89",payload.get("parcel",{}).get("parcel_id")=="parcel_89")
    add("nine_candidates",len(c)==9)
    add("unique_postcodes",len({x["postcode"] for x in c})==9)
    add("postcode_format",all(POSTCODE_RE.match(x["postcode"]) for x in c))
    add("rank_sequence",[x["rank"] for x in c]==list(range(1,10)))
    add("distance_sorted",[x["distance_m"] for x in c]==sorted(x["distance_m"] for x in c))
    add("two_output_areas",set(x["oa21cd"] for x in c)=={"E00000534","E00000536"})
    add("cluster_counts",sorted(x["candidate_count"] for x in clusters.values())==[3,6])
    add("nearest_two_different_oa",c[0]["oa21cd"]!=c[1]["oa21cd"])
    add("nearest_distance",abs(c[0]["distance_m"]-58.3)<0.05)
    add("second_distance",abs(c[1]["distance_m"]-65.1)<0.05)
    add("gap_below_10m",s["nearest_second_gap_m"]<10)
    add("top_three_span_below_15m",s["top_three_distance_span_m"]<15)
    add("five_within_100m",sum(x["distance_m"]<=100 for x in c)==5)
    add("nine_within_160m",sum(x["distance_m"]<=160 for x in c)==9)
    add("no_canonical_selection",not s["canonical_postcode_selected"])
    add("postcode_null_decision",payload.get("decision")=="KEEP_POSTCODE_NULL_FAIL_CLOSED")
    add("accuracy_zero",payload.get("internet_accuracy")=="0/4")
    add("no_broadband_value",payload.get("broadband_value_allowed") is False)
    add("official_direct_rows_zero",payload.get("official_contract",{}).get("direct_feature_rows_read")==0)
    add("no_business_write",payload.get("business_rows_written")==0 and payload.get("db_write") is False)
    add("no_migration",payload.get("migration") is False)
    add("final_ready_false",payload.get("final_ready") is False)
    return checks

def main():
    p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("--output",type=Path); a=p.parse_args()
    payload=json.loads(a.input.read_text(encoding="utf-8"))
    checks=validate(payload); report={"schema_version":1,"slot_id":"internet_access_1","status":"PASS" if all(x["pass"] for x in checks) else "FAIL","checks_passed":sum(x["pass"] for x in checks),"checks_failed":sum(not x["pass"] for x in checks),"checks_total":len(checks),"checks":checks,"business_rows_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    if a.output: a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    raise SystemExit(0 if report["status"]=="PASS" else 1)
if __name__=="__main__":
    main()
