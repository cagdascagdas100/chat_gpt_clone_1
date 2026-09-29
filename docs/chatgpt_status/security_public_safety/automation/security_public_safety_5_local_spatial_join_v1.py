from __future__ import annotations
import hashlib, html, json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
PRIOR=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_planning_data_exact_reference_61674_61723.json"
POINT_BRANCH="codex/aays-single-runner-v5-20260706"
POINT_REL="england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
POINT_BLOB="bb48164e7a0af78df875f30421a6a3068c43edb8"
DOWNLOAD_PAGE="https://use-land-property-data.service.gov.uk/datasets/inspire/download"
DATASET_PAGE="https://use-land-property-data.service.gov.uk/datasets/inspire"
LOCAL_AUTHORITY="London Borough of Lambeth"
SOURCE_WINDOW="hmlr_inspire_lambeth_current_gml_exact_ids_sps5_9_v1"
REQ_FIELDS=["evidence_scope","coverage_area_id","source_resolution","time_window","source_url","measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100","evidence_grade","field_evidence","canonical_parcel_id"]
FORBIDDEN=["parcel_id","accepted_parcel"]

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def sha256(b): return hashlib.sha256(b).hexdigest()
def git(args,timeout=900,stdout=None):
    return subprocess.run(["git","-C",str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(["hash-object",str(path)],180)
    return r.stdout.decode("utf-8","replace").strip() if r.returncode==0 else None
def materialize_point():
    cache=Path(tempfile.gettempdir())/"aays_sps5"/Path(POINT_REL).name
    cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.is_file() and blob_sha(cache)==POINT_BLOB: return cache
    cache.unlink(missing_ok=True)
    for ref in (f"origin/{POINT_BRANCH}",POINT_BRANCH):
        part=cache.with_suffix(".part"); part.unlink(missing_ok=True)
        with part.open("wb") as fh: r=git(["show",f"{ref}:{POINT_REL}"],stdout=fh)
        if r.returncode==0 and blob_sha(part)==POINT_BLOB:
            os.replace(part,cache); return cache
        part.unlink(missing_ok=True)
    r=git(["fetch","origin",POINT_BRANCH],900)
    if r.returncode==0:
        part=cache.with_suffix(".part")
        with part.open("wb") as fh: s=git(["show",f"FETCH_HEAD:{POINT_REL}"],stdout=fh)
        if s.returncode==0 and blob_sha(part)==POINT_BLOB:
            os.replace(part,cache); return cache
        part.unlink(missing_ok=True)
    return None
def pnum(pid):
    try: return int(pid.split("_",1)[1])
    except: return None
def get_point_map(fc):
    out={}
    for f in fc.get("features",[]):
        p=f.get("properties") or {}
        pid=None
        for k in ("security_parcel_id","parcel_id"):
            v=p.get(k)
            if isinstance(v,str) and v.startswith("parcel_"): pid=v; break
        g=f.get("geometry") or {}
        if pid and g.get("type")=="Point" and len(g.get("coordinates") or [])>=2:
            out[pid]=(float(g["coordinates"][0]),float(g["coordinates"][1]))
    return out
def fetch(url,accept="*/*",timeout=120):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-SPS5/HMLR-INSPIRE-v1","Accept":accept})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        return int(resp.status),resp.geturl(),resp.read()
def discover_lambeth_gml(page_bytes):
    text=page_bytes.decode("utf-8","replace")
    pos=text.lower().find(LOCAL_AUTHORITY.lower())
    if pos<0: raise RuntimeError("LAMBETH_DOWNLOAD_ROW_NOT_FOUND")
    window=text[pos:pos+5000]
    candidates=re.findall(r'href=["\']([^"\']+)["\']',window,re.I)
    for href in candidates:
        u=html.unescape(href)
        if ".gml" in u.lower() or "download" in u.lower():
            return urllib.parse.urljoin(DOWNLOAD_PAGE,u)
    before=text[max(0,pos-2500):pos+2500]
    candidates=re.findall(r'href=["\']([^"\']+)["\']',before,re.I)
    for href in reversed(candidates):
        u=html.unescape(href)
        if ".gml" in u.lower() or "download" in u.lower():
            return urllib.parse.urljoin(DOWNLOAD_PAGE,u)
    raise RuntimeError("LAMBETH_GML_LINK_NOT_FOUND")
def lname(tag): return tag.rsplit("}",1)[-1] if "}" in tag else tag
def ensure_pyproj():
    try:
        from pyproj import Transformer
        return Transformer
    except Exception:
        r=subprocess.run([sys.executable,"-m","pip","install","--disable-pip-version-check","--quiet","pyproj>=3.6,<4"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
        if r.returncode!=0: raise RuntimeError("PYPROJ_INSTALL_FAILED:"+r.stderr.decode("utf-8","replace")[-1000:])
        from pyproj import Transformer
        return Transformer
def poslist(el):
    for d in el.iter():
        if lname(d.tag)=="posList" and d.text and d.text.strip():
            vals=[float(x) for x in d.text.split()]
            dim=int(d.attrib.get("srsDimension") or 2)
            return [(vals[i],vals[i+1]) for i in range(0,len(vals)-1,dim)]
    pts=[]
    for d in el.iter():
        if lname(d.tag)=="pos" and d.text and d.text.strip():
            v=[float(x) for x in d.text.split()]
            if len(v)>=2: pts.append((v[0],v[1]))
    return pts
def parse_polygon(poly,transformer):
    outer=None; holes=[]
    for ch in poly:
        ln=lname(ch.tag)
        if ln in ("exterior","outerBoundaryIs"):
            ring=poslist(ch)
            if ring: outer=ring
        elif ln in ("interior","innerBoundaryIs"):
            ring=poslist(ch)
            if ring: holes.append(ring)
    if outer is None:
        ring=poslist(poly)
        if ring: outer=ring
    if not outer or len(outer)<3: return None
    def tx(ring):
        a=[list(transformer.transform(float(x),float(y))) for x,y in ring]
        if a and a[0]!=a[-1]: a.append(a[0])
        return a
    return [tx(outer)]+[tx(h) for h in holes if len(h)>=3]
def feature_for_id(root,parent,id_value,transformer):
    id_nodes=[e for e in root.iter() if lname(e.tag).upper()=="INSPIREID" and (e.text or "").strip()==id_value]
    if not id_nodes: return None
    node=id_nodes[0]
    cur=node
    candidate=None
    while cur in parent:
        cur=parent[cur]
        has_geom=any(lname(d.tag) in ("Polygon","MultiSurface","Surface") for d in cur.iter())
        if has_geom:
            candidate=cur
            break
    if candidate is None: return None
    polys=[]
    for p in candidate.iter():
        if lname(p.tag)=="Polygon":
            q=parse_polygon(p,transformer)
            if q: polys.append(q)
    if not polys:
        return None
    geom={"type":"MultiPolygon","coordinates":polys}
    attrs={}
    for e in candidate.iter():
        ln=lname(e.tag)
        if ln in ("INSPIREID","LABEL","NATIONALCADASTRALREFERENCE","VALIDFROM","BEGINLIFESPANVERSION") and e.text:
            attrs[ln]=(e.text or "").strip()
    return geom,attrs
def point_in_ring(x,y,ring):
    inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i][0],ring[i][1]; xj,yj=ring[j][0],ring[j][1]
        if ((yi>y)!=(yj>y)):
            den=(yj-yi)
            if den and x < (xj-xi)*(y-yi)/den+xi: inside=not inside
        j=i
    return inside
def point_in_geom(x,y,g):
    if g.get("type")=="Polygon": polys=[g.get("coordinates") or []]
    elif g.get("type")=="MultiPolygon": polys=g.get("coordinates") or []
    else: return False
    for poly in polys:
        if not poly: continue
        if point_in_ring(x,y,poly[0]) and not any(point_in_ring(x,y,h) for h in poly[1:]):
            return True
    return False
def semantic_check(f):
    reasons=[]
    g=f.get("geometry") or {}
    if g.get("type") not in ("Polygon","MultiPolygon"): reasons.append("GEOMETRY_MUST_BE_POLYGON_OR_MULTIPOLYGON")
    p=f.get("properties") or {}
    for k in REQ_FIELDS:
        if k not in p or p[k] in (None,"",[]): reasons.append("MISSING_"+k)
    for k in FORBIDDEN:
        if k in p: reasons.append("FORBIDDEN_PROPERTY_"+k)
    if not isinstance(p.get("field_evidence"),dict) or not p.get("field_evidence"): reasons.append("FIELD_EVIDENCE_OBJECT_REQUIRED")
    c=p.get("confidence_score_0_100")
    if not isinstance(c,(int,float)) or c<0 or c>100: reasons.append("INVALID_confidence_score_0_100")
    return reasons
def save(o):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    base={"schema_version":6,"slot_id":SLOT_ID,"lineage_id":LINEAGE_ID,"source_window_id":SOURCE_WINDOW,"first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED","accepted_count_claimed":0,"final_package_written":False,"fake_data":False,"status":"RUNNING"}
    if not PRIOR.is_file():
        base.update(status="BLOCKED",delivery_blocked="PRODUCER_SCHEMA_INVALID",error="PRIOR_VALID_FIELD_EVIDENCE_SNAPSHOT_MISSING");save(base);return 0
    prior=json.loads(PRIOR.read_text(encoding="utf-8-sig"))
    prior_features=(prior.get("records_geojson") or {}).get("features") or []
    targets=[]
    for f in prior_features:
        p=f.get("properties") or {}
        ref=str(p.get("canonical_parcel_reference") or "")
        pid=str(p.get("partition_record_id") or "")
        if ref and pid:
            targets.append({"reference":ref,"partition_record_id":pid,"prior_properties":p})
    targets=targets[:50]
    if len(targets)!=9:
        base.update(status="BLOCKED",delivery_blocked="PRODUCER_SCHEMA_INVALID",error=f"EXPECTED_9_PRIOR_VALID_TARGETS_GOT_{len(targets)}");save(base);return 0
    cp=materialize_point()
    if not cp:
        base.update(status="BLOCKED",delivery_blocked="PRODUCER_SCHEMA_INVALID",error="CANONICAL_POINT_BLOB_NOT_MATERIALIZED");save(base);return 0
    point_fc=json.loads(cp.read_text(encoding="utf-8-sig"))
    points=get_point_map(point_fc)
    page_status,page_url,page_bytes=fetch(DOWNLOAD_PAGE,"text/html")
    page_sha=sha256(page_bytes)
    gml_url=discover_lambeth_gml(page_bytes)
    gml_status,gml_final,gml_bytes=fetch(gml_url,"application/gml+xml,application/xml,text/xml,*/*",180)
    gml_sha=sha256(gml_bytes)
    tmp=Path(tempfile.gettempdir())/"aays_sps5"/"hmlr_lambeth_current.gml"
    tmp.parent.mkdir(parents=True,exist_ok=True); tmp.write_bytes(gml_bytes)
    root=ET.fromstring(gml_bytes)
    parent={c:p for p in root.iter() for c in p}
    Transformer=ensure_pyproj()
    transformer=Transformer.from_crs("EPSG:27700","EPSG:4326",always_xy=True)
    features=[]; rejections=[]
    for i,t in enumerate(targets,1):
        pid=t["partition_record_id"]; ref=t["reference"]; pp=t["prior_properties"]
        reasons=[]
        pt=points.get(pid)
        if pt is None: reasons.append("CANONICAL_POINT_NOT_FOUND")
        got=feature_for_id(root,parent,ref,transformer)
        if got is None: reasons.append("HMLR_INSPIRE_ID_NOT_FOUND_IN_LAMBETH_GML")
        geom=attrs=None
        if got is not None:
            geom,attrs=got
            if pt is not None and not point_in_geom(pt[0],pt[1],geom): reasons.append("CANONICAL_POINT_NOT_INSIDE_HMLR_INSPIRE_POLYGON")
        fe0=pp.get("field_evidence") or {}
        security_fe={k:v for k,v in fe0.items() if k in ("security_source","official_csv_sha256","lsoa_code","official_lsoa_row_count","official_crime_value_sum","official_numeric_cells")}
        if not security_fe or not security_fe.get("official_csv_sha256") or not security_fe.get("lsoa_code"): reasons.append("PRIOR_VERIFIED_FIELD_EVIDENCE_INCOMPLETE")
        if not reasons:
            props={
              "evidence_scope":"parcel",
              "coverage_area_id":pp.get("coverage_area_id"),
              "source_resolution":"HMLR_INSPIRE_index_polygon_with_MPS_LSOA_recorded_crime",
              "time_window":pp.get("time_window"),
              "source_url":pp.get("source_url"),
              "measurement_date":pp.get("measurement_date"),
              "measurement_method":"official_MPS_LSOA_CSV_exact_identifier_join",
              "spatial_binding_method":"canonical_point_inside_exact_HMLR_INSPIRE_GML_polygon",
              "confidence_score_0_100":100,
              "evidence_grade":"A",
              "field_evidence":{
                **security_fe,
                "hmlr_inspire_id":ref,
                "hmlr_inspire_download_page":DOWNLOAD_PAGE,
                "hmlr_inspire_download_page_sha256":page_sha,
                "hmlr_inspire_gml_url":gml_final,
                "hmlr_inspire_gml_sha256":gml_sha,
                "hmlr_local_authority":LOCAL_AUTHORITY,
                "hmlr_gml_INSPIREID":attrs.get("INSPIREID") if attrs else ref,
                "hmlr_gml_NATIONALCADASTRALREFERENCE":attrs.get("NATIONALCADASTRALREFERENCE") if attrs else None,
                "hmlr_gml_VALIDFROM":attrs.get("VALIDFROM") if attrs else None,
                "hmlr_gml_BEGINLIFESPANVERSION":attrs.get("BEGINLIFESPANVERSION") if attrs else None,
                "canonical_point_wgs84":{"type":"Point","coordinates":[pt[0],pt[1]]}
              },
              "canonical_parcel_id":"hmlr-inspire:"+ref,
              "canonical_parcel_reference":ref,
              "partition_record_id":pid,
              "canonical_geometry_source_url":gml_final,
              "canonical_geometry_provider":"HM Land Registry",
              "canonical_geometry_dataset":"INSPIRE Index Polygons",
              "source_window_id":SOURCE_WINDOW,
              "cursor":f"{SOURCE_WINDOW}:record={i}"
            }
            f={"type":"Feature","id":"hmlr-inspire:"+ref,"geometry":geom,"properties":props}
            sr=semantic_check(f)
            if sr: reasons.extend(sr)
            else: features.append(f)
        if reasons:
            rejections.append({"record_index":i,"cursor":f"{SOURCE_WINDOW}:record={i}","partition_record_id":pid,"hmlr_inspire_id":ref,"reasons":reasons})
    fc={"type":"FeatureCollection","features":features}
    passed=len(rejections)==0 and len(features)==len(targets)
    base.update({
      "status":"SEMANTIC_PRECHECK_COMPLETE",
      "download_page":{"url":page_url,"http_status":page_status,"sha256":page_sha},
      "gml":{"discovered_url":gml_url,"final_url":gml_final,"http_status":gml_status,"sha256":gml_sha,"size_bytes":len(gml_bytes),"local_authority":LOCAL_AUTHORITY},
      "processed_count":len(targets),
      "valid_count":len(features),
      "rejected_count":len(rejections),
      "semantic_precheck_passed":passed,
      "delivery_blocked":None if passed else "PRODUCER_SCHEMA_INVALID",
      "records_geojson":fc,
      "rejections":rejections,
      "cursor":f"{SOURCE_WINDOW}:record={len(targets)}"
    })
    save(base)
    print("SOURCE_WINDOW_ID="+SOURCE_WINDOW)
    print("GML_URL="+gml_final)
    print("GML_SHA256="+gml_sha)
    print("PROCESSED_COUNT="+str(len(targets)))
    print("VALID_COUNT="+str(len(features)))
    print("REJECTED_COUNT="+str(len(rejections)))
    print("SEMANTIC_PRECHECK_PASSED="+str(passed).lower())
    return 0

if __name__=="__main__": raise SystemExit(main())
