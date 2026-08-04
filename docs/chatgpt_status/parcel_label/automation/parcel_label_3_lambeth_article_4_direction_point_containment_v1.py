#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from pyproj import Transformer
from shapely.geometry import Point, mapping, shape

INPUT=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
MANIFEST=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_article_4_direction_point_containment_source_manifest_20260804.json')
OUTPUTS=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_article_4_direction_point_containment_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/lambeth_article_4_direction_point_containment_latest.json')]
LAYER='https://gis.lambeth.gov.uk/arcgis/rest/services/LambethArticle4/MapServer/0'; QUERY=LAYER+'/query'; HOST='gis.lambeth.gov.uk'; LIMIT=8*1024*1024
TX=Transformer.from_crs('EPSG:4326','EPSG:27700',always_xy=True)

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(b): return hashlib.sha256(b).hexdigest()
def cj(v): return json.dumps(v,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def write(p,t):
 p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=p.parent,delete=False) as f: f.write(t); q=pathlib.Path(f.name)
 q.replace(p)
def safe(u):
 x=urllib.parse.urlsplit(u)
 if x.scheme!='https' or (x.hostname or '').casefold()!=HOST or x.username or x.password or x.fragment: raise RuntimeError('UNSAFE_URL')
def fetch(u,timeout):
 safe(u); r=urllib.request.Request(u,headers={'User-Agent':'AAYS-parcel-label-3/1.0','Accept':'application/geo+json,application/json;q=0.9'})
 with urllib.request.urlopen(r,timeout=timeout) as z:
  final=z.geturl(); safe(final); b=z.read(LIMIT+1)
  if len(b)>LIMIT: raise RuntimeError('RESPONSE_TOO_LARGE')
  return b,final,int(getattr(z,'status',200))
def load():
 m=json.loads(MANIFEST.read_text());
 if m.get('layer_url')!=LAYER or m.get('query_endpoint')!=QUERY or m.get('harvest_guid')!='e304f6fb73574e00ae1d2493092f0d61_1': raise RuntimeError('MANIFEST_CONTRACT')
 if len(m.get('target_uprns',[]))!=3 or len(m.get('sources',[]))<5: raise RuntimeError('MANIFEST_INCOMPLETE')
 for s in m['sources']:
  e=s.get('retained_excerpt','')
  if not e or sha(e.encode())!=s.get('retained_excerpt_sha256'): raise RuntimeError('MANIFEST_EXCERPT_SHA')
 d=json.loads(INPUT.read_text()); rows=[]; targets=set(m['target_uprns'])
 if len(d.get('records',[]))!=3: raise RuntimeError('EXPECTED_3_ROWS')
 for r in d['records']:
  keys=('parcel_id','UPRN','FULLADDRESS','POSTCODE','longitude','latitude')
  if not r.get('exact_uprn_bound') or any(k not in r for k in keys): raise RuntimeError('INVALID_INPUT')
  x={k:r[k] for k in keys}; x['UPRN']=str(x['UPRN']); x['exact_uprn_bound']=True
  if x['UPRN'] not in targets: raise RuntimeError('UPRN_NOT_TARGET')
  x['easting'],x['northing']=map(float,TX.transform(float(x['longitude']),float(x['latitude']))); rows.append(x)
 if len({r['UPRN'] for r in rows})!=3: raise RuntimeError('NON_UNIQUE_UPRN')
 return rows
def url(r):
 p={'where':'1=1','geometry':f"{r['easting']:.3f},{r['northing']:.3f}",'geometryType':'esriGeometryPoint','inSR':'27700','spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}
 return QUERY+'?'+urllib.parse.urlencode(p)
def attr(p,names):
 f={str(k).casefold():v for k,v in p.items()}
 for n in names:
  if f.get(n.casefold()) not in (None,''): return f[n.casefold()]
def parse(b,r):
 d=json.loads(b); fs=d.get('features')
 if d.get('type')!='FeatureCollection' or not isinstance(fs,list): raise RuntimeError('BAD_GEOJSON')
 pt=Point(float(r['longitude']),float(r['latitude'])); out=[]
 for i,f in enumerate(fs,1):
  if not isinstance(f,dict) or not f.get('geometry'): continue
  g=shape(f['geometry'])
  if g.is_empty or g.geom_type not in {'Polygon','MultiPolygon'}: continue
  if not g.is_valid: g=g.buffer(0)
  if g.is_empty or not g.covers(pt): continue
  p=f.get('properties') if isinstance(f.get('properties'),dict) else {}; gv=mapping(g)
  out.append({'feature_id':f.get('id'),'feature_index':i,'official_article_4_direction_name':attr(p,('NAME','DIRECTION','ARTICLE4','ARTICLE_4','TITLE')),'official_article_4_direction_reference':attr(p,('REF','REFERENCE','A4_REF','ARTICLE4REF','CODE')),'geometry':gv,'geometry_sha256':sha(cj(gv).encode()),'raw_attributes_sha256':sha(cj(p).encode())})
 return out,len(fs)
def synth(r,i,off=0.0):
 x=float(r['longitude'])+off; y=float(r['latitude'])+off; d=.00008; ring=[[x-d,y-d],[x+d,y-d],[x+d,y+d],[x-d,y+d],[x-d,y-d]]
 return {'type':'Feature','id':i,'properties':{'NAME':f'Synthetic Article 4 Direction {i}','A4_REF':f'A4-{i:02d}'},'geometry':{'type':'Polygon','coordinates':[ring]}}
def run(rows,timeout,synthetic=False,ambiguous=False):
 ev={'accessed_at':now(),'layer_url':LAYER,'query_endpoint':QUERY,'query_count':0,'queries':[]}; rec=[]; matched=0
 for i,r in enumerate(rows,1):
  u=url(r); ev['query_count']+=1
  try:
   if synthetic:
    fs=[synth(r,i)]+([synth(r,100+i,.00001)] if ambiguous and i==2 else []); b=cj({'type':'FeatureCollection','features':fs}).encode(); final=u; status=200
   else: b,final,status=fetch(u,timeout)
   c,n=parse(b,r); ev['queries'].append({'UPRN':r['UPRN'],'request_url':u,'final_url':final,'http_status':status,'bytes':len(b),'response_sha256':sha(b),'returned_feature_count':n,'point_covering_candidate_count':len(c),'state':'RESPONSE'})
   o={**r,'source_url':final,'layer_url':LAYER,'candidate_count':len(c),'inferred':False}
   if len(c)==1 and c[0].get('official_article_4_direction_name'): o.update({'state':'MATCHED_UNIQUE_LAMBETH_ARTICLE_4_DIRECTION_POLYGON','official_article_4_direction_designation':True,**c[0]}); matched+=1
   elif len(c)>1: o.update({'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_POINT_CONTAINING_LAMBETH_ARTICLE_4_DIRECTION_POLYGONS','candidate_geometry_sha256':[x['geometry_sha256'] for x in c]})
   elif len(c)==1: o.update({'state':'NO_DATA','reason':'UNIQUE_POLYGON_MISSING_OFFICIAL_NAME','candidate_geometry_sha256':[c[0]['geometry_sha256']]})
   else: o.update({'state':'NO_DATA','reason':'NO_POINT_CONTAINING_LAMBETH_ARTICLE_4_DIRECTION_POLYGON'})
  except Exception as e:
   err=f'{type(e).__name__}:{e}'; ev['queries'].append({'UPRN':r['UPRN'],'request_url':u,'state':'ERROR','error':err}); o={**r,'source_url':QUERY,'layer_url':LAYER,'candidate_count':0,'state':'NO_DATA','reason':err,'inferred':False}
  rec.append(o)
 return ev,rec,matched
def main():
 a=argparse.ArgumentParser(); a.add_argument('--timeout',type=int,default=20); a.add_argument('--validate-only',action='store_true'); a.add_argument('--synthetic-test',action='store_true'); a.add_argument('--synthetic-ambiguous-test',action='store_true'); z=a.parse_args()
 if not 1<=z.timeout<=300: raise RuntimeError('INVALID_TIMEOUT')
 rows=load()
 if z.validate_only: print(json.dumps({'valid':True,'input_count':3,'target_uprns':[r['UPRN'] for r in rows],'layer_url':LAYER,'query_endpoint':QUERY,'resource_class':'network','query_request_limit':3,'max_response_bytes':LIMIT,'write_paths':[str(p) for p in OUTPUTS]},sort_keys=True)); return 0
 syn=z.synthetic_test or z.synthetic_ambiguous_test; ev,rec,m=run(rows,z.timeout,syn,z.synthetic_ambiguous_test)
 if z.synthetic_test:
  names=[r.get('official_article_4_direction_name') for r in rec]
  if m!=3 or any(not n for n in names): raise RuntimeError('SYNTHETIC_UNIQUE_FAILED')
  print(json.dumps({'valid':True,'matched_rows':m,'candidate_counts':[r['candidate_count'] for r in rec],'names':names},sort_keys=True)); return 0
 if z.synthetic_ambiguous_test:
  if m!=2 or rec[1].get('reason')!='AMBIGUOUS_MULTIPLE_POINT_CONTAINING_LAMBETH_ARTICLE_4_DIRECTION_POLYGONS': raise RuntimeError('SYNTHETIC_AMBIGUOUS_FAILED')
  print(json.dumps({'valid':True,'matched_rows':m,'ambiguous_state':rec[1]['state'],'ambiguous_reason':rec[1]['reason']},sort_keys=True)); return 0
 state='PUBLISHED' if m else 'NO_DATA_CONTINUE'; result={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-lambeth-article-4-direction-point-containment-v1-20260804','state':state,'panel_status':'PUBLISHED','completed_count':len(rec),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(rec)/3*100,6),'percent_increase':round(len(rec)/3*100,6),'matched_unique_article_4_direction_rows':m,'evidence_records':len(rec),'source_evidence':ev,'records':rec,'unknown_attributes_promoted_to_label':False,'fake_data':False,'large_raw_files_committed':False,'generated_at':now()}
 text=cj(result)+'\n'
 for p in OUTPUTS: write(p,text)
 print(json.dumps({'completed_count':len(rec),'target_count':3,'matched_unique_article_4_direction_rows':m,'state':state,'output_sha256':sha(text.encode())},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
