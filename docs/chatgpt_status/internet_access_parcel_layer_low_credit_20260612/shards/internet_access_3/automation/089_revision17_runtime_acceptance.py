#!/usr/bin/env python3
"""Final fail-closed acceptance for identity-bound cache and checkpointed UPRN join."""
from __future__ import annotations
import argparse,json,os,re,tempfile
from pathlib import Path
SLOT_ID='internet_access_3';HEX64=re.compile(r'^[0-9a-f]{64}$');BASE='docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/'
def args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--preflight',default=BASE+'052_runtime_resource_download_preflight_latest.json');p.add_argument('--cache-ledger',default=BASE+'055_release_cache_identity_ledger_latest.json');p.add_argument('--hydration',default=BASE+'050_full_release_hydration_manifest_latest.json');p.add_argument('--join',default=BASE+'056_exact_uprn_postcode_join_revision17_latest.json');p.add_argument('--runner-output',default=BASE+'057_revision17_runtime_acceptance_latest.json');p.add_argument('--web-output',default='england_map_web/data/aays_21_slots/internet_access_3/revision17_runtime_acceptance_latest.json');return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError
def load(p):
 with p.open('r',encoding='utf-8-sig') as h:return json.load(h)
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(o,h,ensure_ascii=False,separators=(',',':'));h.write('\n')
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def safe(doc):return all(doc.get(k) is False for k in ('fake_data','db_write','migration','production_deploy','final_ready')) and int(doc.get('parcel_relations_promoted') or 0)==0 and int(doc.get('actual_business_data_rows_written') or 0)==0
def validate(pre,ledger,hydr,join):
 b=[]
 for name,doc in [('preflight',pre),('cache_ledger',ledger),('hydration',hydr),('join',join)]:
  if doc.get('state')!='runtime_validation_passed':b.append(name.upper()+'_NOT_PASSED')
  if not safe(doc):b.append(name.upper()+'_SAFETY_FLAGS')
 if int(pre.get('packages_expected') or 0)!=4:b.append('PREFLIGHT_PACKAGE_COUNT')
 if int(ledger.get('packages_bound') or 0)!=4:b.append('CACHE_BOUND_COUNT')
 if any(not HEX64.fullmatch(str(x.get('identity_sha256') or '')) for x in ledger.get('packages') or []):b.append('CACHE_IDENTITY_HASH')
 if int(hydr.get('packages_hydrated') or 0)!=4:b.append('HYDRATION_PACKAGE_COUNT')
 for x in hydr.get('packages') or []:
  if not HEX64.fullmatch(str(x.get('actual_sha256') or '')):b.append('HYDRATION_SHA256')
  if x.get('size_verified') is not True:b.append('HYDRATION_SIZE')
  if x.get('expected_md5') and x.get('md5_verified') is not True:b.append('HYDRATION_MD5')
  if x.get('media_type')=='application/zip' and x.get('zip_integrity_passed') is not True:b.append('HYDRATION_ZIP')
 if int(join.get('stages_total') or 0)!=4 or int(join.get('stages_resumed') or 0)+int(join.get('stages_executed') or 0)!=4:b.append('JOIN_STAGE_COVERAGE')
 if not HEX64.fullmatch(str(join.get('input_manifest_sha256') or '')):b.append('JOIN_INPUT_MANIFEST')
 for source in ('nsul','onsud'):
  if float(((join.get('join_stats') or {}).get(source) or {}).get('join_ratio') or 0)<.98:b.append(source.upper()+'_JOIN_RATIO')
 if float(join.get('common_exact_ratio') or 0)<.95:b.append('COMMON_EXACT_RATIO')
 if int(join.get('cross_source_postcode_conflicts') or 0)!=0:b.append('CROSS_SOURCE_CONFLICTS')
 if int(join.get('preview_rows_written') or 0)!=40:b.append('PREVIEW_COUNT')
 return sorted(set(b))
def main():
 o=args();r=root(o.repo_root);pre,ledger,hydr,join=[load(r/getattr(o,k)) for k in ('preflight','cache_ledger','hydration','join')];b=validate(pre,ledger,hydr,join);passed=not b;now=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();s={'schema_version':1,'task_id':'aays1-internet-access-3-revision17-runtime-acceptance-20260722','slot_id':SLOT_ID,'state':'runtime_validation_passed' if passed else 'blocked','updated_at':now,'result':{'packages_preflighted':int(pre.get('packages_expected') or 0),'packages_identity_bound':int(ledger.get('packages_bound') or 0),'packages_hydrated':int(hydr.get('packages_hydrated') or 0),'join_stages_covered':int(join.get('stages_resumed') or 0)+int(join.get('stages_executed') or 0),'preview_rows':int(join.get('preview_rows_written') or 0),'input_manifest_sha256':join.get('input_manifest_sha256')},'source_checks_executed':8,'validation':{'passed':passed,'blockers':b},'acceptance_semantics':'SOURCE_RELEASE_AND_EXACT_UPRN_POSTCODE_RELATION_ONLY_NOT_PARCEL_RELATION','parcel_relations_promoted':0,'confidence_uplifts':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
