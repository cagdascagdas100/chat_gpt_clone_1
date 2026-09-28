from __future__ import annotations
import csv,hashlib,io,json,os,subprocess,tempfile,urllib.request
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID='security_public_safety_5'; LINEAGE_ID='86b5e932de484ad26133fa8c'
P0,P1,PC=61524,76903,15380; START_NUM=61624; MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT',r'F:\chatgpt\chat_gpt_clone_1_main'))
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
POINT_BRANCH='codex/aays-single-runner-v5-20260706'
POINT_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
POINT_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
POLY_REL='docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
POLY_BLOB='0180223f125027d55ffea5d908b77f8df08ffe84'
CSV_URL='https://data.london.gov.uk/download/exy3m/221142dd-f7b2-4209-921e-4de833a82285/MPS%20LSOA%20Level%20Crime%20%28most%20recent%2024%20months%29.csv'
SOURCE_WINDOW='mps_lsoa_current_24m_sps5_61624_61673_v1'
REQUIRED=['evidence_scope','coverage_area_id','source_resolution','time_window','source_url','measurement_date','measurement_method','spatial_binding_method','confidence_score_0_100','evidence_grade','field_evidence','canonical_parcel_id']

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def git(args,timeout=900,stdout=None): return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
 r=git(['hash-object',str(path)],180); return r.stdout.decode('utf-8','replace').strip() if r.returncode==0 else None

def materialize_point():
 cache=Path(tempfile.gettempdir())/'aays_sps5'/Path(POINT_REL).name; cache.parent.mkdir(parents=True,exist_ok=True)
 ev={'branch':POINT_BRANCH,'repo_path':POINT_REL,'required_git_blob_sha':POINT_BLOB,'verified':False}
 if cache.is_file() and blob_sha(cache)==POINT_BLOB: ev.update(cache_hit=True,verified=True); return cache,ev
 cache.unlink(missing_ok=True)
 for ref in (f'origin/{POINT_BRANCH}',POINT_BRANCH):
  part=cache.with_suffix('.part'); part.unlink(missing_ok=True)
  with part.open('wb') as fh: r=git(['show',f'{ref}:{POINT_REL}'],stdout=fh)
  if r.returncode==0 and blob_sha(part)==POINT_BLOB: os.replace(part,cache); ev.update(source_ref=ref,verified=True); return cache,ev
  part.unlink(missing_ok=True)
 r=git(['fetch','origin',POINT_BRANCH],900)
 if r.returncode==0:
  part=cache.with_suffix('.part')
  with part.open('wb') as fh: s=git(['show',f'FETCH_HEAD:{POINT_REL}'],stdout=fh)
  if s.returncode==0 and blob_sha(part)==POINT_BLOB: os.replace(part,cache); ev.update(source_ref='FETCH_HEAD',verified=True); return cache,ev
  part.unlink(missing_ok=True)
 ev['error']='POINT_CANONICAL_BLOB_NOT_MATERIALIZED'; return None,ev

def pid_num(pid):
 try: return int(pid.split('_',1)[1]) if isinstance(pid,str) and pid.startswith('parcel_') else None
 except: return None

def get_pid(p):
 for k in ('security_parcel_id','parcel_id'):
  v=p.get(k)
  if isinstance(v,str) and v.startswith('parcel_'): return v
 return None

def point_in_ring(x,y,ring):
 inside=False; j=len(ring)-1
 for i in range(len(ring)):
  xi,yi=ring[i][0],ring[i][1]; xj,yj=ring[j][0],ring[j][1]
  if ((yi>y)!=(yj>y)):
   d=yj-yi
   if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
  j=i
 return inside

def point_in_polygon(x,y,poly):
 if not poly or not point_in_ring(x,y,poly[0]): return False
 return not any(point_in_ring(x,y,h) for h in poly[1:])

def geom_contains_point(g,x,y):
 t=g.get('type'); c=g.get('coordinates') or []
 if t=='Polygon': return point_in_polygon(x,y,c)
 if t=='MultiPolygon': return any(point_in_polygon(x,y,p) for p in c)
 return False

def download_csv():
 req=urllib.request.Request(CSV_URL,headers={'User-Agent':'AAYS-security-public-safety-5/mps-lsoa-v1','Accept':'text/csv,*/*'})
 with urllib.request.urlopen(req,timeout=180) as resp: b=resp.read(); st=int(resp.status)
 return st,b

def parse_num(v):
 try: return int(float(str(v).strip() or '0'))
 except: return 0

def save(x): OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
 base={'schema_version':4,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},'lineage_id':LINEAGE_ID,'generated_at':now(),'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED','source_window_id':SOURCE_WINDOW,'max_official_source_records':MAX_RECORDS,'accepted_count_claimed':0,'final_package_written':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
 pp,pev=materialize_point(); base['point_canonical_materialization']=pev
 if not pp: base.update(status='BLOCKED',blocker='POINT_CANONICAL_BLOB_MATERIALIZATION_FAILED',rows=[]); save(base); return 2
 poly_path=REPO/POLY_REL
 poly_actual=blob_sha(poly_path) if poly_path.is_file() else None
 base['polygon_canonical_materialization']={'repo_path':POLY_REL,'required_git_blob_sha':POLY_BLOB,'actual_git_blob_sha':poly_actual,'verified':poly_actual==POLY_BLOB}
 if poly_actual!=POLY_BLOB: base.update(status='BLOCKED',blocker='POLYGON_CANONICAL_BLOB_NOT_VERIFIED',rows=[]); save(base); return 2
 point_fc=json.loads(pp.read_text(encoding='utf-8-sig')); poly_fc=json.loads(poly_path.read_text(encoding='utf-8-sig'))
 targets=[]
 for f in point_fc.get('features',[]):
  props=f.get('properties') or {}; pid=get_pid(props); n=pid_num(pid); g=f.get('geometry') or {}
  if n is None or n<START_NUM or n>START_NUM+MAX_RECORDS-1 or g.get('type')!='Point': continue
  co=g.get('coordinates') or []
  if len(co)<2: continue
  targets.append((n,pid,float(co[0]),float(co[1]),props))
 targets.sort(); targets=targets[:MAX_RECORDS]
 try: st,body=download_csv()
 except Exception as ex: base.update(status='BLOCKED',blocker='OFFICIAL_MPS_LSOA_CSV_DOWNLOAD_FAILED',error=str(ex),rows=[]); save(base); return 2
 csv_sha=hashlib.sha256(body).hexdigest(); txt=body.decode('utf-8-sig','replace'); rdr=csv.DictReader(io.StringIO(txt)); headers=rdr.fieldnames or []
 month_cols=[h for h in headers if h and len(h)==6 and h.isdigit() and h[:4] in ('2024','2025','2026')]
 if not month_cols: base.update(status='BLOCKED',blocker='MPS_LSOA_CSV_MONTH_SCHEMA_NOT_FOUND',csv_sha256=csv_sha,csv_headers=headers,rows=[]); save(base); return 2
 lsoa={}
 for row in rdr:
  code=(row.get('LSOA Code') or row.get('LSOA code') or '').strip()
  if not code: continue
  d=lsoa.setdefault(code,{'rows':0,'monthly':{m:0 for m in month_cols},'name':(row.get('LSOA Name') or '').strip(),'borough':(row.get('Borough') or '').strip()})
  d['rows']+=1
  for m in month_cols: d['monthly'][m]+=parse_num(row.get(m))
 polys=[]; prop_keys=set()
 for i,f in enumerate(poly_fc.get('features',[])):
  g=f.get('geometry') or {}; p=f.get('properties') or {}; prop_keys.update(p.keys())
  if g.get('type') not in ('Polygon','MultiPolygon'): continue
  polys.append((i,f,p,g))
 rows=[]; invalid=0
 for idx,(n,pid,x,y,pprops) in enumerate(targets,1):
  hits=[]
  for pi,pf,pr,pg in polys:
   if geom_contains_point(pg,x,y): hits.append((pi,pf,pr,pg))
  lcode=(pprops.get('security_lsoa_code') or '').strip() if isinstance(pprops.get('security_lsoa_code'),str) else pprops.get('security_lsoa_code')
  ev=lsoa.get(str(lcode)) if lcode else None
  errs=[]; canonical_id=None; geom=None; id_source=None
  if len(hits)!=1: errs.append('CANONICAL_POLYGON_CONTAINMENT_MATCH_COUNT_'+str(len(hits)))
  else:
   _,pf,pr,pg=hits[0]; geom=pg
   if pr.get('canonical_parcel_id') not in (None,''):
    canonical_id=str(pr.get('canonical_parcel_id')); id_source='properties.canonical_parcel_id'
   else: errs.append('MISSING_CANONICAL_PARCEL_ID_EXACT_FIELD')
  if not ev: errs.append('MPS_LSOA_EXACT_IDENTIFIER_NOT_FOUND_IN_CSV')
  latest=max(month_cols); earliest=min(month_cols)
  monthly=ev['monthly'] if ev else None
  field_evidence={'lsoa_code':str(lcode) if lcode else None,'lsoa_name':ev['name'] if ev else None,'borough':ev['borough'] if ev else None,'crime_rows':ev['rows'] if ev else 0,'monthly_recorded_crime_counts':monthly,'window_total':sum(monthly.values()) if monthly else None}
  props={
   'evidence_scope':'parcel','coverage_area_id':str(lcode) if lcode else None,'source_resolution':'LSOA','time_window':f'{earliest}..{latest}','source_url':CSV_URL,
   'measurement_date':f'{latest[:4]}-{latest[4:]}-01','measurement_method':'Metropolitan Police Service recorded crime counts by LSOA and crime classification; monthly counts aggregated across CSV rows for the exact LSOA code',
   'spatial_binding_method':'canonical point-to-canonical polygon containment plus exact security_lsoa_code join to official MPS LSOA CSV','confidence_score_0_100':100 if not errs else 0,
   'evidence_grade':'official_exact_identifier_canonical_polygon' if not errs else 'rejected','field_evidence':field_evidence,'canonical_parcel_id':canonical_id,
   'canonical_id_source':id_source,'source_window_id':SOURCE_WINDOW,'cursor':f'{SOURCE_WINDOW}:record={idx}'
  }
  if geom is None or geom.get('type') not in ('Polygon','MultiPolygon'): errs.append('GEOMETRY_NOT_POLYGON_OR_MULTIPOLYGON')
  for k in REQUIRED:
   if props.get(k) in (None,''): errs.append('MISSING_REQUIRED_'+k)
  valid=not errs
  if not valid: invalid+=1
  rows.append({'record_index':idx,'source_point_parcel_id':pid,'source_point_parcel_number':n,'source_point':[x,y],'security_lsoa_code':lcode,'polygon_match_count':len(hits),'geometry':geom,'properties':props,'semantic_valid':valid,'semantic_errors':sorted(set(errs))})
 all_valid=(len(rows)==MAX_RECORDS and invalid==0)
 base.update(status='SCHEMA_PRECHECK_PASSED' if all_valid else 'SCHEMA_PRECHECK_FAILED',blocker=None if all_valid else 'PRODUCER_SCHEMA_INVALID',point_canonical_blob_sha=blob_sha(pp),point_canonical_blob_verified=blob_sha(pp)==POINT_BLOB,polygon_canonical_blob_sha=poly_actual,polygon_canonical_blob_verified=poly_actual==POLY_BLOB,polygon_feature_count=len(polys),polygon_property_keys=sorted(prop_keys),official_source={'publisher':'Metropolitan Police Service / London Datastore','url':CSV_URL,'http_status':st,'sha256':csv_sha,'time_window':f'{min(month_cols)}..{max(month_cols)}','month_columns':month_cols,'lsoa_count':len(lsoa)},source_records_processed_count=len(rows),semantic_valid_count=len(rows)-invalid,semantic_invalid_count=invalid,candidate_ready_count=len(rows)-invalid if all_valid else 0,official_source_cursor=f'{SOURCE_WINDOW}:record={len(rows)}',rows=rows,next_step='Package only if all 50 records pass semantic precheck; otherwise no incoming/layer24 commit.')
 save(base)
 print('POINT_CANONICAL_BLOB_VERIFIED='+str(base['point_canonical_blob_verified']))
 print('POLYGON_CANONICAL_BLOB_VERIFIED='+str(base['polygon_canonical_blob_verified']))
 print('POLYGON_FEATURE_COUNT='+str(len(polys)))
 print('POLYGON_PROPERTY_KEYS='+','.join(sorted(prop_keys)))
 print('MPS_CSV_SHA256='+csv_sha)
 print('MPS_TIME_WINDOW='+base['official_source']['time_window'])
 print('PROCESSED='+str(len(rows)))
 print('VALID='+str(len(rows)-invalid))
 print('INVALID='+str(invalid))
 print('OUTPUT='+str(OUT))
 return 0 if all_valid else 2
if __name__=='__main__': raise SystemExit(main())
