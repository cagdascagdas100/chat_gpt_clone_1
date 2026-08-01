from __future__ import annotations
import argparse,csv,hashlib,io,json,math,os,urllib.request
from datetime import datetime,timezone
from pathlib import Path
TASK_ID='parcel-label-3-microsoft-global-buildings-manifest-v1-20260802'
URL='https://bfppub.blob.core.windows.net/%24web/2026-07-24/dataset-links.csv'
PROBE='england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json'
OUT=('docs/chatgpt_status/_shared/slots_21/parcel_label_3/microsoft_global_buildings_manifest_result_latest.json','england_map_web/data/aays_21_slots/parcel_label_3/microsoft_global_buildings_manifest_latest.json')
IDS=('parcel_61523','parcel_61524','parcel_61525'); ZOOM=9; MAX=16*1024*1024
now=lambda:datetime.now(timezone.utc).isoformat()
sha=lambda b:hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def root():return Path(os.environ.get('AAYS_REPO_ROOT','.')).resolve()
def points(r):
 d=json.loads((r/PROBE).read_text()); idx={x.get('parcel_id'):x for x in d.get('canonical_points',[])}; out=[]
 for i in IDS:
  x=idx.get(i)
  if not x or x.get('geometry_type')!='Point' or not x.get('point_valid'):raise ValueError(i)
  if not isinstance(x.get('longitude'),(int,float)) or not isinstance(x.get('latitude'),(int,float)):raise ValueError(i)
  out.append({'parcel_id':i,'longitude':float(x['longitude']),'latitude':float(x['latitude'])})
 return out
def quadkey(lon,lat):
 lat=max(min(lat,85.05112878),-85.05112878); x=(lon+180)/360; s=math.sin(math.radians(lat)); y=.5-math.log((1+s)/(1-s))/(4*math.pi); n=1<<ZOOM; tx=min(max(int(x*n),0),n-1); ty=min(max(int(y*n),0),n-1); q=[]
 for z in range(ZOOM,0,-1):
  m=1<<(z-1); q.append(str((1 if tx&m else 0)+(2 if ty&m else 0)))
 return ''.join(q)
def fetch(timeout):
 at=now(); req=urllib.request.Request(URL,headers={'User-Agent':'AAYS/parcel-label-3'})
 with urllib.request.urlopen(req,timeout=timeout) as res:
  status=getattr(res,'status',None); declared=res.headers.get('Content-Length')
  if declared and int(declared)>MAX:raise ValueError('manifest_too_large')
  data=res.read(MAX+1)
  if len(data)>MAX:raise ValueError('manifest_too_large')
 return data,status,at
def norm(s):return ''.join(c for c in s.lower() if c.isalnum())
def write(r,p,obj):
 d=r/p; d.parent.mkdir(parents=True,exist_ok=True); t=d.with_name(d.name+'.tmp'); t.write_text(json.dumps(obj,separators=(',',':'),ensure_ascii=False)); os.replace(t,d)
def run(timeout):
 r=root(); ps=points(r)
 for p in ps:p['quadkey_l9']=quadkey(p['longitude'],p['latitude'])
 data=None; status=None; at=now(); err=None
 try:data,status,at=fetch(timeout)
 except Exception as e:err=f'{type(e).__name__}:{e}'
 rows=[]; rawsha=None
 if data is not None:
  rawsha=sha(data); rows=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
 evidence=[]; candidates=[]; aliases={'unitedkingdom','uk','greatbritain','england'}
 for p in ps:
  qsha=sha(f"{URL}|{p['parcel_id']}|{p['quadkey_l9']}")
  if err:
   bounded=f'MICROSOFT_GLOBAL_BUILDINGS_MANIFEST_ERROR:{err}'; evidence.append({'parcel_id':p['parcel_id'],'source_url':URL,'accessed_at':at,'quadkey_l9':p['quadkey_l9'],'query_sha256':qsha,'http_status':status,'content_sha256':sha(bounded),'sha256_basis':'bounded_error_evidence_string','relevant_record_ids_or_excerpt':bounded[:1000],'proven_fields':['manifest URL','access time','L9 quadkey','bounded error type'],'record_scope':'dataset-links.csv resolution for one canonical point'}); continue
  match=[]
  for n,row in enumerate(rows,start=2):
   loc=row.get('Location') or row.get('Country') or row.get('RegionName') or ''; q=row.get('QuadKey') or row.get('quadkey') or ''; u=row.get('Url') or row.get('URL') or row.get('url') or ''
   if norm(loc) in aliases and q==p['quadkey_l9'] and u:match.append((n,loc,q,u))
  if match:
   n,loc,q,u=match[0]; candidates.append({'parcel_id':p['parcel_id'],'candidate_only':True,'quadkey_l9':q,'location':loc,'tile_url':u,'manifest_row':n,'exact_parcel_binding':False,'uprn_proven':False,'normalized_property_type_proven':False}); excerpt=f'row {n}: Location={loc}; QuadKey={q}; Url={u}'
  else:excerpt='MICROSOFT_GLOBAL_BUILDINGS_NO_UK_QUADKEY_MANIFEST_ROW'
  evidence.append({'parcel_id':p['parcel_id'],'source_url':URL,'accessed_at':at,'quadkey_l9':p['quadkey_l9'],'query_sha256':qsha,'http_status':status,'content_sha256':rawsha,'sha256_basis':'raw_manifest_bytes','relevant_record_ids_or_excerpt':excerpt,'proven_fields':['manifest URL','access time','manifest SHA-256','L9 quadkey','matching tile URL when present'],'record_scope':f'dataset-links.csv rows 2-{len(rows)+1}'})
 completed=len(ps); target=len(IDS); state='SOURCE_CANDIDATES_PUBLISHED' if candidates else 'NO_DATA_CONTINUE'; blocker=None if candidates else 'MICROSOFT_GLOBAL_BUILDINGS_MANIFEST_NO_USABLE_RESPONSE'
 result={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':TASK_ID,'generated_at':now(),'state':state,'panel_status':'PUBLISHED','completed_count':completed,'target_count':target,'previous_percent':0.0,'progress_percent':completed/target*100,'percent_increase':completed/target*100,'produced_candidate_rows':len(candidates),'candidates':candidates,'source_evidence':evidence,'blocker':{'code':blocker,'state':state,'candidate_research_blocked':False,'manual_action_required':False,'retry_unchanged_route':False},'next_unverified_step':'FETCH_MICROSOFT_GLOBAL_BUILDINGS_TILE_CANDIDATES' if candidates else 'SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_MICROSOFT_GLOBAL_BUILDINGS_MANIFEST','inferred_values':0,'fake_data':False,'final_ready':False}
 for p in OUT:write(r,p,result)
 return result
def validate():
 ps=points(root()); return {'state':'VALID','task_id':TASK_ID,'target_count':len(ps),'resource_class':'network_fetch','script_path_relative':True,'exact_write_paths_relative':all(not Path(x).is_absolute() for x in OUT),'manifest_url':URL,'quadkey_zoom':ZOOM,'quadkeys':[quadkey(p['longitude'],p['latitude']) for p in ps],'manifest_max_bytes':MAX}
def main():
 a=argparse.ArgumentParser(); a.add_argument('--timeout',type=int,default=30); a.add_argument('--validate-only',action='store_true'); x=a.parse_args(); print(json.dumps(validate() if x.validate_only else run(x.timeout),separators=(',',':'),ensure_ascii=False))
if __name__=='__main__':main()
