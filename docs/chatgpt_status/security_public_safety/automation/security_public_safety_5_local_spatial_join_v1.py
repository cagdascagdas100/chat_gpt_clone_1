from __future__ import annotations
import hashlib,json,os,subprocess,tempfile,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID='security_public_safety_5'
LINEAGE_ID='86b5e932de484ad26133fa8c'
P0,P1,PC=61524,76903,15380
MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT',r'F:\chatgpt\chat_gpt_clone_1_main'))
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
CANON_BRANCH='codex/aays-single-runner-v5-20260706'
CANON_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
CANON_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
SOURCE_WINDOW='data_police_neighbourhood_locate_boundary_sps5_partition_61524_76903_first50_v1'
LOCATE='https://data.police.uk/api/locate-neighbourhood'

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def sha256(b): return hashlib.sha256(b).hexdigest()
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

def http_json(url,attempts=3):
    last=None
    for n in range(1,attempts+1):
        req=urllib.request.Request(url,headers={'User-Agent':'AAYS-security-public-safety-5/neighbourhood-boundary-v1','Accept':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=45) as resp:
                body=resp.read(); return int(resp.status),body,json.loads(body.decode('utf-8'))
        except Exception as e:
            last=e
            if n<attempts: time.sleep(min(8,2*n))
    raise RuntimeError(str(last) if last else 'HTTP_FAILED')

def point_in_ring(x,y,ring):
    inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i]; xj,yj=ring[j]
        if ((yi>y)!=(yj>y)):
            d=yj-yi
            if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
        j=i
    return inside

def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    base={'schema_version':2,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},'lineage_id':LINEAGE_ID,'generated_at':now(),'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED','source_window_id':SOURCE_WINDOW,'max_official_source_records':MAX_RECORDS,'accepted_count_claimed':0,'final_package_written':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
    cp,mat=materialize(); base['canonical_materialization']=mat
    if not cp:
        base.update(status='BLOCKED',blocker='CANONICAL_BLOB_MATERIALIZATION_FAILED',candidate_ready_count=0,rows=[]); save(base); return 2
    cg=json.loads(cp.read_text(encoding='utf-8-sig'))
    partition=[]
    for f in cg.get('features',[]):
        if not isinstance(f,dict): continue
        props=f.get('properties') or {}; pid=get_pid(props); n=pid_num(pid)
        g=f.get('geometry') or {}
        if n is None or not P0<=n<=P1 or g.get('type')!='Point' or not isinstance(g.get('coordinates'),list) or len(g['coordinates'])<2: continue
        partition.append((n,pid,g,props))
    partition.sort(key=lambda t:t[0])
    selected=partition[:MAX_RECORDS]
    boundary_cache={}
    rows=[]
    for idx,(n,pid,g,props) in enumerate(selected,1):
        lng,lat=float(g['coordinates'][0]),float(g['coordinates'][1])
        q=urllib.parse.urlencode({'q':f'{lat:.7f},{lng:.7f}'})
        locate_url=f'{LOCATE}?{q}'
        row={'record_index':idx,'cursor':f'{SOURCE_WINDOW}:record={idx}','parcel_id':pid,'parcel_number':n,'canonical_geometry':g,'canonical_security_score':props.get('safety_score') if props.get('safety_score') is not None else props.get('security_score'),'canonical_security_level':props.get('safety_level') or props.get('security_level'),'canonical_lsoa_code':props.get('security_lsoa_code'),'locate_url':locate_url,'locate_http_status':None,'locate_response_sha256':None,'force_id':None,'neighbourhood_id':None,'boundary_url':None,'boundary_http_status':None,'boundary_response_sha256':None,'boundary_vertex_count':0,'local_point_in_boundary':False,'canonical_gate':True,'exact_identifier_gate':False,'official_boundary_gate':False,'local_spatial_join_gate':False,'field_evidence_gate':False,'candidate_ready':False,'error':None}
        try:
            st,b,obj=http_json(locate_url); row['locate_http_status']=st; row['locate_response_sha256']=sha256(b) if st==200 else None
            if st==200 and isinstance(obj,dict) and obj.get('force') and obj.get('neighbourhood'):
                force=str(obj['force']); neigh=str(obj['neighbourhood']); row['force_id']=force; row['neighbourhood_id']=neigh; row['exact_identifier_gate']=True
                key=(force,neigh)
                if key not in boundary_cache:
                    burl=f"https://data.police.uk/api/{urllib.parse.quote(force,safe='')}/{urllib.parse.quote(neigh,safe='')}/boundary"
                    try:
                        bst,bb,bo=http_json(burl)
                        coords=[]
                        if bst==200 and isinstance(bo,list):
                            for p in bo:
                                try: coords.append((float(p['longitude']),float(p['latitude'])))
                                except: pass
                        boundary_cache[key]={'url':burl,'http_status':bst,'sha256':sha256(bb) if bst==200 else None,'coords':coords,'vertex_count':len(coords),'error':None}
                    except Exception as ex:
                        boundary_cache[key]={'url':burl,'http_status':None,'sha256':None,'coords':[],'vertex_count':0,'error':str(ex)}
                    time.sleep(.15)
                be=boundary_cache[key]; row['boundary_url']=be['url']; row['boundary_http_status']=be['http_status']; row['boundary_response_sha256']=be['sha256']; row['boundary_vertex_count']=be['vertex_count']
                if be['http_status']==200 and len(be['coords'])>=3:
                    row['official_boundary_gate']=True
                    row['local_point_in_boundary']=point_in_ring(lng,lat,be['coords'])
                    row['local_spatial_join_gate']=row['local_point_in_boundary']
                    row['field_evidence_gate']=True
                if be.get('error'): row['error']=be['error']
        except Exception as ex: row['error']=str(ex)
        row['candidate_ready']=bool(row['canonical_gate'] and row['exact_identifier_gate'] and row['official_boundary_gate'] and row['local_spatial_join_gate'] and row['field_evidence_gate'])
        rows.append(row); time.sleep(.15)
    ready=sum(1 for r in rows if r['candidate_ready'])
    base.update(status='LOCAL_SPATIAL_JOIN_EXECUTED',canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,canonical_partition_feature_count=len(partition),source_records_processed_count=len(rows),unique_neighbourhood_boundary_count=len(boundary_cache),candidate_ready_count=ready,official_source_cursor=f'{SOURCE_WINDOW}:record={len(rows)}',rows=rows,next_step='Only candidate_ready rows may be packaged by the verified GitHub writer as AAYS_LAYER24_EVIDENCE_V1; no runner delivery claim.')
    save(base)
    print(f'SLOT_ID={SLOT_ID}')
    print(f'CANONICAL_BLOB_VERIFIED={base["canonical_blob_verified"]}')
    print(f'PARTITION_FEATURE_COUNT={len(partition)}')
    print(f'SOURCE_RECORDS_PROCESSED={len(rows)}')
    print(f'UNIQUE_BOUNDARIES={len(boundary_cache)}')
    print(f'CANDIDATE_READY_COUNT={ready}')
    print(f'SOURCE_WINDOW_ID={SOURCE_WINDOW}')
    print(f'OUTPUT={OUT}')
    return 0 if base['canonical_blob_verified'] and ready>0 else 2

if __name__=='__main__': raise SystemExit(main())
