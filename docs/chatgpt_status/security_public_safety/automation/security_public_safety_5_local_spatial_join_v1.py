from __future__ import annotations
import csv, hashlib, io, json, os, subprocess, tempfile, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID='security_public_safety_5'
LINEAGE_ID='86b5e932de484ad26133fa8c'
P0,P1,PC=61524,76903,15380
START_NUM=61624
MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT',r'F:\chatgpt\chat_gpt_clone_1_main'))
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
CANON_BRANCH='codex/aays-single-runner-v5-20260706'
CANON_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
CANON_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
WARD_POLY_REL='incoming/source_area/security_public_safety_5/86b5e932de484ad26133fa8c/planning_data_barnet_ward_polygons_20260927T204546Z/records.geojson'
CSV_URL='https://data.london.gov.uk/download/exy3m/s8b/MPS%20Ward%20Level%20Crime%20%28most%20recent%2024%20months%29.csv'
SOURCE_WINDOW='mps_ward_level_crime_current24m_barnet3_first50_20260925_v1'
WARD_CODES={'E05013628','E05013629','E05013644'}

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def git(args,timeout=900,stdout=None):
    return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(['hash-object',str(path)],180)
    return r.stdout.decode('utf-8','replace').strip() if r.returncode==0 else None
def materialize():
    cache=Path(tempfile.gettempdir())/'aays_sps5'/Path(CANON_REL).name
    cache.parent.mkdir(parents=True,exist_ok=True)
    ev={'branch':CANON_BRANCH,'repo_path':CANON_REL,'required_git_blob_sha':CANON_BLOB,'cache_path':str(cache),'verified':False,'fetch_attempted':False}
    if cache.is_file() and blob_sha(cache)==CANON_BLOB:
        ev.update(cache_hit=True,verified=True); return cache,ev
    cache.unlink(missing_ok=True)
    for ref in (f'origin/{CANON_BRANCH}',CANON_BRANCH):
        part=cache.with_suffix('.part'); part.unlink(missing_ok=True)
        with part.open('wb') as fh: r=git(['show',f'{ref}:{CANON_REL}'],stdout=fh)
        ev.setdefault('attempts',[]).append({'ref':ref,'returncode':r.returncode,'stderr':r.stderr.decode('utf-8','replace')[-1000:]})
        if r.returncode==0 and blob_sha(part)==CANON_BLOB:
            os.replace(part,cache); ev.update(source_ref=ref,verified=True); return cache,ev
        part.unlink(missing_ok=True)
    ev['fetch_attempted']=True
    r=git(['fetch','origin',CANON_BRANCH],900); ev['fetch_returncode']=r.returncode; ev['fetch_stderr']=r.stderr.decode('utf-8','replace')[-2000:]
    if r.returncode==0:
        part=cache.with_suffix('.part')
        with part.open('wb') as fh: s=git(['show',f'FETCH_HEAD:{CANON_REL}'],stdout=fh)
        if s.returncode==0 and blob_sha(part)==CANON_BLOB:
            os.replace(part,cache); ev.update(source_ref='FETCH_HEAD',verified=True); return cache,ev
        part.unlink(missing_ok=True)
    ev['error']='EXACT_CANONICAL_BLOB_NOT_MATERIALIZED'; return None,ev
def pid_num(pid):
    try: return int(pid.split('_',1)[1]) if isinstance(pid,str) and pid.startswith('parcel_') else None
    except: return None
def get_pid(props):
    for k in ('security_parcel_id','parcel_id'):
        v=props.get(k)
        if isinstance(v,str) and v.startswith('parcel_'): return v
    return None
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def download_csv():
    req=urllib.request.Request(CSV_URL,headers={'User-Agent':'AAYS-security-public-safety-5/mps-ward-crime-v1','Accept':'text/csv,*/*'})
    with urllib.request.urlopen(req,timeout=120) as resp:
        body=resp.read()
        return int(resp.status),body,resp.headers.get('Content-Type')

def main():
    base={
      'schema_version':4,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},
      'lineage_id':LINEAGE_ID,'generated_at':now(),
      'source_window_id':SOURCE_WINDOW,'max_official_source_records':MAX_RECORDS,
      'accepted_count_claimed':0,'final_package_written':False,'fake_data':False,
      'db_write':False,'migration':False,'production_deploy':False
    }
    cp,mat=materialize(); base['canonical_materialization']=mat
    if not cp:
        base.update(status='BLOCKED',blocker='CANONICAL_BLOB_MATERIALIZATION_FAILED',first_missing_criterion='CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED',rows=[]); save(base); return 2
    canon=json.loads(cp.read_text(encoding='utf-8-sig'))
    parcel_rows=[]
    for f in canon.get('features',[]):
        if not isinstance(f,dict): continue
        props=f.get('properties') or {}; pid=get_pid(props); n=pid_num(pid)
        if n is None or not START_NUM<=n<START_NUM+MAX_RECORDS: continue
        geom=f.get('geometry') or {}; reasons=[]
        if geom.get('type') not in ('Polygon','MultiPolygon'):
            reasons.append('geometry_type_must_be_Polygon_or_MultiPolygon_got_'+str(geom.get('type')))
        if not props.get('canonical_parcel_id'):
            reasons.append('missing_required_canonical_parcel_id')
        if props.get('accepted_parcel') is True:
            reasons.append('accepted_parcel_label_does_not_satisfy_schema')
        parcel_rows.append({
          'parcel_number':n,'source_parcel_alias':pid,'canonical_parcel_id':props.get('canonical_parcel_id'),
          'geometry_type':geom.get('type'),'schema_valid':not reasons,'rejection_reasons':reasons
        })
    parcel_rows.sort(key=lambda x:x['parcel_number'])
    if len(parcel_rows)>MAX_RECORDS: parcel_rows=parcel_rows[:MAX_RECORDS]

    poly_path=REPO/WARD_POLY_REL
    poly=json.loads(poly_path.read_text(encoding='utf-8'))
    ward_poly={}
    for f in poly.get('features',[]):
        code=str(f.get('id') or (f.get('properties') or {}).get('coverage_area_id') or '')
        if code in WARD_CODES and (f.get('geometry') or {}).get('type') in ('Polygon','MultiPolygon'):
            ward_poly[code]=f.get('geometry')

    try:
        status,body,ctype=download_csv()
    except Exception as ex:
        base.update(status='BLOCKED',blocker='OFFICIAL_MPS_WARD_CSV_DOWNLOAD_FAILED',first_missing_criterion='CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED',error=str(ex),parcel_schema_precheck=parcel_rows); save(base); return 2
    sha=hashlib.sha256(body).hexdigest()
    text=body.decode('utf-8-sig',errors='strict')
    reader=csv.DictReader(io.StringIO(text))
    fieldnames=reader.fieldnames or []
    matched=[]
    for rownum,row in enumerate(reader, start=2):
        code=(row.get('WardCode') or '').strip()
        if code not in WARD_CODES: continue
        geom=ward_poly.get(code)
        reasons=[]
        if not geom or geom.get('type') not in ('Polygon','MultiPolygon'): reasons.append('missing_or_invalid_verified_ward_polygon')
        if not code: reasons.append('missing_coverage_area_id')
        required_meta={
          'evidence_scope':'coverage_area','coverage_area_id':code,'source_resolution':'ward',
          'time_window':'2024-06..2026-05','source_url':CSV_URL,'measurement_date':'2026-05',
          'measurement_method':'MPS recorded crime monthly count by WardCode',
          'spatial_binding_method':'exact WardCode -> verified official ward polygon',
          'confidence_score_0_100':95,'evidence_grade':'A','field_evidence':{
            'group':row.get('Group'),'subgroup':row.get('SubGroup'),'ward_name':row.get('WardName'),
            'ward_code':code,'borough':row.get('LookUp_BoroughName'),
            'monthly_counts':{k:row.get(k) for k in fieldnames if k and k.isdigit() and len(k)==6}
          }
        }
        matched.append({
          'csv_row_number':rownum,'ward_code':code,'ward_name':row.get('WardName'),
          'geometry':geom,'properties':required_meta,'source_schema_valid':not reasons,'source_rejection_reasons':reasons
        })
        if len(matched)>=MAX_RECORDS: break

    source_invalid=sum(1 for x in matched if not x['source_schema_valid'])
    parcel_invalid=sum(1 for x in parcel_rows if not x['schema_valid'])
    base.update(
      status='PRODUCER_SCHEMA_INVALID' if parcel_invalid else 'SOURCE_WINDOW_PROCESSED',
      blocker='PRODUCER_SCHEMA_INVALID' if parcel_invalid else None,
      first_missing_criterion='CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED' if parcel_invalid else 'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED',
      canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,
      parcel_schema_precheck=parcel_rows,parcel_schema_checked_count=len(parcel_rows),parcel_schema_invalid_count=parcel_invalid,
      official_source={
        'publisher':'Metropolitan Police Service / Greater London Authority',
        'dataset':'MPS Recorded Crime: Geographic Breakdown - Ward Level current 24 months',
        'url':CSV_URL,'http_status':status,'content_type':ctype,'sha256':sha,'size_bytes':len(body),
        'columns':fieldnames,'time_window':'2024-06..2026-05','updated_catalog_date':'2026-09-25'
      },
      source_records_processed_count=len(matched),source_schema_invalid_count=source_invalid,
      source_records=matched,
      official_source_cursor=f'{SOURCE_WINDOW}:record={len(matched)}',
      rejection_ledger=[{
        'record_kind':'parcel_candidate','source_parcel_alias':r['source_parcel_alias'],'parcel_number':r['parcel_number'],
        'reasons':r['rejection_reasons']
      } for r in parcel_rows if not r['schema_valid']],
      accepted_count_claimed=0,source_area_count_claimed=0,
      next_step='Do not commit parcel package. Obtain Polygon/MultiPolygon canonical parcel geometry with canonical_parcel_id before any Layer24 acceptance.'
    )
    save(base)
    print(f'CSV_SHA256={sha}')
    print(f'SOURCE_RECORDS_PROCESSED={len(matched)}')
    print(f'PARCEL_SCHEMA_CHECKED={len(parcel_rows)}')
    print(f'PARCEL_SCHEMA_INVALID={parcel_invalid}')
    print(f'FIRST_MISSING={base["first_missing_criterion"]}')
    print(f'OUTPUT={OUT}')
    return 2 if parcel_invalid or source_invalid else 0
if __name__=='__main__': raise SystemExit(main())
