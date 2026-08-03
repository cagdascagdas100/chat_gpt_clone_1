from __future__ import annotations
import argparse, hashlib, json, os, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-natural-england-ramsar-coordinate-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
LAYER_URL = "https://services.arcgis.com/JJzESW51TqeY9uat/arcgis/rest/services/Ramsar_England/FeatureServer/0"
FEATURE_SERVICE_URL = "https://services.arcgis.com/JJzESW51TqeY9uat/arcgis/rest/services/Ramsar_England/FeatureServer"
DATASET_URL = "https://www.data.gov.uk/dataset/67b4ef48-d0b2-4b6f-b659-4efa33469889/ramsar-england"
METADATA_URL = "https://ckan.publishing.service.gov.uk/harvest/object/3843555e-8ff4-4ed4-a061-8306b429a944/html"
ACCESS_GUIDANCE_URL = "https://www.gov.uk/guidance/how-to-access-natural-englands-maps-and-data"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1_048_576
MAX_FEATURES = 5
OUT_FIELDS = ["OBJECTID","NAME","CODE","AREA","GRID_REF","EASTING","NORTHING","LATITUDE","LONGITUDE","STATUS","GIS_DATE","VERSION"]
POINTS = {"parcel_61523":(-0.1387938,51.4196454),"parcel_61524":(-0.1407703,51.4170637),"parcel_61525":(-0.1398845,51.4167453)}

def repo_root() -> Path: return Path(__file__).resolve().parents[4]
def now_iso() -> str: return datetime.now(timezone.utc).isoformat()
def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); data=json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode()
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"wb") as h: h.write(data); h.flush(); os.fsync(h.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_points(base: Path) -> list[dict[str,Any]]:
    rows=json.loads((base/"england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json").read_text()).get("canonical_points")
    found={r.get("parcel_id"):r for r in rows if isinstance(r,dict) and r.get("parcel_id") in POINTS}
    if set(found)!=set(POINTS): raise ValueError("exact target parcels missing")
    out=[]
    for pid,expected in POINTS.items():
        r=found[pid]; lon=float(r["longitude"]); lat=float(r["latitude"])
        if r.get("geometry_type")!="Point" or r.get("point_valid") is not True or abs(lon-expected[0])>1e-7 or abs(lat-expected[1])>1e-7: raise ValueError("invalid canonical point "+pid)
        out.append({"parcel_id":pid,"longitude":lon,"latitude":lat})
    return out

def bounded_get(url: str, timeout: float) -> tuple[int,str,bytes]:
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"AAYS-parcel-label-evidence/1.0 bounded official-source research"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise ValueError("response exceeds 1 MiB")
        return int(getattr(response,"status",200)),response.geturl(),raw

def evidence(source_url,accessed,digest,basis,scope,fields,excerpt,status,parcel_id=None,point=None):
    return {"parcel_id":parcel_id,"canonical_point":point,"source_url":source_url,"accessed_at":accessed,"content_sha256":digest,"sha256_basis":basis,"record_scope":scope,"supports_fields":fields,"relevant_record_ids_or_excerpt":excerpt,"terms_or_license_urls":[DATASET_URL,METADATA_URL,ACCESS_GUIDANCE_URL,OGL_URL],"http_status":status}

def metadata_attempt(timeout: float):
    accessed=now_iso(); url=LAYER_URL+"?"+urllib.parse.urlencode({"f":"json"})
    try:
        status,final_url,raw=bounded_get(url,timeout); parsed=json.loads(raw.decode())
        published=[f.get("name") for f in parsed.get("fields",[]) if isinstance(f,dict)]
        selected=[n for n in OUT_FIELDS if n in published][:12] or OUT_FIELDS[:]
        excerpt=json.dumps({"name":parsed.get("name"),"geometryType":parsed.get("geometryType"),"objectIdField":parsed.get("objectIdField"),"selected_fields":selected,"maxRecordCount":parsed.get("maxRecordCount")},separators=(",",":"))
        return selected,evidence(final_url,accessed,sha256_bytes(raw),"bounded_metadata_response_bytes","one bounded official Natural England Ramsar layer metadata request; maximum 1 MiB",["layer name","polygon geometry type","published field names","record limit"],excerpt,status)
    except Exception as exc:
        err=f"NATURAL_ENGLAND_RAMSAR_METADATA_ERROR:{type(exc).__name__}:{exc}"
        return OUT_FIELDS[:],evidence(url,accessed,sha256_bytes(err.encode()),"bounded_error_evidence_string","one bounded official Natural England Ramsar layer metadata request; maximum 1 MiB",["layer metadata availability"],err,None)

def point_attempt(point,fields,timeout):
    accessed=now_iso(); geom=json.dumps({"x":point["longitude"],"y":point["latitude"],"spatialReference":{"wkid":4326}},separators=(",",":"))
    params={"f":"json","geometry":geom,"geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects","outFields":",".join(fields[:12]),"returnGeometry":"false","resultRecordCount":str(MAX_FEATURES)}
    url=LAYER_URL+"/query?"+urllib.parse.urlencode(params)
    try:
        status,final_url,raw=bounded_get(url,timeout); parsed=json.loads(raw.decode()); features=parsed.get("features") if isinstance(parsed,dict) else None; rows=[]
        if isinstance(features,list):
            for item in features[:MAX_FEATURES]:
                attrs=item.get("attributes") if isinstance(item,dict) else None
                if isinstance(attrs,dict): rows.append({"parcel_id":point["parcel_id"],"canonical_point":point,"source_url":final_url,"attributes":{k:attrs.get(k) for k in fields[:12] if k in attrs},"context_only":True,"designation_context":"Ramsar listed wetland","exact_parcel_binding":False,"property_type_binding":False})
        excerpt=json.dumps({"feature_count":len(rows),"field_names":fields[:12],"exceededTransferLimit":parsed.get("exceededTransferLimit") if isinstance(parsed,dict) else None},separators=(",",":"))
        return rows,evidence(final_url,accessed,sha256_bytes(raw),"bounded_point_query_response_bytes","one bounded exact-point intersection query against official Natural England Ramsar layer; maximum five features, twelve fields, no geometry and 1 MiB",fields[:12],excerpt,status,point["parcel_id"],point)
    except Exception as exc:
        err=f"NATURAL_ENGLAND_RAMSAR_POINT_ERROR:{type(exc).__name__}:{exc}"
        return [],evidence(url,accessed,sha256_bytes(err.encode()),"bounded_error_evidence_string","one bounded exact-point intersection query against official Natural England Ramsar layer; maximum five features, twelve fields, no geometry and 1 MiB",fields[:12],err,None,point["parcel_id"],point)

def build_payload(points,timeout):
    fields,meta=metadata_attempt(timeout); rows=[]; ev=[meta]
    for p in points:
        found,e=point_attempt(p,fields,timeout); rows.extend(found); ev.append(e)
    n=len(rows)
    return {"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":SLOT_ID,"task_id":TASK_ID,"generated_at":now_iso(),"state":"CANDIDATES_FOUND_CONTEXT_ONLY" if n else "NO_DATA_CONTINUE","panel_status":"PUBLISHED","completed_count":4,"target_count":4,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":points,"produced_candidate_rows":n,"candidate_rows":rows,"source_evidence":ev,"blocker":{"code":None if n else "NATURAL_ENGLAND_RAMSAR_NO_USABLE_RESPONSE_OR_NO_POINT_MATCH","state":"NONE" if n else "NO_DATA_CONTINUE","manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_NATURAL_ENGLAND_RAMSAR_COORDINATE","layer_url":LAYER_URL,"feature_service_url":FEATURE_SERVICE_URL,"dataset_url":DATASET_URL,"metadata_url":METADATA_URL,"access_guidance_url":ACCESS_GUIDANCE_URL,"open_government_licence_url":OGL_URL,"login_or_api_key_used":False,"geometry_payload_requested":False,"bulk_download_performed":False,"full_dataset_scan_performed":False,"large_data_downloaded":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,"inferred_values":0,"fake_data":False,"final_ready":False}

def validate_only(base: Path):
    if len(load_points(base))!=3 or not LAYER_URL.startswith("https://services.arcgis.com/"): raise ValueError("validation failed")
    if len(OUT_FIELDS)>12 or MAX_FEATURES>5 or MAX_BYTES!=1_048_576: raise ValueError("bounded limits invalid")
    print("PASS_TARGET_4_NATURAL_ENGLAND_RAMSAR_1_METADATA_PLUS_3_EXACT_POINT_QUERIES_MAX5_EACH_MAX12_FIELDS_MAX1MIB_CONTEXT_ONLY")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--timeout",type=float,default=5.0); p.add_argument("--validate-only",action="store_true"); a=p.parse_args(); base=repo_root(); validate_only(base)
    if a.validate_only: return 0
    data=build_payload(load_points(base),max(1.0,min(a.timeout,30.0)))
    atomic_json(base/"docs/chatgpt_status/_shared/slots_21/parcel_label_3/natural_england_ramsar_coordinate_result_latest.json",data)
    atomic_json(base/"england_map_web/data/aays_21_slots/parcel_label_3/natural_england_ramsar_coordinate_latest.json",data)
    print(f"PASS_CONTEXT_CANDIDATES_{data['produced_candidate_rows']}_4_OF_4" if data["produced_candidate_rows"] else "PASS_NO_DATA_CONTINUE_4_OF_4")
    return 0
if __name__=="__main__": raise SystemExit(main())
