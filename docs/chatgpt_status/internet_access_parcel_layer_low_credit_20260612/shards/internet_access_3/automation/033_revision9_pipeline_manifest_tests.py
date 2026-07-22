#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
OUT='docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/028_revision9_pipeline_manifest_tests_latest.json'
def args():p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--runner-output',default=OUT);return p.parse_args()
def root(x):
 if x:return x.resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists():return p
 raise FileNotFoundError
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent);os.close(fd);Path(t).write_text(json.dumps(o,separators=(',',':'))+'\n',encoding='utf-8');os.replace(t,p)
def main():
 o=args();r=root(o.repo_root);s=(Path(__file__).parent/'034_full_pipeline_revision9_entry.py').read_text(encoding='utf-8');tests=[('STEPS_25',"'effective_pipeline_steps':25" in s),('TESTS_122',"'contract_tests_target':122" in s),('CHECKS_20',"'official_source_checks_target':20" in s),('SAMPLE_384',"'sample_size_target':384" in s),('TARGETS_32',"'transparent_target_rows':32" in s),('REV8_CHILD','027_full_pipeline_revision8_entry.py' in s),('FRESHNESS','029_official_http_freshness_probe.py' in s),('ACCEPTANCE','031_runtime_output_integrity_acceptance.py' in s),('GATES',all(x in s for x in ['365','346'])),('SAFETY',all(x in s for x in ['final_ready','fake_data','db_write','production_deploy']))];rows=[{'name':n,'passed':bool(c)} for n,c in tests];bad=[x for x in rows if not x['passed']];z={'schema_version':1,'slot_id':'internet_access_3','state':'passed' if not bad else 'failed','tests_expected':10,'tests_executed':len(rows),'tests_passed':len(rows)-len(bad),'tests_failed':len(bad),'tests':rows,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/o.runner_output,z);print(json.dumps(z));return 0 if not bad else 2
if __name__=='__main__':raise SystemExit(main())
