from __future__ import annotations
import hashlib,json,os,re,subprocess,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
PAGE_GENERATION=1
PARTITION=[61524,76903]
CATEGORY="AAYS_LAYER24_EVIDENCE_V1"
SOURCE_WINDOW="planning_data_title_boundary_entity_json_exact_reference_authoritative_sps5_9_v1"
API="https://www.planning.data.gov.uk/entity.json"
PRIOR_BLOB="0f7053992b3d3f2bcd6f4783f332535577c610dc"
POINT_BRANCH="codex/aays-single-runner-v5-20260706"
POINT_REL="england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
POINT_BLOB="bb48164e7a0af78df875f30421a6a3068c43edb8"
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
REQUIRED=["evidence_scope","coverage_area_id","source_resolution","time_window","source_url","measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100","evidence_grade","field_evidence","canonical_parcel_id"]

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def sha(b): return hashlib.sha256(b).hexdigest()
def git(args,timeout=900,stdout=subprocess.PIPE):
    return subprocess.run(["git","-C",str(REPO),*args],stdout=stdout,stderr=subprocess.PIPE,check=False,timeout=timeout)
def gblob(p):
    r=git(["hash-object",str(p)],180)
    return r.stdout.decode().strip() if r.returncode==0 else None
def cat_blob(blob):
    r=git(["cat-file","blob",blob],180)
    if r.returncode!=0: raise RuntimeError(r.stderr.decode("utf-8","replace")[-1000:])
    return r.stdout
def materialize_points():
    p=Path(os.environ.get("RUNNER_TEMP") or "/tmp")/"aays_sps5_exact_ref"/Path(POINT_REL).name
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_file() and gblob(p)==POINT_BLOB: return p
    for ref in (f"origin/{POINT_BRANCH}",POINT_BRANCH):
        q=p.with_suffix(".part"); q.unlink(missing_ok=True)
        with q.open("wb") as fh: r=git(["show",f"{ref}:{POINT_REL}"],stdout=fh)
        if r.returncode==0 and gblob(q)==POINT_BLOB:
            os.replace(q,p); return p
        q.unlink(missing_ok=True)
    r=git(["fetch","origin",POINT_BRANCH],900)
    if r.returncode==0:
        q=p.with_suffix(".part"); q.unlink(missing_ok=True)
        with q.open("wb") as fh: s=git(["show",f"FETCH_HEAD:{POINT_REL}"],stdout=fh)
        if s.returncode==0 and gblob(q)==POINT_BLOB:
            os.replace(q,p); return p
        q.unlink(missing_ok=True)
    return None
def pointmap(fc):
    out={}
    for f in fc.get("features",[]):
        p=f.get("properties") or {}; pid=p.get("security_parcel_id") or p.get("parcel_id"); g=f.get("geometry") or {}
        if isinstance(pid,str) and pid.startswith("parcel_") and g.get("type")=="Point" and len(g.get("coordinates") or [])>=2:
            out[pid]=(float(g["coordinates"][0]),float(g["coordinates"][1]))
    return out
def http_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-security-public-safety-5/title-boundary-exact-reference-v1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as resp:
        b=resp.read()
        return int(resp.status),resp.geturl(),resp.headers.get("Content-Type"),b,json.loads(b.decode("utf-8"))
def entity_list(obj):
    if isinstance(obj,list): return obj
    if not isinstance(obj,dict): return []
    for k in ("entities","entity","results","data"):
        v=obj.get(k)
        if isinstance(v,list): return v
    return []
def parse_group(tokens,pos=0):
    if tokens[pos]!="(": raise ValueError("group expected")
    pos+=1; out=[]
    if pos<len(tokens) and tokens[pos]=="(":
        while True:
            g,pos=parse_group(tokens,pos); out.append(g)
            if pos>=len(tokens): raise ValueError("unexpected end")
            if tokens[pos]==",": pos+=1; continue
            if tokens[pos]==")": pos+=1; break
            raise ValueError("bad nested separator")
        return out,pos
    while True:
        if pos>=len(tokens) or tokens[pos] in ("(",")",","): raise ValueError("coordinate expected")
        x=float(tokens[pos]); pos+=1
        if pos>=len(tokens) or tokens[pos] in ("(",")",","): raise ValueError("y expected")
        y=float(tokens[pos]); pos+=1
        while pos<len(tokens) and tokens[pos] not in (",",")"): pos+=1
        out.append([x,y])
        if pos>=len(tokens): raise ValueError("unexpected end")
        if tokens[pos]==",": pos+=1; continue
        if tokens[pos]==")": pos+=1; break
    return out,pos
def wkt_geojson(wkt):
    if not isinstance(wkt,str): raise ValueError("missing WKT")
    s=wkt.strip()
    if ";" in s and s.upper().startswith("SRID="): s=s.split(";",1)[1].strip()
    m=re.match(r"^\s*(POLYGON|MULTIPOLYGON)\s*(.*)$",s,re.I|re.S)
    if not m: raise ValueError("not polygon WKT")
    typ=m.group(1).upper(); body=m.group(2)
    tokens=re.findall(r"\(|\)|,|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",body)
    data,pos=parse_group(tokens,0)
    if pos!=len(tokens): raise ValueError("trailing WKT tokens")
    return {"type":"Polygon" if typ=="POLYGON" else "MultiPolygon","coordinates":data}
def pir(x,y,r):
    inside=False; j=len(r)-1
    for i in range(len(r)):
        xi,yi=r[i][:2]; xj,yj=r[j][:2]
        if ((yi>y)!=(yj>y)) and yj!=yi and x<(xj-xi)*(y-yi)/(yj-yi)+xi: inside=not inside
        j=i
    return inside
def pig(x,y,g):
    ps=[g["coordinates"]] if g.get("type")=="Polygon" else g.get("coordinates",[])
    return any(poly and pir(x,y,poly[0]) and not any(pir(x,y,h) for h in poly[1:]) for poly in ps)
def sem(f):
    bad=[]; g=f.get("geometry") or {}; p=f.get("properties") or {}
    if g.get("type") not in ("Polygon","MultiPolygon"): bad.append("GEOMETRY_MUST_BE_POLYGON_OR_MULTIPOLYGON")
    for k in REQUIRED:
        if p.get(k) in (None,"",[]): bad.append("MISSING_"+k)
    for k in ("parcel_id","accepted_parcel"):
        if k in p: bad.append("FORBIDDEN_"+k)
    return bad
def save(o):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    base={"schema_version":13,"slot_id":SLOT_ID,"owner":None,"partition":PARTITION,"lineage_id":LINEAGE_ID,"page_generation":PAGE_GENERATION,"category":CATEGORY,
          "generated_at_utc":now(),"source_window_id":SOURCE_WINDOW,"first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED",
          "accepted_count_claimed":0,"source_area_count_claimed":0,"final_package_written":False,"fake_data":False,"max_records":9}
    try:
        prior=json.loads(cat_blob(PRIOR_BLOB).decode("utf-8-sig"))
        fs=(prior.get("records_geojson") or {}).get("features") or []
        pf=materialize_points()
        if pf is None: raise RuntimeError("CANONICAL_POINT_FILE_NOT_MATERIALIZED")
        pts=pointmap(json.loads(pf.read_text(encoding="utf-8-sig")))
    except Exception as ex:
        base.update(status="BLOCKED",blocker="PRIOR_READBACK_FAILED",error=str(ex),processed_count=0,valid_count=0,rejected_count=0,records_geojson={"type":"FeatureCollection","features":[]},rejections=[]); save(base); return 0
    targets=[]
    for f in fs:
        p=f.get("properties") or {}; ref=str(p.get("canonical_parcel_reference") or "").strip(); pid=str(p.get("partition_record_id") or "").strip()
        if ref and pid in pts: targets.append((pid,ref,p,pts[pid]))
    if len(targets)!=9:
        base.update(status="BLOCKED",blocker="TARGET_COUNT_MISMATCH",processed_count=len(targets),valid_count=0,rejected_count=len(targets),records_geojson={"type":"FeatureCollection","features":[]},rejections=[]); save(base); return 0
    features=[]; reject=[]; requests=[]
    for i,(pid,ref,pp,pt) in enumerate(targets,1):
        params=[("dataset","title-boundary"),("reference",ref),("quality","authoritative"),("limit","5"),
                ("field","entity"),("field","reference"),("field","dataset"),("field","geometry"),("field","quality"),
                ("field","start-date"),("field","entry-date"),("field","organisation-curie")]
        url=API+"?"+urllib.parse.urlencode(params,doseq=True)
        access=now(); reasons=[]; chosen=None; ev={"url":url,"final_url":None,"accessed_at_utc":access,"http_status":None}
        try:
            status,final_url,ctype,b,obj=http_json(url)
            ev.update(final_url=final_url,http_status=status,content_type=ctype,response_sha256=sha(b),size_bytes=len(b))
            exact=[]
            for e in entity_list(obj):
                if not isinstance(e,dict): continue
                if e.get("dataset")!="title-boundary": continue
                if str(e.get("reference") or "").strip()!=ref: continue
                if str(e.get("quality") or "").lower()!="authoritative": continue
                try: geom=wkt_geojson(e.get("geometry"))
                except Exception: continue
                exact.append((geom,e))
            uniq={}
            for geom,e in exact: uniq[str(e.get("entity") or ref)]=(geom,e)
            if len(uniq)!=1: reasons.append("EXACT_REFERENCE_AUTHORITATIVE_GEOMETRY_COUNT_"+str(len(uniq)))
            else:
                chosen=next(iter(uniq.values()))
                if not pig(pt[0],pt[1],chosen[0]): reasons.append("CANONICAL_POINT_NOT_INSIDE_EXACT_TITLE_BOUNDARY")
        except Exception as ex:
            ev["error"]=str(ex); reasons.append("PLANNING_DATA_EXACT_REFERENCE_HTTP_FAILED")
        requests.append({"partition_record_id":pid,"target_reference":ref,**ev})
        fe0=pp.get("field_evidence") or {}
        sec={k:v for k,v in fe0.items() if k in ("security_source","official_csv_sha256","lsoa_code","official_lsoa_row_count","official_crime_value_sum","official_numeric_cells")}
        if not sec.get("official_csv_sha256") or not sec.get("lsoa_code"): reasons.append("PRIOR_FIELD_EVIDENCE_INCOMPLETE")
        if not reasons and chosen:
            geom,e=chosen
            source_data_date=e.get("entry-date") or e.get("start-date")
            p={"evidence_scope":"parcel","coverage_area_id":pp.get("coverage_area_id"),
               "source_resolution":"HMLR_INSPIRE_AUTHORITATIVE_TITLE_BOUNDARY_EXACT_REFERENCE_PLUS_MPS_LSOA_MONTHLY_CRIME",
               "time_window":pp.get("time_window"),"source_url":pp.get("source_url"),"measurement_date":pp.get("measurement_date"),
               "measurement_method":"official MPS LSOA field evidence joined to authoritative HMLR title-boundary exact reference",
               "spatial_binding_method":"exact HMLR reference query plus local canonical point-in-polygon validation",
               "confidence_score_0_100":100,"evidence_grade":"A",
               "field_evidence":{**sec,"planning_data_publisher":"Planning Data / Ministry of Housing, Communities and Local Government",
                 "planning_data_provider":"HM Land Registry","planning_data_dataset":"title-boundary","planning_data_reference":ref,
                 "planning_data_entity":e.get("entity"),"planning_data_quality":e.get("quality"),"planning_data_entry_date":e.get("entry-date"),
                 "planning_data_start_date":e.get("start-date"),"planning_data_query_url":url,"planning_data_final_url":ev.get("final_url"),
                 "planning_data_accessed_at_utc":access,"planning_data_response_sha256":ev.get("response_sha256"),
                 "planning_data_licence":"Open Government Licence v3.0","canonical_point_wgs84":{"type":"Point","coordinates":[pt[0],pt[1]]}},
               "canonical_parcel_id":ref,"canonical_parcel_id_namespace":"HM_LAND_REGISTRY_INSPIRE","canonical_parcel_reference":ref,
               "partition_record_id":pid,"canonical_geometry_source_url":ev.get("final_url") or url,
               "canonical_geometry_response_sha256":ev.get("response_sha256"),"canonical_geometry_data_date":source_data_date,
               "source_window_id":SOURCE_WINDOW,"cursor":f"{SOURCE_WINDOW}:record={i}","fake_data":False}
            feat={"type":"Feature","id":ref,"geometry":geom,"properties":p}; reasons+=sem(feat)
            if not reasons: features.append(feat)
        if reasons:
            reject.append({"record_index":i,"cursor":f"{SOURCE_WINDOW}:record={i}","partition_record_id":pid,"target_reference":ref,"reasons":reasons,"request":ev})
    ok=len(features)==9 and not reject
    base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=9,valid_count=len(features),accepted_count_claimed=len(features) if ok else 0,
                source_area_count_claimed=0,rejected_count=len(reject),unmatched_count=len(reject),semantic_precheck_passed=ok,
                delivery_blocked=None if ok else "PRODUCER_SCHEMA_INVALID",records_geojson={"type":"FeatureCollection","features":features if ok else []},
                candidate_records_geojson={"type":"FeatureCollection","features":features},rejections=reject,requests=requests,cursor=f"{SOURCE_WINDOW}:record=9",
                official_source={"publisher":"Planning Data / Ministry of Housing, Communities and Local Government","provider":"HM Land Registry",
                  "dataset":"title-boundary","api_url":API,"public_no_login":True,"quality_required":"authoritative","licence":"Open Government Licence v3.0"},
                prior_evidence_blob_sha=PRIOR_BLOB,canonical_point_blob_sha=POINT_BLOB)
    save(base)
    print("VALID_COUNT="+str(len(features))); print("REJECTED_COUNT="+str(len(reject))); print("SEMANTIC_PRECHECK_PASSED="+str(ok).lower())
    return 0
if __name__=="__main__": raise SystemExit(main())
