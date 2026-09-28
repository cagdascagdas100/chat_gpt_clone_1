from __future__ import annotations
import hashlib, json, os, subprocess, sys, tempfile, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime, timezone

SLOT_ID='security_public_safety_5'
LINEAGE_ID='86b5e932de484ad26133fa8c'
P0,P1=61524,76903
START,END=61624,61673
MAX_RECORDS=50
REPO=Path(os.environ.get('AAYS_REPO_ROOT') or Path(__file__).resolve().parents[4])
OUT=REPO/'docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json'
POINT_BRANCH='codex/aays-single-runner-v5-20260706'
POINT_REL='england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
POINT_BLOB='bb48164e7a0af78df875f30421a6a3068c43edb8'
FIELD_EVIDENCE=REPO/'incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/mps_lsoa_recorded_crime_202108_202307_61624_61673_20260928T085212Z/evidence/mps_lsoa_recorded_crime_202108_202307.json'
DOWNLOAD_PAGE='https://use-land-property-data.service.gov.uk/datasets/inspire/download'
SOURCE_WINDOW='hmlr_inspire_index_polygons_2026_09_lambeth_sps5_61624_61673_v1'
LOCAL_AUTHORITY='London Borough of Lambeth'

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def git(args,timeout=900,stdout=None):
    return subprocess.run(['git','-C',str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(['hash-object',str(path)],180)
    return r.stdout.decode('utf-8','replace').strip() if r.returncode==0 else None
def materialize_point_source():
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
    r=git(['fetch','origin',POINT_BRANCH],900)
    ev['fetch_returncode']=r.returncode
    if r.returncode==0:
        part=cache.with_suffix('.part')
        with part.open('wb') as fh: s=git(['show',f'FETCH_HEAD:{POINT_REL}'],stdout=fh)
        if s.returncode==0 and blob_sha(part)==POINT_BLOB:
            os.replace(part,cache); ev.update(source_ref='FETCH_HEAD',verified=True); return cache,ev
        part.unlink(missing_ok=True)
    ev['error']='EXACT_POINT_SOURCE_NOT_MATERIALIZED'; return None,ev

class RowParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_tr=False; self.rows=[]; self.texts=[]; self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='tr':
            self.in_tr=True; self.texts=[]; self.hrefs=[]
        if self.in_tr and tag.lower()=='a':
            d=dict(attrs); h=d.get('href')
            if h: self.hrefs.append(h)
    def handle_data(self,data):
        if self.in_tr and data.strip(): self.texts.append(data.strip())
    def handle_endtag(self,tag):
        if tag.lower()=='tr' and self.in_tr:
            self.rows.append((' '.join(self.texts),list(self.hrefs))); self.in_tr=False
def fetch_bytes(url,timeout=120):
    tmp=Path(tempfile.mkstemp(prefix='aays_hmlr_',suffix='.bin')[1])
    meta=tmp.with_suffix('.meta')
    cmd=['curl','-fL','--max-redirs','20','--retry','2','--retry-delay','1','--compressed','-A','Mozilla/5.0 AAYS-security-public-safety-5','-o',str(tmp),'-w','%{http_code}\\n%{url_effective}',url]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
    if p.returncode!=0:
        raise RuntimeError('curl_failed:'+str(p.returncode)+':'+p.stderr.decode('utf-8','replace')[-2000:])
    out=p.stdout.decode('utf-8','replace').splitlines()
    status=int(out[0]) if out and out[0].isdigit() else 0
    final=out[1].strip() if len(out)>1 else url
    data=tmp.read_bytes()
    tmp.unlink(missing_ok=True)
    return status,data,final
def find_lambeth_link(html_bytes,base):
    p=RowParser(); p.feed(html_bytes.decode('utf-8','replace'))
    for text,hrefs in p.rows:
        if LOCAL_AUTHORITY.lower() in text.lower():
            for h in hrefs:
                if '.gml' in h.lower() or 'download' in h.lower():
                    return urllib.parse.urljoin(base,h),text
    # fallback: local text window around authority
    s=html_bytes.decode('utf-8','replace')
    i=s.lower().find(LOCAL_AUTHORITY.lower())
    if i>=0:
        win=s[max(0,i-2000):i+3000]
        import re
        m=re.search(r"href=[\"']([^\"']+\\.gml[^\"']*)",win,re.I)
        if m: return urllib.parse.urljoin(base,m.group(1)),LOCAL_AUTHORITY
    return None,None

def ensure_pyproj():
    try:
        import pyproj
        return pyproj
    except Exception:
        subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','pyproj'],check=True,timeout=300)
        import pyproj
        return pyproj

def lname(tag): return tag.rsplit('}',1)[-1].upper()
def text_desc(el,names):
    names={n.upper() for n in names}
    for x in el.iter():
        if lname(x.tag) in names and x.text and x.text.strip():
            return x.text.strip()
    return None
def parse_poslist(txt):
    vals=[float(v) for v in (txt or '').replace('\n',' ').split()]
    return [(vals[i],vals[i+1]) for i in range(0,len(vals)-1,2)]
def rings_from_polygon(poly):
    outer=None; holes=[]
    for x in poly.iter():
        ln=lname(x.tag)
        if ln in ('EXTERIOR','OUTERBOUNDARYIS'):
            pos=text_desc(x,['posList'])
            r=parse_poslist(pos)
            if len(r)>=4: outer=r
        elif ln in ('INTERIOR','INNERBOUNDARYIS'):
            pos=text_desc(x,['posList'])
            r=parse_poslist(pos)
            if len(r)>=4: holes.append(r)
    if outer is None:
        poss=[x for x in poly.iter() if lname(x.tag)=='POSLIST' and x.text]
        if poss:
            r=parse_poslist(poss[0].text)
            if len(r)>=4: outer=r
            for p in poss[1:]:
                h=parse_poslist(p.text)
                if len(h)>=4: holes.append(h)
    return outer,holes
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
    if not outer or not point_in_ring(x,y,outer): return False
    return not any(point_in_ring(x,y,h) for h in holes)
def feature_candidates(root):
    seen=set()
    for el in root.iter():
        inspire=text_desc(el,['INSPIREID','INSPIRE_ID'])
        if not inspire: continue
        polys=[p for p in el.iter() if lname(p.tag) in ('POLYGON','POLYGONPATCH')]
        if not polys: continue
        key=(inspire,id(el))
        if key in seen: continue
        seen.add(key)
        yield el,inspire,polys

def geom4326(polys,tr):
    out=[]
    for poly in polys:
        outer,holes=rings_from_polygon(poly)
        if not outer: continue
        def cv(r): return [[round(tr.transform(x,y)[0],8),round(tr.transform(x,y)[1],8)] for x,y in r]
        rings=[cv(outer)]+[cv(h) for h in holes]
        out.append(rings)
    if not out: return None
    return {'type':'Polygon','coordinates':out[0]} if len(out)==1 else {'type':'MultiPolygon','coordinates':out}

def valid_record(f):
    g=f.get('geometry') or {}; p=f.get('properties') or {}
    req=['evidence_scope','coverage_area_id','source_resolution','time_window','source_url','measurement_date','measurement_method','spatial_binding_method','confidence_score_0_100','evidence_grade','field_evidence','canonical_parcel_id']
    reasons=[]
    if g.get('type') not in ('Polygon','MultiPolygon'): reasons.append('geometry_not_polygon_or_multipolygon')
    for k in req:
        if p.get(k) in (None,'',[]): reasons.append('missing_'+k)
    if p.get('evidence_scope')!='parcel': reasons.append('evidence_scope_not_parcel')
    return reasons

def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    base={'schema_version':5,'slot_id':SLOT_ID,'owner':None,'partition':[P0,P1],'lineage_id':LINEAGE_ID,'generated_at':now(),'source_window_id':SOURCE_WINDOW,'max_records':MAX_RECORDS,'first_missing_criterion':'CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED','accepted_count_claimed':0,'final_package_written':False,'fake_data':False}
    point_path,mat=materialize_point_source(); base['point_source_materialization']=mat
    if not point_path:
        base.update(status='BLOCKED',blocker='CANONICAL_POINT_SOURCE_MATERIALIZATION_FAILED',records=[],rejections=[]);save(base);return 2
    point_geo=json.loads(point_path.read_text(encoding='utf-8-sig'))
    points={}
    for f in point_geo.get('features',[]):
        props=f.get('properties') or {}
        pid=props.get('security_parcel_id') or props.get('parcel_id')
        if not isinstance(pid,str) or not pid.startswith('parcel_'): continue
        try:n=int(pid.split('_',1)[1])
        except:continue
        g=f.get('geometry') or {}
        if START<=n<=END and g.get('type')=='Point':
            points[pid]={'n':n,'coord':g.get('coordinates'),'props':props}
    if len(points)!=50:
        base.update(status='BLOCKED',blocker='FIXED_50_POINT_LOCATORS_NOT_FOUND',point_locator_count=len(points),records=[],rejections=[]);save(base);return 2
    fe=json.loads(FIELD_EVIDENCE.read_text(encoding='utf-8'))
    fmap={r['parcel_id']:r for r in fe.get('accepted_records',[]) if r.get('parcel_id')}
    base['prior_field_evidence']={'path':str(FIELD_EVIDENCE.relative_to(REPO)).replace('\\','/'),'source_url':fe.get('source_url'),'source_sha256':fe.get('source_sha256'),'time_window':f"{fe.get('observed_header_period',{}).get('first_month')}-{fe.get('observed_header_period',{}).get('last_month')}",'accepted_alias_count':len(fmap)}
    st,page,final_page=fetch_bytes(DOWNLOAD_PAGE)
    base['hmlr_download_page']={'url':final_page,'http_status':st,'sha256':hashlib.sha256(page).hexdigest(),'size_bytes':len(page)}
    link,rowtext=find_lambeth_link(page,final_page)
    if not link:
        base.update(status='BLOCKED',blocker='HMLR_LAMBETH_GML_LINK_NOT_FOUND',records=[],rejections=[]);save(base);return 2
    st2,gml,gml_url=fetch_bytes(link,180)
    base['hmlr_gml']={'url':gml_url,'http_status':st2,'sha256':hashlib.sha256(gml).hexdigest(),'size_bytes':len(gml),'local_authority':LOCAL_AUTHORITY,'listing_row':rowtext}
    if st2!=200:
        base.update(status='BLOCKED',blocker='HMLR_GML_DOWNLOAD_FAILED',records=[],rejections=[]);save(base);return 2
    pyproj=ensure_pyproj()
    to_bng=pyproj.Transformer.from_crs('EPSG:4326','EPSG:27700',always_xy=True)
    to_wgs=pyproj.Transformer.from_crs('EPSG:27700','EPSG:4326',always_xy=True)
    root=ET.fromstring(gml)
    features=[]
    for el,inspire,polys in feature_candidates(root):
        nat=text_desc(el,['NATIONALCADASTRALREFERENCE'])
        label=text_desc(el,['LABEL'])
        parsed=[]
        for p in polys:
            outer,holes=rings_from_polygon(p)
            if outer:
                xs=[x for x,y in outer];ys=[y for x,y in outer]
                parsed.append((outer,holes,(min(xs),min(ys),max(xs),max(ys))))
        if parsed: features.append({'inspire':inspire,'national_ref':nat,'label':label,'polys':parsed,'xml_polys':polys})
    base['hmlr_gml']['parsed_feature_count']=len(features)
    candidates=[]; rejections=[]
    used_ids=set()
    for pid in sorted(points,key=lambda x:points[x]['n']):
        p=points[pid]; lng,lat=p['coord']; x,y=to_bng.transform(float(lng),float(lat))
        hits=[]
        for hf in features:
            matched=False
            for outer,holes,b in hf['polys']:
                if b[0]<=x<=b[2] and b[1]<=y<=b[3] and point_in_poly(x,y,outer,holes):
                    matched=True;break
            if matched:hits.append(hf)
        field=fmap.get(pid)
        if not field:
            rejections.append({'parcel_alias':pid,'reason':'missing_prior_official_field_evidence'});continue
        if len(hits)!=1:
            rejections.append({'parcel_alias':pid,'reason':'hmlr_polygon_match_count_not_one','match_count':len(hits)});continue
        h=hits[0]; cid=str(h['inspire']).strip()
        if cid in used_ids:
            rejections.append({'parcel_alias':pid,'reason':'duplicate_hmlr_inspire_polygon','canonical_parcel_id':cid});continue
        geometry=geom4326(h['xml_polys'],to_wgs)
        if not geometry:
            rejections.append({'parcel_alias':pid,'reason':'hmlr_geometry_conversion_failed','canonical_parcel_id':cid});continue
        prop={
          'evidence_scope':'parcel',
          'coverage_area_id':field.get('lsoa_code'),
          'source_resolution':'HMLR_INSPIRE_freehold_index_polygon_plus_MPS_LSOA_recorded_crime',
          'time_window':'202108-202307',
          'source_url':gml_url,
          'measurement_date':'2023-07',
          'measurement_method':'MPS_LSOA_recorded_crime_aggregation_with_HMLR_INSPIRE_polygon_identity',
          'spatial_binding_method':'legacy_canonical_point_within_HMLR_INSPIRE_polygon_and_prior_exact_LSOA_attribution',
          'confidence_score_0_100':95,
          'evidence_grade':'A_OFFICIAL_POLYGON_PLUS_OFFICIAL_LSOA',
          'field_evidence':{
             'publisher':'Metropolitan Police Service / Greater London Authority',
             'source_url':fe.get('source_url'),
             'source_sha256':fe.get('source_sha256'),
             'lsoa_code':field.get('lsoa_code'),
             'official_lsoa_row_count':field.get('official_lsoa_row_count'),
             'official_crime_value_sum':field.get('official_crime_value_sum'),
             'official_numeric_cells':field.get('official_numeric_cells')
          },
          'canonical_parcel_id':cid,
          'canonical_identity_source':'HM_LAND_REGISTRY_INSPIRE_ID',
          'national_cadastral_reference':h.get('national_ref'),
          'hmlr_label':h.get('label'),
          'legacy_parcel_alias':pid,
          'hmlr_gml_sha256':base['hmlr_gml']['sha256'],
          'correction_of_commit':'6342cc858dc07de5b050ec67e458b295cb0c1921',
          'program_progress_claimed':False
        }
        feat={'type':'Feature','id':cid,'geometry':geometry,'properties':prop}
        reasons=valid_record(feat)
        if reasons:
            rejections.append({'parcel_alias':pid,'canonical_parcel_id':cid,'reason':'schema_precheck_failed','details':reasons});continue
        used_ids.add(cid);candidates.append(feat)
    base['records']=candidates
    base['rejections']=rejections
    base['candidate_input_count']=50
    base['schema_valid_record_count']=len(candidates)
    base['rejection_count']=len(rejections)
    base['source_records_processed_count']=50
    base['cursor']=SOURCE_WINDOW+':record=50'
    base['precheck_all_records_valid']=all(not valid_record(f) for f in candidates)
    base['accepted_count_claimed']=0
    if not candidates:
        base.update(status='BLOCKED',blocker='PRODUCER_SCHEMA_INVALID_OR_NO_CANONICAL_POLYGON_MATCH')
        save(base);return 2
    base.update(status='SCHEMA_VALID_CORRECTION_CANDIDATES_READY',blocker=None)
    save(base)
    print('HMLR_GML_URL='+gml_url)
    print('HMLR_GML_SHA256='+base['hmlr_gml']['sha256'])
    print('HMLR_FEATURES='+str(len(features)))
    print('SCHEMA_VALID_RECORDS='+str(len(candidates)))
    print('REJECTIONS='+str(len(rejections)))
    print('OUTPUT='+str(OUT))
    return 0

if __name__=='__main__': raise SystemExit(main())
