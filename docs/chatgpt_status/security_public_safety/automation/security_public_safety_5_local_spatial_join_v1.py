from __future__ import annotations
import copy,hashlib,json,os,subprocess,tempfile,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
SLOT_ID='security_public_safety_5';LINEAGE_ID='86b5e932de484ad26133fa8c';P0,P1,PC=61524,76903,15380;START_NUM=61674;MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT') or Path(__file__).resolve().parents[4])
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
CANON_BRANCH='codex/aays-single-runner-v5-20260706';CANON_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson';CANON_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
PRIOR=REPO/'incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/planning_data_title_boundary_mps_lsoa_61624_61673_20260928T221705Z/records.geojson';PRIOR_MPS_SHA='255d63bd759f08d7b0dd7674a38fca25ccb824c6c3a5d75d3fb00e504a34c082'
API='https://www.planning.data.gov.uk/entity.geojson';SOURCE_WINDOW='planning_data_title_boundary_geometry_entity_lambeth_sps5_61674_61723_v1';LAMBETH_ENTITY=626195
REQ=['evidence_scope','coverage_area_id','source_resolution','time_window','source_url','measurement_date','measurement_method','spatial_binding_method','confidence_score_0_100','evidence_grade','field_evidence','canonical_parcel_id']
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def git(args,timeout=900,stdout=None):return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(p):
 r=git(['hash-object',str(p)],180);return r.stdout.decode('utf-8','replace').strip() if r.returncode==0 else None
def materialize():
 c=Path(tempfile.gettempdir())/'aays_sps5'/Path(CANON_REL).name;c.parent.mkdir(parents=True,exist_ok=True)
 ev={'branch':CANON_BRANCH,'repo_path':CANON_REL,'required_git_blob_sha':CANON_BLOB,'verified':False}
 if c.is_file() and blob_sha(c)==CANON_BLOB:ev.update(cache_hit=True,verified=True);return c,ev
 c.unlink(missing_ok=True)
 for ref in (f'origin/{CANON_BRANCH}',CANON_BRANCH):
  part=c.with_suffix('.part');part.unlink(missing_ok=True)
  with part.open('wb') as fh:r=git(['show',f'{ref}:{CANON_REL}'],stdout=fh)
  if r.returncode==0 and blob_sha(part)==CANON_BLOB:os.replace(part,c);ev.update(source_ref=ref,verified=True);return c,ev
  part.unlink(missing_ok=True)
 r=git(['fetch','origin',CANON_BRANCH],900)
 if r.returncode==0:
  part=c.with_suffix('.part')
  with part.open('wb') as fh:s=git(['show',f'FETCH_HEAD:{CANON_REL}'],stdout=fh)
  if s.returncode==0 and blob_sha(part)==CANON_BLOB:os.replace(part,c);ev.update(source_ref='FETCH_HEAD',verified=True);return c,ev
 ev['error']='EXACT_CANONICAL_BLOB_NOT_MATERIALIZED';return None,ev
def pid_num(pid):
 try:return int(pid.split('_',1)[1]) if isinstance(pid,str) and pid.startswith('parcel_') else None
 except:return None
def get_pid(p):
 for k in ('security_parcel_id','parcel_id'):
  v=p.get(k)
  if isinstance(v,str) and v.startswith('parcel_'):return v
 return None
def http_json(url):
 req=urllib.request.Request(url,headers={'User-Agent':'AAYS-security-public-safety-5/planning-data-geometry-entity-v1','Accept':'application/geo+json,application/json'})
 with urllib.request.urlopen(req,timeout=120) as resp:
  b=resp.read();return int(resp.status),resp.geturl(),b,json.loads(b.decode('utf-8'))
def point_in_ring(x,y,ring):
 inside=False;j=len(ring)-1
 for i in range(len(ring)):
  xi,yi=ring[i][:2];xj,yj=ring[j][:2]
  if ((yi>y)!=(yj>y)):
   d=yj-yi
   if d and x<(xj-xi)*(y-yi)/d+xi:inside=not inside
  j=i
 return inside
def point_in_poly(x,y,p):
 return bool(p and point_in_ring(x,y,p[0]) and not any(point_in_ring(x,y,h) for h in p[1:]))
def contains(g,x,y):
 if not g:return False
 if g.get('type')=='Polygon':return point_in_poly(x,y,g.get('coordinates') or [])
 if g.get('type')=='MultiPolygon':return any(point_in_poly(x,y,p) for p in (g.get('coordinates') or []))
 return False
def save(x):OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def semantic(f):
 p=f.get('properties') or {};reasons=[]
 if (f.get('geometry') or {}).get('type') not in ('Polygon','MultiPolygon'):reasons.append('geometry_must_be_Polygon_or_MultiPolygon')
 for k in REQ:
  if k not in p or p[k] in (None,''):reasons.append('missing_required_field:'+k)
 if p.get('evidence_scope')!='parcel':reasons.append('evidence_scope_must_equal_parcel')
 if 'parcel_id' in p:reasons.append('forbidden_property:parcel_id')
 if 'accepted_parcel' in p:reasons.append('forbidden_property:accepted_parcel')
 return reasons
def main():
 base={'schema_version':9,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},'lineage_id':LINEAGE_ID,'generated_at':now(),'source_window_id':SOURCE_WINDOW,'first_missing_criterion':'CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED','max_source_records':MAX_RECORDS,'accepted_count_claimed':0,'final_package_written':False,'fake_data':False}
 cp,mat=materialize();base['canonical_materialization']=mat
 if not cp or not PRIOR.is_file():base.update(status='BLOCKED',blocker='CANONICAL_OR_PRIOR_EVIDENCE_MISSING');save(base);return 0
 prior=json.loads(PRIOR.read_text(encoding='utf-8-sig'));ev_by={};tmpl_by={}
 for f in prior.get('features',[]):
  p=f.get('properties') or {};l=p.get('canonical_lsoa_code');fe=p.get('field_evidence')
  if l and isinstance(fe,dict) and fe.get('official_csv_sha256')==PRIOR_MPS_SHA:ev_by[l]=copy.deepcopy(fe);tmpl_by[l]=p
 cg=json.loads(cp.read_text(encoding='utf-8-sig'));selected=[]
 for f in cg.get('features',[]):
  p=f.get('properties') or {};pid=get_pid(p);n=pid_num(pid);g=f.get('geometry') or {}
  if n is not None and START_NUM<=n<START_NUM+MAX_RECORDS and g.get('type')=='Point':
   xy=g.get('coordinates') or []
   if len(xy)>=2:selected.append((n,pid,float(xy[0]),float(xy[1]),p))
 selected.sort();base['target_record_count']=len(selected)
 q=urllib.parse.urlencode([('dataset','title-boundary'),('geometry_entity',str(LAMBETH_ENTITY)),('geometry_relation','within'),('limit',str(MAX_RECORDS)),('offset','0')])
 url=API+'?'+q
 try:st,final,b,obj=http_json(url)
 except Exception as ex:base.update(status='BLOCKED',blocker='PLANNING_DATA_GEOMETRY_ENTITY_QUERY_FAILED',error=str(ex),query_url=url);save(base);return 0
 base['source_query']={'url':final,'http_status':st,'response_sha256':hashlib.sha256(b).hexdigest(),'record_limit':MAX_RECORDS,'geometry_entity':LAMBETH_ENTITY}
 feats=[]
 if isinstance(obj,dict) and obj.get('type')=='FeatureCollection':feats=obj.get('features') or []
 elif isinstance(obj,dict) and isinstance(obj.get('features'),list):feats=obj['features']
 base['source_records_processed_count']=min(len(feats),MAX_RECORDS);feats=feats[:MAX_RECORDS]
 rows=[]
 for idx,(n,pid,x,y,p0) in enumerate(selected,1):
  lsoa=p0.get('security_lsoa_code');hits=[]
  for sf in feats:
   g=sf.get('geometry') or {};pr=sf.get('properties') or {}
   if g.get('type') in ('Polygon','MultiPolygon') and contains(g,x,y):hits.append((sf,pr))
  reasons=[];feature=None
  if len(hits)!=1:reasons.append(f'title_boundary_unique_match_required:found={len(hits)}')
  fe=ev_by.get(lsoa);tmpl=tmpl_by.get(lsoa)
  if not fe or not tmpl:reasons.append('prior_mps_field_evidence_missing_for_lsoa')
  if not reasons:
   sf,pr=hits[0];ref=str(pr.get('reference') or pr.get('entity') or sf.get('id') or '')
   if not ref:reasons.append('title_boundary_reference_missing')
   else:
    fd=copy.deepcopy(fe);fd.update({'planning_data_geometry_entity_query_sha256':base['source_query']['response_sha256'],'planning_data_title_boundary_reference':ref,'planning_data_query_url':final})
    props={'evidence_scope':'parcel','coverage_area_id':lsoa,'source_resolution':'official_MPS_LSOA_recorded_crime_joined_to_Planning_Data_HMLR_title_boundary','time_window':tmpl.get('time_window'),'source_url':tmpl.get('source_url'),'measurement_date':tmpl.get('measurement_date'),'measurement_method':tmpl.get('measurement_method'),'spatial_binding_method':'shared_canonical_point_intersects_Planning_Data_geometry_entity_title_boundary_polygon','confidence_score_0_100':100,'evidence_grade':'A','field_evidence':fd,'canonical_parcel_id':'title-boundary:'+ref,'canonical_parcel_reference':ref,'partition_record_id':pid,'canonical_lsoa_code':lsoa,'canonical_geometry_source_url':final,'canonical_geometry_provider':'Planning Data / HM Land Registry','canonical_geometry_dataset':'title-boundary','source_window_id':SOURCE_WINDOW,'cursor':f'{SOURCE_WINDOW}:record={idx}'}
    feature={'type':'Feature','id':props['canonical_parcel_id'],'geometry':sf.get('geometry'),'properties':props};reasons.extend(semantic(feature))
  rows.append({'record_index':idx,'partition_record_id':pid,'parcel_number':n,'canonical_point':{'type':'Point','coordinates':[x,y]},'canonical_lsoa_code':lsoa,'candidate_ready':bool(feature and not reasons),'reasons':reasons,'feature':feature})
 ready=sum(1 for r in rows if r['candidate_ready']);base.update(status='SEMANTIC_PRECHECK_COMPLETE',canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,candidate_ready_count=ready,rejected_count=len(rows)-ready,semantic_precheck_passed=all(not semantic(r['feature']) for r in rows if r['feature']),official_source_cursor=f'{SOURCE_WINDOW}:record={len(rows)}',rows=rows,note='Only unique local point-to-polygon matches with strict semantic fields are candidate_ready.')
 save(base);print(json.dumps({'status':base['status'],'source_records':base['source_records_processed_count'],'ready':ready,'rejected':len(rows)-ready,'output':str(OUT)}));return 0
if __name__=='__main__':raise SystemExit(main())
