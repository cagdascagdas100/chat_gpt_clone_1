#!/usr/bin/env python3
"""Revision 15 single-runner pipeline with full UPRN release hydration and exact joins."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SLOT='internet_access_3';TASK='aays1-internet-access-3-revision15-full-uprn-hydration-join-20260722'
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError('repo root')
def run(r,s,n,e=None):
 c=[sys.executable,str(s),'--repo-root',str(r),*(e or [])];x=subprocess.run(c,cwd=r,text=True,capture_output=True,check=False);return {'name':n,'script':str(s.relative_to(r)),'command':c,'exit_code':x.returncode,'stdout_tail':x.stdout[-12000:],'stderr_tail':x.stderr[-12000:]}
def main():
 r=root();a=Path(__file__).parent;plan=[('076_revision15_pipeline_manifest_tests.py','REVISION15_PIPELINE_MANIFEST_TESTS_10',[]),('072_full_release_hydration_manifest_tests.py','FULL_RELEASE_HYDRATION_TESTS_18',[]),('074_exact_uprn_postcode_join_tests.py','EXACT_UPRN_POSTCODE_JOIN_TESTS_18',[]),('069_full_pipeline_revision14_entry.py','REVISION14_EFFECTIVE_55_STEP_PIPELINE',[]),('071_full_release_hydration_manifest.py','FULL_RELEASE_HYDRATION_4_PACKAGES',[]),('073_exact_uprn_postcode_join.py','EXACT_UPRN_POSTCODE_JOIN_98_PERCENT',[])];steps=[]
 for f,n,e in plan:
  z=run(r,a/f,n,e);steps.append(z)
  if z['exit_code']!=0:
   print(json.dumps({'schema_version':1,'slot_id':SLOT,'task_id':TASK,'state':'blocked','steps':steps,'effective_pipeline_steps':60,'contract_tests_target':392,'official_source_checks_target':54,'sample_size_target':384,'uprn_join_ratio_minimum':0.98,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},ensure_ascii=False,indent=2));return z['exit_code']
 print(json.dumps({'schema_version':1,'slot_id':SLOT,'task_id':TASK,'state':'pipeline_passed','steps':steps,'effective_pipeline_steps':60,'contract_tests_target':392,'official_source_checks_target':54,'sample_size_target':384,'full_release_packages_hydrated':4,'uprn_join_ratio_minimum':0.98,'uprn_join_preview_rows':40,'parcel_relations_promoted':0,'confidence_uplifts':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
