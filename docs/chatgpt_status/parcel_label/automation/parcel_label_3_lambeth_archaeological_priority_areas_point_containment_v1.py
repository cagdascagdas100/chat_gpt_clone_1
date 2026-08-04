#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from typing import Any

INPUT=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
MANIFEST=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_archaeological_priority_areas_point_containment_source_manifest_20260804.json')
OUTPUTS=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_archaeological_priority_areas_point_containment_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/lambeth_archaeological_priority_areas_point_containment_latest.json')]
ROOTS=['https://gis.lambeth.gov.uk/arcgis/rest/services/LambethArchaeologicalPriorityAreas/FeatureServer','https://gis.lambeth.gov.uk/arcgis/rest/services/LambethArchaeologicalPriorityAreas/MapServer']
HOST='gis.lambeth.gov.uk'; MAX=8*1024*1024

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(b:bytes): return hashlib.sha256(b).hexdigest()
def cj(v:Any): return json.dumps(v,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def write(path:pathlib.Path,text:str):
 path.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f: f.write(text); t=pathlib.Path(f.name)
 t.replace(path)
def safe(url:str):
 p=urllib.parse.urlsplit(url)
 if p.scheme!='https' or (p.hostname or '').casefold()!=HOST or p.username or p.password or p.fragment: raise RuntimeError('UNSAFE_URL')
 return url
def fetch(url:str,timeout:int):
 safe(url); req=urllib.request.Request(url,headers={'User-Agent':'AAYS-parcel-label-3/1.0','Accept':'application/json,application/geo+json'})
 with urllib.request.urlopen(req,timeout=timeout) as r:
  final=safe(r.geturl()); body=r.read(MAX+1)
  if len(body)>MAX: raise RuntimeError('RESPONSE_TOO_LARGE')
  return body,final,int(getattr(r,'status',200))
def load():
 m=json.loads(MANIFEST.read_text()); rows=json.loads(INPUT.read_text()).get('records',[])
 if m.get('service_roots')!=ROOTS or m.get('harvest_guid')!='e304f6fb73574e00ae1d2493092f0d61_0' or len(m.get('sources',[]))<5: raise RuntimeError('BAD_MANIFEST')
 for s in m['sources']:
  x=s.get('retained_excerpt','')
  if not x or sha(x.encode())!=s.get('retained_excerpt_sha256'): raise RuntimeError('BAD_EXCERPT_SHA')
 if len(rows)!=3: raise RuntimeError('EXPECTED_3_ROWS')
 out=[]; targets=set(m['target_uprns'])
 for r in rows:
  keys=('parcel_id','UPRN','FULLADDRESS','POSTCODE','longitude','latitude')
  if not r.get('exact_uprn_bound') or any(k not in r for k in keys): raise RuntimeError('BAD_INPUT_ROW')
  x={k:r[k] for k in keys}; x['UPRN']=str(x['UPRN']); x['exact_uprn_bound']=True
  if x['UPRN'] not in targets: raise RuntimeError('UPRN_NOT_IN_MANIFEST')
  out.append(x)
 if len({x['UPRN'] for x in out})!=3: raise RuntimeError('DUP_UPRN')
 return out
def discover(timeout:int,e:dict):
 errs=[]
 for root in ROOTS:
  u=root+'?f=json'; e['metadata_attempt_count']+=1
  try:
   b,f,s=fetch(u,timeout); p=json.loads(b); layers=[x for x in p.get('layers',[]) if isinstance(x,dict) and isinstance(x.get('id'),int)]
   if not layers: raise RuntimeError('NO_LAYER')
   layers.sort(key=lambda x:(0 if 'archaeolog' in str(x.get('name','')).casefold() else 1,x['id']))
   x=layers[0]; e['metadata_response_count']+=1; e['metadata_requests'].append({'service_root':root,'request_url':u,'final_url':f,'http_status':s,'bytes':len(b),'response_sha256':sha(b),'selected_layer_id':x['id'],'selected_layer_name':str(x.get('name','')),'state':'RESPONSE'})
   return root,int(x['id']),str(x.get('name',''))
  except Exception as ex:
   z=f'{type(ex).__name__}:{ex}'; errs.append(z); e['metadata_requests'].append({'service_root':root,'request_url':u,'state':'ERROR','error':z})
 raise RuntimeError('ALL_SERVICE_METADATA_ENDPOINTS_FAILED:'+'|'.join(errs))
def name(props:dict):
 ranked=[]
 for k,v in props.items():
  if not isinstance(v,(str,int,float)) or not str(v).strip(): continue
  q=k.casefold(); score=0 if ('name' in q or 'title' in q) else 1 if ('apa' in q or 'archaeolog' in q) else 2 if ('tier' in q or 'priority' in q) else 3 if ('ref' in q or 'code' in q) else 99
  if score<99: ranked.append((score,' '.join(str(v).split())))
 return sorted(ranked,key=lambda x:(x[0],x[1].casefold()))[0][1] if ranked else None
def qurl(root:str,lid:int,row:dict):
 p={'where':'1=1','geometry':f"{float(row['longitude']):.12f},{float(row['latitude']):.12f}",'geometryType':'esriGeometryPoint','inSR':'4326','spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}
 return f'{root}/{lid}/query?'+urllib.parse.urlencode(p)
def parse(body:bytes):
 p=json.loads(body)
 if p.get('type')!='FeatureCollection' or not isinstance(p.get('features'),list): raise RuntimeError('BAD_GEOJSON')
 out=[]
 for i,f in enumerate(p['features'],1):
  if not isinstance(f,dict): continue
  g=f.get('geometry') or {}; props=f.get('properties') if isinstance(f.get('properties'),dict) else {}
  if g.get('type') not in ('Polygon','MultiPolygon'): continue
  n=name(props)
  if not n: continue
  out.append({'feature_id':f.get('id'),'feature_index':i,'official_archaeological_priority_area_name':n,'geometry_sha256':sha(cj(g).encode()),'raw_attributes_sha256':sha(cj(props).encode()),'retained_official_attributes':{k:v for k,v in sorted(props.items()) if isinstance(v,(str,int,float,bool)) or v is None}})
 return out,len(p['features'])
def synth(row:dict,i:int,dup=False):
 def f(j): return {'type':'Feature','id':j,'properties':{'OBJECTID':j,'NAME':f'Synthetic Archaeological Priority Area {j}','TIER':'Tier 2'},'geometry':{'type':'Polygon','coordinates':[[[row['longitude']-.0001,row['latitude']-.0001],[row['longitude']+.0001,row['latitude']-.0001],[row['longitude']+.0001,row['latitude']+.0001],[row['longitude']-.0001,row['latitude']+.0001],[row['longitude']-.0001,row['latitude']-.0001]]]}}
 fs=[f(i)]; fs+=([f(100+i)] if dup else []); return cj({'type':'FeatureCollection','features':fs}).encode()
def run(rows,timeout,synthetic=False,ambiguous=False):
 e={'accessed_at':now(),'service_roots':ROOTS,'metadata_attempt_count':0,'metadata_response_count':0,'metadata_requests':[],'point_query_count':0,'point_queries':[]}
 if synthetic: root,lid,lname=ROOTS[0],0,'Synthetic APA'
 else:
  try: root,lid,lname=discover(timeout,e)
  except Exception as ex:
   z=f'{type(ex).__name__}:{ex}'; e['discovery_error']=z
   return e,[{**r,'source_url':ROOTS[0],'candidate_count':0,'state':'NO_DATA','reason':z,'inferred':False} for r in rows],0
 out=[]; matched=0
 for i,r in enumerate(rows,1):
  u=qurl(root,lid,r); e['point_query_count']+=1
  try:
   if synthetic: b,f,s=synth(r,i,ambiguous and i==2),u,200
   else: b,f,s=fetch(u,timeout)
   c,total=parse(b); e['point_queries'].append({'UPRN':r['UPRN'],'request_url':u,'final_url':f,'http_status':s,'bytes':len(b),'response_sha256':sha(b),'returned_feature_count':total,'named_polygon_candidate_count':len(c),'state':'RESPONSE'})
   x={**r,'source_url':f,'service_root':root,'layer_id':lid,'layer_name':lname,'candidate_count':len(c),'inferred':False}
   if len(c)==1: x.update({'state':'MATCHED_UNIQUE_LAMBETH_ARCHAEOLOGICAL_PRIORITY_AREA_POLYGON','official_archaeological_priority_area_designation':True,'official_archaeological_priority_area_label':'Lambeth Archaeological Priority Area',**c[0]}); matched+=1
   elif len(c)>1: x.update({'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_NAMED_ARCHAEOLOGICAL_PRIORITY_AREA_POLYGONS','candidate_geometry_sha256':[a['geometry_sha256'] for a in c]})
   else: x.update({'state':'NO_DATA','reason':'NO_NAMED_ARCHAEOLOGICAL_PRIORITY_AREA_POLYGON'})
  except Exception as ex:
   z=f'{type(ex).__name__}:{ex}'; e['point_queries'].append({'UPRN':r['UPRN'],'request_url':u,'state':'ERROR','error':z}); x={**r,'source_url':f'{root}/{lid}/query','candidate_count':0,'state':'NO_DATA','reason':z,'inferred':False}
  out.append(x)
 return e,out,matched
def main():
 a=argparse.ArgumentParser(); a.add_argument('--timeout',type=int,default=20); a.add_argument('--validate-only',action='store_true'); a.add_argument('--synthetic-test',action='store_true'); a.add_argument('--synthetic-ambiguous-test',action='store_true'); z=a.parse_args()
 if not 1<=z.timeout<=300: raise RuntimeError('BAD_TIMEOUT')
 rows=load()
 if z.validate_only: print(cj({'valid':True,'input_count':3,'target_uprns':[r['UPRN'] for r in rows],'service_roots':ROOTS,'resource_class':'network','metadata_request_limit':2,'point_query_limit':3,'max_response_bytes':MAX,'write_paths':[str(p) for p in OUTPUTS]})); return 0
 syn=z.synthetic_test or z.synthetic_ambiguous_test; e,records,matched=run(rows,z.timeout,syn,z.synthetic_ambiguous_test)
 if z.synthetic_test:
  cc=[r['candidate_count'] for r in records]
  if matched!=3 or cc!=[1,1,1]: raise RuntimeError('SYNTH_UNIQUE_FAIL')
  print(cj({'valid':True,'matched_rows':matched,'candidate_counts':cc,'point_query_count':e['point_query_count']})); return 0
 if z.synthetic_ambiguous_test:
  if matched!=2 or records[1].get('reason')!='AMBIGUOUS_MULTIPLE_NAMED_ARCHAEOLOGICAL_PRIORITY_AREA_POLYGONS': raise RuntimeError('SYNTH_AMBIG_FAIL')
  print(cj({'valid':True,'matched_rows':matched,'ambiguous_state':records[1]['state'],'point_query_count':e['point_query_count']})); return 0
 state='PUBLISHED' if matched else 'NO_DATA_CONTINUE'; result={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-lambeth-archaeological-priority-areas-point-containment-v1-20260804','state':state,'panel_status':'PUBLISHED','completed_count':len(records),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(records)/3*100,6),'percent_increase':round(len(records)/3*100,6),'matched_unique_archaeological_priority_area_rows':matched,'evidence_records':len(records),'source_evidence':e,'records':records,'unknown_attributes_promoted_to_label':False,'fake_data':False,'large_raw_files_committed':False,'generated_at':now()}; text=cj(result)+'\n'
 for p in OUTPUTS: write(p,text)
 print(cj({'completed_count':len(records),'target_count':3,'matched_unique_archaeological_priority_area_rows':matched,'state':state,'output_sha256':sha(text.encode())})); return 0
if __name__=='__main__': raise SystemExit(main())
