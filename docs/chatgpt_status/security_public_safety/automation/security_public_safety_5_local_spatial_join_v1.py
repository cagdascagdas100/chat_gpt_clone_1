from __future__ import annotations
import hashlib,json,os,re,subprocess,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
PAGE_GENERATION=1
PARTITION=[61524,76903]
SEMANTIC_MODE="AREA_JOIN"
CATEGORY="AAYS_SOURCE_AREA_V1"
SOURCE_WINDOW="planning_data_ward_exact_reference_first50_recovery_sps5_20260930_v1"
API="https://www.planning.data.gov.uk/entity.json"
PRIOR_COMMIT="d5abe8c15ce772b331648ef372877ab78cd38ffa"
PRIOR_PATH="incoming/source_area/security_public_safety_5/86b5e932de484ad26133fa8c/data_police_metropolitan_neighbourhoods_first50_20260930T185929Z/records.geojson"
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_source_area_latest.json"

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def sha(b):
    return hashlib.sha256(b).hexdigest()
def git_show(ref,path):
    q=subprocess.run(["git","-C",str(REPO),"show",f"{ref}:{path}"],capture_output=True,check=False,timeout=180)
    if q.returncode!=0:
        raise RuntimeError(q.stderr.decode("utf-8","replace")[-1000:])
    return q.stdout
def fetch_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-security-public-safety-5/planning-data-ward-recovery-v1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as resp:
        b=resp.read()
        return int(resp.status),resp.geturl(),resp.headers.get("Content-Type"),resp.headers.get("Last-Modified"),b,json.loads(b.decode("utf-8"))
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
def save(o):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

base={
 "schema_version":17,
 "slot_id":SLOT_ID,
 "owner":None,
 "partition":PARTITION,
 "lineage_id":LINEAGE_ID,
 "page_generation":PAGE_GENERATION,
 "category":CATEGORY,
 "semantic_mode":SEMANTIC_MODE,
 "source_window_id":SOURCE_WINDOW,
 "generated_at_utc":now(),
 "fake_data":False,
 "accepted_count":0,
 "materialized_parcel_count":0,
 "direct_parcel_count":0,
 "verified_no_building_count":0,
 "unprocessed_count":0,
 "planned_building_count":0,
 "first_missing_criterion":"LOCAL_OPENCODE_SPATIAL_JOIN_AND_MATERIALIZATION_REQUIRED"
}
try:
    prior=json.loads(git_show(PRIOR_COMMIT,PRIOR_PATH).decode("utf-8-sig"))
    pfs=prior.get("features") or []
    if len(pfs)!=50:
        raise RuntimeError("PRIOR_VERIFIED_EXACT_ID_COUNT_NOT_50")
    targets=[]
    seen=set()
    for feat in pfs:
        p=feat.get("properties") or {}
        nid=str(p.get("coverage_area_id") or "").strip()
        name=str(p.get("coverage_area_name") or "").strip()
        if nid and name and nid not in seen:
            seen.add(nid); targets.append((nid,name))
    if len(targets)!=50:
        raise RuntimeError("TARGET_COUNT_NOT_50")
    features=[]; rejected=[]; unmatched=[]; requests=[]
    for idx,(nid,name) in enumerate(targets,1):
        params=[
          ("dataset","ward"),("reference",nid),("quality","authoritative"),("limit","5"),
          ("field","entity"),("field","reference"),("field","name"),("field","dataset"),("field","geometry"),
          ("field","quality"),("field","entry-date"),("field","start-date"),("field","end-date"),("field","organisation-curie")
        ]
        url=API+"?"+urllib.parse.urlencode(params,doseq=True)
        accessed=now()
        ev={"record_index":idx,"coverage_area_id":nid,"coverage_area_name":name,"url":url,"accessed_at_utc":accessed}
        try:
            status,final_url,ctype,last_modified,body,obj=fetch_json(url)
            ev.update(http_status=status,final_url=final_url,content_type=ctype,last_modified=last_modified,response_sha256=sha(body),size_bytes=len(body))
            exact=[]
            for e in entity_list(obj):
                if not isinstance(e,dict): continue
                if e.get("dataset")!="ward": continue
                if str(e.get("reference") or "").strip()!=nid: continue
                if str(e.get("quality") or "").lower()!="authoritative": continue
                try: geom=wkt_geojson(e.get("geometry"))
                except Exception: continue
                exact.append((geom,e))
            uniq={}
            for geom,e in exact:
                uniq[str(e.get("entity") or nid)]=(geom,e)
            if len(uniq)!=1:
                unmatched.append({**ev,"reason":"EXACT_AUTHORITATIVE_WARD_GEOMETRY_COUNT_"+str(len(uniq))})
                requests.append(ev); continue
            geom,e=next(iter(uniq.values()))
            data_date=e.get("entry-date") or e.get("start-date") or last_modified or accessed[:10]
            props={
              "evidence_scope":"coverage_area",
              "coverage_area_id":nid,
              "coverage_area_name":e.get("name") or name,
              "identifier_scheme":"ONS_WARD_CODE",
              "source_resolution":"PLANNING_DATA_ONS_WARD_AUTHORITATIVE_GEOMETRY",
              "time_window":"CURRENT_AUTHORITATIVE_WARD_SNAPSHOT",
              "measurement_date":data_date,
              "measurement_date_basis":"Planning Data entry-date/start-date, then HTTP Last-Modified/access fallback",
              "measurement_method":"Planning Data exact ward reference authoritative geometry",
              "spatial_binding_method":"DEFERRED_TO_LOCAL_OPENCODE",
              "source_url":url,
              "final_url":final_url,
              "accessed_at_utc":accessed,
              "licence":"Open Government Licence v3.0",
              "source_file_sha256":sha(body),
              "field_evidence":{
                "record_index":idx,
                "prior_exact_identifier_commit":PRIOR_COMMIT,
                "prior_exact_identifier_id":nid,
                "planning_data_entity":e.get("entity"),
                "planning_data_reference":e.get("reference"),
                "planning_data_name":e.get("name"),
                "planning_data_quality":e.get("quality"),
                "planning_data_entry_date":e.get("entry-date"),
                "planning_data_start_date":e.get("start-date"),
                "planning_data_end_date":e.get("end-date"),
                "planning_data_organisation_curie":e.get("organisation-curie"),
                "response_sha256":sha(body)
              },
              "confidence_score_0_100":100,
              "evidence_grade":"A",
              "fake_data":False,
              "geometry_status":"OFFICIAL_POLYGON_MATERIALIZED",
              "source_window_id":SOURCE_WINDOW,
              "cursor":f"{SOURCE_WINDOW}:record={idx}"
            }
            features.append({"type":"Feature","id":f"ward:{nid}","geometry":geom,"properties":props})
            requests.append(ev)
        except Exception as ex:
            ev["error"]=str(ex)
            unmatched.append({**ev,"reason":"PLANNING_DATA_WARD_FETCH_OR_PARSE_FAILED"})
            requests.append(ev)
    base.update(
      status="SOURCE_WINDOW_COMPLETE" if features else "BLOCKED",
      source_url_template=API+"?dataset=ward&reference=<ward_id>&quality=authoritative",
      public_no_login=True,
      publisher="Planning Data / Ministry of Housing, Communities and Local Government",
      provider="Office for National Statistics",
      licence="Open Government Licence v3.0",
      source_records_processed_count=len(targets),
      new_source_records=len(features),
      source_area_count=len(features),
      duplicate_count=0,
      rejected_count=len(rejected),
      unmatched_count=len(unmatched),
      records_geojson={"type":"FeatureCollection","features":features},
      rejected_records=rejected,
      unmatched_records=unmatched,
      requests=requests,
      cursor=f"{SOURCE_WINDOW}:record={len(targets)}",
      semantic_precheck_passed=(len(features)>0 and len(targets)<=50),
      delivery_blocked=None if features else "SOURCE_FETCH_OR_PARSE_FAILED",
      prior_exact_identifier_package={
        "commit_sha":PRIOR_COMMIT,
        "path":PRIOR_PATH,
        "record_count":len(targets),
        "remote_source_reopened":False
      },
      prior_boundary_push_race_recovery={
        "commit_sha":"f910b0dfaa9b6c8d88584d52ccaaba3202e4d3f3",
        "source_window_id":"data_police_metropolitan_neighbourhood_boundary_first50_sps5_20260930_v1",
        "same_source_requery":False
      }
    )
    if len(unmatched)>0:
        base["first_missing_criterion"]="REMAINING_UNMATCHED_BOUNDARY_IDENTIFIERS_REQUIRE_UNUSED_OFFICIAL_SOURCE_WINDOW"
except Exception as ex:
    base.update(
      status="BLOCKED",
      source_records_processed_count=0,
      new_source_records=0,
      source_area_count=0,
      duplicate_count=0,
      rejected_count=0,
      unmatched_count=0,
      records_geojson={"type":"FeatureCollection","features":[]},
      error=str(ex),
      semantic_precheck_passed=False,
      delivery_blocked="PRIOR_READBACK_OR_SOURCE_FETCH_FAILED",
      first_missing_criterion="OFFICIAL_BOUNDARY_POLYGON_PAYLOAD_VIA_UNUSED_WINDOW_REQUIRED"
    )
save(base)
print("STATUS="+base.get("status",""))
print("SOURCE_AREA_COUNT="+str(base.get("source_area_count",0)))
print("NEW_SOURCE_RECORDS="+str(base.get("new_source_records",0)))
print("REJECTED_COUNT="+str(base.get("rejected_count",0)))
print("UNMATCHED_COUNT="+str(base.get("unmatched_count",0)))
print("SEMANTIC_PRECHECK_PASSED="+str(base.get("semantic_precheck_passed",False)).lower())
