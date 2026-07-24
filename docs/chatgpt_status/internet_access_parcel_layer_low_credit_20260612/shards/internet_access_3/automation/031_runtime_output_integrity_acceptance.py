#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
SLOT='internet_access_3';START=61523;END=92283;SHARD=30761;SAMPLE=384
ROOT='docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs'
FILES={'migration':'001_migration_and_no_data_latest.json','archive':'003_ofcom_2026_full_schema_audit_latest.json','release':'015_ons_uprn_arcgis_release_discovery_latest.json','sampler':'017_stratified_candidate_sampler_latest.json','ofcom':'021_stratified_ofcom_adapter_latest.json','onspd':'022_stratified_onspd_adapter_latest.json','hmlr':'019_hmlr_exact_stratified_manifest_audit_latest.json','freshness':'024_official_http_freshness_probe_latest.json'}
TESTS=['000_worker_contract_tests_latest.json','007_hmlr_geometry_contract_tests_latest.json','009_revision6_contract_tests_latest.json','011_corrected_migration_contract_tests_latest.json','014_revision7_pipeline_manifest_tests_latest.json','016_ons_uprn_arcgis_release_discovery_tests_latest.json','018_stratified_candidate_sampler_tests_latest.json','020_exact_manifest_binding_tests_latest.json','023_revision8_pipeline_manifest_tests_latest.json','026_official_http_freshness_probe_tests_latest.json','027_runtime_output_integrity_acceptance_tests_latest.json','028_revision9_pipeline_manifest_tests_latest.json']
def args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--runner-output',default=ROOT+'/025_runtime_output_integrity_acceptance_latest.json');p.add_argument('--web-output',default='england_map_web/data/aays_21_slots/internet_access_3/runtime_output_integrity_acceptance_latest.json');return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError('repo root')
def load(p):
 with p.open('r',encoding='utf-8-sig') as h:return json.load(h)
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.')
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(o,h,ensure_ascii=False,separators=(',',':'));h.write('\n')
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def vals(o,k):
 out=[]
 if isinstance(o,dict):
  for a,b in o.items():
   if a==k:out.append(b)
   out+=vals(b,k)
 elif isinstance(o,list):
  for b in o:out+=vals(b,k)
 return out
def num(o,keys,d=0):
 for k in keys:
  for v in vals(o,k):
   try:return int(v)
   except (TypeError,ValueError):pass
 return d
def unsafe(o):return any(v is True for k in ['final_ready','product_final_ready','fake_data','db_write','migration','production_deploy'] for v in vals(o,k))
def main():
 o=args();r=root(o.repo_root);checks=[];bad=[];data={}
 def ck(n,c,d):checks.append({'name':n,'passed':bool(c),'detail':d});bad.extend([] if c else [n])
 for n,f in FILES.items():
  p=r/ROOT/f;ck(n.upper()+'_EXISTS',p.exists(),str(p.relative_to(r)))
  if p.exists():
   try:data[n]=load(p);ck(n.upper()+'_JSON',True,'parsed')
   except Exception as e:ck(n.upper()+'_JSON',False,str(e))
 for n,x in data.items():ck(n.upper()+'_SAFETY',not unsafe(x),'unsafe flags false')
 total=failed=0;missing=[]
 for f in TESTS:
  p=r/ROOT/f
  if not p.exists():missing.append(f);continue
  x=load(p);total+=num(x,['tests_executed','tests_total','tests_expected']);failed+=num(x,['tests_failed','failed'])
 ck('ALL_TEST_OUTPUTS_EXIST',not missing,repr(missing));ck('TESTS_AT_LEAST_122',total>=122,str(total));ck('TEST_FAILURES_ZERO',failed==0,str(failed))
 m=data.get('migration',{});written=num(m,['shard_rows_written','actual_business_data_rows_written']);matched=num(m,['matched_existing_rows']);nodata=num(m,['no_data_rows']);ck('MIGRATION_30761',written==SHARD,str(written));ck('MIGRATION_PARTITION',matched+nodata==SHARD,f'{matched}+{nodata}')
 a=data.get('archive',{});ck('OFcom_MEMBERS_121',num(a,['corrected_member_count','member_count','official_postcode_members'])==121,str(num(a,['corrected_member_count','member_count','official_postcode_members'])));ck('OFcom_ROWS_1741096',num(a,['total_rows','official_postcode_rows'])==1741096,str(num(a,['total_rows','official_postcode_rows'])))
 mp=r/'england_map_web/data/aays_21_slots/internet_access_3/stratified_candidate_manifest_latest.json';ck('MANIFEST_EXISTS',mp.exists(),str(mp.relative_to(r)))
 if mp.exists():
  x=load(mp);ids=[int(z['row_no']) for z in x] if isinstance(x,list) else [];ck('MANIFEST_384',len(ids)==SAMPLE,str(len(ids)));ck('MANIFEST_UNIQUE',len(ids)==len(set(ids)),str(len(set(ids))));ck('MANIFEST_RANGE',all(START<=z<=END for z in ids),'shard range')
 ck('OFcom_MATCHES_365',num(data.get('ofcom',{}),['official_postcodes_found','exact_matches','matches'])>=365,str(num(data.get('ofcom',{}),['official_postcodes_found','exact_matches','matches'])));ck('ONSPD_MATCHES_365',num(data.get('onspd',{}),['exact_postcodes_found','official_postcodes_found','matches'])>=365,str(num(data.get('onspd',{}),['exact_postcodes_found','official_postcodes_found','matches'])));ck('HMLR_POLYGONS_346',num(data.get('hmlr',{}),['inspire_polygons_found','polygon_matches'])>=346,str(num(data.get('hmlr',{}),['inspire_polygons_found','polygon_matches'])));ck('HMLR_ONSPD_346',num(data.get('hmlr',{}),['onspd_exact_postcodes_found','exact_postcodes_found'])>=346,str(num(data.get('hmlr',{}),['onspd_exact_postcodes_found','exact_postcodes_found'])))
 ck('NO_RELATION_PROMOTIONS',all(num(x,['parcel_relations_promoted','new_parcel_postcode_matches_created'])==0 for x in data.values()),'expected zero')
 passed=not bad;s={'schema_version':1,'slot_id':SLOT,'state':'acceptance_passed' if passed else 'blocked','checks_total':len(checks),'checks_passed':sum(x['passed'] for x in checks),'checks_failed':len(bad),'tests_executed':total,'test_failures':failed,'checks':checks,'blockers':bad,'acceptance':{'sample_size':384,'ofcom_minimum':365,'onspd_minimum':365,'hmlr_minimum':346,'parcel_relations_promoted':0,'confidence_uplifts':0},'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
