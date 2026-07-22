#!/usr/bin/env python3
"""Validate that official checks refer to the same 384-row manifest and source evidence."""
from __future__ import annotations
import argparse,hashlib,json,os,tempfile
from pathlib import Path
SLOT='internet_access_3';SAMPLE=384
ROOT=Path('docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs');WEB=Path('england_map_web/data/aays_21_slots/internet_access_3')
FILES={'provenance':ROOT/'029_official_source_package_provenance_latest.json','migration':ROOT/'001_migration_and_no_data_latest.json','archive':ROOT/'003_ofcom_2026_full_schema_audit_latest.json','release':ROOT/'015_ons_uprn_arcgis_release_discovery_latest.json','sampler':ROOT/'017_stratified_candidate_sampler_latest.json','ofcom':ROOT/'021_stratified_ofcom_adapter_latest.json','onspd':ROOT/'022_stratified_onspd_adapter_latest.json','hmlr':ROOT/'019_hmlr_exact_stratified_manifest_audit_latest.json','integrity':ROOT/'025_runtime_output_integrity_acceptance_latest.json'}
def args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--runner-output',default=str(ROOT/'030_source_provenance_chain_acceptance_latest.json'));p.add_argument('--web-output',default=str(WEB/'source_provenance_chain_acceptance_latest.json'));return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError('repository root')
def load(p):
 with p.open('r',encoding='utf-8-sig') as h:return json.load(h)
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+'.',dir=p.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(o,h,ensure_ascii=False,separators=(',',':'));h.write('\n')
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def vals(o,keys):
 out=[]
 if isinstance(o,dict):
  for k,v in o.items():
   if k in keys:out.append(v)
   out+=vals(v,keys)
 elif isinstance(o,list):
  for v in o:out+=vals(v,keys)
 return out
def row_ids(o):
 out=[]
 for v in vals(o,{'row_no'}):
  try:out.append(int(v))
  except (TypeError,ValueError):pass
 return out
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as h:
  for b in iter(lambda:h.read(1048576),b''):d.update(b)
 return d.hexdigest()
def unsafe(o):return any(v is True for v in vals(o,{'final_ready','product_final_ready','fake_data','db_write','migration','production_deploy'}))
def main():
 a=args();r=root(a.repo_root);checks=[];bad=[];data={};hashes={}
 def ck(n,c,d):checks.append({'name':n,'passed':bool(c),'detail':d});bad.extend([] if c else [n])
 for n,rel in FILES.items():
  p=r/rel;ck(n.upper()+'_EXISTS',p.exists(),str(rel))
  if p.exists():
   try:data[n]=load(p);hashes[n]=sha(p);ck(n.upper()+'_JSON',True,'parsed');ck(n.upper()+'_SAFETY',not unsafe(data[n]),'unsafe flags false')
   except Exception as e:ck(n.upper()+'_JSON',False,f'{type(e).__name__}:{e}')
 mp=r/WEB/'stratified_candidate_manifest_latest.json';ck('MANIFEST_EXISTS',mp.exists(),str(mp.relative_to(r)));ids=[];msha=None
 if mp.exists():
  m=load(mp);msha=sha(mp);ids=[int(x['row_no']) for x in m] if isinstance(m,list) else [];ck('MANIFEST_COUNT_384',len(ids)==SAMPLE,len(ids));ck('MANIFEST_UNIQUE',len(ids)==len(set(ids)),len(set(ids)))
 target=set(ids)
 for n in ('ofcom','onspd','hmlr'):
  distinct=set(row_ids(data.get(n,{})));ck(n.upper()+'_ROW_IDS_PRESENT',len(distinct)>=SAMPLE,len(distinct));ck(n.upper()+'_EXACT_MANIFEST_SET',distinct==target,{'distinct':len(distinct),'manifest':len(target)})
 ck('PROVENANCE_STATE_PASSED',data.get('provenance',{}).get('state')=='provenance_passed',data.get('provenance',{}).get('state'));ck('PROVENANCE_FOUR_SOURCES',int(data.get('provenance',{}).get('sources_passed',0))==4,data.get('provenance',{}).get('sources_passed'));ck('INTEGRITY_ACCEPTANCE_PASSED',data.get('integrity',{}).get('state')=='acceptance_passed',data.get('integrity',{}).get('state'))
 passed=not bad;o={'schema_version':1,'slot_id':SLOT,'state':'provenance_chain_passed' if passed else 'blocked','checks_total':len(checks),'checks_passed':sum(x['passed'] for x in checks),'checks_failed':len(bad),'checks':checks,'blockers':bad,'manifest_sha256':msha,'output_sha256':hashes,'row_identity_contract':{'sample_size':SAMPLE,'ofcom_onspd_hmlr_exact_same_manifest_required':True},'parcel_relations_promoted':0,'confidence_uplifts':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/a.runner_output,o);write(r/a.web_output,o);print(json.dumps(o,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
