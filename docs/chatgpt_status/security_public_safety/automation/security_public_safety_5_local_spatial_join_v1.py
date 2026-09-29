from __future__ import annotations
import json,os,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
SLOT_ID='security_public_safety_5';LINEAGE_ID='86b5e932de484ad26133fa8c'
START_NUM=61624;MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT',r'F:\chatgpt\chat_gpt_clone_1_main'))
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
POINT_BRANCH='codex/aays-single-runner-v5-20260706'
POINT_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
POINT_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
POLY_REL='docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
POLY_BLOB='0180223f125027d55ffea5d908b77f8df08ffe84'
SOURCE_WINDOW='data_police_npt_boundary_archive_2026_05_sps5_61624_61673_polygon_schema_v1'
def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def git(args,timeout=900,stdout=None):
    return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(['hash-object',str(path)],180);return r.stdout.decode().strip() if r.returncode==0 else None
def mat():
    p=Path(tempfile.gettempdir())/'aays_sps5'/Path(POINT_REL).name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_file() and blob_sha(p)==POINT_BLOB:return p
    for ref in (f'origin/{POINT_BRANCH}',POINT_BRANCH):
        q=p.with_suffix('.part');q.unlink(missing_ok=True)
        with q.open('wb') as fh:r=git(['show',f'{ref}:{POINT_REL}'],stdout=fh)
        if r.returncode==0 and blob_sha(q)==POINT_BLOB:os.replace(q,p);return p
        q.unlink(missing_ok=True)
    r=git(['fetch','origin',POINT_BRANCH],900)
    if r.returncode==0:
        q=p.with_suffix('.part')
        with q.open('wb') as fh:s=git(['show',f'FETCH_HEAD:{POINT_REL}'],stdout=fh)
        if s.returncode==0 and blob_sha(q)==POINT_BLOB:os.replace(q,p);return p
    return None
def pidnum(v):
    try:return int(v.split('_',1)[1])
    except:return None
def point_in_ring(x,y,r):
    inside=False;j=len(r)-1
    for i in range(len(r)):
        xi,yi=r[i];xj,yj=r[j]
        if ((yi>y)!=(yj>y)):
            d=yj-yi
            if d and x<(xj-xi)*(y-yi)/d+xi:inside=not inside
        j=i
    return inside
def pip(x,y,g):
    t=(g or {}).get('type');c=(g or {}).get('coordinates') or []
    def pp(p):return bool(p and point_in_ring(x,y,p[0]) and not any(point_in_ring(x,y,h) for h in p[1:]))
    return pp(c) if t=='Polygon' else any(pp(p) for p in c) if t=='MultiPolygon' else False
def bbox(g):
    xs=[];ys=[]
    def w(v):
        if isinstance(v,list) and len(v)>=2 and isinstance(v[0],(int,float)) and isinstance(v[1],(int,float)):xs.append(float(v[0]));ys.append(float(v[1]))
        elif isinstance(v,list):
            for z in v:w(z)
    w((g or {}).get('coordinates'));return (min(xs),min(ys),max(xs),max(ys)) if xs else None
def sid(f):
    p=f.get('properties') or {}
    for k in ('canonical_parcel_id','title_number','title_no','title','inspire_id','INSPIREID','inspireID','reference','ref'):
        if p.get(k) not in (None,''):return str(p[k]),'properties.'+k
    if f.get('id') not in (None,''):return str(f['id']),'feature.id'
    return None,None
def main():
    pp=mat();poly=REPO/POLY_REL
    if not pp or not poly.is_file() or blob_sha(poly)!=POLY_BLOB:raise SystemExit(3)
    pts=json.loads(pp.read_text(encoding='utf-8-sig'));pg=json.loads(poly.read_text(encoding='utf-8-sig'))
    pfs=[f for f in pg.get('features',[]) if (f.get('geometry') or {}).get('type') in ('Polygon','MultiPolygon')]
    idx=[(bbox(f.get('geometry')),f) for f in pfs if bbox(f.get('geometry'))]
    targets=[]
    for f in pts.get('features',[]):
        pr=f.get('properties') or {};pid=pr.get('security_parcel_id') or pr.get('parcel_id');n=pidnum(pid);g=f.get('geometry') or {}
        if n is not None and START_NUM<=n<START_NUM+MAX_RECORDS and g.get('type')=='Point':
            targets.append((n,pid,float(g['coordinates'][0]),float(g['coordinates'][1])))
    targets.sort()
    rej=[];diag=[]
    for i,(n,pid,x,y) in enumerate(targets,1):
        hits=[f for b,f in idx if b[0]<=x<=b[2] and b[1]<=y<=b[3] and pip(x,y,f.get('geometry'))]
        ids=[sid(f) for f in hits]
        reasons=[]
        if len(hits)!=1:reasons.append(f'canonical_polygon_match_count={len(hits)} expected=1')
        if len(hits)==1 and not ids[0][0]:reasons.append('canonical_parcel_id_unavailable_from_verified_polygon_feature')
        if reasons:rej.append({'record_index':i,'partition_alias':pid,'reasons':reasons})
        diag.append({'record_index':i,'partition_alias':pid,'point':[x,y],'canonical_polygon_match_count':len(hits),'candidate_ids':ids[:5],'reasons':reasons})
    out={'schema_version':4,'slot_id':SLOT_ID,'lineage_id':LINEAGE_ID,'generated_at':now(),'audit_kind':'LOCAL_ONLY_SCHEMA_REJECTION_AUDIT_NO_SOURCE_REDOWNLOAD',
         'source_window_id':SOURCE_WINDOW,'source_window_reused':False,'canonical_polygon_blob_sha':POLY_BLOB,'canonical_polygon_feature_count':len(pfs),
         'records_audited':len(diag),'schema_invalid_count':len(rej),'accepted_count_claimed':0,'final_package_written':False,
         'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED','unmatched':rej,'rows':diag}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print('RECORDS_AUDITED='+str(len(diag)));print('SCHEMA_INVALID_COUNT='+str(len(rej)))
    for r in rej:print(r['partition_alias']+'|'+','.join(r['reasons']))
    return 0
if __name__=='__main__':raise SystemExit(main())
