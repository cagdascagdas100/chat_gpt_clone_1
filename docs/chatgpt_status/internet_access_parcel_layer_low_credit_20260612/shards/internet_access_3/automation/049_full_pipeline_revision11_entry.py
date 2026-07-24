#!/usr/bin/env python3
"""Revision 11 single-runner pipeline with attribution, target evidence and browser acceptance."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SLOT="internet_access_3";TASK="aays1-internet-access-3-revision11-browser-evidence-20260722"
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repo root")
def run(r,s,n,e=None):
 c=[sys.executable,str(s),"--repo-root",str(r),*(e or [])];x=subprocess.run(c,cwd=r,text=True,capture_output=True,check=False);return {"name":n,"script":str(s.relative_to(r)),"command":c,"exit_code":x.returncode,"stdout_tail":x.stdout[-12000:],"stderr_tail":x.stderr[-12000:]}
def main():
 r=root();a=Path(__file__).parent;plan=[("050_revision11_pipeline_manifest_tests.py","REVISION11_PIPELINE_MANIFEST_TESTS_10",[]),("044_release_licence_attribution_bundle_tests.py","ATTRIBUTION_BUNDLE_TESTS_12",[]),("046_target_evidence_matrix_tests.py","TARGET_EVIDENCE_MATRIX_TESTS_16",[]),("048_web_acceptance_snapshot_tests.py","WEB_ACCEPTANCE_TESTS_16",[]),("041_full_pipeline_revision10_entry.py","REVISION10_EFFECTIVE_32_STEP_PIPELINE",[]),("043_release_licence_attribution_bundle.py","RELEASE_LICENCE_ATTRIBUTION_BUNDLE_4",[]),("045_target_evidence_matrix.py","TARGET_EVIDENCE_MATRIX_40",[]),("047_web_acceptance_snapshot.py","FINAL_WEB_ACCEPTANCE_SNAPSHOT",[])];steps=[]
 for f,n,e in plan:
  z=run(r,a/f,n,e);steps.append(z)
  if z["exit_code"]!=0:
   print(json.dumps({"schema_version":1,"slot_id":SLOT,"task_id":TASK,"state":"blocked","steps":steps,"effective_pipeline_steps":39,"contract_tests_target":212,"official_source_checks_target":28,"sample_size_target":384,"prepared_candidate_preview_target":40,"transparent_target_rows":40,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2));return z["exit_code"]
 print(json.dumps({"schema_version":1,"slot_id":SLOT,"task_id":TASK,"state":"pipeline_passed","steps":steps,"effective_pipeline_steps":39,"contract_tests_target":212,"official_source_checks_target":28,"sample_size_target":384,"prepared_candidate_preview_target":40,"transparent_target_rows":40,"target_evidence_rows_required":40,"browser_acceptance_required":True,"attribution_sources_required":4,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
