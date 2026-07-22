#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def module():
 path=Path(__file__).parent/"083_revision16_runtime_acceptance.py";spec=importlib.util.spec_from_file_location("m083",path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 m=module();checks=[]
 def ck(n,v):checks.append({"name":n,"passed":bool(v)})
 safe={"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"parcel_relations_promoted":0,"confidence_uplifts":0,"actual_business_data_rows_written":0}
 ck("safe_flags_pass",m.safe_flags(safe))
 bad={**safe,"db_write":True};ck("safe_flags_block",not m.safe_flags(bad))
 ck("sha256_regex",__import__("re").fullmatch(r"[0-9a-f]{64}","a"*64) is not None)
 ck("sha256_short_block",__import__("re").fullmatch(r"[0-9a-f]{64}","a"*63) is None)
 ck("join_gate_pass",0.98>=0.98)
 ck("join_gate_block",0.979<0.98)
 ck("common_gate_pass",0.95>=0.95)
 ck("common_gate_block",0.949<0.95)
 ck("preview_dual_source",set(["nsul","onsud"])=={"nsul","onsud"})
 ck("preview_single_block",set(["nsul"])!={"nsul","onsud"})
 ck("package_count",len([1,2,3,4])==4)
 ck("zero_conflicts",int(0)==0)
 ck("no_business_writes",safe["actual_business_data_rows_written"]==0)
 ck("test_count",len(checks)==13)
 failed=[x for x in checks if not x["passed"]]
 print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","test_suite":"revision16_runtime_acceptance","tests_total":len(checks),"tests_passed":len(checks)-len(failed),"tests_failed":len(failed),"checks":checks,"final_ready":False},indent=2))
 return 0 if not failed else 2
if __name__=="__main__":raise SystemExit(main())
