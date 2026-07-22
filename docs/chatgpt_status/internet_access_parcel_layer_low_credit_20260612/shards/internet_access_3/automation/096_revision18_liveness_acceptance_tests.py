#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def mod():
 p=Path(__file__).resolve().parent/"095_revision18_liveness_acceptance.py";s=importlib.util.spec_from_file_location("acceptance",p)
 if not s or not s.loader:raise ImportError(p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def good(m):
 return {"steps":[{"step_name":n,"state":"passed","exit_code":0,"timeout_kind":None,"parallel_runner":False,"new_runner":False} for n in sorted(m.REQUIRED_PRIOR_STEPS)],"max_active_children":1,"heartbeat_writes":len(m.REQUIRED_PRIOR_STEPS),"single_shared_runner_only":True,"actual_business_data_rows_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
def main():
 m=mod();c=[]
 def ok(n,v):
  if not v:raise AssertionError(n)
  c.append(n)
 p=good(m);ok("valid_pipeline_passes",m.evaluate(p)["passed"])
 q=good(m);q["steps"]=q["steps"][:-1];ok("missing_step_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["state"]="blocked";ok("blocked_step_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["exit_code"]=2;ok("nonzero_exit_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["timeout_kind"]="stall_timeout";ok("timeout_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["max_active_children"]=2;ok("parallel_children_block",not m.evaluate(q)["passed"])
 q=good(m);q["heartbeat_writes"]=0;ok("missing_heartbeats_block",not m.evaluate(q)["passed"])
 q=good(m);q["single_shared_runner_only"]=False;ok("runner_policy_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["parallel_runner"]=True;ok("parallel_runner_flag_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["new_runner"]=True;ok("new_runner_flag_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["fake_data"]=True;ok("fake_data_flag_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["db_write"]=True;ok("db_write_flag_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["actual_business_data_rows_written"]=1;ok("business_row_claim_blocks",not m.evaluate(q)["passed"])
 q=good(m);q["steps"].append("bad");ok("invalid_step_record_blocks",not m.evaluate(q)["passed"])
 e=14;z={"schema_version":1,"suite":"revision18_liveness_acceptance","tests_expected":e,"tests_passed":len(c),"tests_failed":e-len(c),"checks":c,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};print(json.dumps(z,indent=2));return 0 if len(c)==e else 2
if __name__=="__main__":raise SystemExit(main())
