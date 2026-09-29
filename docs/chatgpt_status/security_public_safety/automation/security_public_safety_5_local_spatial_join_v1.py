from __future__ import annotations
import copy, hashlib, html, json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
P0,P1,PC=61524,76903,15380
START_NUM=61674
MAX_RECORDS=50
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
CANON_BRANCH="codex/aays-single-runner-v5-20260706"
CANON_REL="england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
CANON_BLOB="bb48164e7a0af78df875f30421a6a3068c43edb8"
PRIOR_RECORDS=REPO/"incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/planning_data_title_boundary_mps_lsoa_61624_61673_20260928T221705Z/records.geojson"
PRIOR_MPS_SHA="255d63bd759f08d7b0dd7674a38fca25ccb824c6c3a5d75d3fb00e504a34c082"
DOWNLOAD_PAGE="https://use-land-property-data.service.gov.uk/datasets/inspire/download"
SOURCE_WINDOW="hmlr_inspire_lambeth_2026_09_sps5_61674_61723_v1"
UA="AAYS-security-public-safety-5/hmlr-inspire-v1"

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def git(args,timeout=900,stdout=None):
    return subprocess.run(["git","-C",str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(["hash-object",str(path)],180)
    return r.stdout.decode("utf-8","replace").strip() if r.returncode==0 else None
def materialize():
    cache=Path(tempfile.gettempdir())/"aays_sps5"/Path(CANON_REL).name
    cache.parent.mkdir(parents=True,exist_ok=True)
    ev={"branch":CANON_BRANCH,"repo_path":CANON_REL,"required_git_blob_sha":CANON_BLOB,"cache_path":str(cache),"verified":False}
    if cache.is_file() and blob_sha(cache)==CANON_BLOB:
        ev.update(cache_hit=True,verified=True); return cache,ev
    cache.unlink(missing_ok=True)
    for ref in (f"origin/{CANON_BRANCH}",CANON_BRANCH):
        part=cache.with_suffix(".part"); part.unlink(missing_ok=True)
        with part.open("wb") as fh: r=git(["show",f"{ref}:{CANON_REL}"],stdout=fh)
        ev.setdefault("attempts",[]).append({"ref":ref,"returncode":r.returncode,"stderr":r.stderr.decode("utf-8","replace")[-1000:]})
        if r.returncode==0 and blob_sha(part)==CANON_BLOB:
            os.replace(part,cache); ev.update(source_ref=ref,verified=True); return cache,ev
        part.unlink(missing_ok=True)
    r=git(["fetch","origin",CANON_BRANCH],900); ev["fetch_returncode"]=r.returncode; ev["fetch_stderr"]=r.stderr.decode("utf-8","replace")[-2000:]
    if r.returncode==0:
        part=cache.with_suffix(".part")
        with part.open("wb") as fh: s=git(["show",f"FETCH_HEAD:{CANON_REL}"],stdout=fh)
        if s.returncode==0 and blob_sha(part)==CANON_BLOB:
            os.replace(part,cache); ev.update(source_ref="FETCH_HEAD",verified=True); return cache,ev
        part.unlink(missing_ok=True)
    ev["error"]="EXACT_CANONICAL_BLOB_NOT_MATERIALIZED"; return None,ev

def pid_num(pid):
    try: return int(pid.split("_",1)[1]) if isinstance(pid,str) and pid.startswith("parcel_") else None
    except: return None
def get_pid(props):
    for k in ("security_parcel_id","parcel_id"):
        v=props.get(k)
        if isinstance(v,str) and v.startswith("parcel_"): return v
    return None
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def http_bytes(url,timeout=120):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        return int(resp.status),resp.geturl(),resp.read(),dict(resp.headers)

def find_lambeth_gml(page_bytes,base_url):
    txt=page_bytes.decode("utf-8","replace")
    patterns=[
        r"London Borough of Lambeth.{0,1500}?href=[\"']([^\"']+)[\"'][^>]*>[^<]*Download",
        r"href=[\"']([^\"']+)[\"'][^>]*>[^<]*Download[^<]*</a>.{0,1500}?London Borough of Lambeth"
    ]
    for pat in patterns:
        m=re.search(pat,txt,re.I|re.S)
        if m:
            return urllib.parse.urljoin(base_url,html.unescape(m.group(1)))
    pos=txt.lower().find("london borough of lambeth")
    if pos>=0:
        chunk=txt[max(0,pos-1800):pos+1800]
        hrefs=re.findall(r'href=[\"\\']([^\"\\']+)[\"\\']',chunk,re.I)
        for h in hrefs:
            if "gml" in h.lower() or "download" in h.lower():
                return urllib.parse.urljoin(base_url,html.unescape(h))
    raise RuntimeError("LAMBETH_GML_LINK_NOT_FOUND")

def ensure_pyproj():
    try:
        from pyproj import Transformer
        return Transformer
    except Exception:
        r=subprocess.run([sys.executable,"-m","pip","install","--quiet","pyproj==3.7.2"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
        if r.returncode!=0: raise RuntimeError("PYPROJ_INSTALL_FAILED:"+r.stderr.decode("utf-8","replace")[-1500:])
        from pyproj import Transformer
        return Transformer

def local(tag): return tag.rsplit("}",1)[-1] if "}" in tag else tag
def first_text(el,names):
    names={x.lower() for x in names}
    for x in el.iter():
        if local(x.tag).lower() in names and x.text and x.text.strip():
            return x.text.strip()
    return None
def parse_num_pairs(text):
    vals=[float(x) for x in re.split(r"[\s,]+",(text or "").strip()) if x]
    return [(vals[i],vals[i+1]) for i in range(0,len(vals)-1,2)]
def ring_from_container(container,transformer):
    pos=None
    for x in container.iter():
        if local(x.tag) in ("posList","coordinates") and x.text and x.text.strip():
            pos=x.text; break
    if not pos: return []
    pts=parse_num_pairs(pos)
    out=[]
    for e,n in pts:
        lon,lat=transformer.transform(e,n)
        out.append([round(float(lon),8),round(float(lat),8)])
    if out and out[0]!=out[-1]: out.append(out[0])
    return out
def polygons_from_feature(feat,transformer):
    polys=[]
    for poly in [x for x in feat.iter() if local(x.tag)=="Polygon"]:
        outer=None; holes=[]
        for x in poly.iter():
            if local(x.tag)=="exterior":
                rr=ring_from_container(x,transformer)
                if len(rr)>=4: outer=rr
            elif local(x.tag)=="interior":
                rr=ring_from_container(x,transformer)
                if len(rr)>=4: holes.append(rr)
        if outer: polys.append([outer,*holes])
    return polys
def point_in_ring(x,y,ring):
    inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i][0],ring[i][1]; xj,yj=ring[j][0],ring[j][1]
        if ((yi>y)!=(yj>y)):
            d=yj-yi
            if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
        j=i
    return inside
def point_in_poly(x,y,poly):
    if not poly or not point_in_ring(x,y,poly[0]): return False
    for h in poly[1:]:
        if point_in_ring(x,y,h): return False
    return True
def geom_contains(geom,x,y):
    if geom["type"]=="Polygon": return point_in_poly(x,y,geom["coordinates"])
    if geom["type"]=="MultiPolygon": return any(point_in_poly(x,y,p) for p in geom["coordinates"])
    return False
def bbox_of_geom(geom):
    pts=[]
    if geom["type"]=="Polygon":
        for r in geom["coordinates"]: pts.extend(r)
    elif geom["type"]=="MultiPolygon":
        for p in geom["coordinates"]:
            for r in p: pts.extend(r)
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return (min(xs),min(ys),max(xs),max(ys))
def bbox_hit(b,x,y): return b[0]<=x<=b[2] and b[1]<=y<=b[3]

REQ=["evidence_scope","coverage_area_id","source_resolution","time_window","source_url","measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100","evidence_grade","field_evidence","canonical_parcel_id"]
def semantic_check(feature):
    reasons=[]
    if (feature.get("geometry") or {}).get("type") not in ("Polygon","MultiPolygon"): reasons.append("geometry_must_be_Polygon_or_MultiPolygon")
    p=feature.get("properties") or {}
    for k in REQ:
        if k not in p or p[k] is None or p[k]=="": reasons.append("missing_required_field:"+k)
    if p.get("evidence_scope")!="parcel": reasons.append("evidence_scope_must_equal_parcel")
    if "parcel_id" in p: reasons.append("forbidden_property:parcel_id")
    if "accepted_parcel" in p: reasons.append("forbidden_property:accepted_parcel")
    c=p.get("confidence_score_0_100")
    if not isinstance(c,(int,float)) or isinstance(c,bool) or c<0 or c>100: reasons.append("confidence_score_0_100_out_of_range")
    return reasons

def main():
    base={"schema_version":8,"slot_id":SLOT_ID,"owner":None,"partition":{"start":P0,"end":P1,"count":PC},"lineage_id":LINEAGE_ID,
          "generated_at":now(),"first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED","source_window_id":SOURCE_WINDOW,
          "max_official_source_records":MAX_RECORDS,"accepted_count_claimed":0,"final_package_written":False,"fake_data":False,
          "db_write":False,"migration":False,"production_deploy":False}
    cp,mat=materialize(); base["canonical_materialization"]=mat
    if not cp:
        base.update(status="BLOCKED",blocker="CANONICAL_POINT_BLOB_MATERIALIZATION_FAILED",candidate_ready_count=0,rows=[]); save(base); return 2
    if not PRIOR_RECORDS.is_file():
        base.update(status="BLOCKED",blocker="PRIOR_SCHEMA_VALID_FIELD_EVIDENCE_READBACK_MISSING",candidate_ready_count=0,rows=[]); save(base); return 2
    prior=json.loads(PRIOR_RECORDS.read_text(encoding="utf-8-sig"))
    evidence_by_lsoa={}
    templates_by_lsoa={}
    for f in prior.get("features",[]):
        p=f.get("properties") or {}; lsoa=p.get("canonical_lsoa_code")
        if lsoa and isinstance(p.get("field_evidence"),dict) and p["field_evidence"].get("official_csv_sha256")==PRIOR_MPS_SHA:
            evidence_by_lsoa[lsoa]=copy.deepcopy(p["field_evidence"]); templates_by_lsoa[lsoa]=p
    cg=json.loads(cp.read_text(encoding="utf-8-sig"))
    selected=[]
    for f in cg.get("features",[]):
        if not isinstance(f,dict): continue
        props=f.get("properties") or {}; pid=get_pid(props); n=pid_num(pid)
        g=f.get("geometry") or {}
        if n is None or n<START_NUM or n>START_NUM+MAX_RECORDS-1 or g.get("type")!="Point": continue
        xy=g.get("coordinates") or []
        if len(xy)<2: continue
        selected.append((n,pid,float(xy[0]),float(xy[1]),props))
    selected.sort(key=lambda x:x[0])
    if len(selected)!=MAX_RECORDS:
        base.update(status="BLOCKED",blocker="EXPECTED_50_CANONICAL_POINTS_NOT_FOUND",found=len(selected),rows=[]); save(base); return 2

    try:
        page_status,page_final,page_bytes,page_headers=http_bytes(DOWNLOAD_PAGE,120)
        gml_url=find_lambeth_gml(page_bytes,page_final)
        gml_status,gml_final,gml_bytes,gml_headers=http_bytes(gml_url,180)
    except Exception as ex:
        base.update(status="BLOCKED",blocker="HMLR_INSPIRE_LAMBETH_DOWNLOAD_FAILED",error=str(ex),rows=[]); save(base); return 2
    base["source_download"]={"listing_url":DOWNLOAD_PAGE,"listing_http_status":page_status,"listing_sha256":hashlib.sha256(page_bytes).hexdigest(),
        "gml_url":gml_final,"gml_http_status":gml_status,"gml_sha256":hashlib.sha256(gml_bytes).hexdigest(),"gml_size_bytes":len(gml_bytes)}
    if page_status!=200 or gml_status!=200:
        base.update(status="BLOCKED",blocker="HMLR_INSPIRE_HTTP_STATUS_NOT_200",rows=[]); save(base); return 2

    try:
        Transformer=ensure_pyproj()
        transformer=Transformer.from_crs("EPSG:27700","EPSG:4326",always_xy=True)
        root=ET.fromstring(gml_bytes)
    except Exception as ex:
        base.update(status="BLOCKED",blocker="HMLR_INSPIRE_GML_PARSE_OR_TRANSFORM_FAILED",error=str(ex),rows=[]); save(base); return 2

    features=[]
    seen=set()
    candidates=[]
    for fm in [x for x in root.iter() if local(x.tag) in ("featureMember","member")]:
        kids=list(fm)
        if not kids: continue
        feat=kids[0]
        inspire=first_text(feat,["INSPIREID","INSPIRE_ID","inspireId","inspireID"])
        if not inspire or inspire in seen: continue
        polys=polygons_from_feature(feat,transformer)
        if not polys: continue
        seen.add(inspire)
        geom={"type":"Polygon","coordinates":polys[0]} if len(polys)==1 else {"type":"MultiPolygon","coordinates":polys}
        b=bbox_of_geom(geom)
        candidates.append((inspire,geom,b))
    base["source_download"]["parsed_inspire_polygon_count"]=len(candidates)
    if not candidates:
        base.update(status="BLOCKED",blocker="NO_HMLR_INSPIRE_POLYGONS_PARSED",rows=[]); save(base); return 2

    rows=[]
    for idx,(n,pid,lon,lat,props) in enumerate(selected,1):
        reasons=[]; lsoa=props.get("security_lsoa_code")
        if not lsoa: reasons.append("canonical_security_lsoa_code_missing")
        prior_ev=evidence_by_lsoa.get(lsoa)
        tmpl=templates_by_lsoa.get(lsoa)
        if not prior_ev or not tmpl: reasons.append("prior_mps_field_evidence_missing_for_lsoa")
        hits=[]
        for inspire,geom,b in candidates:
            if bbox_hit(b,lon,lat) and geom_contains(geom,lon,lat): hits.append((inspire,geom))
        if len(hits)!=1: reasons.append(f"hmlr_inspire_unique_polygon_required:found={len(hits)}")
        feature=None
        if not reasons:
            inspire,geom=hits[0]
            fe=copy.deepcopy(prior_ev)
            fe.update({"hmlr_inspire_id":inspire,"hmlr_inspire_gml_url":gml_final,"hmlr_inspire_gml_sha256":base["source_download"]["gml_sha256"],
                       "hmlr_inspire_listing_sha256":base["source_download"]["listing_sha256"]})
            p={
              "evidence_scope":"parcel",
              "coverage_area_id":lsoa,
              "source_resolution":"official_MPS_LSOA_recorded_crime_joined_to_HMLR_INSPIRE_polygon",
              "time_window":tmpl.get("time_window"),
              "source_url":tmpl.get("source_url"),
              "measurement_date":tmpl.get("measurement_date"),
              "measurement_method":tmpl.get("measurement_method"),
              "spatial_binding_method":"shared_canonical_point_intersects_HMLR_INSPIRE_polygon",
              "confidence_score_0_100":100,
              "evidence_grade":"A",
              "field_evidence":fe,
              "canonical_parcel_id":"hmlr-inspire:"+str(inspire),
              "canonical_parcel_reference":str(inspire),
              "partition_record_id":pid,
              "canonical_lsoa_code":lsoa,
              "canonical_geometry_source_url":gml_final,
              "canonical_geometry_provider":"HM Land Registry",
              "canonical_geometry_dataset":"INSPIRE Index Polygons",
              "source_window_id":SOURCE_WINDOW,
              "cursor":f"{SOURCE_WINDOW}:record={idx}"
            }
            feature={"type":"Feature","id":p["canonical_parcel_id"],"geometry":geom,"properties":p}
            reasons.extend(semantic_check(feature))
        rows.append({"record_index":idx,"partition_record_id":pid,"parcel_number":n,"canonical_point":{"type":"Point","coordinates":[lon,lat]},
                     "canonical_lsoa_code":lsoa,"candidate_ready":bool(feature and not reasons),"reasons":reasons,"feature":feature})
    ready=sum(1 for r in rows if r["candidate_ready"])
    rejected=len(rows)-ready
    base.update(status="SEMANTIC_PRECHECK_COMPLETE",canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,
                source_records_processed_count=len(rows),candidate_ready_count=ready,rejected_count=rejected,
                semantic_precheck_passed=all(not semantic_check(r["feature"]) for r in rows if r["feature"]),
                official_source_cursor=f"{SOURCE_WINDOW}:record={len(rows)}",rows=rows,
                note="Only candidate_ready features satisfy Polygon/MultiPolygon + canonical_parcel_id + mandatory evidence fields. Rejected rows must not be accepted.")
    save(base)
    print(json.dumps({"status":base["status"],"ready":ready,"rejected":rejected,"gml_sha256":base["source_download"]["gml_sha256"],"output":str(OUT)}))
    return 0
if __name__=="__main__": raise SystemExit(main())
