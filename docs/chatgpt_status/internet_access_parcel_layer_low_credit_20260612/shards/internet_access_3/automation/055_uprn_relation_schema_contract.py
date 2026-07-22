#!/usr/bin/env python3
"""Publish fail-closed OS Open UPRN and ONS UPRN relation schema contract."""
from __future__ import annotations
import argparse,hashlib,json,os,tempfile
from pathlib import Path
SLOT="internet_access_3";OS_FIELDS=["UPRN","X_COORDINATE","Y_COORDINATE","LATITUDE","LONGITUDE"];POSTCODE_ALIASES=["PCDS","PCD","PCD2","POSTCODE"]
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path)
 p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/043_uprn_relation_schema_contract_latest.json")
 p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/uprn_relation_schema_contract_latest.json");return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+".")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def main():
 o=args();r=root(o.repo_root);contract={"os_open_uprn":{"join_key":"UPRN","required_fields":OS_FIELDS,"geometry_semantics":"ADDRESS_POINT_BNG_AND_ETRS89_NOT_PARCEL_BOUNDARY"},"onsud_nsul":{"join_key":"UPRN","postcode_field_aliases":POSTCODE_ALIASES,"allocation_semantics":"UPRN_TO_POSTCODE_OR_GEOGRAPHY_LOOKUP"},"join_acceptance":{"same_uprn_required":True,"postcode_normalization_required":True,"duplicate_uprn_conflicts_expected":0,"minimum_join_ratio":0.98,"nearest_point_join_forbidden":True,"parcel_relation_promotion_forbidden":True}}
 d=hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 s={"schema_version":1,"slot_id":SLOT,"state":"contract_ready_pending_release_bytes","contract":contract,"contract_sha256":d,"source_checks_executed":2,"full_release_bytes_hydrated":False,"schema_runtime_validated":False,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
