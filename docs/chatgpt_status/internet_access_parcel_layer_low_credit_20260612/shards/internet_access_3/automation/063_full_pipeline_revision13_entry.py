#!/usr/bin/env python3
"""Revision 13 single-runner pipeline with release and repository artifact consistency acceptance."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SLOT="internet_access_3";TASK="aays1-internet-access-3-revision13-release-blob-consistency-20260722"
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError
def run(r,s,n,e=None):
 c=[sys.executable,str(s),"--repo-root",str(r),*(e or [])];x=subprocess.run(c,cwd=r,text=True,capture_output=True,check=False);return {"name":n,"script":str(s.relative_to(r)),"command":c,"exit_code":x.returncode,"stdout_tail":x.stdout[-12000:],"stderr_tail":x.stderr[-12000:]}
def main():
 r=root();a=Path(__file__).parent;plan=[("064_revision13_pipeline_manifest_tests.py","REVISION13_PIPELINE_MANIFEST_TESTS_10",[]),("060_os_release_consistency_acceptance_tests.py","OS_RELEASE_CONSISTENCY_TESTS_16",[]),("062_repo_blob_integrity_matrix_tests.py","REPO_BLOB_INTEGRITY_TESTS_14",[]),("057_full_pipeline_revision12_entry.py","REVISION12_EFFECTIVE_45_STEP_PIPELINE",[]),("059_os_release_consistency_acceptance.py","OS_RELEASE_CONSISTENCY_CHECKS_6",[]),("061_repo_blob_integrity_matrix.py","REPO_BLOB_INTEGRITY_MATRIX",[])];steps=[]
 for f,n,e in plan:
  z=run(r,a/f,n,e);steps.append(z)
  if z["exit_code"]!=0:
   print(json.dumps({"schema_version":1,"slot_id":SLOT,"task_id":TASK,"state":"blocked","steps":steps,"effective_pipeline_steps":50,"contract_tests_target":304,"official_source_checks_target":40,"sample_size_target":384,"target_evidence_rows":40,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2));return z["exit_code"]
 print(json.dumps({"schema_version":1,"slot_id":SLOT,"task_id":TASK,"state":"pipeline_passed_pre_hydration","steps":steps,"effective_pipeline_steps":50,"contract_tests_target":304,"official_source_checks_target":40,"sample_size_target":384,"target_evidence_rows":40,"release_consistency_required":True,"repo_blob_integrity_required":True,"full_release_bytes_hydrated":False,"parcel_relations_promoted":0,"confidence_uplifts":0,"first_unverified_step":"HYDRATE_CURRENT_OS_OPEN_UPRN_NSUL_ONSUD_BYTES_THEN_VALIDATE_UPRN_POSTCODE_JOIN","final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
