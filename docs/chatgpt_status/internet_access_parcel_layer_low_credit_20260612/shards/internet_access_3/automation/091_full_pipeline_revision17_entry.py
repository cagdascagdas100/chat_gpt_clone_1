#!/usr/bin/env python3
"""Revision 17 pipeline with cache identity and resumable SQLite checkpoints."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SLOT='internet_access_3';TASK='aays1-internet-access-3-revision17-cache-identity-checkpointed-join-20260722'
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError
def run(r,p,n):
 c=[sys.executable,str(p),'--repo-root',str(r)];x=subprocess.run(c,cwd=r,text=True,capture_output=True,check=False);return {'name':n,'script':str(p.relative_to(r)),'command':c,'exit_code':x.returncode,'stdout_tail':x.stdout[-12000:],'stderr_tail':x.stderr[-12000:]}
def main():
 r=root();a=Path(__file__).parent;plan=[('092_revision17_pipeline_manifest_tests.py','REV17_MANIFEST_TESTS'),('086_release_cache_identity_ledger_tests.py','CACHE_IDENTITY_TESTS'),('088_exact_uprn_postcode_join_revision17_tests.py','CHECKPOINT_JOIN_TESTS'),('090_revision17_runtime_acceptance_tests.py','REV17_ACCEPTANCE_TESTS'),('078_runtime_resource_download_preflight_tests.py','REV16_RESOURCE_TESTS'),('080_exact_uprn_postcode_join_revision16_tests.py','REV16_JOIN_TESTS'),('082_revision16_pipeline_manifest_tests.py','REV16_MANIFEST_TESTS'),('084_revision16_runtime_acceptance_tests.py','REV16_ACCEPTANCE_TESTS'),('069_full_pipeline_revision14_entry.py','REV14_EFFECTIVE_PIPELINE'),('077_runtime_resource_download_preflight.py','RESOURCE_PREFLIGHT'),('085_release_cache_identity_ledger.py','CACHE_IDENTITY_LEDGER'),('071_full_release_hydration_manifest.py','FULL_RELEASE_HYDRATION'),('087_exact_uprn_postcode_join_revision17.py','CHECKPOINTED_EXACT_JOIN'),('089_revision17_runtime_acceptance.py','REV17_RUNTIME_ACCEPTANCE')];steps=[]
 for f,n in plan:
  z=run(r,a/f,n);steps.append(z)
  if z['exit_code']!=0:
   print(json.dumps({'schema_version':1,'slot_id':SLOT,'task_id':TASK,'state':'blocked','steps':steps,'effective_pipeline_steps':69,'contract_tests_target':488,'official_source_checks_target':70,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},ensure_ascii=False,indent=2));return z['exit_code']
 print(json.dumps({'schema_version':1,'slot_id':SLOT,'task_id':TASK,'state':'pipeline_passed','steps':steps,'effective_pipeline_steps':69,'contract_tests_target':488,'official_source_checks_target':70,'release_packages_identity_bound':4,'join_checkpoint_stages':4,'preview_rows':40,'parcel_relations_promoted':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
