#!/usr/bin/env python3
"""Create a fail-closed browser acceptance snapshot for internet_access_3."""
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
WEB="england_map_web/data/aays_21_slots/internet_access_3";SLOT="internet_access_3"
FEEDS=[f"{WEB}/operation_feed_latest.json",f"{WEB}/operation_feed_revision6_latest.json",f"{WEB}/operation_feed_revision7_latest.json",f"{WEB}/operation_feed_revision8_latest.json",f"{WEB}/operation_feed_revision9_latest.json",f"{WEB}/operation_feed_revision10_latest.json",f"{WEB}/operation_feed_revision11_latest.json"]
REQUIRED={"progress":f"{WEB}/progress_latest.json","matrix":f"{WEB}/target_evidence_matrix_latest.json","runtime_acceptance":f"{WEB}/runtime_output_integrity_acceptance_latest.json","source_provenance":f"{WEB}/official_source_package_provenance_latest.json","chain_acceptance":f"{WEB}/source_provenance_chain_acceptance_latest.json","attribution":f"{WEB}/release_licence_attribution_bundle_latest.json"}
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/036_web_acceptance_snapshot_latest.json");p.add_argument("--web-output",default=f"{WEB}/web_acceptance_snapshot_latest.json");return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repository root not found")
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
def passed(x,states):return isinstance(x,dict) and str(x.get("state","")).lower() in states
def main():
 o=args();r=root(o.repo_root);checks=[];blockers=[]
 def ck(n,c,d):checks.append({"name":n,"passed":bool(c),"detail":d});blockers.extend([] if c else [n])
 payloads={}
 for key,rel in REQUIRED.items():
  p=r/rel;ck(key.upper()+"_EXISTS",p.exists(),rel)
  if p.exists():payloads[key]=load(p)
 ops=[]
 for rel in FEEDS:
  p=r/rel;ck("FEED_EXISTS:"+Path(rel).name,p.exists(),rel)
  if p.exists():ops.extend(load(p).get("operations") or [])
 seq=[int(x["sequence"]) for x in ops if x.get("sequence") is not None];ck("OPERATION_ROWS_AT_LEAST_125",len(ops)>=125,len(ops));ck("OPERATION_SEQUENCES_UNIQUE",len(seq)==len(set(seq)),len(set(seq)));ck("OPERATION_SEQUENCE_RANGE",bool(seq) and min(seq)==1 and max(seq)>=125,[min(seq) if seq else None,max(seq) if seq else None])
 progress=payloads.get("progress",{});ck("RUNNER_PICKUP_OBSERVED",progress.get("runner_pickup_observed") is True,progress.get("runner_pickup_observed"));ck("RUNNER_EXECUTION_CLAIMED",progress.get("runner_execution_claimed") is True,progress.get("runner_execution_claimed"));ck("RUNTIME_ACCEPTANCE_PASSED",passed(payloads.get("runtime_acceptance"),{"acceptance_passed"}),(payloads.get("runtime_acceptance") or {}).get("state"));ck("SOURCE_PROVENANCE_PASSED",passed(payloads.get("source_provenance"),{"provenance_passed"}),(payloads.get("source_provenance") or {}).get("state"));ck("CHAIN_ACCEPTANCE_PASSED",passed(payloads.get("chain_acceptance"),{"provenance_passed","acceptance_passed"}),(payloads.get("chain_acceptance") or {}).get("state"));ck("ATTRIBUTION_BUNDLE_PASSED",passed(payloads.get("attribution"),{"attribution_bundle_passed"}),(payloads.get("attribution") or {}).get("state"));matrix=payloads.get("matrix",{});ck("TARGET_MATRIX_40_COMPLETE",matrix.get("target_count")==40 and matrix.get("evidence_complete_count")==40,[matrix.get("target_count"),matrix.get("evidence_complete_count")]);ck("ACTUAL_ROWS_30761",progress.get("actual_business_data_rows_written")==30761,progress.get("actual_business_data_rows_written"));ck("SAFETY_FLAGS_FALSE",all(progress.get(k) is False for k in ["final_ready","fake_data","db_write","migration","production_deploy"]),"progress safety")
 ok=not blockers;s={"schema_version":1,"slot_id":SLOT,"state":"browser_acceptance_passed" if ok else "blocked","checks_total":len(checks),"checks_passed":sum(1 for x in checks if x["passed"]),"checks_failed":len(blockers),"operation_rows":len(ops),"checks":checks,"blockers":blockers,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if ok else 2
if __name__=="__main__":raise SystemExit(main())
