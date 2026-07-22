#!/usr/bin/env python3
from __future__ import annotations
import argparse,ast,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def main():
 o=args();a=Path(__file__).resolve().parent;files=["071_full_release_hydration_manifest.py","072_full_release_hydration_manifest_tests.py","093_runtime_watchdog_supervisor.py","094_runtime_watchdog_supervisor_tests.py","095_revision18_liveness_acceptance.py","096_revision18_liveness_acceptance_tests.py","097_full_pipeline_revision18_entry.py","098_revision18_pipeline_manifest_tests.py"];c=[]
 def ok(n,v):
  if not v:raise AssertionError(n)
  c.append(n)
 texts={n:(a/n).read_text(encoding="utf-8") for n in files}
 for n,t in texts.items():ast.parse(t);c.append("parse_"+n)
 p=texts["097_full_pipeline_revision18_entry.py"];w=texts["093_runtime_watchdog_supervisor.py"];ac=texts["095_revision18_liveness_acceptance.py"];h=texts["071_full_release_hydration_manifest.py"]
 ok("pipeline_has_19_steps",p.count('{"file":')==19);ok("targets_569_tests","569" in p);ok("targets_80_checks","80" in p);ok("hydration_tests_direct","072_full_release_hydration_manifest_tests.py" in p);ok("hydration_worker_direct","071_full_release_hydration_manifest.py" in p);ok("single_child",'"max_active_children":1' in p);ok("actual_heartbeat_sum","heartbeat_cycles_succeeded" in p and "sum(int(x.get" in p);ok("ignores_heartbeat_temp","rp.name.startswith(q.name+\".\")" in w);ok("directory_mtime_not_progress","newest=0" in w);ok("heartbeat_failure_cleanup",'kind="heartbeat_write_error";term=terminate_tree(p)' in w);ok("acceptance_requires_hydration_tests","FULL_RELEASE_HYDRATION_TESTS" in ac);ok("ons_html_json_rejected","HTML_OR_XML_ERROR_BODY" in h and "JSON_ERROR_BODY" in h);ok("ons_uprn_postcode_headers","UPRN_POSTCODE" in h and "POSTCODE_HEADER_MISSING" in h);ok("no_shell_true","shell=True" not in p);ok("hydration_and_join_24h",p.count('"hard":86400')>=2);ok("safety",all(x in p for x in ['"final_ready":False','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False']))
 e=24;z={"schema_version":5,"suite":"revision18_pipeline_manifest","tests_expected":e,"tests_passed":len(c),"tests_failed":e-len(c),"checks":c,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};print(json.dumps(z,indent=2));return 0 if len(c)==e else 2
if __name__=="__main__":raise SystemExit(main())
