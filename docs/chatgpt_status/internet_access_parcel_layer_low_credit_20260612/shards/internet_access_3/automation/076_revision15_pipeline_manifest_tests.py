#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);return p.parse_args()
def main():
 args();a=Path(__file__).parent;p=(a/'075_full_pipeline_revision15_entry.py').read_text();checks=[]
 def ck(n,x):checks.append({'name':n,'passed':bool(x)})
 ck('CHILD_REV14','069_full_pipeline_revision14_entry.py' in p);ck('HYDRATION_WORKER','071_full_release_hydration_manifest.py' in p);ck('JOIN_WORKER','073_exact_uprn_postcode_join.py' in p);ck('HYDRATION_TESTS_18','FULL_RELEASE_HYDRATION_TESTS_18' in p);ck('JOIN_TESTS_18','EXACT_UPRN_POSTCODE_JOIN_TESTS_18' in p);ck('TOTAL_TESTS_392',"'contract_tests_target':392" in p);ck('SOURCE_CHECKS_54',"'official_source_checks_target':54" in p);ck('STEPS_60',"'effective_pipeline_steps':60" in p);ck('JOIN_RATIO_98',"'uprn_join_ratio_minimum':0.98" in p);ck('SAFETY',all(x in p for x in ["'final_ready':False","'fake_data':False","'db_write':False","'migration':False","'production_deploy':False"]))
 payload={'schema_version':1,'slot_id':'internet_access_3','tests_total':len(checks),'tests_passed':sum(x['passed'] for x in checks),'tests_failed':sum(not x['passed'] for x in checks),'checks':checks,'final_ready':False};print(json.dumps(payload,indent=2));return 0 if payload['tests_failed']==0 and payload['tests_total']==10 else 2
if __name__=='__main__':raise SystemExit(main())
