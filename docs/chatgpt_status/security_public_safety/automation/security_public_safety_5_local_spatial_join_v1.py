from __future__ import annotations
import hashlib, html as htmlmod, json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request, zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

SLOT_ID='security_public_safety_5'
LINEAGE_ID='86b5e932de484ad26133fa8c'
PARTITION=[61524,76903]
TARGET_IDS=['parcel_61637','parcel_61648','parcel_61649','parcel_61669','parcel_61672']
REPO=Path(os.environ.get('AAYS_REPO_ROOT') or Path(__file__).resolve().parents[4])
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
CANON_BRANCH='codex/aays-single-runner-v5-20260706'
CANON_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
CANON_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
PREV_PKG_DIR=REPO/'incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/planning_data_title_boundary_mps_lsoa_61624_61673_20260928T221705Z'
PREV_ZIP=PREV_PKG_DIR/'AAYS_LAYER24__security_public_safety_5__86b5e932de484ad26133fa8c__planning_data_title_boundary_mps_lsoa_61624_61673__20260928T221705Z.zip'
PREV_ZIP_SHA='6400ab1c73712e16c53d86c2f503c710a396190704dbf94962890ee950eb70bd'
PRIOR_MPS_RECORDS=REPO/'incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/mps_lsoa_recorded_crime_202108_202307_61624_61673_20260928T085212Z/records.geojson'
INSPIRE_PAGE='https://use-land-property-data.service.gov.uk/datasets/inspire/download'
SOURCE_WINDOW='hmlr_inspire_lambeth_2026_09_sps5_rejected5_v1'
REQUIRED=['evidence_scope','coverage_area_id','source_resolution','time_window','source_url','measurement_date','measurement_method','spatial_binding_method','confidence_score_0_100','evidence_grade','field_evidence','canonical_parcel_id']
FORBIDDEN=['parcel_id','accepted_parcel']

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def git(args,timeout=900,stdout=None):
    return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(['hash-object',str(path)],180)
    return r.stdout.decode('utf-8','replace').strip() if r.returncode==0 else None
def materialize_canonical():
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
    r=git(['fetch','origin',CANON_BRANCH],900); ev['fetch_returncode']=r.returncode; ev['fetch_stderr']=r.stderr.decode('utf-8','replace')[-1000:]
    if r.returncode==0:
        part=cache.with_suffix('.part')
        with part.open('wb') as fh: s=git(['show',f'FETCH_HEAD:{CANON_REL}'],stdout=fh)
        if s.returncode==0 and blob_sha(part)==CANON_BLOB:
            os.replace(part,cache); ev.update(source_ref='FETCH_HEAD',verified=True); return cache,ev
        part.unlink(missing_ok=True)
    ev['error']='EXACT_CANONICAL_BLOB_NOT_MATERIALIZED'
    return None,ev

def verify_previous_zip():
    out={'path':str(PREV_ZIP.relative_to(REPO)).replace('\\','/'),'expected_zip_sha256':PREV_ZIP_SHA,'exists':PREV_ZIP.is_file(),'verified':False}
    if not PREV_ZIP.is_file():
        out['error']='PREVIOUS_ZIP_MISSING'; return out
    out['size_bytes']=PREV_ZIP.stat().st_size
    out['zip_sha256']=sha256_file(PREV_ZIP)
    good=0; bad=[]; members=[]
    try:
        with zipfile.ZipFile(PREV_ZIP) as z:
            names=z.namelist(); members=names
            for s in [n for n in names if n.endswith('.sha256')]:
                raw=z.read(s).decode('utf-8').strip()
                m=re.match(r'^([0-9a-fA-F]{64})\s+\*?(.+)$',raw)
                if not m:
                    bad.append({'sidecar':s,'reason':'invalid_sidecar_format'}); continue
                exp,target=m.groups(); d=os.path.dirname(s)
                t=(d+'/'+target) if d and '/' not in target else target
                if t not in names:
                    bad.append({'sidecar':s,'reason':'target_missing','target':t}); continue
                got=hashlib.sha256(z.read(t)).hexdigest()
                if got.lower()==exp.lower(): good+=1
                else: bad.append({'sidecar':s,'reason':'hash_mismatch','target':t,'expected':exp,'got':got})
    except Exception as e:
        out['error']='ZIP_READ_FAILED:'+str(e); return out
    out.update(member_count=len(members),sidecar_count=good+len(bad),sidecar_good_count=good,sidecar_bad=bad)
    out['verified']=(out['zip_sha256']==PREV_ZIP_SHA and good==7 and not bad and len(members)>=14)
    return out

class RowLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_tr=False; self.text=[]; self.hrefs=[]; self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='tr':
            self.in_tr=True; self.text=[]; self.hrefs=[]
        elif tag.lower()=='a' and self.in_tr:
            d=dict(attrs); h=d.get('href')
            if h: self.hrefs.append(h)
    def handle_data(self,data):
        if self.in_tr: self.text.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=='tr' and self.in_tr:
            self.rows.append((' '.join(' '.join(self.text).split()),list(self.hrefs)))
            self.in_tr=False
def http_bytes(url,timeout=120):
    req=urllib.request.Request(url,headers={'User-Agent':'AAYS-security-public-safety-5/HMLR-INSPIRE-v1','Accept':'*/*'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return int(r.status),r.read(),dict(r.headers)
def find_lambeth_gml(page_bytes):
    s=page_bytes.decode('utf-8','replace')
    p=RowLinkParser(); p.feed(s)
    for text,hrefs in p.rows:
        if 'London Borough of Lambeth' in text and hrefs:
            for h in reversed(hrefs):
                if '.gml' in h.lower() or 'download' in h.lower():
                    return urllib.parse.urljoin(INSPIRE_PAGE,h)
            return urllib.parse.urljoin(INSPIRE_PAGE,hrefs[-1])
    idx=s.find('London Borough of Lambeth')
    if idx>=0:
        seg=s[max(0,idx-2500):idx+3500]
        hrefs=re.findall(r'href=["\']([^"\']+)["\']',seg,re.I)
        for h in hrefs:
            if '.gml' in h.lower():
                return urllib.parse.urljoin(INSPIRE_PAGE,htmlmod.unescape(h))
    return None
def ensure_pyproj():
    try:
        import pyproj
        return pyproj
    except Exception:
        r=subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','pyproj==3.7.2'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
        if r.returncode!=0: raise RuntimeError('PYPROJ_INSTALL_FAILED:'+r.stderr.decode('utf-8','replace')[-1000:])
        import pyproj
        return pyproj
def lname(tag): return tag.rsplit('}',1)[-1] if '}' in tag else tag
def text_first(el,names):
    names={x.lower() for x in names}
    for x in el.iter():
        if lname(x.tag).lower() in names and x.text and x.text.strip():
            return x.text.strip()
    return None
def parse_ring(container):
    for x in container.iter():
        ln=lname(x.tag)
        if ln=='posList' and x.text:
            vals=[float(v) for v in x.text.split()]
            dim=int(x.attrib.get('srsDimension','2') or 2)
            if dim<2: dim=2
            return [(vals[i],vals[i+1]) for i in range(0,len(vals)-dim+1,dim)]
        if ln=='coordinates' and x.text:
            pts=[]
            for tok in x.text.replace('\n',' ').split():
                a=tok.split(',')
                if len(a)>=2:
                    try: pts.append((float(a[0]),float(a[1])))
                    except: pass
            if pts: return pts
    return []
def extract_polygons(feature):
    out=[]
    for poly in [x for x in feature.iter() if lname(x.tag)=='Polygon']:
        ext=None; holes=[]
        for e in poly.iter():
            if lname(e.tag) in ('exterior','outerBoundaryIs'):
                rr=parse_ring(e)
                if len(rr)>=4: ext=rr; break
        if ext is None: continue
        for e in poly.iter():
            if lname(e.tag) in ('interior','innerBoundaryIs'):
                rr=parse_ring(e)
                if len(rr)>=4: holes.append(rr)
        out.append((ext,holes))
    return out
def feature_members(root):
    out=[]
    for m in root.iter():
        if lname(m.tag) in ('featureMember','member'):
            kids=list(m)
            if kids: out.append(kids[0])
    if out: return out
    return [x for x in root.iter() if lname(x.tag) in ('CadastralParcel','LandRegistryUnit')]
def feature_id(f):
    local=text_first(f,['localId'])
    if local: return local,'localId'
    nat=text_first(f,['nationalCadastralReference'])
    if nat: return nat,'nationalCadastralReference'
    for k,v in f.attrib.items():
        if lname(k)=='id' and v: return v,'gml:id'
    return None,None
def source_crs(root):
    for x in root.iter():
        s=x.attrib.get('srsName')
        if s:
            m=re.search(r'(?:EPSG[:/]+)(\d+)',s,re.I)
            if m: return 'EPSG:'+m.group(1)
            if '27700' in s: return 'EPSG:27700'
            if '4326' in s: return 'EPSG:4326'
            if '4258' in s: return 'EPSG:4258'
    return 'EPSG:27700'
def point_in_ring(x,y,ring):
    inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i]; xj,yj=ring[j]
        if ((yi>y)!=(yj>y)):
            den=yj-yi
            if den and x < (xj-xi)*(y-yi)/den+xi: inside=not inside
        j=i
    return inside
def point_in_poly(x,y,outer,holes):
    if not point_in_ring(x,y,outer): return False
    return not any(point_in_ring(x,y,h) for h in holes)
def to_geojson(polys,transformer):
    converted=[]
    for outer,holes in polys:
        rings=[]
        for ring in [outer]+holes:
            rr=[]
            for x,y in ring:
                lon,lat=transformer.transform(x,y)
                rr.append([round(float(lon),7),round(float(lat),7)])
            if rr and rr[0]!=rr[-1]: rr.append(rr[0])
            rings.append(rr)
        converted.append(rings)
    return {'type':'Polygon','coordinates':converted[0]} if len(converted)==1 else {'type':'MultiPolygon','coordinates':converted}
def validate_record(f):
    p=f.get('properties') or {}; reasons=[]
    if (f.get('geometry') or {}).get('type') not in ('Polygon','MultiPolygon'): reasons.append('geometry_not_polygon_or_multipolygon')
    if p.get('evidence_scope')!='parcel': reasons.append('evidence_scope_not_parcel')
    for k in REQUIRED:
        if k not in p or p[k] is None or p[k]=='' or (k=='field_evidence' and not isinstance(p[k],dict)):
            reasons.append('missing_'+k)
    for k in FORBIDDEN:
        if k in p: reasons.append('forbidden_'+k)
    c=p.get('confidence_score_0_100')
    if not isinstance(c,(int,float)) or isinstance(c,bool) or c<0 or c>100: reasons.append('confidence_score_out_of_range')
    return reasons
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    result={'schema_version':6,'slot_id':SLOT_ID,'owner':None,'partition':PARTITION,'lineage_id':LINEAGE_ID,'generated_at_utc':now(),'source_window_id':SOURCE_WINDOW,'first_missing_criterion':'CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED','accepted_count_claimed':0,'final_package_written':False,'fake_data':False}
    rehash=verify_previous_zip(); result['previous_package_physical_rehash']=rehash
    if not rehash.get('verified'):
        result.update(status='BLOCKED',blocker='PREVIOUS_PACKAGE_PHYSICAL_REHASH_FAILED',rows=[],candidate_ready_count=0); save(result); return 2
    cp,mat=materialize_canonical(); result['canonical_materialization']=mat
    if not cp:
        result.update(status='BLOCKED',blocker='CANONICAL_BLOB_MATERIALIZATION_FAILED',rows=[],candidate_ready_count=0); save(result); return 2
    cg=json.loads(cp.read_text(encoding='utf-8-sig'))
    points={}
    for f in cg.get('features',[]):
        p=f.get('properties') or {}
        pid=p.get('security_parcel_id') or p.get('parcel_id')
        if pid in TARGET_IDS and (f.get('geometry') or {}).get('type')=='Point':
            points[pid]=f['geometry']['coordinates'][:2]
    if len(points)!=len(TARGET_IDS):
        result.update(status='BLOCKED',blocker='TARGET_CANONICAL_POINTS_MISSING',target_points=points,rows=[],candidate_ready_count=0); save(result); return 2
    mps={}
    if PRIOR_MPS_RECORDS.is_file():
        pg=json.loads(PRIOR_MPS_RECORDS.read_text(encoding='utf-8-sig'))
        for f in pg.get('features',[]):
            p=f.get('properties') or {}
            pid=p.get('parcel_id')
            if pid in TARGET_IDS: mps[pid]=p
    try:
        st,page,hdr=http_bytes(INSPIRE_PAGE,120)
        result['source_catalog']={'url':INSPIRE_PAGE,'http_status':st,'sha256':sha256_bytes(page),'published_window':'2026-09-06','official':True,'public_no_login':True}
        gml_url=find_lambeth_gml(page)
        if st!=200 or not gml_url: raise RuntimeError('LAMBETH_GML_LINK_NOT_FOUND')
        result['source_catalog']['lambeth_gml_url']=gml_url
        gs,gb,gh=http_bytes(gml_url,180)
        if gs!=200: raise RuntimeError('LAMBETH_GML_HTTP_'+str(gs))
        tmp=Path(tempfile.gettempdir())/'aays_sps5'/'hmlr_inspire_lambeth_2026_09.gml'
        tmp.parent.mkdir(parents=True,exist_ok=True); tmp.write_bytes(gb)
        result['source_gml']={'url':gml_url,'http_status':gs,'sha256':sha256_bytes(gb),'size_bytes':len(gb),'content_type':gh.get('Content-Type')}
    except Exception as e:
        result.update(status='BLOCKED',blocker='HMLR_INSPIRE_SOURCE_DOWNLOAD_FAILED',error=str(e),rows=[],candidate_ready_count=0); save(result); return 2
    try:
        pyproj=ensure_pyproj()
        root=ET.fromstring(gb)
        crs=source_crs(root); result['source_gml']['crs']=crs
        to_src=pyproj.Transformer.from_crs('EPSG:4326',crs,always_xy=True)
        to_wgs=pyproj.Transformer.from_crs(crs,'EPSG:4326',always_xy=True)
        feats=[]
        for f in feature_members(root):
            polys=extract_polygons(f)
            if not polys: continue
            fid,basis=feature_id(f)
            if not fid: continue
            bbs=[]
            for outer,holes in polys:
                xs=[p[0] for p in outer]; ys=[p[1] for p in outer]
                bbs.append((min(xs),min(ys),max(xs),max(ys)))
            feats.append({'id':fid,'id_basis':basis,'label':text_first(f,['label','name']),'polys':polys,'bbs':bbs})
        result['source_gml']['feature_count_with_polygon_and_id']=len(feats)
    except Exception as e:
        result.update(status='BLOCKED',blocker='HMLR_INSPIRE_GML_PARSE_FAILED',error=str(e),rows=[],candidate_ready_count=0); save(result); return 2
    rows=[]; proposed=[]
    for idx,pid in enumerate(TARGET_IDS,1):
        lon,lat=map(float,points[pid]); sx,sy=to_src.transform(lon,lat)
        hits=[]
        for fe in feats:
            hit=False
            for (outer,holes),bb in zip(fe['polys'],fe['bbs']):
                if bb[0]<=sx<=bb[2] and bb[1]<=sy<=bb[3] and point_in_poly(sx,sy,outer,holes):
                    hit=True; break
            if hit: hits.append(fe)
        unique={h['id']:h for h in hits}
        reasons=[]; chosen=None
        if len(unique)==1: chosen=next(iter(unique.values()))
        elif len(unique)==0: reasons.append('hmlr_inspire_unique_polygon_required:found=0')
        else: reasons.append('hmlr_inspire_unique_polygon_required:found='+str(len(unique)))
        prior=mps.get(pid)
        field_ok=prior is not None and bool(prior.get('official_lsoa_identifier_evidence')) and bool(prior.get('field_evidence_gate'))
        if not field_ok: reasons.append('security_field_evidence_required')
        feature=None; val=[]
        if chosen and field_ok:
            geom=to_geojson(chosen['polys'],to_wgs)
            lsoa=prior.get('canonical_lsoa_code')
            field={
                'security_source':prior.get('official_source'),
                'official_csv_url':prior.get('official_csv_url'),
                'official_csv_sha256':prior.get('official_csv_sha256'),
                'lsoa_code':lsoa,
                'official_lsoa_row_count':prior.get('official_lsoa_row_count'),
                'official_crime_value_sum':prior.get('official_crime_value_sum'),
                'official_numeric_cells':prior.get('official_numeric_cells')
            }
            props={
                'evidence_scope':'parcel',
                'coverage_area_id':lsoa,
                'source_resolution':'official_MPS_LSOA_recorded_crime_joined_to_HMLR_INSPIRE_freehold_index_polygon',
                'time_window':'MPS_most_recent_24_months_as_hashed_2026-09-28',
                'source_url':prior.get('official_csv_url'),
                'measurement_date':'2026-09-28',
                'measurement_method':'official_MPS_LSOA_CSV_exact_identifier_join',
                'spatial_binding_method':'canonical_partition_point_intersects_HMLR_INSPIRE_polygon',
                'confidence_score_0_100':100,
                'evidence_grade':'A',
                'field_evidence':field,
                'canonical_parcel_id':'hmlr-inspire:'+chosen['id'],
                'canonical_parcel_reference':chosen['id'],
                'canonical_geometry_source_url':result['source_gml']['url'],
                'canonical_geometry_provider':'HM Land Registry',
                'canonical_geometry_dataset':'INSPIRE Index Polygons',
                'canonical_geometry_source_sha256':result['source_gml']['sha256'],
                'partition_record_id':pid,
                'source_window_id':SOURCE_WINDOW,
                'cursor':f'{SOURCE_WINDOW}:record={idx}'
            }
            feature={'type':'Feature','id':'hmlr-inspire:'+chosen['id'],'geometry':geom,'properties':props}
            val=validate_record(feature)
            if val: reasons.extend(['semantic_precheck:'+x for x in val])
            else: proposed.append(feature)
        rows.append({
            'record_index':idx,'partition_record_id':pid,'canonical_point':{'type':'Point','coordinates':[lon,lat]},
            'hmlr_hit_count':len(unique),'hmlr_candidate_ids':sorted(unique.keys())[:20],
            'selected_hmlr_inspire_id':chosen['id'] if chosen else None,
            'selected_id_basis':chosen['id_basis'] if chosen else None,
            'security_field_evidence_reused':field_ok,'candidate_ready':feature is not None and not val,
            'reasons':reasons,'cursor':f'{SOURCE_WINDOW}:record={idx}'
        })
    invalid=[]
    for i,f in enumerate(proposed):
        rr=validate_record(f)
        if rr: invalid.append({'index':i,'id':f.get('id'),'reasons':rr})
    unresolved_canonical=[r for r in rows if not r['selected_hmlr_inspire_id']]
    field_missing=[r for r in rows if r['selected_hmlr_inspire_id'] and not r['security_field_evidence_reused']]
    nextcrit='CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED' if unresolved_canonical else ('SECURITY_FIELD_EVIDENCE_REQUIRED' if field_missing else 'LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED')
    result.update(
        status='HMLR_INSPIRE_CANONICAL_RESOLUTION_EXECUTED',
        canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,
        processed_count=len(rows),candidate_ready_count=len(proposed),semantic_precheck_invalid_count=len(invalid),
        semantic_precheck_invalid=invalid,proposed_records={'type':'FeatureCollection','features':proposed},
        rows=rows,official_source_cursor=f'{SOURCE_WINDOW}:record={len(rows)}',
        first_missing_criterion=nextcrit,
        accepted_count_claimed=0,
        next_step='Package writer may accept only semantic-precheck-valid proposed_records; remaining rows stay rejection ledger.'
    )
    save(result)
    print('PREVIOUS_PACKAGE_REHASH='+str(rehash['verified']))
    print('GML_URL='+result['source_gml']['url'])
    print('GML_SHA256='+result['source_gml']['sha256'])
    print('GML_FEATURES='+str(result['source_gml']['feature_count_with_polygon_and_id']))
    print('PROCESSED='+str(len(rows)))
    print('CANDIDATE_READY='+str(len(proposed)))
    print('SEMANTIC_INVALID='+str(len(invalid)))
    print('FIRST_MISSING='+nextcrit)
    print('OUTPUT='+str(OUT))
    return 0 if rehash['verified'] and not invalid else 2
if __name__=='__main__': raise SystemExit(main())
