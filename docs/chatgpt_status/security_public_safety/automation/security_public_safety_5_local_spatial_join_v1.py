from __future__ import annotations
import hashlib,json,os,subprocess,tempfile,time,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
START,END=61674,61723
MAX_RECORDS=50
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
PROGRAM=REPO/"england_map_web/data/program_layer_matrix/security.geojson"
PROGRAM_BLOB="8afd1d2bac414cf0f6b9484014e7878a4ceff877"
POINT_BRANCH="codex/aays-single-runner-v5-20260706"
POINT_REL="england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
POINT_BLOB="bb48164e7a0af78df875f30421a6a3068c43edb8"
PREV=REPO/"incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/planning_data_title_boundary_mps_lsoa_61624_61673_20260928T221705Z/records.geojson"
SOURCE_WINDOW="planning_data_title_boundary_exact_reference_sps5_61674_61723_v1"
REQ_FIELDS=["evidence_scope","coverage_area_id","source_resolution","time_window","source_url","measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100","evidence_grade","field_evidence","canonical_parcel_id"]

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
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
def num(pid):
    try:return int(pid.split("_",1)[1])
    except:return None
def feature_map(fc,key_names):
    out={}
    for f in fc.get("features",[]):
        p=f.get("properties") or {}
        pid=None
        for k in key_names:
            v=p.get(k)
            if isinstance(v,str) and v.startswith("parcel_"): pid=v;break
        if pid: out[pid]=f
    return out
def http_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-SPS5/schema-v5","Accept":"application/geo+json,application/json"})
    with urllib.request.urlopen(req,timeout=60) as resp:
        body=resp.read()
        return int(resp.status),body,json.loads(body.decode("utf-8"))
def geofeatures(obj):
    if isinstance(obj,dict) and obj.get("type")=="FeatureCollection": return obj.get("features") or []
    if isinstance(obj,dict) and obj.get("type")=="Feature": return [obj]
    if isinstance(obj,dict) and isinstance(obj.get("entities"),list):
        out=[]
        for e in obj["entities"]:
            if isinstance(e,dict) and isinstance(e.get("geometry"),dict):
                out.append({"type":"Feature","geometry":e["geometry"],"properties":e})
        return out
    return []
def pinring(x,y,ring):
    inside=False;j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i][:2]; xj,yj=ring[j][:2]
        if ((yi>y)!=(yj>y)):
            d=yj-yi
            if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
        j=i
    return inside
def pinpoly(x,y,poly):
    if not poly or not pinring(x,y,poly[0]): return False
    return not any(pinring(x,y,h) for h in poly[1:])
def pingeom(x,y,g):
    if not isinstance(g,dict): return False
    t=g.get("type"); c=g.get("coordinates") or []
    if t=="Polygon": return pinpoly(x,y,c)
    if t=="MultiPolygon": return any(pinpoly(x,y,p) for p in c)
    return False
def validate_feature(f):
    p=f.get("properties") or {}; g=f.get("geometry") or {}; reasons=[]
    if g.get("type") not in ("Polygon","MultiPolygon"): reasons.append(f"geometry_type={g.get('type')}")
    for k in REQ_FIELDS:
        if p.get(k) in (None,""): reasons.append(f"missing_{k}")
    if "parcel_id" in p: reasons.append("forbidden_parcel_id")
    if "accepted_parcel" in p: reasons.append("forbidden_accepted_parcel")
    c=p.get("confidence_score_0_100")
    if not isinstance(c,(int,float)) or c<0 or c>100: reasons.append("invalid_confidence_score_0_100")
    return reasons
def save(o):
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    base={"schema_version":5,"slot_id":SLOT_ID,"lineage_id":LINEAGE_ID,"source_window_id":SOURCE_WINDOW,
          "record_range":[f"parcel_{START}",f"parcel_{END}"],"processed_count":0,
          "first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED","accepted_count_claimed":0,
          "final_package_written":False,"fake_data":False}
    if blob_sha(PROGRAM)!=PROGRAM_BLOB:
        base.update(status="BLOCKED",delivery_blocked="CANONICAL_PROGRAM_BLOB_MISMATCH");save(base);return 0
    point_path=materialize_point()
    if not point_path:
        base.update(status="BLOCKED",delivery_blocked="CANONICAL_POINT_BLOB_MATERIALIZATION_FAILED");save(base);return 0
    if not PREV.is_file():
        base.update(status="BLOCKED",delivery_blocked="PRIOR_FIELD_EVIDENCE_READBACK_MISSING");save(base);return 0
    with PROGRAM.open("r",encoding="utf-8-sig") as f: program=json.load(f)
    with point_path.open("r",encoding="utf-8-sig") as f: points=json.load(f)
    with PREV.open("r",encoding="utf-8-sig") as f: prev=json.load(f)
    pm=feature_map(program,("parcel_id","security_parcel_id"))
    qm=feature_map(points,("security_parcel_id","parcel_id"))
    cache={}
    for f in prev.get("features",[]):
        p=f.get("properties") or {}; code=p.get("coverage_area_id")
        if code and isinstance(p.get("field_evidence"),dict): cache[code]=p
    rows=[]; valid_features=[]; rejection_count=0
    for idx,n in enumerate(range(START,END+1),1):
        pid=f"parcel_{n}"; reasons=[]; pr=pm.get(pid); qr=qm.get(pid)
        if not pr: reasons.append("program_carrier_missing")
        if not qr: reasons.append("point_carrier_missing")
        pp=(pr or {}).get("properties") or {}; qp=(qr or {}).get("properties") or {}
        hmlr=str(pp.get("hmlr_inspire_id") or "").strip()
        lsoa=str(qp.get("security_lsoa_code") or "").strip()
        pg=(qr or {}).get("geometry") or {}
        if not hmlr: reasons.append("missing_hmlr_inspire_id")
        if not lsoa: reasons.append("missing_security_lsoa_code")
        if pg.get("type")!="Point" or len(pg.get("coordinates") or [])<2: reasons.append("canonical_point_missing")
        cached=cache.get(lsoa)
        if not cached: reasons.append("prior_verified_mps_field_evidence_not_cached_for_lsoa")
        row={"record_index":idx,"cursor":f"{SOURCE_WINDOW}:record={idx}","partition_record_id":pid,
             "hmlr_inspire_id":hmlr or None,"lsoa_code":lsoa or None,"schema_valid":False,"reasons":reasons.copy()}
        if not reasons:
            lon,lat=float(pg["coordinates"][0]),float(pg["coordinates"][1])
            urls=[
              f"https://www.planning.data.gov.uk/entity.geojson?dataset=title-boundary&reference={urllib.parse.quote(hmlr)}&limit=5",
              f"https://www.planning.data.gov.uk/entity.geojson?entity=120{urllib.parse.quote(hmlr)}&limit=5",
              f"https://www.planning.data.gov.uk/entity/120{urllib.parse.quote(hmlr)}.geojson"
            ]
            chosen=None; resp_sha=None; used_url=None; http_errors=[]
            for url in urls:
                try:
                    st,body,obj=http_json(url); feats=geofeatures(obj)
                    matches=[]
                    for f in feats:
                        p=f.get("properties") or {}
                        ref=str(p.get("reference") or p.get("REF") or p.get("ref") or "").strip()
                        ent=str(p.get("entity") or "").strip()
                        if ref==hmlr or ent==f"120{hmlr}": matches.append(f)
                    if len(matches)==1:
                        chosen=matches[0];resp_sha=hashlib.sha256(body).hexdigest();used_url=url;break
                    http_errors.append(f"{url}:http={st}:matches={len(matches)}")
                except Exception as ex: http_errors.append(f"{url}:{type(ex).__name__}:{ex}")
                time.sleep(.1)
            if not chosen:
                reasons.append("exact_title_boundary_reference_match_required")
                row["query_errors"]=http_errors
            else:
                g=chosen.get("geometry") or {}
                if g.get("type") not in ("Polygon","MultiPolygon"): reasons.append(f"title_boundary_geometry_type={g.get('type')}")
                if not pingeom(lon,lat,g): reasons.append("canonical_point_not_inside_exact_title_boundary")
                cp=dict(cached)
                field=dict(cp.get("field_evidence") or {})
                field.update({
                  "planning_data_exact_reference_query_url":used_url,
                  "planning_data_response_sha256":resp_sha,
                  "planning_data_reference":hmlr,
                  "planning_data_entity":int(f"120{hmlr}") if hmlr.isdigit() else None,
                  "planning_data_quality":"authoritative"
                })
                props={
                  "evidence_scope":"parcel",
                  "coverage_area_id":lsoa,
                  "source_resolution":"official_MPS_LSOA_recorded_crime_joined_to_exact_HMLR_title_boundary_polygon",
                  "time_window":cp.get("time_window"),
                  "source_url":cp.get("source_url"),
                  "measurement_date":cp.get("measurement_date"),
                  "measurement_method":cp.get("measurement_method"),
                  "spatial_binding_method":"exact_HMLR_INSPIRE_reference_plus_canonical_point_inside_title_boundary",
                  "confidence_score_0_100":100,
                  "evidence_grade":"A",
                  "field_evidence":field,
                  "canonical_parcel_id":f"title-boundary:{hmlr}",
                  "canonical_parcel_reference":hmlr,
                  "canonical_parcel_entity":int(f"120{hmlr}") if hmlr.isdigit() else None,
                  "partition_record_id":pid,
                  "canonical_lsoa_code":lsoa,
                  "canonical_geometry_source_url":used_url,
                  "canonical_geometry_provider":"HM Land Registry via Planning Data",
                  "canonical_geometry_dataset":"title-boundary",
                  "source_window_id":SOURCE_WINDOW,
                  "cursor":row["cursor"]
                }
                feat={"type":"Feature","id":f"title-boundary:{hmlr}","geometry":g,"properties":props}
                sem=validate_feature(feat)
                reasons.extend(sem)
                if not reasons:
                    row["schema_valid"]=True;row["canonical_parcel_id"]=props["canonical_parcel_id"];row["query_url"]=used_url;row["response_sha256"]=resp_sha
                    valid_features.append(feat)
        if reasons:
            rejection_count+=1;row["reasons"]=reasons
        rows.append(row)
    base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=len(rows),valid_count=len(valid_features),rejected_count=rejection_count,
                semantic_precheck_passed=(rejection_count==0 and len(valid_features)==MAX_RECORDS),
                delivery_blocked=None if rejection_count==0 and len(valid_features)==MAX_RECORDS else "PRODUCER_SCHEMA_INVALID",
                records_geojson={"type":"FeatureCollection","features":valid_features},rejections=[r for r in rows if not r["schema_valid"]],
                cursor=f"{SOURCE_WINDOW}:record={len(rows)}")
    save(base)
    print(json.dumps({"status":base["status"],"valid_count":len(valid_features),"rejected_count":rejection_count,"delivery_blocked":base["delivery_blocked"]}))
    return 0
if __name__=="__main__": raise SystemExit(main())
