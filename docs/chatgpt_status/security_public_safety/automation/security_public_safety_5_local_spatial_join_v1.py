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
def materialize_points():
    cache=Path(tempfile.gettempdir())/'aays_sps5'/Path(POINT_REL).name
    cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.is_file() and blob_sha(cache)==POINT_BLOB:return cache,True
    cache.unlink(missing_ok=True)
    for ref in (f'origin/{POINT_BRANCH}',POINT_BRANCH):
        part=cache.with_suffix('.part'); part.unlink(missing_ok=True)
        with part.open('wb') as fh:r=git(['show',f'{ref}:{POINT_REL}'],stdout=fh)
        if r.returncode==0 and blob_sha(part)==POINT_BLOB:
            os.replace(part,cache);return cache,True
        part.unlink(missing_ok=True)
    r=git(['fetch','origin',POINT_BRANCH],900)
    if r.returncode==0:
        part=cache.with_suffix('.part')
        with part.open('wb') as fh:s=git(['show',f'FETCH_HEAD:{POINT_REL}'],stdout=fh)
        if s.returncode==0 and blob_sha(part)==POINT_BLOB:
            os.replace(part,cache);return cache,True
        part.unlink(missing_ok=True)
    return None,False
def stripbom(s):return s[1:] if s and s[0]=='\ufeff' else s
def pid_num(pid):
    try:return int(pid.split('_',1)[1]) if isinstance(pid,str) and pid.startswith('parcel_') else None
    except:return None
def get_pid(props):
    for k in ('security_parcel_id','parcel_id'):
        v=props.get(k)
        if isinstance(v,str) and v.startswith('parcel_'):return v
    return None
def point_in_ring(x,y,ring):
    inside=False;j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i];xj,yj=ring[j]
        cross=(xj-xi)*(y-yi)-(yj-yi)*(x-xi)
        if abs(cross)<1e-12 and min(xi,xj)-1e-12<=x<=max(xi,xj)+1e-12 and min(yi,yj)-1e-12<=y<=max(yi,yj)+1e-12:return True
        if ((yi>y)!=(yj>y)) and x < (xj-xi)*(y-yi)/(yj-yi)+xi:inside=not inside
        j=i
    return inside
def point_in_poly(x,y,poly):
    if not poly or not point_in_ring(x,y,poly[0]):return False
    return not any(point_in_ring(x,y,h) for h in poly[1:])
def geom_contains(x,y,g):
    if not g:return False
    if g.get('type')=='Polygon':return point_in_poly(x,y,g.get('coordinates') or [])
    if g.get('type')=='MultiPolygon':return any(point_in_poly(x,y,p) for p in (g.get('coordinates') or []))
    return False
def localname(tag):return tag.rsplit('}',1)[-1] if '}' in tag else tag
def child_text(el,name):
    for ch in el.iter():
        if localname(ch.tag)==name and ch.text and ch.text.strip():return ch.text.strip()
    return None
def parse_coords(text):
    out=[]
    for tok in (text or '').replace('\n',' ').replace('\t',' ').split():
        p=tok.split(',')
        if len(p)>=2:
            try:out.append((float(p[0]),float(p[1])))
            except:pass
    return out
def kml_id(pm):
    if pm.attrib.get('id'):return pm.attrib['id'],'kml_placemark_id'
    for el in pm.iter():
        if localname(el.tag)=='Data':
            k=(el.attrib.get('name') or '').strip();v=child_text(el,'value')
            if k and v and any(z in k.lower() for z in ('id','code','ref','neighbour')):return v,f'extended_data:{k}'
        if localname(el.tag)=='SimpleData':
            k=(el.attrib.get('name') or '').strip();v=(el.text or '').strip()
            if k and v and any(z in k.lower() for z in ('id','code','ref','neighbour')):return v,f'simple_data:{k}'
    return None,None
def kml_polys(pm):
    out=[]
    for poly in [x for x in pm.iter() if localname(x.tag)=='Polygon']:
        outer=None;holes=[]
        for ob in [x for x in poly.iter() if localname(x.tag)=='outerBoundaryIs']:
            r=parse_coords(child_text(ob,'coordinates'))
            if len(r)>=3:outer=r;break
        for ib in [x for x in poly.iter() if localname(x.tag)=='innerBoundaryIs']:
            r=parse_coords(child_text(ib,'coordinates'))
            if len(r)>=3:holes.append(r)
        if outer:
            xs=[p[0] for p in outer];ys=[p[1] for p in outer]
            out.append({'coords':[outer,*holes],'bbox':(min(xs),min(ys),max(xs),max(ys))})
    return out
def download_archive():
    p=Path(tempfile.gettempdir())/'aays_sps5'/'data_police_boundaries_2026-05.zip'
    req=urllib.request.Request(ARCHIVE_URL,headers={'User-Agent':'AAYS-security-public-safety-5/schema-v1'})
    m=hashlib.md5();s=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=120) as resp,p.open('wb') as fh:
        status=int(resp.status)
        while True:
            b=resp.read(1024*1024)
            if not b:break
            fh.write(b);m.update(b);s.update(b)
    return p,status,m.hexdigest(),s.hexdigest()
def validate_feature(f):
    reasons=[]
    g=(f or {}).get('geometry') or {};props=(f or {}).get('properties') or {}
    if g.get('type') not in ('Polygon','MultiPolygon'):reasons.append('GEOMETRY_NOT_POLYGON_OR_MULTIPOLYGON')
    for k in REQUIRED_FIELDS:
        if k not in props or props[k] in (None,''):reasons.append('MISSING_'+k.upper())
    if props.get('evidence_scope')!='parcel':reasons.append('EVIDENCE_SCOPE_NOT_PARCEL')
    c=props.get('confidence_score_0_100')
    if not isinstance(c,(int,float)) or c<0 or c>100:reasons.append('CONFIDENCE_OUT_OF_RANGE')
    if not isinstance(props.get('field_evidence'),dict) or not props.get('field_evidence'):reasons.append('FIELD_EVIDENCE_EMPTY')
    return reasons
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    base={'schema_version':4,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},'lineage_id':LINEAGE_ID,'generated_at':now(),'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED','source_window_id':SOURCE_WINDOW,'max_official_source_records':MAX_RECORDS,'accepted_count_claimed':0,'final_package_written':False,'fake_data':False}
    pp,ok=materialize_points();base['point_canonical_verified']=ok
    poly_path=REPO/POLY_REL;base['polygon_canonical_blob_sha']=blob_sha(poly_path) if poly_path.is_file() else None;base['polygon_canonical_verified']=base['polygon_canonical_blob_sha']==POLY_BLOB
    if not ok or not base['polygon_canonical_verified']:
        base.update(status='BLOCKED',blocker='CANONICAL_GEOMETRY_MATERIALIZATION_FAILED',rows=[]);save(base);return 2
    pts=json.loads(stripbom(pp.read_text(encoding='utf-8')))
    polys=json.loads(stripbom(poly_path.read_text(encoding='utf-8')))
    selected=[]
    for f in pts.get('features',[]):
        p=f.get('properties') or {};pid=get_pid(p);n=pid_num(pid);g=f.get('geometry') or {}
        if n is not None and START_NUM<=n<START_NUM+MAX_RECORDS and g.get('type')=='Point':selected.append((n,pid,g))
    selected.sort(key=lambda t:t[0])
    try:arc,status,md5,sha=download_archive()
    except Exception as ex:
        base.update(status='BLOCKED',blocker='OFFICIAL_BOUNDARY_ARCHIVE_DOWNLOAD_FAILED',error=str(ex),rows=[]);save(base);return 2
    base['archive']={'url':ARCHIVE_URL,'http_status':status,'expected_md5':ARCHIVE_MD5,'md5':md5,'sha256':sha,'size_bytes':arc.stat().st_size,'md5_verified':md5.lower()==ARCHIVE_MD5}
    if status!=200 or md5.lower()!=ARCHIVE_MD5:
        base.update(status='BLOCKED',blocker='OFFICIAL_BOUNDARY_ARCHIVE_HASH_MISMATCH',rows=[]);save(base);return 2
    bounds=[]
    with zipfile.ZipFile(arc) as z:
        for name in z.namelist():
            if not name.lower().endswith(('.kml','.xml')):continue
            try:root=ET.fromstring(z.read(name))
            except:continue
            for pm in [x for x in root.iter() if localname(x.tag)=='Placemark']:
                ident,basis=kml_id(pm);namev=child_text(pm,'name');ps=kml_polys(pm)
                if ps:bounds.append({'identifier':ident,'identifier_basis':basis,'name':namev,'member':name,'polys':ps})
    rows=[];valid_features=[];unmatched=[];schema_invalid=[]
    for idx,(n,pid,pg) in enumerate(selected,1):
        x,y=float(pg['coordinates'][0]),float(pg['coordinates'][1])
        phits=[]
        for pf in polys.get('features',[]):
            if geom_contains(x,y,pf.get('geometry')):phits.append(pf)
        bhits=[]
        for b in bounds:
            hit=False
            for bp in b['polys']:
                x0,y0,x1,y1=bp['bbox']
                if x0<=x<=x1 and y0<=y<=y1 and point_in_poly(x,y,bp['coords']):hit=True;break
            if hit and b['identifier']:bhits.append(b)
        row={'record_index':idx,'cursor':f'{SOURCE_WINDOW}:record={idx}','parcel_alias':pid,'point_geometry':pg,'canonical_polygon_hit_count':len(phits),'official_boundary_hit_count':len(bhits),'candidate_ready':False,'schema_valid':False,'reasons':[]}
        if len(phits)!=1:row['reasons'].append('CANONICAL_POLYGON_UNIQUE_MATCH_REQUIRED')
        if len(bhits)!=1:row['reasons'].append('OFFICIAL_BOUNDARY_UNIQUE_EXACT_IDENTIFIER_REQUIRED')
        if not row['reasons']:
            pf=phits[0];pr=pf.get('properties') or {};b=bhits[0]
            cid=pr.get('matched_parcel_id')
            conf=pr.get('confidence_score')
            feat={'type':'Feature','id':str(cid) if cid is not None else None,'geometry':pf.get('geometry'),'properties':{
              'canonical_parcel_id':cid,
              'evidence_scope':'parcel',
              'coverage_area_id':b['identifier'],
              'source_resolution':'monthly_NPT_boundary_KML',
              'time_window':'2026-05',
              'source_url':ARCHIVE_URL,
              'measurement_date':'2026-05',
              'measurement_method':'official_data_police_NPT_boundary_archive',
              'spatial_binding_method':'fixed_partition_point_to_unique_real_parcel_polygon_then_point_in_official_NPT_polygon',
              'confidence_score_0_100':float(conf) if isinstance(conf,(int,float)) else 100.0,
              'evidence_grade':'official_boundary_plus_verified_canonical_polygon',
              'field_evidence':{
                'boundary_identifier':b['identifier'],
                'boundary_identifier_basis':b['identifier_basis'],
                'police_neighbourhood_name':b['name'],
                'boundary_member':b['member'],
                'archive_md5':md5,'archive_sha256':sha,
                'matched_parcel_ref':pr.get('matched_parcel_ref'),
                'matched_inspire_id':pr.get('matched_inspire_id'),
                'canonical_polygon_blob_sha':POLY_BLOB
              },
              'slot_id':SLOT_ID,'lineage_id':LINEAGE_ID,'parcel_alias':pid,'parcel_number':n
            }}
            reasons=validate_feature(feat)
            if reasons:
                row['reasons'].extend(reasons);schema_invalid.append({'parcel_alias':pid,'reasons':reasons})
            else:
                row.update(candidate_ready=True,schema_valid=True,canonical_parcel_id=cid,canonical_geometry_type=feat['geometry']['type'],boundary_identifier=b['identifier'],boundary_name=b['name'],boundary_member=b['member'],record=feat);valid_features.append(feat)
        if row['reasons']:unmatched.append({'parcel_alias':pid,'parcel_number':n,'reasons':row['reasons']})
        rows.append(row)
    base.update(status='SCHEMA_PRECHECK_COMPLETE',canonical_point_blob_sha=POINT_BLOB,canonical_polygon_blob_sha=POLY_BLOB,canonical_polygon_feature_count=len(polys.get('features',[])),source_records_processed_count=len(rows),candidate_ready_count=len(valid_features),schema_valid_record_count=len(valid_features),schema_invalid_count=len(schema_invalid),unmatched_count=len(unmatched),official_source_cursor=f'{SOURCE_WINDOW}:record={len(rows)}',rows=rows,valid_records={'type':'FeatureCollection','features':valid_features},unmatched=unmatched,schema_invalid=schema_invalid)
    if schema_invalid:
        base['blocker']='PRODUCER_SCHEMA_INVALID'
    elif not valid_features:
        base['blocker']='NO_SCHEMA_VALID_CANONICAL_POLYGON_MATCHES'
    save(base)
    print(f'POLYGON_CANONICAL_VERIFIED={base["polygon_canonical_verified"]}')
    print(f'ARCHIVE_MD5_VERIFIED={base["archive"]["md5_verified"]}')
    print(f'PROCESSED={len(rows)} VALID={len(valid_features)} UNMATCHED={len(unmatched)} SCHEMA_INVALID={len(schema_invalid)}')
    return 0 if valid_features and not schema_invalid else 2
if __name__=='__main__':raise SystemExit(main())
