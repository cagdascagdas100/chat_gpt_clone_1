#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from pyproj import Transformer
from shapely.geometry import Point, mapping, shape

INPUT=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
MANIFEST=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_building_heights_point_containment_source_manifest_20260803.json')
OUTPUTS=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_building_heights_point_containment_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/lambeth_building_heights_point_containment_latest.json')]
ROOTS=['https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBuildingHeights/FeatureServer','https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBuildingHeights/MapServer']
MAX_RESPONSE=8*1024*1024
TO_BNG=Transformer.from_crs('EPSG:4326','EPSG:27700',always_xy=True)
HEIGHT_KEYS=('height','level','storey','storeys','elevation','above sea','roof','z_')

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(b): return hashlib.sha256(b).hexdigest()
def atomic(p,t):
 p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=p.parent,delete=False) as f: f.write(t); q=pathlib.Path(f.name)
 q.replace(p)
def safe(url):
 x=urllib.parse.urlsplit(url)
 if x.scheme!='https' or (x.hostname or '').casefold()!='gis.lambeth.gov.uk' or x.username or x.password or x.fragment: raise RuntimeError('UNSAFE_OR_UNTRUSTED_URL:'+url)
 return url
def fetch(url,timeout):
 safe(url); r=urllib.request.Request(url,headers={'User-Agent':'AAYS-parcel-label-3/1.0'})
 with urllib.request.urlopen(r,timeout=timeout) as z:
  final=z.geturl(); safe(final); out=bytearray()
  while True:
   b=z.read(min(1024*1024,MAX_RESPONSE-len(out)+1))
   if not b: break
   out.extend(b)
   if len(out)>MAX_RESPONSE: raise RuntimeError(f'RESPONSE_TOO_LARGE:{len(out)}:{MAX_RESPONSE}')
  return bytes(out),final,int(getattr(z,'status',200))
def rows():
 p=json.loads(INPUT.read_text()); a=p.get('records',[])
 if len(a)!=3: raise RuntimeError(f'EXPECTED_3_INPUT_ROWS:{len(a)}')
 out=[]
 for x in a:
  req=('parcel_id','UPRN','FULLADDRESS','POSTCODE','longitude','latitude')
  if not x.get('exact_uprn_bound') or any(k not in x for k in req): raise RuntimeError('INVALID_INPUT_ROW')
  y={k:x[k] for k in req}; y['UPRN']=str(y['UPRN']); y['exact_uprn_bound']=True
  e,n=TO_BNG.transform(float(y['longitude']),float(y['latitude'])); y['easting']=float(e); y['northing']=float(n); out.append(y)
 if len({x['UPRN'] for x in out})!=3: raise RuntimeError('INPUT_UPRNS_NOT_UNIQUE')
 return out
def manifest():
 p=json.loads(MANIFEST.read_text())
 if p.get('service_name')!='LambethBuildingHeights' or p.get('service_roots')!=ROOTS: raise RuntimeError('WRONG_MANIFEST_SCOPE')
 for s in p.get('sources',[]):
  e=s.get('retained_excerpt','')
  if not e or sha(e.encode())!=s.get('retained_excerpt_sha256'): raise RuntimeError('MANIFEST_EXCERPT_SHA_MISMATCH')
 if len(p.get('sources',[]))<4: raise RuntimeError('SOURCE_MANIFEST_INCOMPLETE')
 return p
def metadata_url(root): return root+'?'+urllib.parse.urlencode({'f':'pjson'})
def discover(timeout,synthetic=False):
 attempts=[]
 for root in ROOTS:
  try:
   if synthetic:
    body=json.dumps({'currentVersion':11.3,'layers':[{'id':0,'name':'Building Heights'}]}).encode(); final=metadata_url(root); status=200
   else: body,final,status=fetch(metadata_url(root),timeout)
   p=json.loads(body); layers=p.get('layers')
   if not isinstance(layers,list) or len(layers)!=1 or not isinstance(layers[0],dict) or 'id' not in layers[0]: raise RuntimeError(f'EXPECTED_ONE_LAYER:{len(layers) if isinstance(layers,list) else -1}')
   layer_id=int(layers[0]['id']); layer_name=str(layers[0].get('name') or '')
   attempts.append({'url':metadata_url(root),'final_url':final,'http_status':status,'bytes':len(body),'content_sha256':sha(body),'layer_id':layer_id,'layer_name':layer_name,'state':'RESPONSE'})
   return root,layer_id,layer_name,attempts
  except Exception as e:
   attempts.append({'url':metadata_url(root),'state':'ERROR','error':f'{type(e).__name__}:{e}'})
 raise RuntimeError('ALL_SERVICE_METADATA_ENDPOINTS_FAILED:'+attempts[-1]['error'])
def query_url(root,layer_id,row):
 params={'where':'1=1','geometry':f"{row['easting']:.3f},{row['northing']:.3f}",'geometryType':'esriGeometryPoint','inSR':'27700','spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}
 return f'{root}/{layer_id}/query?'+urllib.parse.urlencode(params)
def synthetic_feature(row,i):
 lon=float(row['longitude']); lat=float(row['latitude']); d=0.00008
 ring=[[lon-d,lat-d],[lon+d,lat-d],[lon+d,lat+d],[lon-d,lat+d],[lon-d,lat-d]]
 return {'type':'Feature','id':i,'properties':{'OBJECTID':i,'BUILDING_HEIGHT':str(8+i),'HEIGHT_SOURCE':'Synthetic'},'geometry':{'type':'Polygon','coordinates':[ring]}}
def parse(body,row):
 p=json.loads(body)
 if p.get('type')!='FeatureCollection' or not isinstance(p.get('features'),list): raise RuntimeError('NOT_GEOJSON_FEATURE_COLLECTION')
 point=Point(float(row['longitude']),float(row['latitude'])); cand=[]
 for idx,f in enumerate(p['features'],1):
  if not isinstance(f,dict) or not f.get('geometry'): continue
  g=shape(f['geometry'])
  if g.is_empty or g.geom_type not in {'Polygon','MultiPolygon'}: continue
  if not g.is_valid: g=g.buffer(0)
  if not g.is_empty and g.covers(point):
   props={str(k):str(v)[:500] for k,v in (f.get('properties') or {}).items() if v not in (None,'')}
   raw=json.dumps(props,ensure_ascii=False,separators=(',',':'),sort_keys=True)
   geom=json.dumps(mapping(g),separators=(',',':'),sort_keys=True)
   heights={k:v for k,v in props.items() if any(q in k.casefold() for q in HEIGHT_KEYS)}
   cand.append({'feature_id':f.get('id'),'feature_index':idx,'geometry':mapping(g),'geometry_sha256':sha(geom.encode()),'raw_attributes_sha256':sha(raw.encode()),'retained_height_fields':dict(list(heights.items())[:30]),'retained_attributes':dict(list(props.items())[:50])})
 return cand,len(p['features'])
def run(a,timeout,synth=False):
 ev={'service_roots':ROOTS,'accessed_at':now(),'metadata_attempts':[],'requests':[],'network_request_count':0}
 try:
  root,layer_id,layer_name,attempts=discover(timeout,synth); ev['metadata_attempts']=attempts; ev['network_request_count']+=len(attempts); ev|={'selected_service_root':root,'selected_layer_id':layer_id,'selected_layer_name':layer_name}
 except Exception as e:
  ev['error']=f'{type(e).__name__}:{e}'; ev['network_request_count']=2 if not synth else 0
  return ev,[x|{'source_url':ROOTS[0],'candidate_count':0,'state':'NO_DATA','reason':ev['error'],'inferred':False} for x in a],0
 out=[]; matched=0
 for i,row in enumerate(a,1):
  u=query_url(root,layer_id,row); ev['network_request_count']+=1
  try:
   if synth:
    body=json.dumps({'type':'FeatureCollection','features':[synthetic_feature(row,i)]}).encode(); final=u; status=200
   else: body,final,status=fetch(u,timeout)
   cand,total=parse(body,row)
   ev['requests'].append({'UPRN':row['UPRN'],'url':u,'final_url':final,'http_status':status,'bytes':len(body),'content_sha256':sha(body),'returned_feature_count':total,'point_covering_candidate_count':len(cand),'state':'RESPONSE'})
   z=row|{'source_url':final,'candidate_count':len(cand),'inferred':False,'height_values_interpreted':False}
   if len(cand)==1: z|={'state':'MATCHED_UNIQUE_LAMBETH_BUILDING_HEIGHT_POLYGON'}|cand[0]; matched+=1
   elif len(cand)>1: z|={'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_POINT_CONTAINING_BUILDING_HEIGHT_POLYGONS','candidate_geometry_sha256':[x['geometry_sha256'] for x in cand]}
   else: z|={'state':'NO_DATA','reason':'NO_POINT_CONTAINING_LAMBETH_BUILDING_HEIGHT_POLYGON'}
  except Exception as e:
   err=f'{type(e).__name__}:{e}'; ev['requests'].append({'UPRN':row['UPRN'],'url':u,'state':'ERROR','error':err}); z=row|{'source_url':root,'candidate_count':0,'state':'NO_DATA','reason':err,'inferred':False,'height_values_interpreted':False}
  out.append(z)
 return ev,out,matched
def main():
 p=argparse.ArgumentParser(); p.add_argument('--timeout',type=int,default=20); p.add_argument('--validate-only',action='store_true'); p.add_argument('--synthetic-test',action='store_true'); q=p.parse_args()
 if not 1<=q.timeout<=300: raise RuntimeError('INVALID_TIMEOUT')
 a=rows(); m=manifest()
 if q.validate_only:
  print(json.dumps({'valid':True,'input_count':3,'target_uprns':[x['UPRN'] for x in a],'service_roots':ROOTS,'resource_class':'network','metadata_request_limit':2,'point_request_limit':3,'max_response_bytes':MAX_RESPONSE,'write_paths':[str(x) for x in OUTPUTS]},sort_keys=True)); return 0
 ev,o,n=run(a,q.timeout,q.synthetic_test)
 if q.synthetic_test:
  counts=[x['candidate_count'] for x in o]
  if n!=3 or counts!=[1,1,1]: raise RuntimeError(f'SYNTHETIC_FAILED:{n}:{counts}')
  print(json.dumps({'valid':True,'matched_unique_rows':n,'candidate_counts':counts,'selected_layer_id':ev['selected_layer_id'],'network_request_count':ev['network_request_count'],'geometry_sha256':[x['geometry_sha256'] for x in o]},sort_keys=True)); return 0
 state='PUBLISHED' if n else 'NO_DATA_CONTINUE'; d={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-lambeth-building-heights-point-containment-v1-20260803','state':state,'panel_status':'PUBLISHED','completed_count':len(o),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(o)/3*100,6),'percent_increase':round(len(o)/3*100,6),'matched_unique_building_height_rows':n,'evidence_records':len(o),'source_evidence':ev,'records':o,'height_values_promoted_as_verified':False,'fake_data':False,'large_raw_files_committed':False,'generated_at':now()}
 t=json.dumps(d,ensure_ascii=False,separators=(',',':'),sort_keys=True)+'\n'
 for x in OUTPUTS: atomic(x,t)
 print(json.dumps({'completed_count':len(o),'target_count':3,'matched_unique_building_height_rows':n,'state':state,'output_sha256':sha(t.encode())},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
