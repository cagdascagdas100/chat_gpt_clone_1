#!/usr/bin/env python3
"""Revision 14 single-runner pipeline with Code-Point Open and four-source consensus."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SLOT="internet_access_3";TASK="aays1-internet-access-3-revision14-codepoint-consensus-20260722"
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError
def run(r,s,n,e=None):
 c=[sys.executable,str(s),"--repo-root",str(r),*(e or [])];x=subprocess.run(c,cwd=r,text=True,capture_output=True,check=False);return {"name":n,"script":str(s.relative_to(r)),"command":c,"exit_code":x.returncode,"stdout_tail":x.stdout[-12000:],"stderr_tail":x.stderr[-12000:]}
def main():
 r=root();a=Path(__file__).parent;plan=[("070_revision14_pipeline_manifest_tests.py","REVISION14_PIPELINE_MANIFEST_TESTS_10",[]),("066_codepoint_open_exact_crosscheck_tests.py","CODEPOINT_OPEN_EXACT_CROSSCHECK_TESTS_16",[]),("068_official_postcode_source_consensus_tests.py","OFFICIAL_SOURCE_CONSENSUS_TESTS_16",[]),("063_full_pipeline_revision13_entry.py","REVISION13_EFFECTIVE_50_STEP_PIPELINE",[]),("065_codepoint_open_exact_crosscheck.py","CODEPOINT_OPEN_EXACT_384_CROSSCHECK",[]),("067_official_postcode_source_consensus.py","FOUR_SOURCE_POSTCODE_CONSENSUS",[])];steps=[]
 for f,n,e in plan:
  z=run(r,a/f,n,e);steps.append(z)
  if z["exit_code"]!=0:
   print(json.dumps({"schema_version":1,"slot_id":SLOT,"task_id":TASK,"state":"blocked","steps":steps,"effective_pipeline_steps":55,"contract_tests_target":346,"official_source_checks_target":46,"sample_size_target":384,"codepoint_minimum_matches":365,"source_consensus_minimum_rows":365,"spatial_support_minimum_rows":346,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2));return z["exit_code"]
 print(json.dumps({"schema_version":1,"slot_id":SLOT,"task_id":TASK,"state":"pipeline_passed","steps":steps,"effective_pipeline_steps":55,"contract_tests_target":346,"official_source_checks_target":46,"sample_size_target":384,"codepoint_minimum_matches":365,"source_consensus_minimum_rows":365,"spatial_support_minimum_rows":346,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
