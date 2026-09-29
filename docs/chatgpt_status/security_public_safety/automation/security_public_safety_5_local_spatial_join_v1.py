from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,tempfile,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
PRIOR=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_planning_data_exact_reference_61674_61723.json"
POINT_BRANCH="codex/aays-single-runner-v5-20260706"
POINT_REL="england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
POINT_BLOB="bb48164e7a0af78df875f30421a6a3068c43edb8"
WMS="https://inspire.landregistry.gov.uk/inspire/ows"
LAYER="inspire:CP.CadastralParcel"
SOURCE_WINDOW="hmlr_inspire_wms_getfeatureinfo_sps5_9_v1"
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
def get_point_map(fc):
    out={}
    for f in fc.get("features",[]):
        p=f.get("properties") or {}
        pid=None
        for k in ("security_parcel_id","parcel_id"):
            v=p.get(k)
            if isinstance(v,str) and v.startswith("parcel_"): pid=v;break
        g=f.get("geometry") or {}
        if pid and g.get("type")=="Point" and len(g.get("coordinates") or [])>=2:
            out[pid]=(float(g["coordinates"][0]),float(g["coordinates"][1]))
    return out
def ensure_pyproj():
    try:
        from pyproj import Transformer
        return Transformer
    except Exception:
        r=subprocess.run([sys.executable,"-m","pip","install","--disable-pip-version-check","--quiet","pyproj>=3.6,<4"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
        if r.returncode!=0: raise RuntimeError("PYPROJ_INSTALL_FAILED:"+r.stderr.decode("utf-8","replace")[-1000:])
        from pyproj import Transformer
        return Transformer
def http(url,timeout=90):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-SPS5/HMLR-WMS-GFI-v1","Accept":"application/vnd.ogc.gml,application/xml,text/xml,*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        return int(resp.status),resp.geturl(),resp.read(),resp.headers.get("Content-Type")
def lname(tag): return tag.rsplit("}",1)[-1] if "}" in tag else tag
def leaf_props(el):
    d={}
    for x in el.iter():
        if len(list(x))==0 and x.text and x.text.strip():
            k=lname(x.tag)
            d.setdefault(k,[]).append(x.text.strip())
    return d
def splitnums(text):
    vals=[]
    for t in re.split(r"[\s,]+",(text or "").strip()):
        if not t: continue
        try: vals.append(float(t))
        except: pass
    return vals
def parse_ring(el):
    for x in el.iter():
        ln=lname(x.tag)
        if ln=="posList" and x.text:
            v=splitnums(x.text); dim=int(x.attrib.get("srsDimension") or 2)
            pts=[(v[i],v[i+1]) for i in range(0,len(v)-1,dim)]
            return pts
        if ln=="coordinates" and x.text:
            pts=[]
            for tok in x.text.strip().split():
                p=tok.split(",")
                if len(p)>=2:
                    try: pts.append((float(p[0]),float(p[1])))
                    except: pass
            if pts:return pts
    pts=[]
    for x in el.iter():
        if lname(x.tag)=="pos" and x.text:
            v=splitnums(x.text)
            if len(v)>=2: pts.append((v[0],v[1]))
    return pts
def polygon_from_element(poly):
    outer=None;holes=[];srs=None
    for x in poly.iter():
        if not srs and x.attrib.get("srsName"): srs=x.attrib.get("srsName")
    for ch in poly:
        ln=lname(ch.tag)
        if ln in ("exterior","outerBoundaryIs"):
            r=parse_ring(ch)
            if len(r)>=3: outer=r
        elif ln in ("interior","innerBoundaryIs"):
            r=parse_ring(ch)
            if len(r)>=3: holes.append(r)
    if outer is None:
        r=parse_ring(poly)
        if len(r)>=3: outer=r
    return (outer,holes,srs) if outer else None
def txring(ring,to_wgs,assume_bng):
    out=[]
    for a,b in ring:
        if assume_bng or abs(a)>180 or abs(b)>90:
            x,y=to_wgs.transform(a,b)
        else:
            x,y=a,b
        out.append([float(x),float(y)])
    if out and out[0]!=out[-1]: out.append(out[0])
    return out
def extract_features(xml_bytes,to_wgs):
    root=ET.fromstring(xml_bytes)
    candidates=[]
    members=[e for e in root.iter() if lname(e.tag) in ("featureMember","member")]
    if not members: members=[root]
    for member in members:
        props=leaf_props(member)
        ids=[]
        for k,vals in props.items():
            kl=k.lower()
            if "inspire" in kl and "id" in kl or kl in ("inspireid","nationalcadastralreference","reference"):
                ids.extend(vals)
        polys=[]
        for p in member.iter():
            if lname(p.tag)=="Polygon":
                parsed=polygon_from_element(p)
                if not parsed: continue
                outer,holes,srs=parsed
                assume_bng=bool(srs and ("27700" in srs or "EPSG::27700" in srs)) or (outer and (abs(outer[0][0])>180 or abs(outer[0][1])>90))
                polys.append([txring(outer,to_wgs,assume_bng)]+[txring(h,to_wgs,assume_bng) for h in holes])
        geom=None
        if len(polys)==1: geom={"type":"Polygon","coordinates":polys[0]}
        elif len(polys)>1: geom={"type":"MultiPolygon","coordinates":polys}
        if ids or geom:
            candidates.append({"ids":sorted(set(ids)),"properties":props,"geometry":geom})
    return candidates
def pinring(x,y,ring):
    inside=False;j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i][:2];xj,yj=ring[j][:2]
        if ((yi>y)!=(yj>y)):
            den=yj-yi
            if den and x < (xj-xi)*(y-yi)/den+xi: inside=not inside
        j=i
    return inside
def point_in_geom(x,y,g):
    if not g:return False
    polys=[g.get("coordinates") or []] if g.get("type")=="Polygon" else (g.get("coordinates") or [] if g.get("type")=="MultiPolygon" else [])
    for poly in polys:
        if poly and pinring(x,y,poly[0]) and not any(pinring(x,y,h) for h in poly[1:]):return True
    return False
def semantic_check(f):
    reasons=[];g=f.get("geometry") or {};p=f.get("properties") or {}
    if g.get("type") not in ("Polygon","MultiPolygon"): reasons.append("GEOMETRY_MUST_BE_POLYGON_OR_MULTIPOLYGON")
    for k in REQ_FIELDS:
        if k not in p or p[k] in (None,"",[]):reasons.append("MISSING_"+k)
    for k in FORBIDDEN:
        if k in p:reasons.append("FORBIDDEN_PROPERTY_"+k)
    if not isinstance(p.get("field_evidence"),dict) or not p.get("field_evidence"):reasons.append("FIELD_EVIDENCE_OBJECT_REQUIRED")
    c=p.get("confidence_score_0_100")
    if not isinstance(c,(int,float)) or not (0<=c<=100):reasons.append("INVALID_confidence_score_0_100")
    return reasons
def save(o):
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    base={"schema_version":7,"slot_id":SLOT_ID,"lineage_id":LINEAGE_ID,"source_window_id":SOURCE_WINDOW,"first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED","accepted_count_claimed":0,"final_package_written":False,"fake_data":False}
    prior=json.loads(PRIOR.read_text(encoding="utf-8-sig"))
    prior_features=(prior.get("records_geojson") or {}).get("features") or []
    targets=[]
    for f in prior_features:
        p=f.get("properties") or {};ref=str(p.get("canonical_parcel_reference") or "");pid=str(p.get("partition_record_id") or "")
        if ref and pid:targets.append({"reference":ref,"partition_record_id":pid,"prior_properties":p})
    if len(targets)!=9:
        base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=len(targets),valid_count=0,rejected_count=len(targets),semantic_precheck_passed=False,delivery_blocked="PRODUCER_SCHEMA_INVALID",error=f"EXPECTED_9_TARGETS_GOT_{len(targets)}",records_geojson={"type":"FeatureCollection","features":[]},rejections=[]);save(base);return 0
    cp=materialize_point()
    if not cp:
        base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=9,valid_count=0,rejected_count=9,semantic_precheck_passed=False,delivery_blocked="PRODUCER_SCHEMA_INVALID",error="CANONICAL_POINT_BLOB_NOT_MATERIALIZED",records_geojson={"type":"FeatureCollection","features":[]},rejections=[]);save(base);return 0
    points=get_point_map(json.loads(cp.read_text(encoding="utf-8-sig")))
    Transformer=ensure_pyproj()
    to_bng=Transformer.from_crs("EPSG:4326","EPSG:27700",always_xy=True)
    to_wgs=Transformer.from_crs("EPSG:27700","EPSG:4326",always_xy=True)
    features=[];rejections=[];requests=[]
    for i,t in enumerate(targets,1):
        ref=t["reference"];pid=t["partition_record_id"];pp=t["prior_properties"];reasons=[]
        pt=points.get(pid)
        if pt is None:
            reasons.append("CANONICAL_POINT_NOT_FOUND")
            rejections.append({"record_index":i,"cursor":f"{SOURCE_WINDOW}:record={i}","partition_record_id":pid,"hmlr_inspire_id":ref,"reasons":reasons});continue
        bx,by=to_bng.transform(pt[0],pt[1])
        pad=20.0
        params={
          "SERVICE":"WMS","VERSION":"1.1.1","REQUEST":"GetFeatureInfo",
          "LAYERS":LAYER,"QUERY_LAYERS":LAYER,"STYLES":"",
          "SRS":"EPSG:27700","BBOX":f"{bx-pad:.3f},{by-pad:.3f},{bx+pad:.3f},{by+pad:.3f}",
          "WIDTH":"101","HEIGHT":"101","X":"50","Y":"50",
          "INFO_FORMAT":"application/vnd.ogc.gml","FEATURE_COUNT":"20",
          "EXCEPTIONS":"application/vnd.ogc.se_xml"
        }
        url=WMS+"?"+urllib.parse.urlencode(params)
        try:
            st,final,body,ctype=http(url)
            reqev={"url":final,"http_status":st,"content_type":ctype,"sha256":sha256(body),"size_bytes":len(body)}
            candidates=extract_features(body,to_wgs) if st==200 else []
        except Exception as ex:
            reqev={"url":url,"http_status":None,"error":str(ex)};candidates=[]
        requests.append({"partition_record_id":pid,"target_reference":ref,**reqev})
        exact=[]
        for c in candidates:
            idset=set(str(v).strip() for v in c["ids"])
            if ref in idset and c.get("geometry"):exact.append(c)
        if len(exact)!=1:
            reasons.append(f"EXACT_INSPIRE_ID_WITH_GEOMETRY_COUNT_{len(exact)}")
        chosen=exact[0] if len(exact)==1 else None
        if chosen and not point_in_geom(pt[0],pt[1],chosen["geometry"]):
            reasons.append("CANONICAL_POINT_NOT_INSIDE_WMS_GML_POLYGON")
        fe0=pp.get("field_evidence") or {}
        sec={k:v for k,v in fe0.items() if k in ("security_source","official_csv_sha256","lsoa_code","official_lsoa_row_count","official_crime_value_sum","official_numeric_cells")}
        if not sec or not sec.get("official_csv_sha256") or not sec.get("lsoa_code"):reasons.append("PRIOR_VERIFIED_FIELD_EVIDENCE_INCOMPLETE")
        if not reasons and chosen:
            props={
              "evidence_scope":"parcel",
              "coverage_area_id":pp.get("coverage_area_id"),
              "source_resolution":"HMLR_INSPIRE_WMS_GML_with_MPS_LSOA_recorded_crime",
              "time_window":pp.get("time_window"),
              "source_url":pp.get("source_url"),
              "measurement_date":pp.get("measurement_date"),
              "measurement_method":"official_MPS_LSOA_CSV_exact_identifier_join",
              "spatial_binding_method":"canonical_point_inside_exact_HMLR_INSPIRE_WMS_GML_polygon",
              "confidence_score_0_100":100,
              "evidence_grade":"A",
              "field_evidence":{
                **sec,
                "hmlr_inspire_id":ref,
                "hmlr_wms_service":WMS,
                "hmlr_wms_layer":LAYER,
                "hmlr_getfeatureinfo_url":reqev.get("url"),
                "hmlr_getfeatureinfo_sha256":reqev.get("sha256"),
                "hmlr_getfeatureinfo_content_type":reqev.get("content_type"),
                "hmlr_feature_properties":chosen.get("properties"),
                "canonical_point_wgs84":{"type":"Point","coordinates":[pt[0],pt[1]]}
              },
              "canonical_parcel_id":"hmlr-inspire:"+ref,
              "canonical_parcel_reference":ref,
              "partition_record_id":pid,
              "canonical_geometry_source_url":reqev.get("url"),
              "canonical_geometry_provider":"HM Land Registry",
              "canonical_geometry_dataset":"INSPIRE Index Polygons WMS",
              "source_window_id":SOURCE_WINDOW,
              "cursor":f"{SOURCE_WINDOW}:record={i}"
            }
            f={"type":"Feature","id":"hmlr-inspire:"+ref,"geometry":chosen["geometry"],"properties":props}
            sr=semantic_check(f)
            if sr:reasons.extend(sr)
            else:features.append(f)
        if reasons:
            rejections.append({"record_index":i,"cursor":f"{SOURCE_WINDOW}:record={i}","partition_record_id":pid,"hmlr_inspire_id":ref,"reasons":reasons,"request":reqev})
    passed=len(rejections)==0 and len(features)==9
    base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=9,valid_count=len(features),rejected_count=len(rejections),semantic_precheck_passed=passed,delivery_blocked=None if passed else "PRODUCER_SCHEMA_INVALID",records_geojson={"type":"FeatureCollection","features":features},rejections=rejections,requests=requests,cursor=f"{SOURCE_WINDOW}:record=9")
    save(base)
    print("SOURCE_WINDOW_ID="+SOURCE_WINDOW);print("VALID_COUNT="+str(len(features)));print("REJECTED_COUNT="+str(len(rejections)));print("SEMANTIC_PRECHECK_PASSED="+str(passed).lower())
    return 0
if __name__=="__main__": raise SystemExit(main())
