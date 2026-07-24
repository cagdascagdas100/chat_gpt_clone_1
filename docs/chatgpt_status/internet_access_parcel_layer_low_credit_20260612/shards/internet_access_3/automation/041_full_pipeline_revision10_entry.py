#!/usr/bin/env python3
"""Revision 10 single-runner pipeline with source-package and row-provenance acceptance."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SLOT='internet_access_3';TASK='aays1-internet-access-3-revision10-provenance-chain-20260722'
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError('repository root')
def run(repo,script,name,extra=None):
 c=[sys.executable,str(script),'--repo-root',str(repo),*(extra or [])];x=subprocess.run(c,cwd=repo,text=True,capture_output=True,check=False);return {'name':name,'script':str(script.relative_to(repo)),'command':c,'exit_code':x.returncode,'stdout_tail':x.stdout[-12000:],'stderr_tail':x.stderr[-12000:]}
def main():
 r=root();a=Path(__file__).parent;plan=[('042_revision10_pipeline_manifest_tests.py','REVISION10_PIPELINE_MANIFEST_TESTS_10',[]),('037_official_source_package_provenance_tests.py','OFFICIAL_SOURCE_PACKAGE_PROVENANCE_TESTS_12',[]),('038_source_provenance_chain_acceptance_tests.py','SOURCE_PROVENANCE_CHAIN_TESTS_14',[]),('034_full_pipeline_revision9_entry.py','REVISION9_EFFECTIVE_26_STEP_PIPELINE',[]),('018_prepared_candidate_preview.py','PUBLISH_40_PREPARED_CANDIDATE_PREVIEW_ROWS',['--preview-size','40']),('035_official_source_package_provenance.py','OFFICIAL_SOURCE_PACKAGE_PROVENANCE_CHECKS_4',[]),('036_source_provenance_chain_acceptance.py','FINAL_SOURCE_AND_ROW_PROVENANCE_CHAIN_ACCEPTANCE',[])];steps=[]
 for f,n,e in plan:
  z=run(r,a/f,n,e);steps.append(z)
  if z['exit_code']!=0:
   print(json.dumps({'schema_version':1,'slot_id':SLOT,'task_id':TASK,'state':'blocked','steps':steps,'effective_pipeline_steps':32,'contract_tests_target':158,'official_source_checks_target':24,'sample_size_target':384,'prepared_candidate_preview_target':40,'transparent_target_rows':40,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},ensure_ascii=False,indent=2));return z['exit_code']
 print(json.dumps({'schema_version':1,'slot_id':SLOT,'task_id':TASK,'state':'pipeline_passed','steps':steps,'effective_pipeline_steps':32,'contract_tests_target':158,'official_source_checks_target':24,'sample_size_target':384,'prepared_candidate_preview_target':40,'transparent_target_rows':40,'ofcom_minimum_matches':365,'onspd_minimum_matches':365,'hmlr_minimum_matches':346,'provenance_sources_required':4,'exact_manifest_row_identity_required':True,'parcel_relations_promoted':0,'confidence_uplifts':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
