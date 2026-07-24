#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SLOT='internet_access_3';TASK='aays1-internet-access-3-revision9-integrity-freshness-20260722'
def root():
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError
def run(repo,script,name,extra=None):
 c=[sys.executable,str(script),'--repo-root',str(repo),*(extra or [])];x=subprocess.run(c,cwd=repo,text=True,capture_output=True,check=False);return {'name':name,'script':str(script.relative_to(repo)),'command':c,'exit_code':x.returncode,'stdout_tail':x.stdout[-12000:],'stderr_tail':x.stderr[-12000:]}
def main():
 r=root();a=Path(__file__).parent;plan=[('033_revision9_pipeline_manifest_tests.py','REVISION9_PIPELINE_MANIFEST_TESTS_10',[]),('030_official_http_freshness_probe_tests.py','OFFICIAL_HTTP_FRESHNESS_TESTS_12',[]),('032_runtime_output_integrity_acceptance_tests.py','RUNTIME_OUTPUT_ACCEPTANCE_TESTS_16',[]),('027_full_pipeline_revision8_entry.py','REVISION8_EFFECTIVE_20_STEP_PIPELINE',[]),('018_prepared_candidate_preview.py','PUBLISH_32_PREPARED_CANDIDATE_PREVIEW_ROWS',['--preview-size','32']),('029_official_http_freshness_probe.py','OFFICIAL_HTTP_FRESHNESS_CHECKS_7',[]),('031_runtime_output_integrity_acceptance.py','FINAL_RUNTIME_OUTPUT_INTEGRITY_ACCEPTANCE',[])];steps=[]
 for f,n,e in plan:
  z=run(r,a/f,n,e);steps.append(z)
  if z['exit_code']!=0:
   print(json.dumps({'schema_version':2,'slot_id':SLOT,'task_id':TASK,'state':'blocked','steps':steps,'effective_pipeline_steps':26,'contract_tests_target':122,'official_source_checks_target':20,'sample_size_target':384,'prepared_candidate_preview_target':32,'transparent_target_rows':32,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},ensure_ascii=False,indent=2));return z['exit_code']
 print(json.dumps({'schema_version':2,'slot_id':SLOT,'task_id':TASK,'state':'pipeline_passed','steps':steps,'effective_pipeline_steps':26,'contract_tests_target':122,'official_source_checks_target':20,'sample_size_target':384,'prepared_candidate_preview_target':32,'transparent_target_rows':32,'ofcom_minimum_matches':365,'onspd_minimum_matches':365,'hmlr_minimum_matches':346,'parcel_relations_promoted':0,'confidence_uplifts':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
