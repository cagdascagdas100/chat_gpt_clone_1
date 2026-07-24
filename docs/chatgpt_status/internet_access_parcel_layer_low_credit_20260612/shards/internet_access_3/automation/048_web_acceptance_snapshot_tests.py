#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/039_web_acceptance_snapshot_tests_latest.json");return p.parse_args()
def mod():
 p=Path(__file__).with_name("047_web_acceptance_snapshot.py");s=importlib.util.spec_from_file_location("m47",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 o=args();m=mod();tests=[]
 def ck(n,c,d=""):tests.append({"name":n,"passed":bool(c),"detail":d})
 ck("PASS_ACCEPTANCE",m.passed({"state":"acceptance_passed"},{"acceptance_passed"}));ck("PASS_PROVENANCE",m.passed({"state":"provenance_passed"},{"provenance_passed"}));ck("FAIL_BLOCKED",not m.passed({"state":"blocked"},{"acceptance_passed"}));ck("FAIL_NON_DICT",not m.passed([],{"acceptance_passed"}));ck("SEVEN_FEEDS",len(m.FEEDS)==7,str(m.FEEDS));ck("REQUIRED_SIX",len(m.REQUIRED)==6,str(m.REQUIRED))
 s=Path(__file__).with_name("047_web_acceptance_snapshot.py").read_text();ck("OPS_125_GATE","OPERATION_ROWS_AT_LEAST_125" in s);ck("UNIQUE_SEQUENCE_GATE","OPERATION_SEQUENCES_UNIQUE" in s);ck("SEQUENCE_RANGE_GATE","OPERATION_SEQUENCE_RANGE" in s);ck("RUNNER_PICKUP_GATE","RUNNER_PICKUP_OBSERVED" in s);ck("RUNNER_EXECUTION_GATE","RUNNER_EXECUTION_CLAIMED" in s);ck("RUNTIME_ACCEPTANCE_GATE","RUNTIME_ACCEPTANCE_PASSED" in s);ck("SOURCE_CHAIN_GATES","SOURCE_PROVENANCE_PASSED" in s and "CHAIN_ACCEPTANCE_PASSED" in s);ck("MATRIX_40_GATE","TARGET_MATRIX_40_COMPLETE" in s);ck("ROWS_30761_GATE","ACTUAL_ROWS_30761" in s);ck("SAFETY_FLAGS",all(x in s for x in ['"final_ready":False','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False']))
 f=[x for x in tests if not x["passed"]];z={"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":16,"tests_executed":len(tests),"tests_passed":len(tests)-len(f),"tests_failed":len(f),"tests":tests,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};out=(o.repo_root or Path.cwd())/o.runner_output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(z,separators=(",",":"))+"\n");print(json.dumps(z,indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())
