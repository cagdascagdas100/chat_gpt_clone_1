#!/usr/bin/env python3
"""Wave350 bounded Source Cooperative Overture mirror metadata gate."""
from __future__ import annotations
import argparse,hashlib,json,os,re,tempfile,time
from pathlib import Path
from urllib import request
UA='AAYS-Wave350/1.0 metadata-only'
def h(b): return hashlib.sha256(b).hexdigest()
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.',suffix='.tmp')
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,sort_keys=True,separators=(',',':'));f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 finally:
  if os.path.exists(t): os.unlink(t)
def probe(url,method,timeout,limit=0):
 o={'source_url':url,'method':method,'http_status':None,'content_type':None,'content_length_header':None,'bytes_read':0,'content_sha256':h(b''),'truncated':False,'network_error':None,'_text':''}
 try:
  q=request.Request(url,headers={'User-Agent':UA,'Accept':'*/*'},method=method)
  with request.urlopen(q,timeout=timeout) as r:
   o['http_status']=getattr(r,'status',None);o['content_type']=r.headers.get('Content-Type');o['content_length_header']=r.headers.get('Content-Length')
   if method=='GET':
    b=r.read(limit+1);o['truncated']=len(b)>limit;b=b[:limit];o['bytes_read']=len(b);o['content_sha256']=h(b);o['_text']=b.decode('utf-8','replace')
 except Exception as e:o['network_error']=f'{type(e).__name__}:{e}'
 return o
def rows(d):
 z=[]
 for r in d.get('rows',[]):
  p=r.get('properties') or {};z.append({'parcel_id':r.get('parcel_id') or p.get('parcel_id'),'row_no':p.get('row_no'),'hmlr_inspire_id':p.get('hmlr_inspire_id'),'longitude':p.get('hmlr_lon'),'latitude':p.get('hmlr_lat'),'london_authority':p.get('london_authority'),'geometry_type':r.get('geometry_type')})
 return z
def live(p): return p['network_error'] is None and p['http_status'] is not None and 200<=p['http_status']<400
def selftest():
 assert h(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';assert sorted(set(re.findall(r'20\d{2}-\d{2}-\d{2}-\d+','2026-04-15-0 2026-05-20-0')))[-1]=='2026-05-20-0';print('SELF_TEST_PASS')
def main():
 a=argparse.ArgumentParser();a.add_argument('--canonical');a.add_argument('--fixture');a.add_argument('--output');a.add_argument('--timeout',type=float,default=30);a.add_argument('--delay',type=float,default=1);a.add_argument('--accessed-at');a.add_argument('--self-test',action='store_true');x=a.parse_args()
 if x.self_test:selftest();return 0
 if not(x.canonical and x.fixture and x.output):a.error('required paths missing')
 c=json.loads(Path(x.canonical).read_text());f=json.loads(Path(x.fixture).read_text());scope=[r for r in rows(c) if r['parcel_id'] in {'parcel_30762','parcel_30763','parcel_30764'}]
 if len(scope)!=3 or any(r['london_authority']!='Enfield' for r in scope):raise SystemExit('CANONICAL_SCOPE_VALIDATION_FAILED')
 u=f['candidate_urls'];spec=[('product_page','GET',500000),('readme','GET',120000),('current_release_metadata','HEAD',0),('visible_latest_metadata','HEAD',0),('visible_latest_sample','HEAD',0)];ps=[]
 for i,(n,m,l) in enumerate(spec):p=probe(u[n],m,x.timeout,l);p['probe_name']=n;ps.append(p);time.sleep(x.delay if i<4 else 0)
 text={p['probe_name']:p.pop('_text','') for p in ps};rels=sorted(set(re.findall(r'20\d{2}-\d{2}-\d{2}-\d+',text['product_page'])));latest=rels[-1] if rels else None;by={p['probe_name']:p for p in ps}
 public='Visibility' in text['product_page'] and 'Public' in text['product_page'];contract=all(q in text['readme'] for q in ('GeoParquet','_metadata','_sample'));cur=live(by['current_release_metadata']);oldm=live(by['visible_latest_metadata']);olds=live(by['visible_latest_sample'])
 current=f['current_official_release_mirror_name'];visible=f['documented_visible_latest_mirror_release'];ok=public and contract and cur and latest==current;lag=public and contract and oldm and olds and not cur and latest==visible
 if ok:state='SOURCE_COOPERATIVE_OVERTURE_MIRROR_CURRENT_METADATA_AVAILABLE_CONTINUE_BBOX_QUERY';block='GEOPARQUET_NOT_DOWNLOADED_BY_DESIGN;THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_SELECTED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE';nxt='ASSESS_SOURCE_COOPERATIVE_BUILDING_BBOX_QUERY_FOR_THREE_CANONICAL_POINTS'
 elif lag:state='NO_DATA_CONTINUE';block='SOURCE_COOPERATIVE_OVERTURE_MIRROR_LAGS_CURRENT_OFFICIAL_RELEASE;CURRENT_OFFICIAL_RELEASE_2026_07_22_0_NOT_AVAILABLE_ON_MIRROR;GEOPARQUET_NOT_DOWNLOADED_BY_DESIGN;THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_SELECTED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE';nxt='ASSESS_FUSED_OVERTURE_UDF_BBOX_QUERY_CONTRACT_OR_NO_DATA_CONTINUE'
 else:state='NO_DATA_CONTINUE';block='SOURCE_COOPERATIVE_OVERTURE_MIRROR_METADATA_NOT_LIVE_ACQUIRED;CURRENT_OFFICIAL_RELEASE_2026_07_22_0_NOT_CONFIRMED_ON_MIRROR;GEOPARQUET_NOT_DOWNLOADED_BY_DESIGN;THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_SELECTED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE';nxt='ASSESS_FUSED_OVERTURE_UDF_BBOX_QUERY_CONTRACT_OR_NO_DATA_CONTINUE'
 receipts=[f"{p['probe_name']}:{p['network_error'] or p['http_status']}" for p in ps];runtime=[{'source_url':'https://source.coop/fused/overture','accessed_at':x.accessed_at,'content_sha256':h('\n'.join(receipts).encode()),'hash_scope':'five_bounded_mirror_probe_receipts','record_scope':'Product/README GET plus current and visible-release building metadata/sample HEAD; no GeoParquet body.','relevant_record_ids_or_excerpt':'; '.join(receipts),'supports_fields':['public_repository','mirror_release_visibility','metadata_sample_headers','no_body_download','no_exact_binding'],'license_or_terms_url':'https://docs.overturemaps.org/attribution/'}]
 out={'schema_version':1,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'gas_emissions_2','wave':350,'accessed_at':x.accessed_at,'state':state,'decision':'SOURCE_COOPERATIVE_OVERTURE_MIRROR_METADATA_GATE_ASSESSED','canonical_sample_rows_in_scope':3,'assessments':scope,'current_official_release_mirror_name':current,'documented_visible_latest_mirror_release':visible,'runtime_discovered_latest_release':latest,'product_public':public,'readme_metadata_sample_contract':contract,'current_release_metadata_live':cur,'visible_latest_metadata_live':oldm,'visible_latest_sample_live':olds,'probe_count':5,'live_probe_count':sum(live(p) for p in ps),'network_error_count':sum(bool(p['network_error']) for p in ps),'total_bytes_read':sum(p['bytes_read'] for p in ps),'geoparquet_body_downloaded':False,'probes':ps,'source_evidence_manifest':f['source_evidence_manifest'],'runtime_source_evidence':runtime,'business_rows_produced':0,'parcel_rows_bound':0,'completed_count':0,'target_count':30761,'previous_percent':0.0,'current_percent':0.0,'percent_increase':0.0,'blocker':block,'first_unverified_step':nxt,'fake_data':False,'final_ready':False}
 write(x.output,out);print(json.dumps({'state':state,'probe_count':5,'live_probe_count':out['live_probe_count'],'network_error_count':out['network_error_count'],'total_bytes_read':out['total_bytes_read'],'geoparquet_body_downloaded':False,'business_rows_produced':0,'parcel_rows_bound':0,'first_unverified_step':nxt},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
