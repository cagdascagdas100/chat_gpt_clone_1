#!/usr/bin/env python3
"""Wave354: bounded Overture STAC asset and Parquet-footer range gate."""
from __future__ import annotations
import argparse,hashlib,importlib.util,io,json,os,struct,sys,tempfile,time,urllib.request
from pathlib import Path
D=.00035; CATMAX=500000; IDXMAX=20000000; FOOTMAX=2000000; REQLIM=12

def H(b):return hashlib.sha256(b).hexdigest()
def atomic(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+'.',dir=p.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,sort_keys=True,separators=(',',':'));f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 finally:
  if os.path.exists(t):os.unlink(t)
def rows(d):
 out=[]
 for r in d.get('rows',[]):
  p=r.get('properties') or {};out.append({'parcel_id':r.get('parcel_id') or p.get('parcel_id'),'hmlr_inspire_id':p.get('hmlr_inspire_id'),'longitude':p.get('hmlr_lon'),'latitude':p.get('hmlr_lat'),'london_authority':p.get('london_authority'),'geometry_type':r.get('geometry_type')})
 return out
def bb(r):
 x=float(r['longitude']);y=float(r['latitude']);return [round(x-D,7),round(y-D,7),round(x+D,7),round(y+D,7)]
def ov(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def https(u):
 if not u.startswith('s3://'):return u
 b,_,k=u[5:].partition('/');return f"https://{b}.s3.us-west-2.amazonaws.com/{k}" if b=='overturemaps-us-west-2' else f"https://{b}.s3.amazonaws.com/{k}"
class P:
 def __init__(s,to):s.to=to;s.n=0
 def q(s,name,url,method='GET',mx=0,rng=None):
  if s.n>=REQLIM:raise RuntimeError('REQUEST_LIMIT_EXCEEDED')
  s.n+=1;h={'User-Agent':'AAYS-Wave354/1.0'}
  if rng:h['Range']=rng
  rec={'name':name,'url':url,'method':method,'range':rng,'success':False,'status':None,'bytes_read':0,'content_length':None,'content_range':None,'error':None};t=time.monotonic()
  try:
   with urllib.request.urlopen(urllib.request.Request(url,method=method,headers=h),timeout=s.to) as z:
    rec.update(status=getattr(z,'status',None),content_length=z.headers.get('Content-Length'),content_range=z.headers.get('Content-Range'),etag=z.headers.get('ETag'))
    b=b'' if method=='HEAD' else z.read(mx+1 if mx else 1)
    if mx and len(b)>mx:rec['error']=f'MAX_BYTES_EXCEEDED:{mx}';b=b[:mx]
    else:rec['success']=True
    rec.update(bytes_read=len(b),body_sha256=H(b));return rec,b
  except Exception as e:rec['error']=f'{type(e).__name__}:{e}';return rec,b''
  finally:rec['duration_seconds']=round(time.monotonic()-t,3)
def href(a):
 if not isinstance(a,dict):return None
 w=a.get('aws')
 if isinstance(w,str):return w
 if isinstance(w,dict):
  if isinstance(w.get('href'),str):return w['href']
  x=(w.get('alternate') or {}).get('s3') if isinstance(w.get('alternate'),dict) else None
  if isinstance(x,dict) and isinstance(x.get('href'),str):return x['href']
 for v in a.values():
  if isinstance(v,dict) and isinstance(v.get('href'),str) and ('parquet' in v['href'] or v['href'].startswith('s3://')):return v['href']
 return None
def parse(b,boxes):
 try:
  import pyarrow.parquet as pq
  rs=pq.read_table(io.BytesIO(b)).to_pylist();m=[]
  for r in rs:
   if r.get('collection')!='building' or r.get('type')!='Feature':continue
   x=r.get('bbox');x=[x.get(k) for k in ('xmin','ymin','xmax','ymax')] if isinstance(x,dict) else x
   try:x=[float(v) for v in x]
   except Exception:continue
   hit=[i for i,q in enumerate(boxes) if ov(x,q)]
   if hit:m.append({'item_bbox':x,'query_bbox_indexes':hit,'asset_href':href(r.get('assets'))})
  sel=[];cov=set()
  for x in m:
   if x['asset_href'] and any(i not in cov for i in x['query_bbox_indexes']):sel.append(x);cov.update(x['query_bbox_indexes'])
   if len(sel)>=3 or len(cov)==3:break
  return {'success':True,'pyarrow_version':__import__('pyarrow').__version__,'index_row_count':len(rs),'matching_item_count':len(m),'selected_assets':sel,'covered_bbox_indexes':sorted(cov)}
 except Exception as e:return {'success':False,'error':f'{type(e).__name__}:{e}','selected_assets':[],'covered_bbox_indexes':[]}
def footer(p,i,u):
 u=https(u);h,_=p.q(f'a{i}_head',u,'HEAD');t,b=p.q(f'a{i}_tail',u,mx=8,rng='bytes=-8');o={'href':u,'head':h,'tail':t,'success':False}
 if len(b)==8:
  n,m=struct.unpack('<I4s',b);o.update(footer_length=n,parquet_magic=m.decode('ascii','replace'))
  try:L=int(h.get('content_length'))
  except Exception:L=0
  if m==b'PAR1' and 0<n<=FOOTMAX and L>n+8:
   r,d=p.q(f'a{i}_footer',u,mx=FOOTMAX,rng=f'bytes={L-n-8}-{L-9}');o.update(footer_range=r,footer_sha256=H(d),success=bool(r.get('success')) and len(d)==n)
 return o
def test():
 assert ov([0,0,2,2],[1,1,3,3]) and not ov([0,0,1,1],[2,2,3,3]);n,m=struct.unpack('<I4s',struct.pack('<I4s',7,b'PAR1'));assert(n,m)==(7,b'PAR1');assert https('s3://overturemaps-us-west-2/x').startswith('https://');print('SELF_TEST_PASS')
def main():
 a=argparse.ArgumentParser();a.add_argument('--canonical');a.add_argument('--fixture');a.add_argument('--output');a.add_argument('--timeout',type=int,default=30);a.add_argument('--delay',type=float,default=1);a.add_argument('--accessed-at');a.add_argument('--self-test',action='store_true');x=a.parse_args()
 if x.self_test:test();return 0
 if not(x.canonical and x.fixture and x.output and x.accessed_at):a.error('required args missing')
 c=json.loads(Path(x.canonical).read_text());f=json.loads(Path(x.fixture).read_text());rr=[r for r in rows(c) if r['parcel_id'] in {'parcel_30762','parcel_30763','parcel_30764'}]
 if len(rr)!=3 or any(r['london_authority']!='Enfield' for r in rr):raise SystemExit('CANONICAL_SCOPE_VALIDATION_FAILED')
 boxes=[bb(r) for r in rr];p=P(x.timeout);pro=[];cr,cb=p.q('catalog',f['catalog_url'],mx=CATMAX);pro.append(cr);latest=None;ce=None
 try:latest=json.loads(cb).get('latest') if cr['success'] else None
 except Exception as e:ce=f'{type(e).__name__}:{e}'
 iu=f['collections_url_template'].format(release=latest) if latest else None;ih=ig=None;ib=b''
 if iu:
  ih,_=p.q('index_head',iu,'HEAD');pro.append(ih)
  try:L=int(ih.get('content_length')) if ih.get('content_length') else 0
  except Exception:L=0
  if not L or L<=IDXMAX:ig,ib=p.q('index_get',iu,mx=IDXMAX);pro.append(ig)
 pa=importlib.util.find_spec('pyarrow') is not None;parsed=parse(ib,boxes) if ib and pa else {'success':False,'error':'PYARROW_NOT_PREINSTALLED' if ib else 'INDEX_NOT_AVAILABLE','selected_assets':[],'covered_bbox_indexes':[]};fr=[]
 for i,z in enumerate(parsed.get('selected_assets',[])[:3]):
  if isinstance(z.get('asset_href'),str):fr.append(footer(p,i,z['asset_href']));time.sleep(x.delay if i+1<3 else 0)
 sel=len(parsed.get('selected_assets',[]));cov=len(parsed.get('covered_bbox_indexes',[]));ok=sum(bool(z.get('success')) for z in fr);net=sum(1 for z in pro if z.get('error'))+sum(1 for z in fr for k in ('head','tail','footer_range') if isinstance(z.get(k),dict) and z[k].get('error'));byt=sum(int(z.get('bytes_read') or 0) for z in pro)+sum(int((z.get('tail') or {}).get('bytes_read') or 0)+int((z.get('footer_range') or {}).get('bytes_read') or 0) for z in fr)
 bl=[]
 if not latest:bl+=['OVERTURE_STAC_LATEST_RELEASE_NOT_LIVE_ACQUIRED']
 if not ib:bl+=['OVERTURE_STAC_COLLECTIONS_PARQUET_NOT_ACQUIRED']
 if ib and not pa:bl+=['PYARROW_NOT_PREINSTALLED','OVERTURE_STAC_BUILDING_ASSET_LIST_NOT_PARSED']
 if cov<3:bl+=['THREE_ENFIELD_BBOX_ASSET_COVERAGES_NOT_CONFIRMED']
 if ok<max(1,sel):bl+=['BOUNDED_PARQUET_FOOTER_RANGE_READS_NOT_COMPLETED']
 bl+=['THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED','THREE_EXACT_UPRNS_NOT_ACQUIRED','EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE']
 passed=bool(latest and parsed.get('success') and cov==3 and sel and ok==sel);state='STAC_ASSET_RANGE_METADATA_ACQUIRED_CONTINUE_EXACT_FEATURE_QUERY' if passed else 'NO_DATA_CONTINUE';nxt='ASSESS_PYARROW_FILTERED_ROW_GROUP_READ_FOR_THREE_BBOXES_OR_NO_DATA_CONTINUE';rc={'catalog':cr,'catalog_error':ce,'latest':latest,'index_url':iu,'index_head':ih,'index_get':ig,'pyarrow_preinstalled':pa,'parsed':parsed,'footer_results':fr};rb=json.dumps(rc,sort_keys=True,default=str).encode();runtime=[{'source_url':f['catalog_url'],'accessed_at':x.accessed_at,'content_sha256':H(rb),'hash_scope':'stac_catalog_collections_parquet_and_bounded_footer_range_receipts','record_scope':'STAC latest release, collections.parquet building asset selection and up to three bounded Parquet footer range reads; no complete building file.','relevant_record_ids_or_excerpt':f'latest={latest}; request_count={p.n}; network_error_count={net}; index_bytes={len(ib)}; selected_asset_count={sel}; covered_bbox_count={cov}; successful_footer_range_count={ok}','supports_fields':['latest_release','building_asset_list','asset_bbox_coverage','parquet_footer_length','HTTP_range_support','no_full_file_download','no_exact_binding_claim'],'license_or_terms_url':'https://docs.overturemaps.org/attribution/'}]
 o={'schema_version':1,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'gas_emissions_2','wave':354,'accessed_at':x.accessed_at,'state':state,'decision':'OVERTURE_STAC_BUILDING_ASSET_LIST_AND_BOUNDED_PARQUET_RANGE_GATE_ASSESSED','canonical_sample_rows_in_scope':3,'assessments':[dict(r,bbox=bb(r)) for r in rr],'catalog_url':f['catalog_url'],'latest_release':latest,'collections_index_url':iu,'request_count':p.n,'network_error_count':net,'total_bytes_read':byt,'catalog_probe':cr,'collections_index_head':ih,'collections_index_get':ig,'collections_index_bytes':len(ib),'pyarrow_preinstalled':pa,'asset_index_parse':parsed,'selected_asset_count':sel,'covered_bbox_count':cov,'bounded_footer_range_results':fr,'successful_footer_range_count':ok,'full_geoparquet_downloaded':False,'candidate_feature_count':0,'source_evidence_manifest':f['source_evidence_manifest'],'runtime_source_evidence':runtime,'business_rows_produced':0,'parcel_rows_bound':0,'completed_count':0,'target_count':30761,'previous_percent':0.0,'current_percent':0.0,'percent_increase':0.0,'blocker':';'.join(dict.fromkeys(bl)),'first_unverified_step':nxt,'fake_data':False,'final_ready':False};atomic(Path(x.output),o);print(json.dumps({'state':state,'latest_release':latest,'request_count':p.n,'network_error_count':net,'total_bytes_read':byt,'selected_asset_count':sel,'covered_bbox_count':cov,'successful_footer_range_count':ok,'business_rows_produced':0,'parcel_rows_bound':0,'first_unverified_step':nxt},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
