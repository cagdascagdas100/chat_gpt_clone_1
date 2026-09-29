from __future__ import annotations
import json,os,subprocess,tempfile
from pathlib import Path

SLOT_ID='security_public_safety_5'
LINEAGE_ID='86b5e932de484ad26133fa8c'
START_NUM=61624
MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT',r'F:\chatgpt\chat_gpt_clone_1_main'))
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
POINT_BRANCH='codex/aays-single-runner-v5-20260706'
POINT_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
POINT_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
POLY_REL='docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
POLY_BLOB='0180223f125027d55ffea5d908b77f8df08ffe84'
SOURCE_WINDOW='data_police_npt_boundary_archive_2026_05_sps5_61624_61673_polygon_schema_v1'

def git(args,timeout=900,stdout=None):
    return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(['hash-object',str(path)],180);return r.stdout.decode().strip() if r.returncode==0 else None
def stripbom(s):return s[1:] if s and s[0]=='\ufeff' else s
def materialize():
    cache=Path(tempfile.gettempdir())/'aays_sps5'/Path(POINT_REL).name;cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.is_file() and blob_sha(cache)==POINT_BLOB:return cache
    cache.unlink(missing_ok=True)
    for ref in (f'origin/{POINT_BRANCH}',POINT_BRANCH):
        part=cache.with_suffix('.part');part.unlink(missing_ok=True)
        with part.open('wb') as fh:r=git(['show',f'{ref}:{POINT_REL}'],stdout=fh)
        if r.returncode==0 and blob_sha(part)==POINT_BLOB:os.replace(part,cache);return cache
        part.unlink(missing_ok=True)
    r=git(['fetch','origin',POINT_BRANCH],900)
    if r.returncode==0:
        part=cache.with_suffix('.part')
        with part.open('wb') as fh:s=git(['show',f'FETCH_HEAD:{POINT_REL}'],stdout=fh)
        if s.returncode==0 and blob_sha(part)==POINT_BLOB:os.replace(part,cache);return cache
        part.unlink(missing_ok=True)
    return None
def pnum(props):
    v=props.get('security_parcel_id') or props.get('parcel_id')
    try:return int(v.split('_',1)[1]) if isinstance(v,str) and v.startswith('parcel_') else None
    except:return None
def ring(x,y,r):
    inside=False;j=len(r)-1
    for i in range(len(r)):
        xi,yi=r[i];xj,yj=r[j]
        cross=(xj-xi)*(y-yi)-(yj-yi)*(x-xi)
        if abs(cross)<1e-12 and min(xi,xj)-1e-12<=x<=max(xi,xj)+1e-12 and min(yi,yj)-1e-12<=y<=max(yi,yj)+1e-12:return True
        if ((yi>y)!=(yj>y)) and x < (xj-xi)*(y-yi)/(yj-yi)+xi:inside=not inside
        j=i
    return inside
def pinpoly(x,y,p):
    return bool(p and ring(x,y,p[0]) and not any(ring(x,y,h) for h in p[1:]))
def contains(x,y,g):
    if g.get('type')=='Polygon':return pinpoly(x,y,g.get('coordinates') or [])
    if g.get('type')=='MultiPolygon':return any(pinpoly(x,y,p) for p in (g.get('coordinates') or []))
    return False

pp=materialize(); poly=REPO/POLY_REL
if pp is None or blob_sha(poly)!=POLY_BLOB:raise SystemExit(3)
pts=json.loads(stripbom(pp.read_text(encoding='utf-8')));pg=json.loads(stripbom(poly.read_text(encoding='utf-8')))
sel=[]
for f in pts.get('features',[]):
    n=pnum(f.get('properties') or {});g=f.get('geometry') or {}
    if n is not None and START_NUM<=n<START_NUM+MAX_RECORDS and g.get('type')=='Point':sel.append((n,g))
sel.sort()
rej=[]
for i,(n,g) in enumerate(sel,1):
    x,y=g['coordinates'][:2];hits=[]
    for pf in pg.get('features',[]):
        if contains(float(x),float(y),pf.get('geometry') or {}):
            p=pf.get('properties') or {}
            hits.append({'canonical_parcel_id':p.get('matched_parcel_id'),'matched_parcel_ref':p.get('matched_parcel_ref'),'matched_inspire_id':p.get('matched_inspire_id'),'geometry_type':(pf.get('geometry') or {}).get('type')})
    if len(hits)==0:reason='CANONICAL_POLYGON_NOT_FOUND_FOR_FIXED_PARTITION_POINT'
    elif len(hits)>1:reason='CANONICAL_POLYGON_AMBIGUOUS_FOR_FIXED_PARTITION_POINT'
    elif hits[0].get('canonical_parcel_id') in (None,''):reason='CANONICAL_PARCEL_ID_MISSING'
    else:reason='CANONICAL_POLYGON_MATCH_AVAILABLE'
    rej.append({'record_index':i,'cursor':f'{SOURCE_WINDOW}:record={i}','parcel_alias':f'parcel_{n}','point_geometry':g,'canonical_polygon_hit_count':len(hits),'reason':reason,'hits':hits})
summary={
 'schema_version':4,
 'slot_id':SLOT_ID,'lineage_id':LINEAGE_ID,
 'source_window_id':SOURCE_WINDOW,
 'mode':'READBACK_ONLY_NO_SOURCE_WINDOW_REPEAT',
 'processed_count':len(rej),
 'canonical_polygon_source':POLY_REL,
 'canonical_polygon_blob_sha':POLY_BLOB,
 'canonical_polygon_verified':True,
 'unique_polygon_match_count':sum(1 for r in rej if r['reason']=='CANONICAL_POLYGON_MATCH_AVAILABLE'),
 'no_polygon_match_count':sum(1 for r in rej if r['reason']=='CANONICAL_POLYGON_NOT_FOUND_FOR_FIXED_PARTITION_POINT'),
 'ambiguous_polygon_match_count':sum(1 for r in rej if r['reason']=='CANONICAL_POLYGON_AMBIGUOUS_FOR_FIXED_PARTITION_POINT'),
 'accepted_count_claimed':0,
 'source_area_count':0,
 'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED',
 'delivery_blocked':'PRODUCER_SCHEMA_INVALID',
 'rejections':rej
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f"PROCESSED={len(rej)} UNIQUE={summary['unique_polygon_match_count']} NO_MATCH={summary['no_polygon_match_count']} AMBIGUOUS={summary['ambiguous_polygon_match_count']}")
raise SystemExit(0)
