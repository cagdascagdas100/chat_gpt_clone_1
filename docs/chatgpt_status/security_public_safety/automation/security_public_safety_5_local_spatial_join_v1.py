from __future__ import annotations
import hashlib,json,os,subprocess,tempfile,urllib.request,zipfile
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID='security_public_safety_5'
LINEAGE_ID='86b5e932de484ad26133fa8c'
P0,P1,PC=61524,76903,15380
START_NUM=61624
MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT',r'F:\chatgpt\chat_gpt_clone_1_main'))
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
POINT_BRANCH='codex/aays-single-runner-v5-20260706'
POINT_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
POINT_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
POLY_REL='docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
POLY_BLOB='0180223f125027d55ffea5d908b77f8df08ffe84'
ARCHIVE_URL='https://data.police.uk/data/boundaries/2026-05.zip'
ARCHIVE_MD5='a39d88624434ff668270b82f33fb77d3'
SOURCE_WINDOW='data_police_npt_boundary_archive_2026_05_sps5_61624_61673_polygon_schema_v1'
REQUIRED_FIELDS=['evidence_scope','coverage_area_id','source_resolution','time_window','source_url','measurement_date','measurement_method','spatial_binding_method','confidence_score_0_100','evidence_grade','field_evidence','canonical_parcel_id']

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def git(args,timeout=900,stdout=None):
    return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(['hash-object',str(path)],180)
    return r.stdout.decode('utf-8','replace').strip() if r.returncode==0 else None
def materialize_point():
    cache=Path(tempfile.gettempdir())/'aays_sps5'/Path(POINT_REL).name
    cache.parent.mkdir(parents=True,exist_ok=True)
    ev={'branch':POINT_BRANCH,'repo_path':POINT_REL,'required_git_blob_sha':POINT_BLOB,'cache_path':str(cache),'verified':False}
    if cache.is_file() and blob_sha(cache)==POINT_BLOB:
        ev.update(cache_hit=True,verified=True); return cache,ev
    cache.unlink(missing_ok=True)
    for ref in (f'origin/{POINT_BRANCH}',POINT_BRANCH):
        part=cache.with_suffix('.part'); part.unlink(missing_ok=True)
        with part.open('wb') as fh: r=git(['show',f'{ref}:{POINT_REL}'],stdout=fh)
        if r.returncode==0 and blob_sha(part)==POINT_BLOB:
            os.replace(part,cache); ev.update(source_ref=ref,verified=True); return cache,ev
        part.unlink(missing_ok=True)
    r=git(['fetch','origin',POINT_BRANCH],900); ev['fetch_returncode']=r.returncode
    if r.returncode==0:
        part=cache.with_suffix('.part')
        with part.open('wb') as fh: s=git(['show',f'FETCH_HEAD:{POINT_REL}'],stdout=fh)
        if s.returncode==0 and blob_sha(part)==POINT_BLOB:
            os.replace(part,cache); ev.update(source_ref='FETCH_HEAD',verified=True); return cache,ev
        part.unlink(missing_ok=True)
    ev['error']='EXACT_POINT_CANONICAL_BLOB_NOT_MATERIALIZED'; return None,ev

def pid_num(pid):
    try: return int(pid.split('_',1)[1]) if isinstance(pid,str) and pid.startswith('parcel_') else None
    except: return None
def get_pid(props):
    for k in ('security_parcel_id','parcel_id'):
        v=props.get(k)
        if isinstance(v,str) and v.startswith('parcel_'): return v
    return None
def localname(tag): return tag.rsplit('}',1)[-1] if '}' in tag else tag
def child_text(el,name):
    for ch in el.iter():
        if localname(ch.tag)==name and ch.text and ch.text.strip(): return ch.text.strip()
    return None
def parse_coords(text):
    out=[]
    for tok in (text or '').replace('\n',' ').replace('\t',' ').split():
        p=tok.split(',')
        if len(p)>=2:
            try: out.append((float(p[0]),float(p[1])))
            except: pass
    return out
def exact_identifier(pm):
    pid=pm.attrib.get('id')
    if pid: return pid,'kml_placemark_id'
    for el in pm.iter():
        if localname(el.tag) in ('Data','SimpleData'):
            key=(el.attrib.get('name') or '').strip()
            val=child_text(el,'value') if localname(el.tag)=='Data' else (el.text or '').strip()
            if key and val and any(t in key.lower() for t in ('id','code','reference','ref','neighbourhood','neighborhood','ward')):
                return val,f'extended_data:{key}'
    return None,None
def point_in_ring(x,y,ring):
    inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i]; xj,yj=ring[j]
        if ((yi>y)!=(yj>y)):
            d=yj-yi
            if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
        j=i
    return inside
def point_in_polygon(x,y,poly):
    if not poly or not point_in_ring(x,y,poly[0]): return False
    for hole in poly[1:]:
        if point_in_ring(x,y,hole): return False
    return True
def point_in_geojson(x,y,g):
    if not isinstance(g,dict): return False
    t=g.get('type'); c=g.get('coordinates') or []
    if t=='Polygon': return point_in_polygon(x,y,c)
    if t=='MultiPolygon': return any(point_in_polygon(x,y,p) for p in c)
    return False
def polygon_bbox(g):
    xs=[];ys=[]
    def walk(v):
        if isinstance(v,list) and len(v)>=2 and isinstance(v[0],(int,float)) and isinstance(v[1],(int,float)):
            xs.append(float(v[0]));ys.append(float(v[1]));return
        if isinstance(v,list):
            for z in v: walk(z)
    walk((g or {}).get('coordinates'))
    return (min(xs),min(ys),max(xs),max(ys)) if xs else None
def stable_poly_id(f):
    props=f.get('properties') or {}
    keys=('canonical_parcel_id','title_number','title_no','title','inspire_id','INSPIREID','inspireID','reference','ref')
    for k in keys:
        v=props.get(k)
        if v not in (None,''): return str(v),f'properties.{k}'
    fid=f.get('id')
    if fid not in (None,''): return str(fid),'feature.id'
    return None,None
def download_archive():
    p=Path(tempfile.gettempdir())/'aays_sps5'/'data_police_boundaries_2026-05.zip'
    req=urllib.request.Request(ARCHIVE_URL,headers={'User-Agent':'AAYS-security-public-safety-5/schema-v4'})
    md5=hashlib.md5();sha=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=120) as resp,p.open('wb') as fh:
        st=int(resp.status)
        while True:
            b=resp.read(1024*1024)
            if not b: break
            fh.write(b);md5.update(b);sha.update(b)
    return p,st,md5.hexdigest(),sha.hexdigest()
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    base={'schema_version':4,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},'lineage_id':LINEAGE_ID,
          'generated_at':now(),'source_window_id':SOURCE_WINDOW,'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED',
          'max_official_source_records':MAX_RECORDS,'accepted_count_claimed':0,'final_package_written':False,'fake_data':False}
    point_path,mat=materialize_point();base['point_canonical_materialization']=mat
    poly_path=REPO/POLY_REL
    base['polygon_canonical']={'repo_path':POLY_REL,'required_git_blob_sha':POLY_BLOB,'present':poly_path.is_file(),'actual_git_blob_sha':blob_sha(poly_path) if poly_path.is_file() else None}
    if not point_path or not poly_path.is_file() or blob_sha(poly_path)!=POLY_BLOB:
        base.update(status='BLOCKED',blocker='CANONICAL_POLYGON_SOURCE_UNAVAILABLE_OR_HASH_MISMATCH',rows=[]);save(base);return 2
    points=json.loads(point_path.read_text(encoding='utf-8-sig'))
    polyfc=json.loads(poly_path.read_text(encoding='utf-8-sig'))
    poly_features=[f for f in polyfc.get('features',[]) if (f.get('geometry') or {}).get('type') in ('Polygon','MultiPolygon')]
    poly_index=[]
    keys=set()
    for f in poly_features:
        keys.update((f.get('properties') or {}).keys())
        b=polygon_bbox(f.get('geometry'))
        if b: poly_index.append((b,f))
    base['polygon_canonical'].update(feature_count=len(poly_features),property_keys=sorted(keys),feature_id_count=sum(1 for f in poly_features if f.get('id') not in (None,'')))
    selected=[]
    for f in points.get('features',[]):
        props=f.get('properties') or {};pid=get_pid(props);n=pid_num(pid);g=f.get('geometry') or {}
        if n is None or n<START_NUM or n>START_NUM+MAX_RECORDS-1 or g.get('type')!='Point': continue
        selected.append((n,pid,float(g['coordinates'][0]),float(g['coordinates'][1])))
    selected.sort()
    try: arc,st,md5,sha=download_archive()
    except Exception as ex:
        base.update(status='BLOCKED',blocker='OFFICIAL_BOUNDARY_ARCHIVE_DOWNLOAD_FAILED',error=str(ex),rows=[]);save(base);return 2
    base['archive']={'url':ARCHIVE_URL,'http_status':st,'expected_md5':ARCHIVE_MD5,'md5':md5,'sha256':sha,'size_bytes':arc.stat().st_size,'md5_verified':md5.lower()==ARCHIVE_MD5}
    if st!=200 or md5.lower()!=ARCHIVE_MD5:
        base.update(status='BLOCKED',blocker='OFFICIAL_BOUNDARY_ARCHIVE_HASH_MISMATCH',rows=[]);save(base);return 2
    boundaries=[]
    with zipfile.ZipFile(arc) as z:
        for name in z.namelist():
            if not name.lower().endswith(('.kml','.xml')): continue
            try: root=ET.fromstring(z.read(name))
            except: continue
            for pm in [x for x in root.iter() if localname(x.tag)=='Placemark']:
                ident,basis=exact_identifier(pm);pname=child_text(pm,'name')
                for pel in [x for x in pm.iter() if localname(x.tag)=='Polygon']:
                    outer=None;holes=[]
                    for ob in [x for x in pel.iter() if localname(x.tag)=='outerBoundaryIs']:
                        r=parse_coords(child_text(ob,'coordinates'))
                        if len(r)>=3: outer=r;break
                    for ib in [x for x in pel.iter() if localname(x.tag)=='innerBoundaryIs']:
                        r=parse_coords(child_text(ib,'coordinates'))
                        if len(r)>=3: holes.append(r)
                    if outer:
                        xs=[p[0] for p in outer];ys=[p[1] for p in outer]
                        boundaries.append({'identifier':ident,'identifier_basis':basis,'name':pname,'member':name,'poly':[outer,*holes],'bbox':(min(xs),min(ys),max(xs),max(ys))})
    base['archive']['parsed_boundary_polygon_count']=len(boundaries)
    rows=[];invalid=[]
    for idx,(n,pid,x,y) in enumerate(selected,1):
        ph=[]
        for b,f in poly_index:
            if b[0]<=x<=b[2] and b[1]<=y<=b[3] and point_in_geojson(x,y,f.get('geometry')): ph.append(f)
        police=[]
        for b in boundaries:
            bb=b['bbox']
            if bb[0]<=x<=bb[2] and bb[1]<=y<=bb[3] and point_in_polygon(x,y,b['poly']): police.append(b)
        reasons=[]
        if len(ph)!=1: reasons.append(f'canonical_polygon_match_count={len(ph)} expected=1')
        if len(police)!=1: reasons.append(f'police_boundary_match_count={len(police)} expected=1')
        cpf=ph[0] if len(ph)==1 else None
        cid,cid_basis=stable_poly_id(cpf) if cpf else (None,None)
        if not cid: reasons.append('canonical_parcel_id_unavailable_from_verified_polygon_feature')
        pb=police[0] if len(police)==1 else None
        if pb and not pb.get('identifier'): reasons.append('official_police_boundary_exact_identifier_missing')
        props={
          'evidence_scope':'parcel',
          'coverage_area_id':pb.get('identifier') if pb else None,
          'source_resolution':'neighbourhood_policing_team_boundary',
          'time_window':'2026-05',
          'source_url':ARCHIVE_URL,
          'measurement_date':'2026-05',
          'measurement_method':'official_monthly_NPT_boundary_archive',
          'spatial_binding_method':'canonical_point_within_unique_canonical_polygon_and_unique_official_NPT_polygon',
          'confidence_score_0_100':100 if not reasons else 0,
          'evidence_grade':'OFFICIAL_EXACT_POLYGON_IDENTIFIER' if not reasons else 'REJECTED',
          'field_evidence':({'criterion':'security_public_safety','boundary_identifier':pb.get('identifier'),'boundary_name':pb.get('name'),'boundary_member':pb.get('member'),'archive_md5':md5,'archive_sha256':sha} if pb else None),
          'canonical_parcel_id':cid,
          'canonical_parcel_id_basis':cid_basis,
          'partition_alias':pid
        }
        geom=cpf.get('geometry') if cpf else None
        if not geom or geom.get('type') not in ('Polygon','MultiPolygon'): reasons.append('geometry_not_polygon_or_multipolygon')
        for k in REQUIRED_FIELDS:
            if props.get(k) in (None,''): reasons.append(f'missing_required_field:{k}')
        if props.get('confidence_score_0_100') is None or not (0<=props.get('confidence_score_0_100',-1)<=100): reasons.append('invalid_confidence_score_0_100')
        row={'record_index':idx,'cursor':f'{SOURCE_WINDOW}:record={idx}','partition_alias':pid,'parcel_number':n,'geometry':geom,'properties':props,'schema_valid':not reasons,'rejection_reasons':sorted(set(reasons))}
        rows.append(row)
        if reasons: invalid.append({'record_index':idx,'partition_alias':pid,'reasons':sorted(set(reasons))})
    all_valid=(len(rows)==MAX_RECORDS and not invalid)
    base.update(status='SCHEMA_PRECHECK_PASSED' if all_valid else 'BLOCKED',blocker=None if all_valid else 'PRODUCER_SCHEMA_INVALID',
                source_records_processed_count=len(rows),schema_valid_count=sum(1 for r in rows if r['schema_valid']),schema_invalid_count=len(invalid),
                accepted_count_claimed=MAX_RECORDS if all_valid else 0,official_source_cursor=f'{SOURCE_WINDOW}:record={len(rows)}',
                records_geojson={'type':'FeatureCollection','features':[{'type':'Feature','id':r['properties'].get('canonical_parcel_id'),'geometry':r['geometry'],'properties':r['properties']} for r in rows if r['schema_valid']]},
                unmatched=invalid,rows=rows,
                next_step='Package only if all 50 rows pass semantic precheck; otherwise no incoming Layer24 commit.')
    save(base)
    print(f'POLYGON_FEATURE_COUNT={len(poly_features)}')
    print(f'POLYGON_PROPERTY_KEYS={sorted(keys)}')
    print(f'SOURCE_RECORDS_PROCESSED={len(rows)}')
    print(f'SCHEMA_VALID_COUNT={base["schema_valid_count"]}')
    print(f'SCHEMA_INVALID_COUNT={base["schema_invalid_count"]}')
    print(f'ALL_VALID={all_valid}')
    return 0 if all_valid else 2
if __name__=='__main__': raise SystemExit(main())
