#!/usr/bin/env python3
from __future__ import annotations
import argparse,ast,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def main():
 o=args();a=Path(__file__).resolve().parent;files=["093_runtime_watchdog_supervisor.py","094_runtime_watchdog_supervisor_tests.py","095_revision18_liveness_acceptance.py","096_revision18_liveness_acceptance_tests.py","097_full_pipeline_revision18_entry.py","098_revision18_pipeline_manifest_tests.py"];c=[]
 def ok(n,v):
  if not v:raise AssertionError(n)
  c.append(n)
 texts={n:(a/n).read_text(encoding="utf-8") for n in files}
 for n,t in texts.items():ast.parse(t);c.append("parse_"+n)
 p=texts["097_full_pipeline_revision18_entry.py"];w=texts["093_runtime_watchdog_supervisor.py"];ac=texts["095_revision18_liveness_acceptance.py"]
 ok("uses_watchdog","wd.supervise(" in p);ok("pipeline_has_19_steps",p.count('{"file":')==19);ok("hard_timeout_24h","86400" in p);ok("stall_timeout","stall_timeout_seconds" in p);ok("single_child",'"max_active_children":1' in p);ok("live_feed","operation_feed_revision18_runtime_latest.json" in p);ok("targets_562_tests","562" in p);ok("targets_78_checks","78" in p);ok("hydration_tests_direct","072_full_release_hydration_manifest_tests.py" in p);ok("hydration_worker_direct","071_full_release_hydration_manifest.py" in p);ok("ignores_heartbeat_exact","ignored=_resolved_set(heartbeat_paths)" in w);ok("ignores_heartbeat_temp","rp.name.startswith(q.name+\".\")" in w);ok("directory_own_mtime_not_progress","newest=0" in w);ok("heartbeat_failure_cleanup",'kind="heartbeat_write_error";term=terminate_tree(p)' in w);ok("taskkill_fallback","process_kill_after_taskkill_nonzero" in w);ok("actual_heartbeat_sum","heartbeat_cycles_succeeded" in p and "sum(int(x.get" in p);ok("acceptance_requires_hydration_tests","FULL_RELEASE_HYDRATION_TESTS" in ac and "len(REQUIRED_PRIOR_STEPS)" in ac);ok("safety",all(x in p for x in ['"final_ready":False','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False']))
 e=24;z={"schema_version":4,"suite":"revision18_pipeline_manifest","tests_expected":e,"tests_passed":len(c),"tests_failed":e-len(c),"checks":c,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};print(json.dumps(z,indent=2));return 0 if len(c)==e else 2
if __name__=="__main__":raise SystemExit(main())
