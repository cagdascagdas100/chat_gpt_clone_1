#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def validate(p):
 s=p.get("sources") or []; checks=[]
 def c(n,v,a=None): checks.append({"name":n,"pass":bool(v),"actual":a})
 c("seven_sources",len(s)==7,len(s)); names={x["name"]:x for x in s}
 allowed=[x for x in s if x.get("broadband_value_allowed")]
 c("exactly_one_broadband_source",len(allowed)==1,[x["name"] for x in allowed])
 c("only_ofcom_package_allows_values",len(allowed)==1 and allowed[0]["name"].startswith("Ofcom Spring 2026 fixed broadband"))
 c("ofcom_upgrade_requires_r2",allowed and allowed[0].get("accuracy_upgrade_allowed_only_after_corrected_r2_row") is True)
 c("methodology_no_values",names["Ofcom Spring 2026 methodology v2"]["broadband_value_allowed"] is False)
 c("onspd_no_values",names["ONSPD May 2026 postcode centroids"]["broadband_value_allowed"] is False)
 c("nhspd_no_values",names["NHSPD May 2026 postcode centroids"]["broadband_value_allowed"] is False)
 c("nhs_ods_no_values",names["NHS England ODS London pcodey56"]["broadband_value_allowed"] is False)
 c("postcodes_io_no_values",names["Postcodes.io"]["broadband_value_allowed"] is False)
 c("metadata_sources_no_accuracy_upgrade",all(x.get("accuracy_upgrade_allowed") is False for x in s if not x.get("broadband_value_allowed")))
 c("addressbase_not_promoted",names["Ordnance Survey AddressBase Premium"]["promoted"] is False)
 c("nhspd_new_promoted",names["NHSPD May 2026 postcode centroids"]["new_in_this_round"] is True and names["NHSPD May 2026 postcode centroids"]["promoted"] is True)
 c("no_business_write",p.get("business_rows_written")==0)
 c("safety_flags",p.get("fake_data") is False and p.get("db_write") is False and p.get("migration") is False and p.get("production_deploy") is False and p.get("final_ready") is False)
 return {"schema_version":1,"slot_id":"internet_access_1","status":"PASS" if all(x["pass"] for x in checks) else "FAIL","checks_total":len(checks),"checks_passed":sum(x["pass"] for x in checks),"checks_failed":sum(not x["pass"] for x in checks),"checks":checks,"new_source_candidates":1,"new_promoted_sources":1,"internet_accuracy_upgraded_rows":0,"business_rows_written":0,"fake_data":False,"final_ready":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();o=validate(json.loads(a.input.read_text()));a.output.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n");raise SystemExit(0 if o["status"]=="PASS" else 1)
if __name__=="__main__":main()
