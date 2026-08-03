#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from pathlib import Path
from urllib.parse import urlparse

TARGETS=((30762,'Enfield','London Borough of Enfield'),(46142,'Havering','London Borough of Havering'),(61522,'Lambeth','London Borough of Lambeth'))
REQUIRED_KINDS=('wms_view_service','download_service','information_service')

def sha256_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def atomic_write(path:Path,value:dict)->None:
 path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+'.',suffix='.tmp')
 try:
  with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:
   json.dump(value,f,ensure_ascii=False,sort_keys=True,separators=(',',':'));f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def is_exact_gml(url:str)->bool:
 p=urlparse(url);return p.scheme=='https' and p.path.lower().endswith('.gml')
def validate_manifest(m:dict)->tuple[list[dict],list[str]]:
 errs=[];sources=m.get('records',[]);locators=[]
 for s in sources:
  for x in s.get('service_locators',[]):
   if x.get('kind') in REQUIRED_KINDS:locators.append(x)
 kinds={x.get('kind') for x in locators}
 for k in REQUIRED_KINDS:
  if k not in kinds:errs.append('MISSING_'+k.upper())
 for x in locators:
  p=urlparse(str(x.get('url') or ''))
  if p.scheme!='https' or not p.netloc:errs.append('INVALID_HTTPS_LOCATOR:'+str(x.get('kind')))
 return locators,errs
def build(m:dict,key:str)->dict:
 locators,errs=validate_manifest(m);exact=[x for x in locators if is_exact_gml(str(x.get('url') or ''))]
 authorities={int(x['row_no']):x for x in m.get('authority_scope',[])}
 rows=[]
 for n,l,a in TARGETS:
  scope=authorities.get(n);ok=scope and scope.get('authority')==a
  status='OFFICIAL_SERVICE_LOCATORS_FOUND_NO_EXACT_GML_URL' if not errs and ok and not exact else ('EXACT_OFFICIAL_GML_URL_FOUND' if exact and ok else 'SOURCE_EVIDENCE_INVALID')
  rows.append({'row_no':n,'lpa':l,'authority':a,'authority_listing_verified':bool(ok),'official_service_locators':locators,'exact_gml_urls':[x['url'] for x in exact],'exact_gml_url_count':len(exact),'data_status':status,'full_gml_downloaded':False,'geometry_copied':False,'membership_inferred':False,'score_written':False,'fake_data':False})
 state='PUBLISHED' if len(exact)>0 and not errs else 'NO_DATA_CONTINUE'
 return {'schema_version':3,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'future_growth_2','task_continuation_key':key,'state':state,'panel_status':'PUBLISHED','completed_count':3,'target_count':3,'progress_percent':100.0,'official_service_locator_count':len(locators),'exact_gml_url_count':len(exact),'validation_errors':errs,'global_business_completed_count':0,'global_business_target_count':30761,'global_progress_percent':0.0,'records':rows,'source_manifest_sha256':m.get('manifest_sha256'),'full_gml_downloaded':False,'raw_source_body_copied':False,'geometry_copied':False,'membership_inferred':False,'scores_written':False,'fake_data':False}
def fixture()->dict:
 return {'authority_scope':[{'row_no':n,'authority':a} for n,_,a in TARGETS],'records':[{'service_locators':[{'kind':'wms_view_service','url':'https://example.test/ows?Service=WMS'},{'kind':'download_service','url':'https://example.test/download'},{'kind':'information_service','url':'https://example.test/info'}]}]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--task-continuation-key',required=True);p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if len(a.task_continuation_key)!=64 or any(c not in '0123456789abcdef' for c in a.task_continuation_key):raise ValueError('bad continuation key')
 m=fixture() if a.self_test else json.loads(a.source_manifest.read_text(encoding='utf-8'))
 out=build(m,a.task_continuation_key);atomic_write(a.output,out);print(json.dumps({'state':out['state'],'completed_count':3,'target_count':3,'official_service_locator_count':out['official_service_locator_count'],'exact_gml_url_count':out['exact_gml_url_count'],'output':str(a.output)},sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
