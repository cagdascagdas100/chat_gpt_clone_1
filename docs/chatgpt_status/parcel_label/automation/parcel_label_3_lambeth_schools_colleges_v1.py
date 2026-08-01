from __future__ import annotations
import argparse,hashlib,json,os,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
TASK_ID='parcel-label-3-lambeth-schools-colleges-v1-20260801'
ENDPOINT='https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSchoolsAndColleges/FeatureServer/0/query'
DIR='https://gis.lambeth.gov.uk/arcgis/rest/services'
SERVICE='https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSchoolsAndColleges/FeatureServer'
OPEN='https://www.lambeth.gov.uk/about-council/transparency-open-data/open-mapping-data'
LIC='https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
PROBE='england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json'
OUT=('docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_schools_colleges_result_latest.json','england_map_web/data/aays_21_slots/parcel_label_3/lambeth_schools_colleges_latest.json')
IDS=('parcel_61523','parcel_61524','parcel_61525'); RADIUS=100; LIMIT=25; SPACING=1.2
now=lambda:datetime.now(timezone.utc).isoformat()
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
def points(root):
 d=json.loads((root/PROBE).read_text()); idx={x.get('parcel_id'):x for x in d.get('canonical_points',[])}; out=[]
 for i in IDS:
  x=idx.get(i)
  if not x or x.get('geometry_type')!='Point' or not x.get('point_valid'): raise ValueError(i)
  if not isinstance(x.get('longitude'),(int,float)) or not isinstance(x.get('latitude'),(int,float)): raise ValueError(i)
  out.append({'parcel_id':i,'longitude':float(x['longitude']),'latitude':float(x['latitude'])})
 return out
def url(p):
 q={'where':'1=1','geometry':f"{p['longitude']},{p['latitude']}",'geometryType':'esriGeometryPoint','inSR':'4326','spatialRel':'esriSpatialRelIntersects','distance':str(RADIUS),'units':'esriSRUnit_Meter','outFields':'*','returnGeometry':'true','outSR':'4326','resultRecordCount':str(LIMIT),'f':'json'}
 return ENDPOINT+'?'+urllib.parse.urlencode(q)
def one(p,timeout):
 u=url(p); at=now(); qsha=sha(u)
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'AAYS/parcel-label-3'})
  with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read(); status=getattr(r,'status',None)
  csha=hashlib.sha256(raw).hexdigest(); data=json.loads(raw.decode()); fs=data.get('features',[]) if isinstance(data,dict) else []; cs=[]
  for f in fs:
   if isinstance(f,dict) and isinstance(f.get('attributes'),dict) and isinstance(f.get('geometry'),dict):
    cs.append({'parcel_id':p['parcel_id'],'candidate_label':'School or College','candidate_only':True,'source_attributes':f['attributes'],'source_geometry':f['geometry'],'source_url':u,'accessed_at':at,'content_sha256':csha})
  e={'parcel_id':p['parcel_id'],'source_url':u,'accessed_at':at,'query_sha256':qsha,'http_status':status,'content_sha256':csha,'sha256_basis':'raw_response_bytes','relevant_record_ids_or_excerpt':f'features={len(fs)} accepted={len(cs)}','proven_fields':['query URL','access time','query SHA-256','raw-response SHA-256','feature count']}
 except Exception as ex:
  b=f'LAMBETH_SCHOOLS_COLLEGES_ERROR:{type(ex).__name__}'; cs=[]; e={'parcel_id':p['parcel_id'],'source_url':u,'accessed_at':at,'query_sha256':qsha,'http_status':None,'content_sha256':sha(b),'sha256_basis':'bounded_error_evidence_string','relevant_record_ids_or_excerpt':b,'proven_fields':['query URL','access time','query SHA-256','bounded error type']}
 e.update({'query_scope':{'radius_metres':RADIUS,'result_limit':LIMIT,'layer':0},'service_directory_url':DIR,'service_url':SERVICE,'open_mapping_url':OPEN,'license_or_terms_url':LIC})
 return e,cs
def validate(root):
 ps=points(root)
 if any(os.path.isabs(x) for x in OUT): raise ValueError('relative outputs required')
 return {'state':'VALIDATED','task_id':TASK_ID,'target_count':len(ps),'resource_class':'network_fetch','relative_script_path':'docs/chatgpt_status/parcel_label/automation/parcel_label_3_lambeth_schools_colleges_v1.py','relative_outputs':list(OUT),'radius_metres':RADIUS,'result_limit':LIMIT,'spacing_seconds':SPACING}
def run(root,timeout):
 es=[]; cs=[]
 for n,p in enumerate(points(root)):
  if n: time.sleep(SPACING)
  e,c=one(p,timeout); es.append(e); cs+=c
 done_count=len(es); target=3; progress=done_count/target*100
 result={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':TASK_ID,'generated_at':now(),'state':'CANDIDATES_PUBLISHED' if cs else 'NO_DATA_CONTINUE','panel_status':'PUBLISHED','completed_count':done_count,'target_count':target,'previous_percent':0.0,'progress_percent':progress,'percent_increase':progress,'produced_candidate_rows':len(cs),'candidates':cs,'source_evidence':es,'blocker':None if cs else {'code':'LAMBETH_SCHOOLS_COLLEGES_NO_USABLE_RESPONSE','state':'NO_DATA_CONTINUE','candidate_research_blocked':False,'manual_action_required':False,'retry_unchanged_route':False},'next_unverified_step':'SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_SCHOOLS_COLLEGES','inferred_values':0,'fake_data':False,'final_ready':False}
 text=json.dumps(result,separators=(',',':'),ensure_ascii=False)
 for o in OUT:
  p=root/o; p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+'.tmp'); t.write_text(text); os.replace(t,p)
 return result
def main():
 a=argparse.ArgumentParser(); a.add_argument('--root',default='.'); a.add_argument('--timeout',type=int,default=30); a.add_argument('--validate-only',action='store_true'); x=a.parse_args(); r=Path(x.root).resolve(); print(json.dumps(validate(r) if x.validate_only else run(r,x.timeout),indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
