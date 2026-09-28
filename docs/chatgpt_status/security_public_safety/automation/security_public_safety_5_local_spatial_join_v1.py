from __future__ import annotations
import hashlib,json,os,re,subprocess,tempfile,urllib.parse,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
SLOT='security_public_safety_5';LIN='86b5e932de484ad26133fa8c'
TARGETS=['parcel_61637','parcel_61648','parcel_61649','parcel_61669','parcel_61672']
REPO=Path(os.environ.get('AAYS_REPO_ROOT') or Path(__file__).resolve().parents[4])
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
CANON_BRANCH='codex/aays-single-runner-v5-20260706';CANON_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson';CANON_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
PREV=REPO/'incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/planning_data_title_boundary_mps_lsoa_61624_61673_20260928T221705Z'
PREV_ZIP=PREV/'AAYS_LAYER24__security_public_safety_5__86b5e932de484ad26133fa8c__planning_data_title_boundary_mps_lsoa_61624_61673__20260928T221705Z.zip';PREV_SHA='6400ab1c73712e16c53d86c2f503c710a396190704dbf94962890ee950eb70bd'
PRIOR=REPO/'incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/mps_lsoa_recorded_crime_202108_202307_61624_61673_20260928T085212Z/records.geojson'
API='https://www.planning.data.gov.uk/entity.geojson';WIN='planning_data_title_boundary_custom_area_sps5_rejected5_v1'
REQ=['evidence_scope','coverage_area_id','source_resolution','time_window','source_url','measurement_date','measurement_method','spatial_binding_method','confidence_score_0_100','evidence_grade','field_evidence','canonical_parcel_id'];FORBID=['parcel_id','accepted_parcel']
def git(a,timeout=900,stdout=None):return subprocess.run(['git','-C',str(REPO),*a],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False)
def blob(p):r=git(['hash-object',str(p)],180);return r.stdout.decode().strip() if r.returncode==0 else None
def shafile(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rehash():
 o={'expected_sha256':PREV_SHA,'exists':PREV_ZIP.is_file(),'verified':False}
 if not PREV_ZIP.is_file():return o
 o['sha256']=shafile(PREV_ZIP);o['size_bytes']=PREV_ZIP.stat().st_size;good=0;bad=[]
 try:
  with zipfile.ZipFile(PREV_ZIP) as z:
   names=z.namelist();o['member_count']=len(names)
   for s in [x for x in names if x.endswith('.sha256')]:
    m=re.match(r'^([0-9a-fA-F]{64})\s+\*?(.+)$',z.read(s).decode().strip())
    if not m:bad.append([s,'format']);continue
    exp,t=m.groups();d=os.path.dirname(s);t=(d+'/'+t) if d and '/' not in t else t
    if t not in names:bad.append([s,'missing']);continue
    if hashlib.sha256(z.read(t)).hexdigest().lower()==exp.lower():good+=1
    else:bad.append([s,'hash'])
 except Exception as e:o['error']=str(e);return o
 o.update(sidecar_good_count=good,sidecar_bad=bad,verified=(o['sha256']==PREV_SHA and good==7 and not bad and o['member_count']>=14));return o
def materialize():
 c=Path(tempfile.gettempdir())/'aays_sps5'/Path(CANON_REL).name;c.parent.mkdir(parents=True,exist_ok=True)
 if c.is_file() and blob(c)==CANON_BLOB:return c,{'verified':True,'cache_hit':True}
 c.unlink(missing_ok=True)
 for ref in (f'origin/{CANON_BRANCH}',CANON_BRANCH):
  p=c.with_suffix('.part');p.unlink(missing_ok=True)
  with p.open('wb') as fh:r=git(['show',f'{ref}:{CANON_REL}'],stdout=fh)
  if r.returncode==0 and blob(p)==CANON_BLOB:os.replace(p,c);return c,{'verified':True,'source_ref':ref}
  p.unlink(missing_ok=True)
 r=git(['fetch','origin',CANON_BRANCH],900)
 if r.returncode==0:
  p=c.with_suffix('.part')
  with p.open('wb') as fh:s=git(['show',f'FETCH_HEAD:{CANON_REL}'],stdout=fh)
  if s.returncode==0 and blob(p)==CANON_BLOB:os.replace(p,c);return c,{'verified':True,'source_ref':'FETCH_HEAD'}
  p.unlink(missing_ok=True)
 return None,{'verified':False,'error':'CANONICAL_BLOB_NOT_MATERIALIZED'}
def httpj(url):
 req=urllib.request.Request(url,headers={'User-Agent':'AAYS-SPS5/custom-area-v1','Accept':'application/geo+json,application/json'})
 with urllib.request.urlopen(req,timeout=60) as r:
  b=r.read();return int(r.status),b,json.loads(b.decode())
def pir(x,y,r):
 inside=False;j=len(r)-1
 for i in range(len(r)):
  xi,yi=r[i][:2];xj,yj=r[j][:2]
  if (yi>y)!=(yj>y):
   d=yj-yi
   if d and x<(xj-xi)*(y-yi)/d+xi:inside=not inside
  j=i
 return inside
def contains(x,y,g):
 if not g:return False
 c=g.get('coordinates') or [];ps=[c] if g.get('type')=='Polygon' else c if g.get('type')=='MultiPolygon' else []
 return any(p and pir(x,y,p[0]) and not any(pir(x,y,h) for h in p[1:]) for p in ps)
def valid(f):
 p=f.get('properties') or {};r=[]
 if (f.get('geometry') or {}).get('type') not in ('Polygon','MultiPolygon'):r.append('geometry_not_polygon')
 if p.get('evidence_scope')!='parcel':r.append('evidence_scope_not_parcel')
 for k in REQ:
  if k not in p or p[k] in (None,'') or (k=='field_evidence' and not isinstance(p[k],dict)):r.append('missing_'+k)
 for k in FORBID:
  if k in p:r.append('forbidden_'+k)
 c=p.get('confidence_score_0_100')
 if isinstance(c,bool) or not isinstance(c,(int,float)) or not 0<=c<=100:r.append('confidence_out_of_range')
 return r
def save(x):OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 o={'schema_version':7,'slot_id':SLOT,'owner':None,'partition':[61524,76903],'lineage_id':LIN,'source_window_id':WIN,'accepted_count_claimed':0,'final_package_written':False,'fake_data':False}
 rh=rehash();o['previous_package_physical_rehash']=rh
 if not rh.get('verified'):o.update(status='BLOCKED',blocker='PREVIOUS_PACKAGE_PHYSICAL_REHASH_FAILED',first_missing_criterion='CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED',rows=[]);save(o);return 2
 cp,cm=materialize();o['canonical_materialization']=cm
 if not cp:o.update(status='BLOCKED',blocker='CANONICAL_BLOB_MATERIALIZATION_FAILED',first_missing_criterion='CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED',rows=[]);save(o);return 2
 cg=json.loads(cp.read_text(encoding='utf-8-sig'));pts={}
 for f in cg.get('features',[]):
  p=f.get('properties') or {};pid=p.get('security_parcel_id') or p.get('parcel_id')
  if pid in TARGETS and (f.get('geometry') or {}).get('type')=='Point':pts[pid]=f['geometry']['coordinates'][:2]
 if len(pts)!=5:o.update(status='BLOCKED',blocker='TARGET_POINTS_MISSING',first_missing_criterion='CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED',points=pts,rows=[]);save(o);return 2
 fld={}
 if PRIOR.is_file():
  pg=json.loads(PRIOR.read_text(encoding='utf-8-sig'))
  for f in pg.get('features',[]):
   p=f.get('properties') or {};pid=p.get('parcel_id')
   if pid in TARGETS and p.get('official_lsoa_identifier_evidence') and p.get('field_evidence_gate'):fld[pid]=p
 rows=[];propsed=[];errors=0;eps=.000015
 for i,pid in enumerate(TARGETS,1):
  lon,lat=map(float,pts[pid]);w=f'POLYGON(({lon-eps:.7f} {lat-eps:.7f},{lon+eps:.7f} {lat-eps:.7f},{lon+eps:.7f} {lat+eps:.7f},{lon-eps:.7f} {lat+eps:.7f},{lon-eps:.7f} {lat-eps:.7f}))'
  q=urllib.parse.urlencode([('dataset','title-boundary'),('geometry',w),('geometry_relation','intersects'),('limit','20')]);url=API+'?'+q;reasons=[];cs=[];hs=None;st=None
  try:
   st,b,x=httpj(url);hs=hashlib.sha256(b).hexdigest()
   for f in x.get('features',[]) if isinstance(x,dict) else []:
    p=f.get('properties') or {};ref=p.get('reference');g=f.get('geometry')
    if ref and g and g.get('type') in ('Polygon','MultiPolygon') and contains(lon,lat,g):cs.append({'ref':str(ref),'ent':p.get('entity'),'q':p.get('quality'),'g':g})
  except Exception as e:reasons.append('custom_area_api_error:'+str(e));errors+=1
  u={c['ref']:c for c in cs};sel=next(iter(u.values())) if len(u)==1 else None
  if len(u)!=1:reasons.append('unique_point_polygon_required:found='+str(len(u)))
  fp=fld.get(pid)
  if not fp:reasons.append('security_field_evidence_required')
  feat=None;vr=[]
  if sel and fp:
   lsoa=fp.get('canonical_lsoa_code');fe={'security_source':fp.get('official_source'),'official_csv_url':fp.get('official_csv_url'),'official_csv_sha256':fp.get('official_csv_sha256'),'lsoa_code':lsoa,'official_lsoa_row_count':fp.get('official_lsoa_row_count'),'official_crime_value_sum':fp.get('official_crime_value_sum'),'official_numeric_cells':fp.get('official_numeric_cells'),'planning_data_custom_area_query_url':url,'planning_data_response_sha256':hs,'planning_data_reference':sel['ref'],'planning_data_entity':sel['ent'],'planning_data_quality':sel['q']}
   pp={'evidence_scope':'parcel','coverage_area_id':lsoa,'source_resolution':'official_MPS_LSOA_recorded_crime_joined_to_HMLR_title_boundary_polygon_custom_area','time_window':'MPS_most_recent_24_months_as_hashed_2026-09-28','source_url':fp.get('official_csv_url'),'measurement_date':'2026-09-28','measurement_method':'official_MPS_LSOA_CSV_exact_identifier_join','spatial_binding_method':'canonical_partition_point_intersects_Planning_Data_custom_area_title_boundary_polygon','confidence_score_0_100':100,'evidence_grade':'A','field_evidence':fe,'canonical_parcel_id':'title-boundary:'+sel['ref'],'canonical_parcel_reference':sel['ref'],'canonical_parcel_entity':sel['ent'],'partition_record_id':pid,'canonical_lsoa_code':lsoa,'canonical_geometry_source_url':url,'canonical_geometry_provider':'HM Land Registry via Planning Data','canonical_geometry_dataset':'title-boundary','canonical_geometry_response_sha256':hs,'source_window_id':WIN,'cursor':f'{WIN}:record={i}'}
   feat={'type':'Feature','id':'title-boundary:'+sel['ref'],'geometry':sel['g'],'properties':pp};vr=valid(feat)
   if vr:reasons += ['semantic_precheck:'+z for z in vr]
   else:propsed.append(feat)
  rows.append({'record_index':i,'partition_record_id':pid,'canonical_point':{'type':'Point','coordinates':[lon,lat]},'query_url':url,'response_http_status':st,'response_sha256':hs,'point_containing_unique_reference_count':len(u),'candidate_references':sorted(u),'selected_reference':sel['ref'] if sel else None,'security_field_evidence_reused':fp is not None,'candidate_ready':feat is not None and not vr,'reasons':reasons,'cursor':f'{WIN}:record={i}'})
 inv=[{'id':f.get('id'),'reasons':valid(f)} for f in propsed if valid(f)]
 unresolved=[r for r in rows if not r['selected_reference']];fm=[r for r in rows if r['selected_reference'] and not r['security_field_evidence_reused']]
 nxt='CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED' if unresolved else ('SECURITY_FIELD_EVIDENCE_REQUIRED' if fm else 'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED')
 o.update(status='CUSTOM_AREA_CANONICAL_RESOLUTION_EXECUTED',canonical_blob_sha=blob(cp),canonical_blob_verified=blob(cp)==CANON_BLOB,processed_count=5,candidate_ready_count=len(propsed),api_error_count=errors,semantic_precheck_invalid_count=len(inv),semantic_precheck_invalid=inv,proposed_records={'type':'FeatureCollection','features':propsed},rows=rows,official_source_cursor=f'{WIN}:record=5',first_missing_criterion=nxt)
 save(o);print('PREVIOUS_PACKAGE_REHASH='+str(rh['verified']));print('CANDIDATE_READY='+str(len(propsed)));print('FIRST_MISSING='+nxt);print('OUTPUT='+str(OUT));return 0 if not inv and errors==0 else 2
if __name__=='__main__':raise SystemExit(main())
