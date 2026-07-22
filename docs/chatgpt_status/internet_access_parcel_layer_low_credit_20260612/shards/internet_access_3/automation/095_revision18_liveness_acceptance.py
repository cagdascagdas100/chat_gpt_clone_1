#!/usr/bin/env python3
"""Fail-closed acceptance for the 17 prior watchdog-supervised steps.

This acceptance is the 18th pipeline step, so it validates only the 17 steps that
must complete before it. Requiring itself would create a permanent circular block.
"""
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
from typing import Any
SLOT_ID="internet_access_3";BASE="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/"
DEFAULT_PIPELINE=BASE+"059_revision18_watchdog_pipeline_latest.json";DEFAULT_RUNNER_OUTPUT=BASE+"060_revision18_liveness_acceptance_latest.json";DEFAULT_WEB_OUTPUT="england_map_web/data/aays_21_slots/internet_access_3/revision18_liveness_acceptance_latest.json"
REQUIRED_PRIOR_STEPS={"REV18_PIPELINE_MANIFEST_TESTS","RUNTIME_WATCHDOG_TESTS","REV18_LIVENESS_ACCEPTANCE_TESTS","REV17_MANIFEST_TESTS","CACHE_IDENTITY_TESTS","CHECKPOINT_JOIN_TESTS","REV17_ACCEPTANCE_TESTS","REV16_RESOURCE_TESTS","REV16_JOIN_TESTS","REV16_MANIFEST_TESTS","REV16_ACCEPTANCE_TESTS","REV14_EFFECTIVE_PIPELINE","RESOURCE_PREFLIGHT","CACHE_IDENTITY_LEDGER","FULL_RELEASE_HYDRATION","CHECKPOINTED_EXACT_JOIN","REV17_RUNTIME_ACCEPTANCE"}
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--pipeline",default=DEFAULT_PIPELINE);p.add_argument("--runner-output",default=DEFAULT_RUNNER_OUTPUT);p.add_argument("--web-output",default=DEFAULT_WEB_OUTPUT);return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repo root")
def load(p):
 with p.open("r",encoding="utf-8-sig") as h:return json.load(h)
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=p.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def evaluate(pipeline:dict[str,Any]):
 b=[];steps=pipeline.get("steps") or [];names={str(x.get("step_name") or x.get("name") or "") for x in steps if isinstance(x,dict)};missing=sorted(REQUIRED_PRIOR_STEPS-names)
 if missing:b.append("MISSING_REQUIRED_PRIOR_STEPS:"+",".join(missing))
 if len(steps)!=len(REQUIRED_PRIOR_STEPS):b.append(f"PRIOR_STEP_COUNT_MISMATCH:{len(steps)}!={len(REQUIRED_PRIOR_STEPS)}")
 if "REV18_LIVENESS_ACCEPTANCE" in names:b.append("CIRCULAR_SELF_STEP_PRESENT_BEFORE_ACCEPTANCE")
 for x in steps:
  if not isinstance(x,dict):b.append("INVALID_STEP_RECORD");continue
  n=str(x.get("step_name") or x.get("name") or "UNKNOWN")
  if x.get("state")!="passed":b.append(n+"_NOT_PASSED")
  if int(x.get("exit_code") if x.get("exit_code") is not None else -999)!=0:b.append(n+"_NONZERO_EXIT")
  if x.get("timeout_kind") is not None:b.append(n+"_TIMEOUT:"+str(x.get("timeout_kind")))
  if x.get("parallel_runner") is not False or x.get("new_runner") is not False:b.append(n+"_RUNNER_POLICY_VIOLATION")
 if int(pipeline.get("max_active_children") or 0)!=1:b.append("MAX_ACTIVE_CHILDREN_NOT_ONE")
 if int(pipeline.get("heartbeat_writes") or 0)<len(steps):b.append("INSUFFICIENT_HEARTBEAT_WRITES")
 if pipeline.get("single_shared_runner_only") is not True:b.append("SINGLE_SHARED_RUNNER_POLICY_MISSING")
 for f in ("fake_data","db_write","migration","production_deploy"):
  if pipeline.get(f) is not False:b.append(f.upper()+"_SAFETY_FLAG")
 if int(pipeline.get("actual_business_data_rows_written") or 0)!=0:b.append("WATCHDOG_PIPELINE_MUST_NOT_CLAIM_BUSINESS_ROWS")
 return {"passed":not b,"blockers":b,"prior_steps_observed":len(steps),"required_prior_steps":len(REQUIRED_PRIOR_STEPS),"self_dependency_forbidden":True,"timeout_steps":[str(x.get("step_name")) for x in steps if isinstance(x,dict) and x.get("timeout_kind")],"failed_steps":[str(x.get("step_name")) for x in steps if isinstance(x,dict) and x.get("state")!="passed"]}
def main():
 o=args();r=root(o.repo_root);result=evaluate(load(r/o.pipeline));now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat();s={"schema_version":1,"slot_id":SLOT_ID,"task_id":"aays1-internet-access-3-revision18-liveness-acceptance-20260722","state":"runtime_validation_passed" if result["passed"] else "blocked","updated_at":now,"result":result,"source_checks_executed":4,"actual_business_data_rows_written":0,"parcel_relations_promoted":0,"confidence_uplifts":0,"single_shared_runner_only":True,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if result["passed"] else 2
if __name__=="__main__":raise SystemExit(main())
