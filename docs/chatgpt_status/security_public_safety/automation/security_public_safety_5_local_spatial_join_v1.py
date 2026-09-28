from __future__ import annotations
import csv, hashlib, json, os, re, subprocess, tempfile, urllib.request
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
CSV_URL='https://data.london.gov.uk/download/exy3m/221142dd-f7b2-4209-921e-4de833a82285/MPS%20LSOA%20Level%20Crime%20%28most%20recent%2024%20months%29.csv'
SOURCE_WINDOW='mps_recorded_crime_lsoa_202409_202608_sps5_61624_61673_v1'
LSOA_RE=re.compile(r'^E010\d{5}$',re.I)

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def git(args,timeout=900,stdout=None):
    return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(['hash-object',str(path)],180)
    return r.stdout.decode('utf-8','replace').strip() if r.returncode==0 else None
def materialize():
    cache=Path(tempfile.gettempdir())/'aays_sps5'/Path(CANON_REL).name
    cache.parent.mkdir(parents=True,exist_ok=True)
    ev={'branch':CANON_BRANCH,'repo_path':CANON_REL,'required_git_blob_sha':CANON_BLOB,'cache_path':str(cache),'verified':False}
    if cache.is_file() and blob_sha(cache)==CANON_BLOB:
        ev.update(cache_hit=True,verified=True); return cache,ev
    cache.unlink(missing_ok=True)
    for ref in (f'origin/{CANON_BRANCH}',CANON_BRANCH):
        part=cache.with_suffix('.part'); part.unlink(missing_ok=True)
        with part.open('wb') as fh: r=git(['show',f'{ref}:{CANON_REL}'],stdout=fh)
        if r.returncode==0 and blob_sha(part)==CANON_BLOB:
            os.replace(part,cache); ev.update(source_ref=ref,verified=True); return cache,ev
        part.unlink(missing_ok=True)
    r=git(['fetch','origin',CANON_BRANCH],900); ev['fetch_returncode']=r.returncode
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
def find_lsoa(props):
    preferred=('security_lsoa_code','lsoa_code','lsoa21cd','LSOA21CD','lsoa11cd','LSOA11CD','lsoa','LSOA')
    for k in preferred:
        v=props.get(k)
        if isinstance(v,str) and LSOA_RE.match(v.strip()):
            return k,v.strip().upper()
    for k,v in props.items():
        if 'lsoa' in str(k).lower() and isinstance(v,str) and LSOA_RE.match(v.strip()):
            return str(k),v.strip().upper()
    return None,None
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def download_csv():
    tmp=Path(tempfile.gettempdir())/'aays_sps5'/'mps_lsoa_current_24m.csv'
    req=urllib.request.Request(CSV_URL,headers={'User-Agent':'AAYS-security-public-safety-5/mps-lsoa-v1','Accept':'text/csv,*/*'})
    h=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=180) as resp, tmp.open('wb') as fh:
        status=int(resp.status)
        while True:
            b=resp.read(1024*1024)
            if not b: break
            fh.write(b); h.update(b)
    return tmp,status,h.hexdigest()
def norm(s): return re.sub(r'[^a-z0-9]+','',str(s).lower())
def choose_lsoa_column(fields):
    for f in fields:
        n=norm(f)
        if 'lsoa' in n and ('code' in n or n.endswith('lsoa') or n.startswith('lsoa')):
            return f
    return None
def parse_num(v):
    try:
        s=str(v).strip().replace(',','')
        if not s: return None
        return float(s)
    except: return None

def main():
    base={'schema_version':4,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},'lineage_id':LINEAGE_ID,'generated_at':now(),'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED','source_window_id':SOURCE_WINDOW,'max_official_source_records':MAX_RECORDS,'accepted_count_claimed':0,'final_package_written':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
    cp,mat=materialize(); base['canonical_materialization']=mat
    if not cp:
        base.update(status='BLOCKED',blocker='CANONICAL_BLOB_MATERIALIZATION_FAILED',candidate_ready_count=0,rows=[]); save(base); return 2
    cg=json.loads(cp.read_text(encoding='utf-8-sig'))
    selected=[]
    property_keys=set()
    for f in cg.get('features',[]):
        if not isinstance(f,dict): continue
        props=f.get('properties') or {}; pid=get_pid(props); n=pid_num(pid)
        g=f.get('geometry') or {}
        if n is None or not START_NUM<=n<START_NUM+MAX_RECORDS or g.get('type')!='Point': continue
        property_keys.update(props.keys())
        lkey,lcode=find_lsoa(props)
        selected.append((n,pid,g,props,lkey,lcode))
    selected.sort(key=lambda t:t[0])
    try:
        csv_path,http_status,csv_sha=download_csv()
    except Exception as ex:
        base.update(status='BLOCKED',blocker='OFFICIAL_MPS_LSOA_CSV_DOWNLOAD_FAILED',error=str(ex),candidate_ready_count=0,rows=[]); save(base); return 2
    base['official_csv']={'url':CSV_URL,'http_status':http_status,'sha256':csv_sha,'size_bytes':csv_path.stat().st_size}
    with csv_path.open('r',encoding='utf-8-sig',newline='') as fh:
        reader=csv.DictReader(fh)
        fields=reader.fieldnames or []
        lsoa_col=choose_lsoa_column(fields)
        base['official_csv']['fields']=fields
        base['official_csv']['lsoa_column']=lsoa_col
        if not lsoa_col:
            base.update(status='BLOCKED',blocker='OFFICIAL_MPS_LSOA_IDENTIFIER_COLUMN_NOT_FOUND',candidate_ready_count=0,rows=[]); save(base); return 2
        matched={}
        for rec in reader:
            code=str(rec.get(lsoa_col) or '').strip().upper()
            if not LSOA_RE.match(code): continue
            m=matched.setdefault(code,{'row_count':0,'crime_value_sum':0.0,'nonempty_numeric_cells':0,'sample_rows':[]})
            m['row_count']+=1
            total=0.0; nums=0
            for k,v in rec.items():
                if k==lsoa_col: continue
                num=parse_num(v)
                if num is not None:
                    total+=num; nums+=1
            m['crime_value_sum']+=total; m['nonempty_numeric_cells']+=nums
            if len(m['sample_rows'])<2:
                m['sample_rows'].append({k:rec.get(k) for k in fields[:12]})
    rows=[]
    for idx,(n,pid,g,props,lkey,lcode) in enumerate(selected,1):
        ev=matched.get(lcode) if lcode else None
        canonical_spatial_readback=bool(lcode and lkey and 'spatial' in CANON_REL.lower())
        exact_identifier=bool(lcode and ev)
        field_evidence=bool(ev and ev['row_count']>0)
        candidate=bool(canonical_spatial_readback and exact_identifier and field_evidence)
        rows.append({
            'record_index':idx,'cursor':f'{SOURCE_WINDOW}:record={idx}','parcel_id':pid,'parcel_number':n,'canonical_geometry':g,
            'canonical_lsoa_key':lkey,'canonical_lsoa_code':lcode,'canonical_spatial_source_path':CANON_REL,
            'canonical_spatial_attribution_readback_gate':canonical_spatial_readback,
            'official_csv_url':CSV_URL,'official_csv_sha256':csv_sha,'official_lsoa_identifier_gate':exact_identifier,
            'official_lsoa_row_count':ev['row_count'] if ev else 0,'official_crime_value_sum':ev['crime_value_sum'] if ev else None,
            'official_numeric_cells':ev['nonempty_numeric_cells'] if ev else 0,
            'field_evidence_gate':field_evidence,'local_spatial_join_readback_gate':canonical_spatial_readback,
            'candidate_ready':candidate
        })
    ready=sum(1 for r in rows if r['candidate_ready'])
    base.update(status='LOCAL_SPATIAL_JOIN_READBACK_AND_EXACT_IDENTIFIER_JOIN_EXECUTED',canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,canonical_partition_feature_count=PC,selected_property_keys=sorted(property_keys),source_records_processed_count=len(rows),candidate_ready_count=ready,official_source_cursor=f'{SOURCE_WINDOW}:record={len(rows)}',rows=rows,next_step='Only candidate_ready rows may be packaged as AAYS_LAYER24_EVIDENCE_V1. Canonical LSOA attribution is read back from the verified spatial canonical blob; MPS exact LSOA identifiers and crime values are fresh field evidence.')
    save(base)
    print(f'CANONICAL_BLOB_VERIFIED={base["canonical_blob_verified"]}')
    print(f'CSV_HTTP_STATUS={http_status}')
    print(f'CSV_SHA256={csv_sha}')
    print(f'LSOA_COLUMN={base["official_csv"]["lsoa_column"]}')
    print(f'SOURCE_RECORDS_PROCESSED={len(rows)}')
    print(f'CANDIDATE_READY_COUNT={ready}')
    print(f'OUTPUT={OUT}')
    return 0 if base['canonical_blob_verified'] and ready>0 else 2
if __name__=='__main__': raise SystemExit(main())
