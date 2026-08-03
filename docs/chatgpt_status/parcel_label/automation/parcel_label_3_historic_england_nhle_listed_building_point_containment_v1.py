#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib,tempfile,urllib.parse,urllib.request
from datetime import datetime,timezone
from pyproj import Transformer
from shapely.geometry import Point,mapping,shape
I=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
M=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/historic_england_nhle_listed_building_point_containment_source_manifest_20260804.json')
O=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/historic_england_nhle_listed_building_point_containment_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/historic_england_nhle_listed_building_point_containment_latest.json')]
R='https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer'; L=R+'/3'; Q=L+'/query'; X=8*1024*1024
T=Transformer.from_crs('EPSG:4326','EPSG:27700',always_xy=True); F='OBJECTID,ListEntry,Name,Grade,ListDate,AmendDate,CaptureScale,hyperlink,area_ha,NGR,Easting,Northing'
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sh(b):return hashlib.sha256(b).hexdigest()
def aw(p,t):
 p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=p.parent,delete=False) as f:f.write(t);q=pathlib.Path(f.name)
 q.replace(p)
def safe(u):
 x=urllib.parse.urlsplit(u)
 if x.scheme!='https' or (x.hostname or '').casefold()!='services-eu1.arcgis.com' or x.username or x.password or x.fragment:raise RuntimeError('UNSAFE_URL')
def get(u,to):
 safe(u);r=urllib.request.Request(u,headers={'User-Agent':'AAYS-parcel-label-3/1.0','Accept':'application/geo+json,application/json;q=0.9'})
 with urllib.request.urlopen(r,timeout=to) as z:
  fu=z.geturl();safe(fu);b=z.read(X+1)
  if len(b)>X:raise RuntimeError('RESPONSE_TOO_LARGE')
  return b,fu,int(getattr(z,'status',200))
def manifest():
 d=json.loads(M.read_text())
 if d.get('service_root')!=R or d.get('layer_url')!=L or d.get('layer_id')!=3 or len(d.get('sources',[]))<4:raise RuntimeError('BAD_MANIFEST')
 for s in d['sources']:
  e=s.get('retained_excerpt','')
  if not e or sh(e.encode())!=s.get('retained_excerpt_sha256'):raise RuntimeError('MANIFEST_SHA')
 return d
def rows():
 d=json.loads(I.read_text());a=d.get('records',[]);m=manifest();us=set(m['target_uprns'])
 if len(a)!=3:raise RuntimeError('EXPECTED_3_ROWS')
 o=[]
 for x in a:
  ks=('parcel_id','UPRN','FULLADDRESS','POSTCODE','longitude','latitude')
  if not x.get('exact_uprn_bound') or any(k not in x for k in ks):raise RuntimeError('BAD_INPUT')
  y={k:x[k] for k in ks};y['UPRN']=str(y['UPRN']);y['exact_uprn_bound']=True
  if y['UPRN'] not in us:raise RuntimeError('UPRN_SCOPE')
  y['easting'],y['northing']=map(float,T.transform(float(y['longitude']),float(y['latitude'])));o.append(y)
 if len({x['UPRN'] for x in o})!=3:raise RuntimeError('DUP_UPRN')
 return o
def url(x):
 p={'where':'1=1','geometry':f"{x['easting']:.3f},{x['northing']:.3f}",'geometryType':'esriGeometryPoint','inSR':'27700','spatialRel':'esriSpatialRelIntersects','outFields':F,'returnGeometry':'true','outSR':'4326','f':'geojson'}
 return Q+'?'+urllib.parse.urlencode(p)
def sf(x,i,off=0):
 a=float(x['longitude'])+off;b=float(x['latitude'])+off;d=.00008;r=[[a-d,b-d],[a+d,b-d],[a+d,b+d],[a-d,b+d],[a-d,b-d]]
 return {'type':'Feature','id':i,'properties':{'OBJECTID':i,'ListEntry':1400000+i,'Name':f'Synthetic {i}','Grade':'II','ListDate':946684800000,'CaptureScale':'1:1250','hyperlink':f'https://historicengland.org.uk/listing/the-list/list-entry/{1400000+i}','area_ha':.01,'NGR':'TQ0000000000','Easting':x['easting'],'Northing':x['northing']},'geometry':{'type':'Polygon','coordinates':[r]}}
def parse(b,x):
 d=json.loads(b);fs=d.get('features')
 if d.get('type')!='FeatureCollection' or not isinstance(fs,list):raise RuntimeError('BAD_GEOJSON')
 p=Point(float(x['longitude']),float(x['latitude']));c=[]
 for n,f in enumerate(fs,1):
  if not isinstance(f,dict) or not f.get('geometry'):continue
  g=shape(f['geometry'])
  if g.is_empty or g.geom_type not in {'Polygon','MultiPolygon'}:continue
  if not g.is_valid:g=g.buffer(0)
  if g.is_empty or not g.covers(p):continue
  pr=f.get('properties') or {};at={k:pr.get(k) for k in F.split(',') if pr.get(k) is not None};gj=json.dumps(mapping(g),separators=(',',':'),sort_keys=True);aj=json.dumps(at,ensure_ascii=False,separators=(',',':'),sort_keys=True)
  c.append({'feature_id':f.get('id'),'feature_index':n,'geometry':mapping(g),'geometry_sha256':sh(gj.encode()),'official_attributes':at,'official_attributes_sha256':sh(aj.encode())})
 return c,len(fs)
def run(a,to,syn=False,amb=False):
 ev={'accessed_at':now(),'layer_url':L,'query_endpoint':Q,'request_count':0,'requests':[]};out=[];hit=0
 for i,x in enumerate(a,1):
  u=url(x);ev['request_count']+=1
  try:
   if syn:
    fs=[sf(x,i)];fs+=([sf(x,100+i,.00001)] if amb and i==2 else []);b=json.dumps({'type':'FeatureCollection','features':fs},separators=(',',':')).encode();fu=u;st=200
   else:b,fu,st=get(u,to)
   c,tot=parse(b,x);ev['requests'].append({'UPRN':x['UPRN'],'url':u,'final_url':fu,'http_status':st,'bytes':len(b),'response_sha256':sh(b),'returned_feature_count':tot,'point_covering_candidate_count':len(c),'state':'RESPONSE'});z=x|{'source_url':fu,'candidate_count':len(c),'inferred':False}
   if len(c)==1:
    q=c[0];at=q['official_attributes'];z|={'state':'MATCHED_UNIQUE_NHLE_LISTED_BUILDING_POLYGON','official_list_entry':at.get('ListEntry'),'official_listed_building_name':at.get('Name'),'official_grade':at.get('Grade'),'official_list_date':at.get('ListDate'),'official_amend_date':at.get('AmendDate'),'official_nhle_url':at.get('hyperlink')}|q;hit+=1
   elif len(c)>1:z|={'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_POINT_CONTAINING_NHLE_LISTED_BUILDING_POLYGONS','candidate_geometry_sha256':[q['geometry_sha256'] for q in c]}
   else:z|={'state':'NO_DATA','reason':'NO_POINT_CONTAINING_NHLE_LISTED_BUILDING_POLYGON'}
  except Exception as e:
   er=f'{type(e).__name__}:{e}';ev['requests'].append({'UPRN':x['UPRN'],'url':u,'state':'ERROR','error':er});z=x|{'source_url':Q,'candidate_count':0,'state':'NO_DATA','reason':er,'inferred':False}
  out.append(z)
 return ev,out,hit
def main():
 p=argparse.ArgumentParser();p.add_argument('--timeout',type=int,default=20);p.add_argument('--validate-only',action='store_true');p.add_argument('--synthetic-test',action='store_true');p.add_argument('--synthetic-ambiguous-test',action='store_true');q=p.parse_args()
 if not 1<=q.timeout<=300:raise RuntimeError('BAD_TIMEOUT')
 a=rows()
 if q.validate_only:print(json.dumps({'valid':True,'input_count':3,'target_uprns':[x['UPRN'] for x in a],'layer_url':L,'resource_class':'network','request_limit':3,'max_response_bytes':X,'write_paths':[str(x) for x in O]},sort_keys=True));return 0
 syn=q.synthetic_test or q.synthetic_ambiguous_test;ev,o,n=run(a,q.timeout,syn,q.synthetic_ambiguous_test)
 if q.synthetic_test:
  c=[x['candidate_count'] for x in o]
  if n!=3 or c!=[1,1,1]:raise RuntimeError('SYN_UNIQUE_FAIL')
  print(json.dumps({'valid':True,'matched_rows':n,'candidate_counts':c,'request_count':ev['request_count']},sort_keys=True));return 0
 if q.synthetic_ambiguous_test:
  s=[x['state'] for x in o]
  if n!=2 or s[1]!='NO_DATA' or o[1].get('reason')!='AMBIGUOUS_MULTIPLE_POINT_CONTAINING_NHLE_LISTED_BUILDING_POLYGONS':raise RuntimeError('SYN_AMBIG_FAIL')
  print(json.dumps({'valid':True,'matched_rows':n,'ambiguous_state':s[1],'request_count':ev['request_count']},sort_keys=True));return 0
 st='PUBLISHED' if n else 'NO_DATA_CONTINUE';d={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-historic-england-nhle-listed-building-point-containment-v1-20260804','state':st,'panel_status':'PUBLISHED','completed_count':len(o),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(o)/3*100,6),'percent_increase':round(len(o)/3*100,6),'matched_unique_nhle_listed_building_rows':n,'evidence_records':len(o),'source_evidence':ev,'records':o,'fake_data':False,'large_raw_files_committed':False,'generated_at':now()};t=json.dumps(d,ensure_ascii=False,separators=(',',':'),sort_keys=True)+'\n'
 for x in O:aw(x,t)
 print(json.dumps({'completed_count':len(o),'target_count':3,'matched_unique_nhle_listed_building_rows':n,'state':st,'output_sha256':sh(t.encode())},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
