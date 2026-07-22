#!/usr/bin/env python3
from __future__ import annotations
import argparse,ast,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def main():
 o=args();root=(o.repo_root or Path.cwd()).resolve();a=Path(__file__).resolve().parent;files=["093_runtime_watchdog_supervisor.py","094_runtime_watchdog_supervisor_tests.py","095_revision18_liveness_acceptance.py","096_revision18_liveness_acceptance_tests.py","097_full_pipeline_revision18_entry.py","098_revision18_pipeline_manifest_tests.py"];c=[]
 def ok(n,v):
  if not v:raise AssertionError(n)
  c.append(n)
 texts={n:(a/n).read_text(encoding="utf-8") for n in files}
 for n,t in texts.items():ast.parse(t);c.append("parse_"+n)
 p=texts["097_full_pipeline_revision18_entry.py"];ok("pipeline_uses_watchdog_supervise","wd.supervise(" in p);ok("pipeline_has_18_steps",p.count('{"file":')==18);ok("pipeline_hard_timeout_24h","86400" in p);ok("pipeline_stall_timeout","stall_timeout_seconds" in p);ok("pipeline_single_child","max_active_children" in p and '"max_active_children":1' in p);ok("pipeline_live_feed","operation_feed_revision18_runtime_latest.json" in p);ok("pipeline_targets_530_tests","530" in p);ok("pipeline_targets_74_checks","74" in p);ok("pipeline_no_shell_true","shell=True" not in p);ok("safety_flags_retained",all(x in p for x in ['"final_ready":False','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False']))
 e=16;z={"schema_version":1,"suite":"revision18_pipeline_manifest","tests_expected":e,"tests_passed":len(c),"tests_failed":e-len(c),"checks":c,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};print(json.dumps(z,indent=2));return 0 if len(c)==e else 2
if __name__=="__main__":raise SystemExit(main())
