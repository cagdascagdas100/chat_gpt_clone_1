#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def mod(path):
 s=importlib.util.spec_from_file_location('prov',path)
 if s is None or s.loader is None:raise ImportError(path)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--runner-output',default='docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/031_official_source_package_provenance_tests_latest.json');a=p.parse_args();r=(a.repo_root or Path.cwd()).resolve();script=Path(__file__).parent/'035_official_source_package_provenance.py';m=mod(script);tests=[]
 def ck(n,c,d):tests.append({'name':n,'passed':bool(c),'detail':d})
 ids=[x['id'] for x in m.SOURCES];ck('FOUR_SOURCES',len(ids)==4,ids);ck('ALL_REQUIRED',all(x['required'] for x in m.SOURCES),'required');ck('SOURCE_IDS_UNIQUE',len(ids)==len(set(ids)),ids);ck('OFcom_PRESENT','ofcom_spring_2026' in ids,ids);ck('ONSPD_PRESENT','onspd_may_2026' in ids,ids);ck('HMLR_PRESENT','hmlr_inspire_july_2026' in ids,ids);ck('UPRN_PRESENT','os_open_uprn' in ids,ids);urls=m.recursive_urls({'a':{'url':'https://example/a'},'b':[{'documentation_url':'https://example/b'}]},{'url','documentation_url'});ck('RECURSIVE_URLS',urls==['https://example/a','https://example/b'],urls);source=script.read_text(encoding='utf-8');ck('RANGE_REQUEST','Range' in source,'partial identity');ck('SHA256_PRESENT','sha256' in source.lower(),'hash');ck('NO_PROMOTION_GUARD',"'parcel_relations_promoted':0" in source,'zero');ck('SAFETY_FLAGS',all(x in source for x in ["'final_ready':False","'fake_data':False","'db_write':False","'migration':False","'production_deploy':False"]),'flags');bad=[x for x in tests if not x['passed']];o={'schema_version':1,'slot_id':'internet_access_3','state':'passed' if not bad else 'failed','tests_expected':12,'tests_executed':len(tests),'tests_passed':len(tests)-len(bad),'tests_failed':len(bad),'tests':tests,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};q=r/a.runner_output;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(o,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8');print(json.dumps(o,ensure_ascii=False,indent=2));return 0 if not bad else 2
if __name__=='__main__':raise SystemExit(main())
