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
REPO=Path(os.environ.get('AAYS_REPO_ROOT') or '.').resolve()
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
CANON_BRANCH='codex/aays-single-runner-v5-20260706'
CANON_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
CANON_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
ARCHIVE_URL='https://data.police.uk/data/boundaries/2026-05.zip'
ARCHIVE_MD5='a39d88624434ff668270b82f33fb77d3'
SOURCE_WINDOW='data_police_npt_boundary_archive_2026_05_sps5_61624_61673_v1'

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
def lname(tag): return tag.rsplit('}',1)[-1] if '}' in tag else tag
def child_text(el,name):
    for ch in el.iter():
        if lname(ch.tag)==name and ch.text and ch.text.strip(): return ch.text.strip()
    return None
def parse_coords(text):
    out=[]
    for tok in (text or '').replace('\n',' ').replace('\t',' ').split():
        p=tok.split(',')
        if len(p)>=2:
            try: out.append([float(p[0]),float(p[1])])
            except: pass
    return out
def exact_identifier(pm):
    if pm.attrib.get('id'): return pm.attrib['id'],'kml_placemark_id'
    vals=[]
    for el in pm.iter():
        if lname(el.tag)=='Data':
            k=(el.attrib.get('name') or '').strip(); v=child_text(el,'value')
            if k and v: vals.append((k,v))
        elif lname(el.tag)=='SimpleData':
            k=(el.attrib.get('name') or '').strip(); v=(el.text or '').strip()
            if k and v: vals.append((k,v))
    for p in ('id','code','reference','ref','neighbourhood','neighborhood','ward'):
        for k,v in vals:
            if p in k.lower(): return v,f'extended_data:{k}'
    return None,None
def polygons_from_pm(pm):
    polys=[]
    for poly in [x for x in pm.iter() if lname(x.tag)=='Polygon']:
        outer=None; holes=[]
        for ob in [x for x in poly.iter() if lname(x.tag)=='outerBoundaryIs']:
            r=parse_coords(child_text(ob,'coordinates'))
            if len(r)>=3: outer=r; break
        for ib in [x for x in poly.iter() if lname(x.tag)=='innerBoundaryIs']:
            r=parse_coords(child_text(ib,'coordinates'))
            if len(r)>=3: holes.append(r)
        if outer:
            if outer[0]!=outer[-1]: outer.append(outer[0])
            for h in holes:
                if h[0]!=h[-1]: h.append(h[0])
            xs=[p[0] for p in outer]; ys=[p[1] for p in outer]
            polys.append({'outer':outer,'holes':holes,'bbox':(min(xs),min(ys),max(xs),max(ys))})
    return polys
def point_in_ring(x,y,ring):
    inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i]; xj,yj=ring[j]
        if ((yi>y)!=(yj>y)):
            d=yj-yi
            if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
        j=i
    return inside
def point_in_poly(x,y,p):
    if not point_in_ring(x,y,p['outer']): return False
    return not any(point_in_ring(x,y,h) for h in p['holes'])
def geojson_geom(polys):
    coords=[[p['outer'],*p['holes']] for p in polys]
    return {'type':'Polygon','coordinates':coords[0]} if len(coords)==1 else {'type':'MultiPolygon','coordinates':coords}
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    base={'schema_version':4,'slot_id':SLOT_ID,'owner':None,'partition':{'start':P0,'end':P1,'count':PC},'lineage_id':LINEAGE_ID,'generated_at':now(),'source_window_id':SOURCE_WINDOW,'max_records':MAX_RECORDS,'accepted_count_claimed':0,'source_area_count_claimed':0,'first_missing_criterion':'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED','fake_data':False}
    cp,mat=materialize(); base['canonical_materialization']=mat
    if not cp:
        base.update(status='BLOCKED',blocker='CANONICAL_BLOB_MATERIALIZATION_FAILED',rows=[],source_area_candidates=[]); save(base); return 2
    cg=json.loads(cp.read_text(encoding='utf-8-sig'))
    selected=[]
    for f in cg.get('features',[]):
        props=f.get('properties') or {}; pid=get_pid(props); n=pid_num(pid); g=f.get('geometry') or {}
        if n is not None and START_NUM<=n<START_NUM+MAX_RECORDS:
            selected.append((n,pid,g,props))
    selected.sort(key=lambda x:x[0])
    tmp=Path(tempfile.gettempdir())/'aays_sps5'/'data_police_boundaries_2026-05.zip'
    try:
        req=urllib.request.Request(ARCHIVE_URL,headers={'User-Agent':'AAYS-security-public-safety-5/schema-v4'})
        md5=hashlib.md5(); sha=hashlib.sha256()
        with urllib.request.urlopen(req,timeout=120) as resp,tmp.open('wb') as fh:
            status=int(resp.status)
            while True:
                b=resp.read(1024*1024)
                if not b: break
                fh.write(b); md5.update(b); sha.update(b)
    except Exception as ex:
        base.update(status='BLOCKED',blocker='OFFICIAL_BOUNDARY_ARCHIVE_DOWNLOAD_FAILED',error=str(ex),rows=[],source_area_candidates=[]); save(base); return 2
    md5h,shah=md5.hexdigest(),sha.hexdigest()
    base['archive']={'url':ARCHIVE_URL,'http_status':status,'expected_md5':ARCHIVE_MD5,'md5':md5h,'sha256':shah,'size_bytes':tmp.stat().st_size,'md5_verified':md5h.lower()==ARCHIVE_MD5}
    if status!=200 or md5h.lower()!=ARCHIVE_MD5:
        base.update(status='BLOCKED',blocker='OFFICIAL_BOUNDARY_ARCHIVE_HASH_MISMATCH',rows=[],source_area_candidates=[]); save(base); return 2
    boundaries=[]
    with zipfile.ZipFile(tmp) as z:
        for name in z.namelist():
            if not name.lower().endswith(('.kml','.xml')): continue
            try: root=ET.fromstring(z.read(name))
            except: continue
            for pm in [x for x in root.iter() if lname(x.tag)=='Placemark']:
                ident,basis=exact_identifier(pm); polys=polygons_from_pm(pm)
                if not ident or not polys: continue
                boundaries.append({'identifier':ident,'basis':basis,'name':child_text(pm,'name'),'member':name,'polygons':polys})
    rejections=[]; hit_keys={}
    for idx,(n,pid,g,props) in enumerate(selected,1):
        reasons=[]
        if g.get('type') not in ('Polygon','MultiPolygon'): reasons.append(f"PARCEL_GEOMETRY_TYPE_{g.get('type')}_NOT_ALLOWED")
        if not props.get('canonical_parcel_id'): reasons.append('MISSING_CANONICAL_PARCEL_ID')
        hits=[]
        if g.get('type')=='Point':
            lng,lat=float(g['coordinates'][0]),float(g['coordinates'][1])
            for b in boundaries:
                if any(p['bbox'][0]<=lng<=p['bbox'][2] and p['bbox'][1]<=lat<=p['bbox'][3] and point_in_poly(lng,lat,p) for p in b['polygons']):
                    hits.append(b)
                    hit_keys[(b['identifier'],b['member'])]=b
        rejections.append({'record_index':idx,'cursor':f'{SOURCE_WINDOW}:record={idx}','parcel_id_alias':pid,'parcel_number':n,'geometry_type':g.get('type'),'canonical_parcel_id':props.get('canonical_parcel_id'),'matched_boundary_ids':[h['identifier'] for h in hits],'rejection_reasons':reasons or ['SCHEMA_PRECHECK_UNEXPECTED_PASS']})
    source_area=[]
    for (_, _),b in sorted(hit_keys.items(),key=lambda kv:(kv[0][0],kv[0][1])):
        geom=geojson_geom(b['polygons'])
        props={
          'evidence_scope':'coverage_area',
          'coverage_area_id':b['identifier'],
          'source_resolution':'neighbourhood_policing_team_boundary',
          'time_window':'2026-05',
          'source_url':ARCHIVE_URL,
          'measurement_date':'2026-05-01',
          'measurement_method':'official_monthly_npt_kml_boundary_archive',
          'spatial_binding_method':'official_kml_geometry_exact_identifier',
          'confidence_score_0_100':100,
          'evidence_grade':'A',
          'field_evidence':{'placemark_id':b['identifier'],'identifier_basis':b['basis'],'name':b['name'],'archive_member':b['member'],'archive_md5':md5h,'archive_sha256':shah}
        }
        required=['evidence_scope','coverage_area_id','source_resolution','time_window','source_url','measurement_date','measurement_method','spatial_binding_method','confidence_score_0_100','evidence_grade','field_evidence']
        valid=geom.get('type') in ('Polygon','MultiPolygon') and all(props.get(k) is not None for k in required)
        source_area.append({'type':'Feature','id':b['identifier'],'geometry':geom,'properties':props,'schema_valid':valid})
    valid_source=[f for f in source_area if f['schema_valid']]
    base.update(
      status='SCHEMA_PRECHECK_COMPLETE',
      canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,
      canonical_records_examined=len(selected),
      parcel_schema_valid_count=0,
      parcel_schema_invalid_count=len(rejections),
      source_area_candidate_count=len(source_area),
      source_area_valid_count=len(valid_source),
      accepted_count_claimed=0,
      source_area_count_claimed=len(valid_source),
      official_source_cursor=f'{SOURCE_WINDOW}:record={len(selected)}',
      next_first_missing_criterion='CANONICAL_PARCEL_POLYGON_GEOMETRY_REQUIRED',
      rows=rejections,
      source_area_candidates=valid_source
    )
    save(base)
    print(f'CANONICAL_RECORDS_EXAMINED={len(selected)}')
    print(f'PARCEL_SCHEMA_INVALID_COUNT={len(rejections)}')
    print(f'SOURCE_AREA_VALID_COUNT={len(valid_source)}')
    print(f'ARCHIVE_MD5_VERIFIED={base["archive"]["md5_verified"]}')
    return 0 if base['canonical_blob_verified'] and len(valid_source)>0 else 2
if __name__=='__main__': raise SystemExit(main())
