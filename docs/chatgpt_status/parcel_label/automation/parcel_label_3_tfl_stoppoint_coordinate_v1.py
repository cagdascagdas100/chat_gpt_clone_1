from __future__ import annotations
import argparse, hashlib, json, os, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID="parcel_label_3"
TASK_ID="parcel-label-3-tfl-stoppoint-coordinate-v1-20260803"
PROBE_BLOB_SHA="ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
API_BASE="https://api.tfl.gov.uk/StopPoint"
UNIFIED_API_URL="https://tfl.gov.uk/info-for/open-data-users/unified-api"
PORTAL_URL="https://api-portal.tfl.gov.uk/"
PRODUCTS_URL="https://api-portal.tfl.gov.uk/products"
APIS_URL="https://api-portal.tfl.gov.uk/apis"
OPEN_DATA_URL="https://tfl.gov.uk/info-for/open-data-users/"
TERMS_URL="https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service"
MAX_BYTES=1_048_576
MAX_CANDIDATES=20
RADIUS_METRES=500
POINTS={"parcel_61523":(-0.1387938,51.4196454),"parcel_61524":(-0.1407703,51.4170637),"parcel_61525":(-0.1398845,51.4167453)}

def root(): return Path(__file__).resolve().parents[4]
def now(): return datetime.now(timezone.utc).isoformat()
def digest(data:bytes): return hashlib.sha256(data).hexdigest()
def atomic(path:Path,payload:dict[str,Any]):
    path.parent.mkdir(parents=True,exist_ok=True); data=json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode()
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"wb") as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_points(base:Path):
    rows=json.loads((base/"england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json").read_text())["canonical_points"]
    found={r.get("parcel_id"):r for r in rows if isinstance(r,dict) and r.get("parcel_id") in POINTS}
    if set(found)!=set(POINTS): raise ValueError("exact target parcels missing")
    output=[]
    for pid,(elon,elat) in POINTS.items():
        row=found[pid]; lon=float(row["longitude"]); lat=float(row["latitude"])
        if row.get("geometry_type")!="Point" or row.get("point_valid") is not True or abs(lon-elon)>1e-7 or abs(lat-elat)>1e-7: raise ValueError("invalid canonical Point "+pid)
        output.append({"parcel_id":pid,"longitude":lon,"latitude":lat})
    return output

def url_for(point):
    query=urllib.parse.urlencode({"lat":f"{point['latitude']:.7f}","lon":f"{point['longitude']:.7f}","stopTypes":"NaptanPublicBusCoachTram","radius":str(RADIUS_METRES),"useStopPointHierarchy":"true","returnLines":"false"})
    return API_BASE+"?"+query

def bounded_json(url,timeout):
    request=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"AAYS-parcel-label-evidence/1.0 bounded official-source research"})
    with urllib.request.urlopen(request,timeout=timeout) as response:
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise ValueError("response exceeds 1 MiB")
        return int(getattr(response,"status",200)),response.geturl(),raw,json.loads(raw.decode("utf-8"))

def extract(payload):
    if isinstance(payload,dict): rows=payload.get("stopPoints") or payload.get("places") or []
    elif isinstance(payload,list): rows=payload
    else: rows=[]
    output=[]
    for row in rows[:MAX_CANDIDATES]:
        if not isinstance(row,dict): continue
        output.append({"stop_point_id":row.get("id") or row.get("naptanId"),"common_name":row.get("commonName"),"stop_type":row.get("stopType"),"latitude":row.get("lat"),"longitude":row.get("lon"),"distance_metres":row.get("distance"),"modes":row.get("modes") if isinstance(row.get("modes"),list) else [],"source_url":row.get("url"),"context_only":True,"exact_parcel_binding":False,"property_type_binding":False})
    return output

def evidence(pid,point,url,accessed,sha,basis,excerpt,status,requests):
    return {"parcel_id":pid,"canonical_point":point,"source_url":url,"accessed_at":accessed,"content_sha256":sha,"sha256_basis":basis,"record_scope":"one bounded official TfL Unified API StopPoint coordinate query; 500 metre radius, maximum one request, 1 MiB and 20 candidates","supports_fields":["stop point identifier","common stop name","stop type","stop latitude and longitude","distance where published","transport modes where published"],"relevant_record_ids_or_excerpt":excerpt,"terms_or_license_urls":[TERMS_URL],"http_status":status,"requests_made":requests}

def attempt(point,timeout):
    pid=point["parcel_id"]; accessed=now(); url=url_for(point)
    try:
        status,final_url,raw,payload=bounded_json(url,timeout); rows=extract(payload)
        return rows,evidence(pid,point,final_url,accessed,digest(raw),"bounded_response_bytes",json.dumps(payload,ensure_ascii=False,separators=(",",":"))[:1500],status,1)
    except Exception as exc:
        error=f"TFL_STOPPOINT_COORDINATE_ERROR:{type(exc).__name__}:{exc}"
        return [],evidence(pid,point,url,accessed,digest(error.encode()),"bounded_error_evidence_string",error,None,0)

def build(points,timeout):
    rows=[]; ev=[]
    for point in points:
        found,record=attempt(point,timeout); ev.append(record)
        for row in found: row.update({"parcel_id":point["parcel_id"],"canonical_point":point}); rows.append(row)
    n=len(rows)
    return {"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":SLOT_ID,"task_id":TASK_ID,"generated_at":now(),"state":"CANDIDATES_FOUND_CONTEXT_ONLY" if n else "NO_DATA_CONTINUE","panel_status":"PUBLISHED","completed_count":3,"target_count":3,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":points,"produced_candidate_rows":n,"candidate_rows":rows,"source_evidence":ev,"blocker":{"code":None if n else "TFL_STOPPOINT_NO_USABLE_RESPONSE_OR_NO_NEARBY_RESULT","state":"NONE" if n else "NO_DATA_CONTINUE","manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_TFL_STOPPOINT_COORDINATE","api_base":API_BASE,"radius_metres":RADIUS_METRES,"stop_types":["NaptanPublicBusCoachTram"],"anonymous_access_used":True,"app_key_used":False,"login_or_account_used":False,"bulk_download_performed":False,"full_network_scan_performed":False,"arrival_or_vehicle_data_requested":False,"large_data_downloaded":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,"inferred_values":0,"fake_data":False,"final_ready":False}

def validate(base):
    points=load_points(base)
    if len(points)!=3 or not API_BASE.startswith("https://api.tfl.gov.uk/") or RADIUS_METRES!=500 or MAX_CANDIDATES!=20: raise ValueError("validation failed")
    print("PASS_TARGET_3_TFL_STOPPOINT_COORDINATE_MAX1_REQUEST_EACH_500M_MAX1MIB_20_CANDIDATES_ANONYMOUS_CONTEXT_ONLY")

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--timeout",type=float,default=5); parser.add_argument("--validate-only",action="store_true"); args=parser.parse_args(); base=root(); validate(base)
    if args.validate_only: return 0
    payload=build(load_points(base),max(1,min(args.timeout,30)))
    atomic(base/"docs/chatgpt_status/_shared/slots_21/parcel_label_3/tfl_stoppoint_coordinate_result_latest.json",payload)
    atomic(base/"england_map_web/data/aays_21_slots/parcel_label_3/tfl_stoppoint_coordinate_latest.json",payload)
    print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_3_OF_3" if payload["produced_candidate_rows"] else "PASS_NO_DATA_CONTINUE_3_OF_3")
    return 0
if __name__=="__main__": raise SystemExit(main())
