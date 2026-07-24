#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def mod():
 p=Path(__file__).with_name("067_official_postcode_source_consensus.py");s=importlib.util.spec_from_file_location("c",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 m=mod();c=[]
 def ck(n,x,d=""):c.append({"name":n,"passed":bool(x),"detail":d})
 ck("POSTCODE_NORMALIZE",m.pc("SW1A 1AA")=="SW1A1AA");ck("POSTCODE_INVALID",m.pc("x") is None);ck("INDEX_ONE",list(m.index([{"row_no":1}]))==[1])
 try:m.index([{"row_no":1},{"row_no":1}]);dup=False
 except ValueError:dup=True
 ck("INDEX_DUPLICATE_BLOCK",dup);rows=[{"row_no":i} for i in range(100)];preview=m.evenly_spaced(rows,40);ck("PREVIEW_40",len(preview)==40);ck("PREVIEW_ENDPOINTS",preview[0]["row_no"]==0 and preview[-1]["row_no"]==99)
 source=Path(__file__).with_name("067_official_postcode_source_consensus.py").read_text();ck("SAMPLE_384",m.SAMPLE_SIZE==384);ck("OFcom_REQUIRED",'"ofcom_exact_postcode"' in source);ck("ONSPD_REQUIRED",'"onspd_exact_postcode"' in source);ck("CODEPOINT_REQUIRED",'"codepoint_exact_postcode"' in source);ck("HMLR_REQUIRED",'"hmlr_polygon"' in source);ck("CORE_95","minimum_core_ratio" in source and ".95" in source);ck("SPATIAL_90","minimum_spatial_ratio" in source and ".90" in source);ck("ROW_IDENTITY","ROW_IDENTITY" in source);ck("NO_PROMOTION",'"parcel_relation_promoted":False' in source);ck("NO_WRITES",'"actual_business_data_rows_written":0' in source)
 failed=[x for x in c if not x["passed"]];out={"schema_version":1,"slot_id":"internet_access_3","tests_executed":len(c),"tests_passed":len(c)-len(failed),"tests_failed":len(failed),"checks":c,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 if (o:=args()).repo_root:
  p=o.repo_root/"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/049_official_postcode_source_consensus_tests_latest.json";p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,separators=(",",":"))+"\n")
 print(json.dumps(out,indent=2));return 0 if not failed else 2
if __name__=="__main__":raise SystemExit(main())
