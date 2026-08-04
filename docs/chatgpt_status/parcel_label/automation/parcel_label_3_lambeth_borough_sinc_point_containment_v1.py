#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from typing import Any

INPUT=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
MANIFEST=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_borough_sinc_point_containment_source_manifest_20260804.json')
OUTPUTS=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_borough_sinc_point_containment_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/lambeth_borough_sinc_point_containment_latest.json')]
LAYER_ROOTS=['https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSitesOfBoroughNatureConservationImportance/FeatureServer/0','https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSitesOfBoroughNatureConservationImportance/MapServer/0']
ALLOWED_HOST='gis.lambeth.gov.uk'; MAX_RESPONSE_BYTES=8*1024*1024; MAX_METADATA_REQUESTS=2; MAX_POINT_REQUESTS=3
ATTR_HINTS=('objectid','name','site','reference','ref','code','grade','tier','status','description','address','url')

def now()->str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha256_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def canonical_json(v:Any)->str:return json.dumps(v,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def atomic_write(path:pathlib.Path,text:str)->None:
 path.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as h:h.write(text); t=pathlib.Path(h.name)
 t.replace(path)
def safe_url(url:str)->str:
 p=urllib.parse.urlsplit(url)
 if p.scheme!='https' or (p.hostname or '').casefold()!=ALLOWED_HOST or p.username or p.password or p.fragment:raise RuntimeError(f'UNSAFE_OR_UNTRUSTED_URL:{url}')
 return url
def fetch(url:str,timeout:int,accept:str)->tuple[bytes,str,int]:
 safe_url(url); req=urllib.request.Request(url,headers={'User-Agent':'AAYS-parcel-label-3/1.0','Accept':accept})
 with urllib.request.urlopen(req,timeout=timeout) as r:
  final=r.geturl(); safe_url(final); body=bytearray()
  while True:
   chunk=r.read(min(1024*1024,MAX_RESPONSE_BYTES-len(body)+1))
   if not chunk:break
   body.extend(chunk)
   if len(body)>MAX_RESPONSE_BYTES:raise RuntimeError(f'RESPONSE_TOO_LARGE:{len(body)}:{MAX_RESPONSE_BYTES}')
  return bytes(body),final,int(getattr(r,'status',200))
def load_manifest()->dict[str,Any]:
 p=json.loads(MANIFEST.read_text(encoding='utf-8'))
 if p.get('service_roots')!=LAYER_ROOTS:raise RuntimeError('WRONG_MANIFEST_SERVICE_ROOTS')
 if p.get('harvest_guid')!='88f412c44fcb44b298495e9282343807_1':raise RuntimeError('WRONG_MANIFEST_HARVEST_GUID')
 if len(p.get('target_uprns',[]))!=3:raise RuntimeError('SOURCE_MANIFEST_TARGET_COUNT')
 ss=p.get('sources',[])
 if len(ss)<5:raise RuntimeError('SOURCE_MANIFEST_INCOMPLETE')
 for s in ss:
  e=s.get('retained_excerpt','')
  if not e or sha256_bytes(e.encode())!=s.get('retained_excerpt_sha256'):raise RuntimeError('MANIFEST_EXCERPT_SHA_MISMATCH')
 return p
def load_rows()->list[dict[str,Any]]:
 p=json.loads(INPUT.read_text(encoding='utf-8')); recs=p.get('records',[]); targets=set(load_manifest()['target_uprns'])
 if len(recs)!=3:raise RuntimeError(f'EXPECTED_3_INPUT_ROWS:{len(recs)}')
 rows=[]
 for r in recs:
  req=('parcel_id','UPRN','FULLADDRESS','POSTCODE','longitude','latitude')
  if not r.get('exact_uprn_bound') or any(k not in r for k in req):raise RuntimeError('INVALID_INPUT_ROW')
  row={k:r[k] for k in req}; row['UPRN']=str(row['UPRN']); row['exact_uprn_bound']=True
  if row['UPRN'] not in targets:raise RuntimeError(f"UPRN_NOT_IN_MANIFEST:{row['UPRN']}")
  rows.append(row)
 if len({r['UPRN'] for r in rows})!=3:raise RuntimeError('INPUT_UPRNS_NOT_UNIQUE')
 return rows
def point_on_segment(px,py,x1,y1,x2,y2,eps=1e-12):
 cross=(px-x1)*(y2-y1)-(py-y1)*(x2-x1)
 return abs(cross)<=eps and min(x1,x2)-eps<=px<=max(x1,x2)+eps and min(y1,y2)-eps<=py<=max(y1,y2)+eps
def ring_contains_or_touches(ring,point):
 px,py=point; inside=False
 if len(ring)<4:return False
 for i in range(len(ring)-1):
  x1,y1=ring[i][:2]; x2,y2=ring[i+1][:2]
  if point_on_segment(px,py,x1,y1,x2,y2):return True
  if (y1>py)!=(y2>py) and px < (x2-x1)*(py-y1)/(y2-y1)+x1:inside=not inside
 return inside
def polygon_covers(coords,point):return bool(coords and ring_contains_or_touches(coords[0],point) and not any(ring_contains_or_touches(h,point) for h in coords[1:]))
def geometry_covers(g,point):
 c=g.get('coordinates'); t=g.get('type')
 return polygon_covers(c,point) if t=='Polygon' and isinstance(c,list) else any(polygon_covers(x,point) for x in c) if t=='MultiPolygon' and isinstance(c,list) else False
def metadata_url(root):return root+'?'+urllib.parse.urlencode({'f':'json'})
def discover_layer(timeout,evidence):
 errors=[]
 for root in LAYER_ROOTS:
  evidence['metadata_request_count']+=1; url=metadata_url(root)
  try:
   body,final,status=fetch(url,timeout,'application/json'); p=json.loads(body)
   if p.get('type')!='Feature Layer':raise RuntimeError('NOT_FEATURE_LAYER')
   if p.get('geometryType')!='esriGeometryPolygon':raise RuntimeError('NOT_POLYGON_LAYER')
   fields=sorted(str(f.get('name','')) for f in p.get('fields',[]) if isinstance(f,dict))
   evidence['metadata_response_count']+=1; evidence['metadata_requests'].append({'layer_root':root,'request_url':url,'final_url':final,'http_status':status,'bytes':len(body),'response_sha256':sha256_bytes(body),'geometry_type':p.get('geometryType'),'field_names':fields,'state':'RESPONSE'}); return root
  except Exception as exc:
   err=f'{type(exc).__name__}:{exc}'; errors.append(err); evidence['metadata_requests'].append({'layer_root':root,'request_url':url,'state':'ERROR','error':err})
 raise RuntimeError('ALL_LAYER_METADATA_ENDPOINTS_FAILED:'+'|'.join(errors))
def query_url(root,row):
 q={'where':'1=1','geometry':f"{float(row['longitude']):.15f},{float(row['latitude']):.15f}",'geometryType':'esriGeometryPoint','inSR':'4326','spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}
 return root+'/query?'+urllib.parse.urlencode(q)
def retained_attributes(props):
 out={}
 for k in sorted(props):
  if any(h in str(k).casefold() for h in ATTR_HINTS) and (isinstance(props[k],(str,int,float,bool)) or props[k] is None):out[str(k)]=props[k]
  if len(out)>=24:break
 return out
def parse_candidates(body,row):
 p=json.loads(body); fs=p.get('features')
 if p.get('type')!='FeatureCollection' or not isinstance(fs,list):raise RuntimeError('NOT_GEOJSON_FEATURE_COLLECTION')
 point=(float(row['longitude']),float(row['latitude'])); out=[]
 for i,f in enumerate(fs,1):
  if not isinstance(f,dict) or not isinstance(f.get('geometry'),dict) or not geometry_covers(f['geometry'],point):continue
  props=f.get('properties') if isinstance(f.get('properties'),dict) else {}; g=f['geometry']
  out.append({'feature_id':f.get('id'),'feature_index':i,'official_sinc_tier':'Borough','official_borough_sinc_designation':True,'retained_official_attributes':retained_attributes(props),'raw_attributes_sha256':sha256_bytes(canonical_json(props).encode()),'geometry_sha256':sha256_bytes(canonical_json(g).encode()),'geometry':g})
 return out,len(fs)
def synthetic_feature(row,i,offset=0.0):
 lon=float(row['longitude'])+offset; lat=float(row['latitude'])+offset; d=.00008; ring=[[lon-d,lat-d],[lon+d,lat-d],[lon+d,lat+d],[lon-d,lat+d],[lon-d,lat-d]]
 return {'type':'Feature','id':i,'properties':{'OBJECTID':i,'SITE_NAME':f'Synthetic Borough SINC {i}','SINC_TIER':'Borough'},'geometry':{'type':'Polygon','coordinates':[ring]}}
def run(rows,timeout,synthetic=False,ambiguous=False):
 ev={'accessed_at':now(),'layer_roots':LAYER_ROOTS,'metadata_request_count':0,'metadata_response_count':0,'metadata_requests':[],'point_query_count':0,'point_queries':[]}
 if synthetic:root=LAYER_ROOTS[0]; ev['selected_layer_root']=root
 else:
  try:root=discover_layer(timeout,ev); ev['selected_layer_root']=root
  except Exception as exc:
   err=f'{type(exc).__name__}:{exc}'; ev['discovery_error']=err; return ev,[{**r,'source_url':LAYER_ROOTS[0],'candidate_count':0,'state':'NO_DATA','reason':err,'inferred':False} for r in rows],0
 recs=[]; matched=0
 for idx,row in enumerate(rows,1):
  url=query_url(root,row); ev['point_query_count']+=1
  try:
   if synthetic:
    fs=[synthetic_feature(row,idx)]
    if ambiguous and idx==2:fs.append(synthetic_feature(row,100+idx,.00001))
    body=canonical_json({'type':'FeatureCollection','features':fs}).encode(); final=url; status=200
   else:body,final,status=fetch(url,timeout,'application/geo+json,application/json;q=0.9')
   candidates,total=parse_candidates(body,row); ev['point_queries'].append({'UPRN':row['UPRN'],'request_url':url,'final_url':final,'http_status':status,'bytes':len(body),'response_sha256':sha256_bytes(body),'returned_feature_count':total,'point_covering_candidate_count':len(candidates),'state':'RESPONSE'})
   o={**row,'source_url':final,'layer_root':root,'candidate_count':len(candidates),'inferred':False}
   if len(candidates)==1:o.update({'state':'MATCHED_UNIQUE_LAMBETH_BOROUGH_SINC_POLYGON',**candidates[0]}); matched+=1
   elif len(candidates)>1:o.update({'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_POINT_CONTAINING_LAMBETH_BOROUGH_SINC_POLYGONS','candidate_geometry_sha256':[c['geometry_sha256'] for c in candidates]})
   else:o.update({'state':'NO_DATA','reason':'NO_POINT_CONTAINING_LAMBETH_BOROUGH_SINC_POLYGON'})
  except Exception as exc:
   err=f'{type(exc).__name__}:{exc}'; ev['point_queries'].append({'UPRN':row['UPRN'],'request_url':url,'state':'ERROR','error':err}); o={**row,'source_url':root+'/query','layer_root':root,'candidate_count':0,'state':'NO_DATA','reason':err,'inferred':False}
  recs.append(o)
 return ev,recs,matched
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--timeout',type=int,default=20); ap.add_argument('--validate-only',action='store_true'); ap.add_argument('--synthetic-test',action='store_true'); ap.add_argument('--synthetic-ambiguous-test',action='store_true'); a=ap.parse_args()
 if not 1<=a.timeout<=300:raise RuntimeError('INVALID_TIMEOUT')
 rows=load_rows()
 if a.validate_only:
  print(json.dumps({'valid':True,'input_count':3,'target_uprns':[r['UPRN'] for r in rows],'layer_roots':LAYER_ROOTS,'resource_class':'network','metadata_request_limit':MAX_METADATA_REQUESTS,'point_query_limit':MAX_POINT_REQUESTS,'max_response_bytes':MAX_RESPONSE_BYTES,'write_paths':[str(p) for p in OUTPUTS]},sort_keys=True)); return 0
 syn=a.synthetic_test or a.synthetic_ambiguous_test; ev,recs,matched=run(rows,a.timeout,syn,a.synthetic_ambiguous_test)
 if a.synthetic_test:
  if matched!=3 or [r['candidate_count'] for r in recs]!=[1,1,1]:raise RuntimeError(f'SYNTHETIC_UNIQUE_FAILED:{matched}')
  print(json.dumps({'valid':True,'matched_rows':matched,'point_query_count':ev['point_query_count']},sort_keys=True)); return 0
 if a.synthetic_ambiguous_test:
  states=[r['state'] for r in recs]
  if matched!=2 or states[1]!='NO_DATA' or recs[1].get('reason')!='AMBIGUOUS_MULTIPLE_POINT_CONTAINING_LAMBETH_BOROUGH_SINC_POLYGONS':raise RuntimeError(f'SYNTHETIC_AMBIGUOUS_FAILED:{matched}:{states}')
  print(json.dumps({'valid':True,'matched_rows':matched,'ambiguous_state':states[1]},sort_keys=True)); return 0
 state='PUBLISHED' if matched else 'NO_DATA_CONTINUE'; result={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-lambeth-borough-sinc-point-containment-v1-20260804','state':state,'panel_status':'PUBLISHED','completed_count':len(recs),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(recs)/3*100,6),'percent_increase':round(len(recs)/3*100,6),'matched_unique_borough_sinc_rows':matched,'evidence_records':len(recs),'source_evidence':ev,'records':recs,'unknown_attributes_promoted_to_label':False,'fake_data':False,'large_raw_files_committed':False,'generated_at':now()}
 text=canonical_json(result)+'\n'
 for p in OUTPUTS:atomic_write(p,text)
 print(json.dumps({'completed_count':len(recs),'target_count':3,'matched_unique_borough_sinc_rows':matched,'state':state,'output_sha256':sha256_bytes(text.encode())},sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
