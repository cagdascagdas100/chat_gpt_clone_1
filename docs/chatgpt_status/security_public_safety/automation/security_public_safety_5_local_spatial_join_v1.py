from __future__ import annotations
import hashlib,json,os,subprocess,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
PAGE_GENERATION=1
PARTITION=[61524,76903]
SEMANTIC_MODE="AREA_JOIN"
CATEGORY="AAYS_SOURCE_AREA_V1"
SOURCE_WINDOW="data_police_metropolitan_neighbourhood_boundary_first50_sps5_20260930_v1"
FORCE_ID="metropolitan"
API_ROOT="https://data.police.uk/api"
PRIOR_COMMIT="ad1ba605f7898660fedc4dfed06d45ed5a61d6bd"
PRIOR_PATH="docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_source_area_latest.json"
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
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-security-public-safety-5/data-police-neighbourhood-boundary-v1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as resp:
        body=resp.read()
        return int(resp.status),resp.geturl(),resp.headers.get("Content-Type"),resp.headers.get("Last-Modified"),body
def save(o):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

base={
 "schema_version":16,
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
    prior_features=(prior.get("records_geojson") or {}).get("features") or []
    if len(prior_features)!=50:
        raise RuntimeError("PRIOR_VERIFIED_ID_WINDOW_COUNT_NOT_50")
    targets=[]
    seen=set()
    for feat in prior_features:
        p=feat.get("properties") or {}
        nid=str(p.get("coverage_area_id") or "").strip()
        name=str(p.get("coverage_area_name") or "").strip()
        if not nid or not name or nid in seen:
            continue
        seen.add(nid)
        targets.append((nid,name))
    if len(targets)!=50:
        raise RuntimeError("PRIOR_EXACT_ID_TARGET_COUNT_NOT_50")
    features=[]
    rejected=[]
    unmatched=[]
    requests=[]
    for idx,(nid,name) in enumerate(targets,1):
        quoted=urllib.parse.quote(nid,safe="")
        url=f"{API_ROOT}/{FORCE_ID}/{quoted}/boundary"
        accessed=now()
        ev={"record_index":idx,"coverage_area_id":nid,"coverage_area_name":name,"url":url,"accessed_at_utc":accessed}
        try:
            status,final_url,ctype,last_modified,body=fetch(url)
            ev.update(http_status=status,final_url=final_url,content_type=ctype,last_modified=last_modified,response_sha256=sha(body),size_bytes=len(body))
            if status!=200:
                unmatched.append({**ev,"reason":"NON_200_STATUS"})
                requests.append(ev)
                continue
            obj=json.loads(body.decode("utf-8"))
            if not isinstance(obj,list) or len(obj)<3:
                unmatched.append({**ev,"reason":"EMPTY_OR_SHORT_BOUNDARY"})
                requests.append(ev)
                continue
            ring=[]
            bad=False
            for pt in obj:
                if not isinstance(pt,dict):
                    bad=True; break
                try:
                    lat=float(pt.get("latitude")); lon=float(pt.get("longitude"))
                except Exception:
                    bad=True; break
                if not (-90<=lat<=90 and -180<=lon<=180):
                    bad=True; break
                ring.append([lon,lat])
            if bad or len(ring)<3:
                rejected.append({**ev,"reason":"INVALID_BOUNDARY_COORDINATES"})
                requests.append(ev)
                continue
            if ring[0]!=ring[-1]:
                ring.append(ring[0])
            if len(ring)<4:
                rejected.append({**ev,"reason":"BOUNDARY_RING_TOO_SHORT"})
                requests.append(ev)
                continue
            data_date=last_modified or accessed[:10]
            props={
              "evidence_scope":"coverage_area",
              "coverage_area_id":nid,
              "coverage_area_name":name,
              "identifier_scheme":"DATA_POLICE_FORCE_SPECIFIC_NEIGHBOURHOOD_ID",
              "force_id":FORCE_ID,
              "source_resolution":"OFFICIAL_NEIGHBOURHOOD_BOUNDARY_POLYGON",
              "time_window":"CURRENT_API_SNAPSHOT",
              "measurement_date":data_date,
              "measurement_date_basis":"HTTP Last-Modified header when supplied; otherwise UTC snapshot access date",
              "measurement_method":"official data.police.uk neighbourhood boundary endpoint polygon",
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
                "boundary_point_count":len(obj),
                "boundary_response_sha256":sha(body),
                "http_status":status,
                "content_type":ctype,
                "last_modified":last_modified
              },
              "confidence_score_0_100":100,
              "evidence_grade":"A",
              "fake_data":False,
              "geometry_status":"OFFICIAL_POLYGON_MATERIALIZED",
              "source_window_id":SOURCE_WINDOW,
              "cursor":f"{SOURCE_WINDOW}:record={idx}"
            }
            features.append({"type":"Feature","id":f"{FORCE_ID}:{nid}","geometry":{"type":"Polygon","coordinates":[ring]},"properties":props})
            requests.append(ev)
        except Exception as ex:
            ev["error"]=str(ex)
            unmatched.append({**ev,"reason":"BOUNDARY_FETCH_OR_PARSE_FAILED"})
            requests.append(ev)
    base.update(
      status="SOURCE_WINDOW_COMPLETE" if features else "BLOCKED",
      source_url_template=f"{API_ROOT}/{FORCE_ID}/<neighbourhood_id>/boundary",
      public_no_login=True,
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
      prior_exact_identifier_window={
        "commit_sha":PRIOR_COMMIT,
        "source_window_id":prior.get("source_window_id"),
        "record_count":len(targets),
        "reopened_remote_url":False
      }
    )
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
      delivery_blocked="PRIOR_READBACK_OR_SOURCE_FETCH_FAILED"
    )
save(base)
print("STATUS="+base.get("status",""))
print("SOURCE_AREA_COUNT="+str(base.get("source_area_count",0)))
print("NEW_SOURCE_RECORDS="+str(base.get("new_source_records",0)))
print("REJECTED_COUNT="+str(base.get("rejected_count",0)))
print("UNMATCHED_COUNT="+str(base.get("unmatched_count",0)))
print("SEMANTIC_PRECHECK_PASSED="+str(base.get("semantic_precheck_passed",False)).lower())
