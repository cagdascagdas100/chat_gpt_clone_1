#!/usr/bin/env python3
"""Revision 12 single-runner pipeline with OS OpenData discovery and resumable package probes."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SLOT="internet_access_3";TASK="aays1-internet-access-3-revision12-download-resolution-schema-20260722"
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError
def run(r,s,n,e=None):
 c=[sys.executable,str(s),"--repo-root",str(r),*(e or [])];x=subprocess.run(c,cwd=r,text=True,capture_output=True,check=False);return {"name":n,"script":str(s.relative_to(r)),"command":c,"exit_code":x.returncode,"stdout_tail":x.stdout[-12000:],"stderr_tail":x.stderr[-12000:]}
def main():
 r=root();a=Path(__file__).parent;plan=[("058_revision12_pipeline_manifest_tests.py","REVISION12_PIPELINE_MANIFEST_TESTS_10",[]),("052_os_opendata_download_resolution_tests.py","OS_OPENDATA_DOWNLOAD_RESOLUTION_TESTS_14",[]),("054_resumable_download_probe_ledger_tests.py","RESUMABLE_DOWNLOAD_LEDGER_TESTS_14",[]),("056_uprn_relation_schema_contract_tests.py","UPRN_RELATION_SCHEMA_TESTS_14",[]),("049_full_pipeline_revision11_entry.py","REVISION11_EFFECTIVE_39_STEP_PIPELINE",[]),("051_os_opendata_download_resolution.py","OS_OPENDATA_DOWNLOAD_RESOLUTION_2",[]),("053_resumable_download_probe_ledger.py","RESUMABLE_DOWNLOAD_RANGE_PROBES",[]),("055_uprn_relation_schema_contract.py","UPRN_RELATION_SCHEMA_CONTRACT_2",[])];steps=[]
 for f,n,e in plan:
  z=run(r,a/f,n,e);steps.append(z)
  if z["exit_code"]!=0:
   print(json.dumps({"schema_version":1,"slot_id":SLOT,"task_id":TASK,"state":"blocked","steps":steps,"effective_pipeline_steps":45,"contract_tests_target":264,"official_source_checks_target":34,"sample_size_target":384,"target_evidence_rows":40,"full_release_bytes_hydrated":False,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2));return z["exit_code"]
 print(json.dumps({"schema_version":1,"slot_id":SLOT,"task_id":TASK,"state":"pipeline_passed_pre_hydration","steps":steps,"effective_pipeline_steps":45,"contract_tests_target":264,"official_source_checks_target":34,"sample_size_target":384,"target_evidence_rows":40,"os_opendata_download_resolution_required":True,"resumable_download_probe_required":True,"uprn_relation_schema_contract_required":True,"full_release_bytes_hydrated":False,"parcel_relations_promoted":0,"confidence_uplifts":0,"first_unverified_step":"HYDRATE_CURRENT_OS_OPEN_UPRN_NSUL_ONSUD_BYTES_THEN_VALIDATE_UPRN_POSTCODE_JOIN","final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
