#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def mod():
 p=Path(__file__).resolve().parent/"095_revision18_liveness_acceptance.py";s=importlib.util.spec_from_file_location("a",p)
 if not s or not s.loader:raise ImportError(p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def good(m):
 steps=[{"step_name":n,"state":"passed","exit_code":0,"timeout_kind":None,"parallel_runner":False,"new_runner":False,"heartbeat_cycles_succeeded":1,"heartbeat_write_errors":[]} for n in sorted(m.REQUIRED_PRIOR_STEPS)]
 return {"steps":steps,"max_active_children":1,"heartbeat_writes":len(steps),"heartbeat_write_errors":0,"single_shared_runner_only":True,"actual_business_data_rows_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
def main():
 m=mod();c=[]
 def ok(n,v):
  if not v:raise AssertionError(n)
  c.append(n)
 ok("requires_18_prior_steps",len(m.REQUIRED_PRIOR_STEPS)==18 and "FULL_RELEASE_HYDRATION_TESTS" in m.REQUIRED_PRIOR_STEPS and "REV18_LIVENESS_ACCEPTANCE" not in m.REQUIRED_PRIOR_STEPS);ok("valid",m.evaluate(good(m))["passed"])
 q=good(m);q["steps"]=q["steps"][:-1];q["heartbeat_writes"]-=1;ok("missing",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["state"]="blocked";ok("blocked",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["exit_code"]=2;ok("exit",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["timeout_kind"]="stall_timeout";ok("timeout",not m.evaluate(q)["passed"])
 q=good(m);q["max_active_children"]=2;ok("parallel",not m.evaluate(q)["passed"])
 q=good(m);q["heartbeat_writes"]=0;ok("aggregate",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["heartbeat_cycles_succeeded"]=0;q["heartbeat_writes"]-=1;ok("no_cycle",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["heartbeat_write_errors"]=[{"error":"x"}];q["heartbeat_write_errors"]=1;ok("heartbeat_error",not m.evaluate(q)["passed"])
 q=good(m);q["heartbeat_write_errors"]=1;ok("error_aggregate",not m.evaluate(q)["passed"])
 q=good(m);q["single_shared_runner_only"]=False;ok("policy",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["parallel_runner"]=True;ok("parallel_flag",not m.evaluate(q)["passed"])
 q=good(m);q["steps"][0]["new_runner"]=True;ok("new_runner",not m.evaluate(q)["passed"])
 q=good(m);q["fake_data"]=True;ok("fake",not m.evaluate(q)["passed"])
 q=good(m);q["db_write"]=True;ok("db",not m.evaluate(q)["passed"])
 q=good(m);q["actual_business_data_rows_written"]=1;ok("rows",not m.evaluate(q)["passed"])
 e=17;z={"schema_version":3,"suite":"revision18_liveness_acceptance","tests_expected":e,"tests_passed":len(c),"tests_failed":e-len(c),"checks":c,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};print(json.dumps(z,indent=2));return 0 if len(c)==e else 2
if __name__=="__main__":raise SystemExit(main())
