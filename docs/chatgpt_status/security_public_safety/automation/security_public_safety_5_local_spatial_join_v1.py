from __future__ import annotations
import hashlib,json,os,urllib.request
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
PAGE_GENERATION=1
PARTITION=[61524,76903]
SEMANTIC_MODE="AREA_JOIN"
CATEGORY="AAYS_SOURCE_AREA_V1"
SOURCE_WINDOW="data_police_metropolitan_neighbourhoods_first50_sps5_20260930_v1"
URL="https://data.police.uk/api/metropolitan/neighbourhoods"
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_source_area_latest.json"

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def sha(b):
    return hashlib.sha256(b).hexdigest()
def save(o):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

base={
 "schema_version":15,"slot_id":SLOT_ID,"owner":None,"partition":PARTITION,"lineage_id":LINEAGE_ID,
 "page_generation":PAGE_GENERATION,"category":CATEGORY,"semantic_mode":SEMANTIC_MODE,
 "source_window_id":SOURCE_WINDOW,"generated_at_utc":now(),"fake_data":False,
 "accepted_count":0,"materialized_parcel_count":0,"direct_parcel_count":0,
 "verified_no_building_count":0,"unprocessed_count":0,"planned_building_count":0,
 "first_missing_criterion":"LOCAL_OPENCODE_SPATIAL_JOIN_AND_MATERIALIZATION_REQUIRED"
}
try:
    accessed=now()
    req=urllib.request.Request(URL,headers={"User-Agent":"AAYS-security-public-safety-5/data-police-neighbourhood-list-v1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as resp:
        body=resp.read()
        status=int(resp.status)
        final_url=resp.geturl()
        ctype=resp.headers.get("Content-Type")
        last_modified=resp.headers.get("Last-Modified")
    if status!=200:
        raise RuntimeError("DATA_POLICE_HTTP_STATUS_"+str(status))
    obj=json.loads(body.decode("utf-8"))
    if not isinstance(obj,list):
        raise RuntimeError("DATA_POLICE_NEIGHBOURHOODS_NOT_LIST")
    selected=obj[:50]
    if not selected:
        raise RuntimeError("DATA_POLICE_NEIGHBOURHOODS_EMPTY")
    valid=[]; rejected=[]; seen=set(); dup=0
    for idx,item in enumerate(selected,1):
        if not isinstance(item,dict):
            rejected.append({"record_index":idx,"reason":"NON_OBJECT_RECORD"}); continue
        nid=str(item.get("id") or "").strip()
        name=str(item.get("name") or "").strip()
        if not nid or not name:
            rejected.append({"record_index":idx,"reason":"MISSING_ID_OR_NAME","record":item}); continue
        if nid in seen:
            dup+=1; continue
        seen.add(nid)
        slice_bytes=json.dumps({"id":nid,"name":name},ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
        props={
          "evidence_scope":"coverage_area",
          "coverage_area_id":nid,
          "identifier_scheme":"DATA_POLICE_FORCE_SPECIFIC_NEIGHBOURHOOD_ID",
          "force_id":"metropolitan",
          "coverage_area_name":name,
          "source_resolution":"METROPOLITAN_POLICE_NEIGHBOURHOOD_TEAM_IDENTIFIER",
          "time_window":"CURRENT_API_SNAPSHOT",
          "measurement_date":(last_modified or accessed[:10]),
          "measurement_date_basis":"HTTP Last-Modified header when supplied; otherwise UTC snapshot access date",
          "measurement_method":"official data.police.uk metropolitan neighbourhood list exact identifier record",
          "spatial_binding_method":"DEFERRED_TO_LOCAL_OPENCODE",
          "source_url":URL,
          "final_url":final_url,
          "accessed_at_utc":accessed,
          "licence":"Open Government Licence v3.0",
          "source_file_sha256":sha(body),
          "field_evidence":{"record_index":idx,"id":nid,"name":name,"record_slice_sha256":sha(slice_bytes)},
          "confidence_score_0_100":100,
          "evidence_grade":"A",
          "fake_data":False,
          "source_window_id":SOURCE_WINDOW,
          "cursor":f"{SOURCE_WINDOW}:record={idx}"
        }
        valid.append({"type":"Feature","id":nid,"geometry":None,"properties":props})
    base.update(
      status="SOURCE_WINDOW_COMPLETE",
      source_url=URL,final_url=final_url,http_status=status,content_type=ctype,accessed_at_utc=accessed,
      data_date=(last_modified or accessed[:10]),data_date_basis="HTTP_LAST_MODIFIED_OR_ACCESS_DATE",
      licence="Open Government Licence v3.0",source_file_sha256=sha(body),
      source_records_processed_count=len(selected),new_source_records=len(selected),
      source_area_count=len(valid),duplicate_count=dup,rejected_count=len(rejected),unmatched_count=0,
      records_geojson={"type":"FeatureCollection","features":valid},
      rejected_records=rejected,
      cursor=f"{SOURCE_WINDOW}:record={len(selected)}",
      semantic_precheck_passed=(len(selected)<=50 and len(valid)>0 and len(rejected)==0),
      delivery_blocked=None
    )
except Exception as ex:
    base.update(status="BLOCKED",source_records_processed_count=0,new_source_records=0,source_area_count=0,duplicate_count=0,rejected_count=0,unmatched_count=0,
                records_geojson={"type":"FeatureCollection","features":[]},error=str(ex),semantic_precheck_passed=False,delivery_blocked="SOURCE_FETCH_OR_PARSE_FAILED")
save(base)
print("STATUS="+base.get("status",""))
print("SOURCE_AREA_COUNT="+str(base.get("source_area_count",0)))
print("NEW_SOURCE_RECORDS="+str(base.get("new_source_records",0)))
print("SEMANTIC_PRECHECK_PASSED="+str(base.get("semantic_precheck_passed",False)).lower())
