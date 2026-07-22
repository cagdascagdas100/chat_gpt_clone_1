#!/usr/bin/env python3
"""Revision 18 serial pipeline with child watchdogs, stall detection and live web heartbeats."""
from __future__ import annotations
import importlib.util,json,os,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
SLOT_ID="internet_access_3";TASK_ID="aays1-internet-access-3-revision18-2-watchdog-failsafe-20260722"
BASE="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/"
RUNNER_OUTPUT=BASE+"runner_outputs/059_revision18_watchdog_pipeline_latest.json";WEB_OUTPUT="england_map_web/data/aays_21_slots/internet_access_3/revision18_watchdog_pipeline_latest.json"
RUNNER_HEARTBEAT=BASE+"runner_outputs/058_runtime_watchdog_latest.json";WEB_HEARTBEAT="england_map_web/data/aays_21_slots/internet_access_3/runtime_watchdog_latest.json";RUNTIME_FEED="england_map_web/data/aays_21_slots/internet_access_3/operation_feed_revision18_runtime_latest.json"
def now():return datetime.now(timezone.utc).isoformat()
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repo root")
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=p.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def watchdog():
 p=Path(__file__).resolve().parent/"093_runtime_watchdog_supervisor.py";s=importlib.util.spec_from_file_location("rev18_watchdog",p)
 if not s or not s.loader:raise ImportError(p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def payload(state,steps,plan,current,events):
 return {"schema_version":2,"slot_id":SLOT_ID,"task_id":TASK_ID,"state":state,"updated_at":now(),"current_step":current,"steps_completed":len(steps),"steps_total":len(plan),"steps":steps,"max_active_children":1,"heartbeat_writes":len(steps),"effective_pipeline_steps":73,"contract_tests_target":534,"official_source_checks_target":74,"events_count":len(events),"single_shared_runner_only":True,"new_runner":False,"parallel_runner":False,"parcel_relations_promoted":0,"confidence_uplifts":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
def main():
 r=root();a=Path(__file__).resolve().parent;wd=watchdog();tmp=Path(tempfile.gettempdir());ro=r/(BASE+"runner_outputs");web=r/"england_map_web/data/aays_21_slots/internet_access_3";cache=tmp/"aays_internet_access_3_release_cache";db=tmp/"aays_internet_access_3_uprn_join_revision17.sqlite"
 plan=[
  {"file":"098_revision18_pipeline_manifest_tests.py","name":"REV18_PIPELINE_MANIFEST_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"094_runtime_watchdog_supervisor_tests.py","name":"RUNTIME_WATCHDOG_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"096_revision18_liveness_acceptance_tests.py","name":"REV18_LIVENESS_ACCEPTANCE_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"092_revision17_pipeline_manifest_tests.py","name":"REV17_MANIFEST_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"086_release_cache_identity_ledger_tests.py","name":"CACHE_IDENTITY_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"088_exact_uprn_postcode_join_revision17_tests.py","name":"CHECKPOINT_JOIN_TESTS","hard":1200,"stall":1200,"watch":[]},
  {"file":"090_revision17_runtime_acceptance_tests.py","name":"REV17_ACCEPTANCE_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"078_runtime_resource_download_preflight_tests.py","name":"REV16_RESOURCE_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"080_exact_uprn_postcode_join_revision16_tests.py","name":"REV16_JOIN_TESTS","hard":1200,"stall":1200,"watch":[]},
  {"file":"082_revision16_pipeline_manifest_tests.py","name":"REV16_MANIFEST_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"084_revision16_runtime_acceptance_tests.py","name":"REV16_ACCEPTANCE_TESTS","hard":900,"stall":900,"watch":[]},
  {"file":"069_full_pipeline_revision14_entry.py","name":"REV14_EFFECTIVE_PIPELINE","hard":21600,"stall":7200,"watch":[ro,web]},
  {"file":"077_runtime_resource_download_preflight.py","name":"RESOURCE_PREFLIGHT","hard":1200,"stall":600,"watch":[ro/"052_runtime_resource_download_preflight_latest.json",web/"runtime_resource_download_preflight_latest.json"]},
  {"file":"085_release_cache_identity_ledger.py","name":"CACHE_IDENTITY_LEDGER","hard":1200,"stall":600,"watch":[cache,ro/"055_release_cache_identity_ledger_latest.json",web/"release_cache_identity_ledger_latest.json"]},
  {"file":"071_full_release_hydration_manifest.py","name":"FULL_RELEASE_HYDRATION","hard":86400,"stall":3600,"watch":[cache,ro/"050_full_release_hydration_manifest_latest.json",web/"full_release_hydration_manifest_latest.json"]},
  {"file":"087_exact_uprn_postcode_join_revision17.py","name":"CHECKPOINTED_EXACT_JOIN","hard":86400,"stall":7200,"watch":[db,ro/"056_exact_uprn_postcode_join_revision17_latest.json",web/"exact_uprn_postcode_join_revision17_latest.json",web/"exact_uprn_postcode_join_revision17_preview_latest.json"]},
  {"file":"089_revision17_runtime_acceptance.py","name":"REV17_RUNTIME_ACCEPTANCE","hard":1200,"stall":600,"watch":[ro/"057_revision17_runtime_acceptance_latest.json",web/"revision17_runtime_acceptance_latest.json"]},
  {"file":"095_revision18_liveness_acceptance.py","name":"REV18_LIVENESS_ACCEPTANCE","hard":1200,"stall":600,"watch":[ro/"060_revision18_liveness_acceptance_latest.json",web/"revision18_liveness_acceptance_latest.json"]}]
 steps=[];events=[];pr=r/RUNNER_OUTPUT;pw=r/WEB_OUTPUT;feed=r/RUNTIME_FEED;hearts=[r/RUNNER_HEARTBEAT,r/WEB_HEARTBEAT]
 def publish(state,current):
  z=payload(state,steps,plan,current,events);write(pr,z);write(pw,z);write(feed,{"schema_version":2,"slot_id":SLOT_ID,"contract_revision":18,"updated_at":now(),"display_mode":"line_by_line_runtime","operations":events,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False})
 publish("running",None);total=len(plan)
 for i,x in enumerate(plan,1):
  n=x["name"];events.append({"sequence":1000+i*2-1,"status":"RUNNING","operation":n,"detail":f"Sequential watchdog-supervised step {i}/{total} started.","updated_at":now()});publish("running",n)
  z=wd.supervise(command=[sys.executable,str(a/x["file"]),"--repo-root",str(r)],cwd=r,step_name=n,hard_timeout_seconds=int(x["hard"]),stall_timeout_seconds=int(x["stall"]),watch_paths=[Path(p) for p in x["watch"]],heartbeat_paths=hearts,poll_seconds=5.,heartbeat_seconds=30.,step_index=i,step_total=total);steps.append(z)
  events.append({"sequence":1000+i*2,"status":"PASS" if z["state"]=="passed" else "BLOCKED","operation":n,"detail":f"exit={z['exit_code']} timeout={z['timeout_kind']} elapsed={z['elapsed_seconds']}s","updated_at":now()})
  if z["state"]!="passed":publish("blocked",n);print(json.dumps(payload("blocked",steps,plan,n,events),ensure_ascii=False,indent=2));return 2
  publish("running",None)
 publish("pipeline_passed",None);print(json.dumps(payload("pipeline_passed",steps,plan,None,events),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
