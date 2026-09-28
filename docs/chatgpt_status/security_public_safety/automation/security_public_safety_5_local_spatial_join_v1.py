from __future__ import annotations
import hashlib, json, os, subprocess, tempfile, urllib.request, zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID='security_public_safety_5'
LINEAGE_ID='86b5e932de484ad26133fa8c'
P0,P1,PC=61524,76903,15380
START_NUM=61574
MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT',r'F:\chatgpt\chat_gpt_clone_1_main'))
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
CANON_BRANCH='codex/aays-single-runner-v5-20260706'
CANON_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
CANON_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
ARCHIVE_URL='https://data.police.uk/data/boundaries/2026-06.zip'
ARCHIVE_MD5='62f89304c7d1e453bec3a307e5126372'
SOURCE_WINDOW='data_police_npt_boundary_archive_2026_06_sps5_61574_61623_v1'

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

def point_in_ring(x,y,ring):
    inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i]; xj,yj=ring[j]
        if ((yi>y)!=(yj>y)):
            d=yj-yi
            if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
        j=i
    return inside
def point_in_poly(x,y,outer,holes):
    if not point_in_ring(x,y,outer): return False
    for h in holes:
        if point_in_ring(x,y,h): return False
    return True
def parse_coords(text):
    out=[]
    for tok in (text or '').replace('\n',' ').replace('\t',' ').split():
        parts=tok.split(',')
        if len(parts)>=2:
            try: out.append((float(parts[0]),float(parts[1])))
            except: pass
    return out
def localname(tag): return tag.rsplit('}',1)[-1] if '}' in tag else tag
def child_text(el,name):
    for ch in el.iter():
        if localname(ch.tag)==name and ch.text and ch.text.strip():
            return ch.text.strip()
    return None
def exact_identifier(pm):
    pid=pm.attrib.get('id')
    if pid: return pid,'kml_placemark_id'
    vals=[]
    for el in pm.iter():
        ln=localname(el.tag)
        if ln=='Data':
            key=(el.attrib.get('name') or '').strip()
            val=child_text(el,'value')
            if key and val: vals.append((key,val))
        elif ln=='SimpleData':
            key=(el.attrib.get('name') or '').strip()
            val=(el.text or '').strip()
            if key and val: vals.append((key,val))
    pref=('id','code','reference','ref','neighbourhood','neighborhood','ward')
    for p in pref:
        for k,v in vals:
            if p in k.lower(): return v,f'extended_data:{k}'
    return None,None
def polygons_from_pm(pm):
    polys=[]
    for poly in [x for x in pm.iter() if localname(x.tag)=='Polygon']:
        outer=None; holes=[]
        for ob in [x for x in poly.iter() if localname(x.tag)=='outerBoundaryIs']:
            c=child_text(ob,'coordinates'); r=parse_coords(c)
            if len(r)>=3: outer=r; break
        for ib in [x for x in poly.iter() if localname(x.tag)=='innerBoundaryIs']:
            c=child_text(ib,'coordinates'); r=parse_coords(c)
            if len(r)>=3: holes.append(r)
        if outer:
            xs=[p[0] for p in outer]; ys=[p[1] for p in outer]
            polys.append({'outer':outer,'holes':holes,'bbox':(min(xs),min(ys),max(xs),max(ys))})
    return polys

def download_archive():
    tmp=Path(tempfile.gettempdir())/'aays_sps5'/'data_police_boundaries_2026-06.zip'
    req=urllib.request.Request(ARCHIVE_URL,headers={'User-Agent':'AAYS-security-public-safety-5/archive-v1'})
    h_md5=hashlib.md5(); h_sha=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=120) as resp, tmp.open('wb') as fh:
        status=int(resp.status)
        while True:
            b=resp.read(1024*1024)
            if not b: break
            fh.write(b); h_md5.update(b); h_sha.update(b)
    return tmp,status,h_md5.hexdigest(),h_sha.hexdigest()

def main():
    base={'schema_version':3,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},'lineage_id':LINEAGE_ID,'generated_at':now(),'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED','source_window_id':SOURCE_WINDOW,'max_official_source_records':MAX_RECORDS,'accepted_count_claimed':0,'final_package_written':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
    cp,mat=materialize(); base['canonical_materialization']=mat
    if not cp:
        base.update(status='BLOCKED',blocker='CANONICAL_BLOB_MATERIALIZATION_FAILED',candidate_ready_count=0,rows=[]); save(base); return 2
    cg=json.loads(cp.read_text(encoding='utf-8-sig'))
    partition=[]
    for f in cg.get('features',[]):
        if not isinstance(f,dict): continue
        props=f.get('properties') or {}; pid=get_pid(props); n=pid_num(pid)
        g=f.get('geometry') or {}
        if n is None or not P0<=n<=P1 or n<START_NUM or g.get('type')!='Point' or not isinstance(g.get('coordinates'),list) or len(g['coordinates'])<2: continue
        partition.append((n,pid,g))
    partition.sort(key=lambda t:t[0]); selected=partition[:MAX_RECORDS]
    try:
        arc,status,md5,sha256=download_archive()
    except Exception as ex:
        base.update(status='BLOCKED',blocker='OFFICIAL_BOUNDARY_ARCHIVE_DOWNLOAD_FAILED',archive_url=ARCHIVE_URL,error=str(ex),candidate_ready_count=0,rows=[]); save(base); return 2
    base['archive']={'url':ARCHIVE_URL,'http_status':status,'expected_md5':ARCHIVE_MD5,'md5':md5,'sha256':sha256,'size_bytes':arc.stat().st_size,'md5_verified':md5.lower()==ARCHIVE_MD5}
    if status!=200 or md5.lower()!=ARCHIVE_MD5:
        base.update(status='BLOCKED',blocker='OFFICIAL_BOUNDARY_ARCHIVE_HASH_MISMATCH',candidate_ready_count=0,rows=[]); save(base); return 2
    boundaries=[]
    member_count=0
    with zipfile.ZipFile(arc) as z:
        for name in z.namelist():
            if not name.lower().endswith(('.kml','.xml')): continue
            member_count+=1
            try:
                root=ET.fromstring(z.read(name))
            except Exception:
                continue
            for pm in [x for x in root.iter() if localname(x.tag)=='Placemark']:
                ident,basis=exact_identifier(pm)
                pname=child_text(pm,'name')
                polys=polygons_from_pm(pm)
                if not polys: continue
                boundaries.append({'member':name,'identifier':ident,'identifier_basis':basis,'name':pname,'polygons':polys})
    base['archive']['parsed_kml_member_count']=member_count
    base['archive']['parsed_boundary_placemark_count']=len(boundaries)
    rows=[]
    for idx,(n,pid,g) in enumerate(selected,1):
        lng,lat=float(g['coordinates'][0]),float(g['coordinates'][1])
        hits=[]
        for b in boundaries:
            matched=False
            for poly in b['polygons']:
                x0,y0,x1,y1=poly['bbox']
                if not (x0<=lng<=x1 and y0<=lat<=y1): continue
                if point_in_poly(lng,lat,poly['outer'],poly['holes']):
                    matched=True; break
            if matched:
                hits.append({'identifier':b['identifier'],'identifier_basis':b['identifier_basis'],'name':b['name'],'member':b['member']})
        exact_hits=[h for h in hits if h['identifier']]
        distinct={(h['identifier'],h['member']) for h in exact_hits}
        unique=(len(distinct)==1)
        chosen=exact_hits[0] if unique else None
        row={'record_index':idx,'cursor':f'{SOURCE_WINDOW}:record={idx}','parcel_id':pid,'parcel_number':n,'canonical_geometry':g,'archive_url':ARCHIVE_URL,'archive_md5':md5,'archive_sha256':sha256,'boundary_hit_count':len(hits),'exact_identifier_hit_count':len(exact_hits),'boundary_identifier':chosen['identifier'] if chosen else None,'boundary_identifier_basis':chosen['identifier_basis'] if chosen else None,'boundary_name':chosen['name'] if chosen else None,'boundary_member':chosen['member'] if chosen else None,'canonical_gate':True,'official_archive_gate':True,'exact_identifier_gate':bool(chosen),'local_spatial_join_gate':bool(chosen),'field_evidence_gate':bool(chosen),'candidate_ready':bool(chosen)}
        rows.append(row)
    ready=sum(1 for r in rows if r['candidate_ready'])
    base.update(status='LOCAL_SPATIAL_JOIN_EXECUTED',canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,canonical_partition_feature_count=PC,source_records_processed_count=len(rows),candidate_ready_count=ready,official_source_cursor=f'{SOURCE_WINDOW}:record={len(rows)}',rows=rows,next_step='Only candidate_ready rows may be packaged as AAYS_LAYER24_EVIDENCE_V1.')
    save(base)
    print(f'CANONICAL_BLOB_VERIFIED={base["canonical_blob_verified"]}')
    print(f'ARCHIVE_MD5_VERIFIED={base["archive"]["md5_verified"]}')
    print(f'ARCHIVE_SHA256={sha256}')
    print(f'BOUNDARY_PLACEMARKS={len(boundaries)}')
    print(f'SOURCE_RECORDS_PROCESSED={len(rows)}')
    print(f'CANDIDATE_READY_COUNT={ready}')
    print(f'OUTPUT={OUT}')
    return 0 if base['canonical_blob_verified'] and ready>0 else 2
if __name__=='__main__': raise SystemExit(main())
