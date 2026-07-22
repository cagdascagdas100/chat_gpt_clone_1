#!/usr/bin/env python3
"""Build a 40-row source evidence matrix without promoting parcel-level claims."""
from __future__ import annotations
import argparse,hashlib,json,os,tempfile
from pathlib import Path
from typing import Any
SLOT="internet_access_3";ROOT="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs";TARGETS="england_map_web/data/aays_21_slots/internet_access_3/prepared_target_rows_revision10_latest.json";MANIFEST="england_map_web/data/aays_21_slots/internet_access_3/stratified_candidate_manifest_latest.json"
SOURCES={"migration":f"{ROOT}/001_migration_and_no_data_latest.json","ofcom":f"{ROOT}/021_stratified_ofcom_adapter_latest.json","onspd":f"{ROOT}/022_stratified_onspd_adapter_latest.json","hmlr":f"{ROOT}/019_hmlr_exact_stratified_manifest_audit_latest.json","runtime_acceptance":f"{ROOT}/025_runtime_output_integrity_acceptance_latest.json","source_provenance":f"{ROOT}/029_official_source_package_provenance_latest.json","chain_acceptance":f"{ROOT}/030_source_provenance_chain_acceptance_latest.json"}
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--runner-output",default=f"{ROOT}/035_target_evidence_matrix_latest.json");p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/target_evidence_matrix_latest.json");return p.parse_args()
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
def recursive_rows(v:Any):
 found={}
 if isinstance(v,dict):
  row=v.get("row_no")
  try:
   if row is not None:found[int(row)]=v
  except (TypeError,ValueError):pass
  for c in v.values():found.update(recursive_rows(c))
 elif isinstance(v,list):
  for c in v:found.update(recursive_rows(c))
 return found
def state_pass(x):return isinstance(x,dict) and str(x.get("state","")).lower() in {"passed","acceptance_passed","runtime_validation_passed","pipeline_passed","provenance_passed","attribution_bundle_passed","matrix_complete"}
def main():
 o=args();r=root(o.repo_root);tp=r/TARGETS
 if not tp.exists():raise FileNotFoundError(TARGETS)
 targets=load(tp).get("targets") or []
 if len(targets)!=40:raise ValueError(f"target count mismatch: {len(targets)}")
 ids=set();mp=r/MANIFEST
 if mp.exists():
  m=load(mp)
  if isinstance(m,list):ids={int(x["row_no"]) for x in m}
 payloads={};maps={};missing=[]
 for key,rel in SOURCES.items():
  p=r/rel
  if not p.exists():missing.append(key);continue
  payloads[key]=load(p);maps[key]=recursive_rows(payloads[key])
 rows=[]
 for t in targets:
  n=int(t["row_no"]);cells={"migration":n in maps.get("migration",{}),"stratified_manifest":n in ids,"ofcom":n in maps.get("ofcom",{}),"onspd":n in maps.get("onspd",{}),"hmlr":n in maps.get("hmlr",{}),"source_provenance":state_pass(payloads.get("source_provenance")),"runtime_acceptance":state_pass(payloads.get("runtime_acceptance")),"chain_acceptance":state_pass(payloads.get("chain_acceptance"))};complete=all(cells.values());rows.append({"target_index":t.get("target_index"),"row_no":n,"status":"EVIDENCE_COMPLETE_NOT_PROMOTED" if complete else "PENDING_RUNTIME_EVIDENCE","checks":cells,"checks_passed":sum(1 for v in cells.values() if v),"checks_total":len(cells),"candidate_claimed":False,"parcel_relation_promoted":False,"confidence_uplift":0})
 complete=sum(1 for x in rows if x["status"]=="EVIDENCE_COMPLETE_NOT_PROMOTED");s={"schema_version":1,"slot_id":SLOT,"state":"matrix_complete" if complete==40 else "pending_runtime","target_count":40,"evidence_complete_count":complete,"pending_count":40-complete,"missing_runtime_sources":missing,"rows":rows,"manifest_sha256":hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest() if ids else None,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if complete==40 else 2
if __name__=="__main__":raise SystemExit(main())
