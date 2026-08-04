#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone

INPUT=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
MANIFEST=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_flood_risk_zone_3_point_containment_source_manifest_20260804.json')
OUTPUTS=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_flood_risk_zone_3_point_containment_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/lambeth_flood_risk_zone_3_point_containment_latest.json')]
ROOTS=['https://gis.lambeth.gov.uk/arcgis/rest/services/LambethFloodRiskZone3/FeatureServer','https://gis.lambeth.gov.uk/arcgis/rest/services/LambethFloodRiskZone3/MapServer']
HOST='gis.lambeth.gov.uk'; LIMIT=8*1024*1024
now=lambda:datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
sha=lambda b:hashlib.sha256(b).hexdigest()
cj=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def safe(u):
 p=urllib.parse.urlsplit(u)
 if p.scheme!='https' or (p.hostname or '').casefold()!=HOST or p.username or p.password or p.fragment: raise RuntimeError('UNSAFE_URL')
 return u
def fetch(u,t):
 r=urllib.request.Request(safe(u),headers={'User-Agent':'AAYS-parcel-label-3/1.0','Accept':'application/json,application/geo+json'})
 with urllib.request.urlopen(r,timeout=t) as x:
  b=x.read(LIMIT+1)
  if len(b)>LIMIT: raise RuntimeError('RESPONSE_TOO_LARGE')
  return b,safe(x.geturl()),int(getattr(x,'status',200))
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=p.parent,delete=False) as f:f.write(s);q=pathlib.Path(f.name)
 q.replace(p)
def load():
 m=json.loads(MANIFEST.read_text()); rows=json.loads(INPUT.read_text()).get('records',[])
 if m.get('service_roots')!=ROOTS or m.get('harvest_guid')!='b67578fd84bf478cac78a0ef1e6e2d46_1' or len(m.get('sources',[]))<5:raise RuntimeError('BAD_MANIFEST')
 for s in m['sources']:
  e=s.get('retained_excerpt','')
  if not e or sha(e.encode())!=s.get('retained_excerpt_sha256'):raise RuntimeError('BAD_EXCERPT_SHA')
 if len(rows)!=3:raise RuntimeError('EXPECTED_3_ROWS')
 out=[]; targets=set(m['target_uprns'])
 for r in rows:
  keys=('parcel_id','UPRN','FULLADDRESS','POSTCODE','longitude','latitude')
  if not r.get('exact_uprn_bound') or any(k not in r for k in keys):raise RuntimeError('BAD_INPUT')
  z={k:r[k] for k in keys};z['UPRN']=str(z['UPRN']);z['exact_uprn_bound']=True
  if z['UPRN'] not in targets:raise RuntimeError('UPRN_NOT_IN_MANIFEST')
  out.append(z)
 if len({r['UPRN'] for r in out})!=3:raise RuntimeError('DUP_UPRN')
 return out
def discover(t,e):
 errors=[]
 for root in ROOTS:
  u=root+'?f=json';e['metadata_attempt_count']+=1
  try:
   b,f,s=fetch(u,t);p=json.loads(b);ls=[x for x in p.get('layers',[]) if isinstance(x,dict) and isinstance(x.get('id'),int)]
   if not ls:raise RuntimeError('NO_LAYER')
   ls.sort(key=lambda x:(0 if 'flood' in str(x.get('name','')).casefold() else 1,x['id']));x=ls[0]
   e['metadata_response_count']+=1;e['metadata_requests'].append({'request_url':u,'final_url':f,'http_status':s,'response_sha256':sha(b),'selected_layer_id':x['id'],'selected_layer_name':str(x.get('name','')),'state':'RESPONSE'})
   return root,int(x['id']),str(x.get('name',''))
  except Exception as ex:
   z=f'{type(ex).__name__}:{ex}';errors.append(z);e['metadata_requests'].append({'request_url':u,'state':'ERROR','error':z})
 raise RuntimeError('ALL_METADATA_ENDPOINTS_FAILED:'+'|'.join(errors))
def qurl(root,lid,r):
 p={'where':'1=1','geometry':f"{float(r['longitude']):.12f},{float(r['latitude']):.12f}",'geometryType':'esriGeometryPoint','inSR':'4326','spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}
 return f'{root}/{lid}/query?'+urllib.parse.urlencode(p)
def named(props):
 for k,v in sorted(props.items()):
  if isinstance(v,(str,int,float)) and str(v).strip() and any(x in k.casefold() for x in ('name','zone','flood','risk','type','class')):return ' '.join(str(v).split())
 return 'Flood Risk Zone 3'
def parse(b):
 p=json.loads(b)
 if p.get('type')!='FeatureCollection' or not isinstance(p.get('features'),list):raise RuntimeError('BAD_GEOJSON')
 out=[]
 for i,f in enumerate(p['features'],1):
  if not isinstance(f,dict):continue
  g=f.get('geometry') or {};a=f.get('properties') if isinstance(f.get('properties'),dict) else {}
  if g.get('type') not in ('Polygon','MultiPolygon'):continue
  out.append({'feature_id':f.get('id'),'feature_index':i,'official_flood_risk_zone_3_name':named(a),'geometry_sha256':sha(cj(g).encode()),'raw_attributes_sha256':sha(cj(a).encode())})
 return out,len(p['features'])
def synthetic(r,i,dup=False):
 def f(j):return {'type':'Feature','id':j,'properties':{'NAME':'Flood Risk Zone 3'},'geometry':{'type':'Polygon','coordinates':[[[r['longitude']-.0001,r['latitude']-.0001],[r['longitude']+.0001,r['latitude']-.0001],[r['longitude']+.0001,r['latitude']+.0001],[r['longitude']-.0001,r['latitude']+.0001],[r['longitude']-.0001,r['latitude']-.0001]]]}}
 fs=[f(i)]+([f(i+100)] if dup else []);return cj({'type':'FeatureCollection','features':fs}).encode()
def run(rows,t,syn=False,amb=False):
 e={'accessed_at':now(),'service_roots':ROOTS,'metadata_attempt_count':0,'metadata_response_count':0,'metadata_requests':[],'point_query_count':0,'point_queries':[]}
 if syn:root,lid,lname=ROOTS[0],0,'Flood Risk Zone 3'
 else:
  try:root,lid,lname=discover(t,e)
  except Exception as ex:
   z=f'{type(ex).__name__}:{ex}';e['discovery_error']=z;return e,[{**r,'source_url':ROOTS[0],'candidate_count':0,'state':'NO_DATA','reason':z,'inferred':False} for r in rows],0
 records=[];matched=0
 for i,r in enumerate(rows,1):
  u=qurl(root,lid,r);e['point_query_count']+=1
  try:
   b,f,s=(synthetic(r,i,amb and i==2),u,200) if syn else fetch(u,t);c,total=parse(b)
   e['point_queries'].append({'UPRN':r['UPRN'],'request_url':u,'final_url':f,'http_status':s,'response_sha256':sha(b),'returned_feature_count':total,'polygon_candidate_count':len(c),'state':'RESPONSE'})
   x={**r,'source_url':f,'service_root':root,'layer_id':lid,'layer_name':lname,'candidate_count':len(c),'inferred':False}
   if len(c)==1:x.update({'state':'MATCHED_UNIQUE_LAMBETH_FLOOD_RISK_ZONE_3_POLYGON','official_flood_risk_zone_3_designation':True,'official_flood_risk_zone_3_label':'Lambeth Flood Risk Zone 3',**c[0]});matched+=1
   elif len(c)>1:x.update({'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_FLOOD_RISK_ZONE_3_POLYGONS','candidate_geometry_sha256':[a['geometry_sha256'] for a in c]})
   else:x.update({'state':'NO_DATA','reason':'NO_FLOOD_RISK_ZONE_3_POLYGON'})
  except Exception as ex:
   z=f'{type(ex).__name__}:{ex}';e['point_queries'].append({'UPRN':r['UPRN'],'request_url':u,'state':'ERROR','error':z});x={**r,'source_url':f'{root}/{lid}/query','candidate_count':0,'state':'NO_DATA','reason':z,'inferred':False}
  records.append(x)
 return e,records,matched
def main():
 a=argparse.ArgumentParser();a.add_argument('--timeout',type=int,default=20);a.add_argument('--validate-only',action='store_true');a.add_argument('--synthetic-test',action='store_true');a.add_argument('--synthetic-ambiguous-test',action='store_true');z=a.parse_args()
 if not 1<=z.timeout<=300:raise RuntimeError('BAD_TIMEOUT')
 rows=load()
 if z.validate_only:print(cj({'valid':True,'input_count':3,'target_uprns':[r['UPRN'] for r in rows],'service_roots':ROOTS,'resource_class':'network','metadata_request_limit':2,'point_query_limit':3,'max_response_bytes':LIMIT,'write_paths':[str(p) for p in OUTPUTS]}));return 0
 e,rs,m=run(rows,z.timeout,z.synthetic_test or z.synthetic_ambiguous_test,z.synthetic_ambiguous_test)
 if z.synthetic_test:
  if m!=3 or [r['candidate_count'] for r in rs]!=[1,1,1]:raise RuntimeError('SYNTH_UNIQUE_FAIL')
  print(cj({'valid':True,'matched_rows':m,'candidate_counts':[1,1,1]}));return 0
 if z.synthetic_ambiguous_test:
  if m!=2 or rs[1].get('reason')!='AMBIGUOUS_MULTIPLE_FLOOD_RISK_ZONE_3_POLYGONS':raise RuntimeError('SYNTH_AMBIG_FAIL')
  print(cj({'valid':True,'matched_rows':m,'ambiguous_state':rs[1]['state']}));return 0
 state='PUBLISHED' if m else 'NO_DATA_CONTINUE';result={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-lambeth-flood-risk-zone-3-point-containment-v1-20260804','state':state,'panel_status':'PUBLISHED','completed_count':len(rs),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(rs)/3*100,6),'percent_increase':round(len(rs)/3*100,6),'matched_unique_flood_risk_zone_3_rows':m,'evidence_records':len(rs),'source_evidence':e,'records':rs,'unknown_attributes_promoted_to_label':False,'fake_data':False,'large_raw_files_committed':False,'generated_at':now()};text=cj(result)+'\n'
 for p in OUTPUTS:write(p,text)
 print(cj({'completed_count':len(rs),'target_count':3,'matched_unique_flood_risk_zone_3_rows':m,'state':state,'output_sha256':sha(text.encode())}));return 0
if __name__=='__main__':raise SystemExit(main())
