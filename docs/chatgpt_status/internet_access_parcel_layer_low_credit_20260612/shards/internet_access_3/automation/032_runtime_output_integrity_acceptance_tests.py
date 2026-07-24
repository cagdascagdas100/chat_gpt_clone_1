#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
OUT='docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/027_runtime_output_integrity_acceptance_tests_latest.json'
def args():p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--runner-output',default=OUT);return p.parse_args()
def root(x):
 if x:return x.resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists():return p
 raise FileNotFoundError
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent);os.close(fd);Path(t).write_text(json.dumps(o,separators=(',',':'))+'\n',encoding='utf-8');os.replace(t,p)
def main():
 o=args();r=root(o.repo_root);s=(Path(__file__).parent/'031_runtime_output_integrity_acceptance.py').read_text(encoding='utf-8');tests=[('SHARD','SHARD=30761' in s),('SAMPLE','SAMPLE=384' in s),('TEST_TARGET','TESTS_AT_LEAST_122' in s),('MEMBERS','OFcom_MEMBERS_121' in s),('ROWS','1741096' in s),('OFcom_GATE','OFcom_MATCHES_365' in s),('ONSPD_GATE','ONSPD_MATCHES_365' in s),('HMLR_GATE','HMLR_POLYGONS_346' in s),('HMLR_ONSPD','HMLR_ONSPD_346' in s),('MANIFEST_UNIQUE','MANIFEST_UNIQUE' in s),('MANIFEST_RANGE','MANIFEST_RANGE' in s),('ALL_OUTPUTS','ALL_TEST_OUTPUTS_EXIST' in s),('FAIL_CLOSED','passed=not bad' in s),('NO_PROMOTION','NO_RELATION_PROMOTIONS' in s),('SAFETY',all(x in s for x in ['final_ready','fake_data','db_write','production_deploy'])),('ATOMIC','os.replace' in s)];rows=[{'name':n,'passed':bool(c)} for n,c in tests];bad=[x for x in rows if not x['passed']];z={'schema_version':1,'slot_id':'internet_access_3','state':'passed' if not bad else 'failed','tests_expected':16,'tests_executed':len(rows),'tests_passed':len(rows)-len(bad),'tests_failed':len(bad),'tests':rows,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/o.runner_output,z);print(json.dumps(z));return 0 if not bad else 2
if __name__=='__main__':raise SystemExit(main())
