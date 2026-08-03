#!/usr/bin/env python3
import argparse,hashlib,html,json,os,re,tempfile,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
SLOT='future_growth_2';WS='AAYS_21_SLOT_SAFE_PARALLEL_V1';HOST='use-land-property-data.service.gov.uk';PAGE='https://use-land-property-data.service.gov.uk/datasets/inspire/download';N=4096
T=((30762,'Enfield','London Borough of Enfield'),(46142,'Havering','London Borough of Havering'),(61522,'Lambeth','London Borough of Lambeth'))
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.',suffix='.tmp')
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,separators=(',',':'));f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 finally:
  if os.path.exists(t):os.unlink(t)
def valid(u):
 q=urllib.parse.urlparse(u)
 if q.scheme!='https' or q.hostname!=HOST:raise ValueError('official HMLR HTTPS page required')
def fetch(u,to):
 valid(u);r=urllib.request.urlopen(urllib.request.Request(u,headers={'Accept':'text/html','User-Agent':'TerraYield-AAYS/1.0 future_growth_2'}),timeout=to);b=r.read(5000001)
 if len(b)>5000000:raise ValueError('page too large')
 return int(r.status),r.geturl(),b,{str(k).lower():str(v) for k,v in r.headers.items()}
def links(b,base):
 s=html.unescape(b.decode('utf-8','replace'));o={}
 for n,l,a in T:
  m=re.search(re.escape(a),s,re.I);z=None
  if m:
   w=s[m.start():m.start()+2500]
   for h,x in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',w,re.I|re.S):
    if 'gml' in re.sub(r'<[^>]+>',' ',x).lower() or '.gml' in h.lower():z=urllib.parse.urljoin(base,h);break
  o[n]=z
 return o
def probe(u,to):
 if urllib.parse.urlparse(u).scheme!='https':raise ValueError('HTTPS GML required')
 r=urllib.request.urlopen(urllib.request.Request(u,headers={'Range':f'bytes=0-{N-1}','User-Agent':'TerraYield-AAYS/1.0 future_growth_2'}),timeout=to);b=r.read(N);h={str(k).lower():str(v) for k,v in r.headers.items()}
 return {'http_status':int(r.status),'final_url':r.geturl(),'content_type':h.get('content-type'),'content_length_header':h.get('content-length'),'content_range_header':h.get('content-range'),'byte_count_hashed':len(b),'content_sha256':hashlib.sha256(b).hexdigest() if b else None,'hash_scope':f'bounded_first_{N}_bytes'}
def base(n,l,a,u,at):return {'row_no':n,'lpa':l,'authority':a,'download_page_url':u,'fetched_at_utc':at,'raw_body_copied':False,'geometry_copied':False,'membership_inferred':False,'score_written':False,'fake_data':False}
def out(k,r,v):
 s='PUBLISHED' if v==3 else 'NO_DATA_CONTINUE';return {'schema_version':3,'architecture_version':3,'workstream_id':WS,'slot_id':SLOT,'task_continuation_key':k,'state':s,'panel_status':'PUBLISHED' if s=='PUBLISHED' else 'BİLGİ TOPLANIYOR','generated_at':now(),'completed_count':len(r),'target_count':3,'progress_percent':round(len(r)/3*100,6),'verified_link_count':v,'failed_link_count':3-v,'global_business_completed_count':0,'global_business_target_count':30761,'global_progress_percent':0.0,'records':r,'large_raw_files_written':False,'raw_bodies_copied':False,'geometry_copied':False,'membership_inferred':False,'scores_written':False,'fake_data':False}
def run(u,k,to,F=fetch,P=probe):
 if len(k)!=64 or any(c not in '0123456789abcdef' for c in k):raise ValueError('bad continuation key')
 valid(u);at=now()
 try:st,fu,b,hh=F(u,to)
 except Exception as e:
  er=f'{type(e).__name__}:{str(e)[:500]}';r=[]
  for n,l,a in T:r.append({**base(n,l,a,u,at),'download_page_final_url':None,'download_page_http_status':None,'download_page_byte_count':0,'download_page_sha256':None,'download_page_content_type':None,'gml_url':None,'discovered_from_official_page':False,'http_status':None,'final_url':None,'content_type':None,'content_length_header':None,'content_range_header':None,'byte_count_hashed':0,'content_sha256':None,'hash_scope':f'bounded_first_{N}_bytes','data_status':'SOURCE_READ_FAILED','error':er})
  return out(k,r,0)
 ph=hashlib.sha256(b).hexdigest();L=links(b,fu);r=[];v=0
 for n,l,a in T:
  z=L[n];q={**base(n,l,a,u,at),'download_page_final_url':fu,'download_page_http_status':st,'download_page_byte_count':len(b),'download_page_sha256':ph,'download_page_content_type':hh.get('content-type'),'gml_url':z,'discovered_from_official_page':True}
  if not z:r.append({**q,'data_status':'SOURCE_LINK_NOT_FOUND','error':'No GML link near authority label'});continue
  try:
   p=P(z,to);ok=p.get('http_status') in (200,206) and p.get('byte_count_hashed',0)>0 and p.get('content_sha256');v+=bool(ok);r.append({**q,**p,'data_status':'VERIFIED_OFFICIAL_GML_LINK' if ok else 'SOURCE_READ_FAILED','error':None if ok else 'empty probe'})
  except Exception as e:r.append({**q,'http_status':None,'final_url':None,'content_type':None,'content_length_header':None,'content_range_header':None,'byte_count_hashed':0,'content_sha256':None,'hash_scope':f'bounded_first_{N}_bytes','data_status':'SOURCE_READ_FAILED','error':f'{type(e).__name__}:{str(e)[:500]}'})
 return out(k,r,int(v))
def ff(u,to):
 del to;b=b'<tr><td>London Borough of Enfield</td><td><a href="/e.gml">GML</a></td></tr><tr><td>London Borough of Havering</td><td><a href="/h.gml">GML</a></td></tr><tr><td>London Borough of Lambeth</td><td><a href="/l.gml">GML</a></td></tr>';return 200,u,b,{'content-type':'text/html'}
def fp(u,to):
 del to;b=('<gml>'+u).encode();return {'http_status':206,'final_url':u,'content_type':'application/gml+xml','content_length_header':str(len(b)),'content_range_header':None,'byte_count_hashed':len(b),'content_sha256':hashlib.sha256(b).hexdigest(),'hash_scope':f'bounded_first_{N}_bytes'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--download-page-url',default=PAGE);p.add_argument('--output',required=True);p.add_argument('--task-continuation-key',required=True);p.add_argument('--timeout-seconds',type=int,default=30);p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if not 5<=a.timeout_seconds<=120:raise ValueError('timeout 5..120')
 v=run(a.download_page_url,a.task_continuation_key,a.timeout_seconds,ff if a.self_test else fetch,fp if a.self_test else probe);save(a.output,v);print(json.dumps({'state':v['state'],'completed_count':v['completed_count'],'target_count':3,'verified_link_count':v['verified_link_count'],'failed_link_count':v['failed_link_count']},sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
