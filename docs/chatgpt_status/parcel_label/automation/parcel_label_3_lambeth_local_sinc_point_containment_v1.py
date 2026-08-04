#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib,tempfile,urllib.parse,urllib.request
from datetime import datetime,timezone

I=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
M=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_local_sinc_point_containment_source_manifest_20260804.json')
O=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_local_sinc_point_containment_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/lambeth_local_sinc_point_containment_latest.json')]
R=['https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSitesOfLocalNatureConservationImportance/FeatureServer/0','https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSitesOfLocalNatureConservationImportance/MapServer/0']
H='gis.lambeth.gov.uk'; LIM=8*1024*1024
now=lambda:datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
sha=lambda b:hashlib.sha256(b).hexdigest()
cj=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'),sort_keys=True)

def safe(u):
 p=urllib.parse.urlsplit(u)
 if p.scheme!='https' or (p.hostname or '').casefold()!=H or p.username or p.password or p.fragment:raise RuntimeError('UNSAFE_URL')
 return u

def get(u,t,a='application/json'):
 safe(u); q=urllib.request.Request(u,headers={'User-Agent':'AAYS-parcel-label-3/1.0','Accept':a})
 with urllib.request.urlopen(q,timeout=t) as r:
  f=safe(r.geturl()); b=r.read(LIM+1)
  if len(b)>LIM:raise RuntimeError('RESPONSE_TOO_LARGE')
  return b,f,int(getattr(r,'status',200))

def manifest():
 p=json.loads(M.read_text())
 if p.get('service_roots')!=R or p.get('harvest_guid')!='88f412c44fcb44b298495e9282343807_2':raise RuntimeError('BAD_MANIFEST')
 if len(p.get('target_uprns',[]))!=3 or len(p.get('sources',[]))<5:raise RuntimeError('INCOMPLETE_MANIFEST')
 for s in p['sources']:
  e=s.get('retained_excerpt','')
  if not e or sha(e.encode())!=s.get('retained_excerpt_sha256'):raise RuntimeError('BAD_EXCERPT_HASH')
 return p

def rows():
 p=json.loads(I.read_text()); rs=p.get('records',[]); targets=set(manifest()['target_uprns']); out=[]
 if len(rs)!=3:raise RuntimeError('EXPECTED_3_ROWS')
 for x in rs:
  keys=('parcel_id','UPRN','FULLADDRESS','POSTCODE','longitude','latitude')
  if not x.get('exact_uprn_bound') or any(k not in x for k in keys):raise RuntimeError('BAD_INPUT_ROW')
  y={k:x[k] for k in keys}; y['UPRN']=str(y['UPRN']); y['exact_uprn_bound']=True
  if y['UPRN'] not in targets:raise RuntimeError('UPRN_NOT_IN_MANIFEST')
  out.append(y)
 if len({x['UPRN'] for x in out})!=3:raise RuntimeError('DUPLICATE_UPRN')
 return out

def onseg(p,a,b,e=1e-12):
 x,y=p;x1,y1=a[:2];x2,y2=b[:2];c=(x-x1)*(y2-y1)-(y-y1)*(x2-x1)
 return abs(c)<=e and min(x1,x2)-e<=x<=max(x1,x2)+e and min(y1,y2)-e<=y<=max(y1,y2)+e

def ring(r,p):
 if len(r)<4:return False
 ins=False;x,y=p
 for a,b in zip(r,r[1:]):
  if onseg(p,a,b):return True
  x1,y1=a[:2];x2,y2=b[:2]
  if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:ins=not ins
 return ins

def covers(g,p):
 c=g.get('coordinates');t=g.get('type')
 def poly(q):return bool(q and ring(q[0],p) and not any(ring(h,p) for h in q[1:]))
 return poly(c) if t=='Polygon' and isinstance(c,list) else any(poly(q) for q in c) if t=='MultiPolygon' and isinstance(c,list) else False

def discover(t,e):
 errs=[]
 for r in R:
  u=r+'?f=json';e['metadata_request_count']+=1
  try:
   b,f,s=get(u,t);p=json.loads(b)
   if p.get('type')!='Feature Layer' or p.get('geometryType')!='esriGeometryPolygon':raise RuntimeError('NOT_POLYGON_FEATURE_LAYER')
   e['metadata_response_count']+=1;e['metadata_requests'].append({'layer_root':r,'request_url':u,'final_url':f,'http_status':s,'bytes':len(b),'response_sha256':sha(b),'geometry_type':p.get('geometryType'),'state':'RESPONSE'});return r
  except Exception as z:
   q=f'{type(z).__name__}:{z}';errs.append(q);e['metadata_requests'].append({'layer_root':r,'request_url':u,'state':'ERROR','error':q})
 raise RuntimeError('ALL_LAYER_METADATA_ENDPOINTS_FAILED:'+'|'.join(errs))

def qurl(r,x):
 q={'where':'1=1','geometry':f"{float(x['longitude']):.15f},{float(x['latitude']):.15f}",'geometryType':'esriGeometryPoint','inSR':'4326','spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}
 return r+'/query?'+urllib.parse.urlencode(q)

def candidates(b,x):
 p=json.loads(b);fs=p.get('features')
 if p.get('type')!='FeatureCollection' or not isinstance(fs,list):raise RuntimeError('BAD_GEOJSON')
 pt=(float(x['longitude']),float(x['latitude']));out=[]
 for n,f in enumerate(fs,1):
  if not isinstance(f,dict) or not isinstance(f.get('geometry'),dict) or not covers(f['geometry'],pt):continue
  a=f.get('properties') if isinstance(f.get('properties'),dict) else {};g=f['geometry']
  out.append({'feature_id':f.get('id'),'feature_index':n,'official_sinc_tier':'Local','official_local_sinc_designation':True,'raw_attributes_sha256':sha(cj(a).encode()),'geometry_sha256':sha(cj(g).encode()),'geometry':g})
 return out,len(fs)

def synth(x,n,o=0):
 lon=float(x['longitude'])+o;lat=float(x['latitude'])+o;d=.00008;r=[[lon-d,lat-d],[lon+d,lat-d],[lon+d,lat+d],[lon-d,lat+d],[lon-d,lat-d]]
 return {'type':'Feature','id':n,'properties':{'OBJECTID':n,'SITE_NAME':f'Synthetic Local SINC {n}'},'geometry':{'type':'Polygon','coordinates':[r]}}

def run(rs,t,syn=False,amb=False):
 e={'accessed_at':now(),'layer_roots':R,'metadata_request_count':0,'metadata_response_count':0,'metadata_requests':[],'point_query_count':0,'point_queries':[]}
 if syn:r=R[0]
 else:
  try:r=discover(t,e)
  except Exception as z:
   q=f'{type(z).__name__}:{z}';e['discovery_error']=q;return e,[{**x,'source_url':R[0],'candidate_count':0,'state':'NO_DATA','reason':q,'inferred':False} for x in rs],0
 e['selected_layer_root']=r;out=[];matched=0
 for n,x in enumerate(rs,1):
  u=qurl(r,x);e['point_query_count']+=1
  try:
   if syn:
    fs=[synth(x,n)]+([synth(x,100+n,.00001)] if amb and n==2 else []);b=cj({'type':'FeatureCollection','features':fs}).encode();f=u;s=200
   else:b,f,s=get(u,t,'application/geo+json,application/json;q=0.9')
   cs,total=candidates(b,x);e['point_queries'].append({'UPRN':x['UPRN'],'request_url':u,'final_url':f,'http_status':s,'bytes':len(b),'response_sha256':sha(b),'returned_feature_count':total,'point_covering_candidate_count':len(cs),'state':'RESPONSE'});y={**x,'source_url':f,'layer_root':r,'candidate_count':len(cs),'inferred':False}
   if len(cs)==1:y.update({'state':'MATCHED_UNIQUE_LAMBETH_LOCAL_SINC_POLYGON',**cs[0]});matched+=1
   elif len(cs)>1:y.update({'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_POINT_CONTAINING_LAMBETH_LOCAL_SINC_POLYGONS','candidate_geometry_sha256':[c['geometry_sha256'] for c in cs]})
   else:y.update({'state':'NO_DATA','reason':'NO_POINT_CONTAINING_LAMBETH_LOCAL_SINC_POLYGON'})
  except Exception as z:
   q=f'{type(z).__name__}:{z}';e['point_queries'].append({'UPRN':x['UPRN'],'request_url':u,'state':'ERROR','error':q});y={**x,'source_url':r+'/query','layer_root':r,'candidate_count':0,'state':'NO_DATA','reason':q,'inferred':False}
  out.append(y)
 return e,out,matched

def write(p,text):
 p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=p.parent,delete=False) as h:h.write(text);q=pathlib.Path(h.name)
 q.replace(p)

def main():
 a=argparse.ArgumentParser();a.add_argument('--timeout',type=int,default=20);a.add_argument('--validate-only',action='store_true');a.add_argument('--synthetic-test',action='store_true');a.add_argument('--synthetic-ambiguous-test',action='store_true');z=a.parse_args()
 if not 1<=z.timeout<=300:raise RuntimeError('BAD_TIMEOUT')
 rs=rows()
 if z.validate_only:print(json.dumps({'valid':True,'input_count':3,'target_uprns':[x['UPRN'] for x in rs],'layer_roots':R,'resource_class':'network','metadata_request_limit':2,'point_query_limit':3,'max_response_bytes':LIM,'write_paths':[str(x) for x in O]},sort_keys=True));return 0
 syn=z.synthetic_test or z.synthetic_ambiguous_test;e,rec,m=run(rs,z.timeout,syn,z.synthetic_ambiguous_test)
 if z.synthetic_test:
  if m!=3 or [x['candidate_count'] for x in rec]!=[1,1,1]:raise RuntimeError('SYNTHETIC_UNIQUE_FAILED')
  print(json.dumps({'valid':True,'matched_rows':m,'point_query_count':e['point_query_count']},sort_keys=True));return 0
 if z.synthetic_ambiguous_test:
  if m!=2 or rec[1].get('reason')!='AMBIGUOUS_MULTIPLE_POINT_CONTAINING_LAMBETH_LOCAL_SINC_POLYGONS':raise RuntimeError('SYNTHETIC_AMBIGUOUS_FAILED')
  print(json.dumps({'valid':True,'matched_rows':m,'ambiguous_state':rec[1]['state']},sort_keys=True));return 0
 state='PUBLISHED' if m else 'NO_DATA_CONTINUE';v={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-lambeth-local-sinc-point-containment-v1-20260804','state':state,'panel_status':'PUBLISHED','completed_count':len(rec),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(rec)/3*100,6),'percent_increase':round(len(rec)/3*100,6),'matched_unique_local_sinc_rows':m,'evidence_records':len(rec),'source_evidence':e,'records':rec,'unknown_attributes_promoted_to_label':False,'fake_data':False,'large_raw_files_committed':False,'generated_at':now()};text=cj(v)+'\n'
 for p in O:write(p,text)
 print(json.dumps({'completed_count':len(rec),'target_count':3,'matched_unique_local_sinc_rows':m,'state':state,'output_sha256':sha(text.encode())},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
