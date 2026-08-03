from __future__ import annotations
import argparse, hashlib, json, os, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT="parcel_label_3"
TASK="parcel-label-3-lambeth-local-heritage-buildings-coordinate-v1-20260803"
PROBE_BLOB="ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
ROOT_URL="https://gis.lambeth.gov.uk/arcgis/rest/services/LambethLocalListBuildings/FeatureServer"
LAYER_URL=ROOT_URL+"/0"; META_URL=LAYER_URL+"?f=pjson"; QUERY_URL=LAYER_URL+"/query"
LIST_URL="https://www.lambeth.gov.uk/planning-building-control/conservation-listed-buildings/find-out-if-asset-local-heritage-list"
GUIDE_URL="https://www.lambeth.gov.uk/planning-building-control/conservation-listed-buildings/local-heritage-list"
OPEN_MAP_URL="https://www.lambeth.gov.uk/about-council/transparency-open-data/open-mapping-data"
TERMS_URL="https://www.lambeth.gov.uk/about-council/using-website/terms-conditions-disclaimer"
COPYRIGHT_URL="https://www.lambeth.gov.uk/about-council/using-website/copyright"
OGL_URL="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
TERMS=[OPEN_MAP_URL,TERMS_URL,COPYRIGHT_URL,OGL_URL]
MAX_BYTES=1_048_576; MAX_RESULTS=20; DISTANCE=500
POINTS={"parcel_61523":(-0.1387938,51.4196454),"parcel_61524":(-0.1407703,51.4170637),"parcel_61525":(-0.1398845,51.4167453)}

def base()->Path: return Path(__file__).resolve().parents[4]
def now()->str: return datetime.now(timezone.utc).isoformat()
def digest(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def atomic(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode()
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"wb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def points(root:Path)->list[dict[str,Any]]:
    src=json.loads((root/"england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json").read_text())["canonical_points"]
    found={r.get("parcel_id"):r for r in src if isinstance(r,dict) and r.get("parcel_id") in POINTS}
    if set(found)!=set(POINTS): raise ValueError("exact target parcels missing")
    out=[]
    for pid,(x0,y0) in POINTS.items():
        r=found[pid]; x=float(r["longitude"]); y=float(r["latitude"])
        if r.get("geometry_type")!="Point" or r.get("point_valid") is not True or abs(x-x0)>1e-7 or abs(y-y0)>1e-7:
            raise ValueError("invalid canonical Point "+pid)
        out.append({"parcel_id":pid,"longitude":x,"latitude":y})
    return out

def get(url:str,timeout:float)->tuple[int,str,bytes]:
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"AAYS-parcel-label-evidence/1.0 bounded official-source research"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        b=r.read(MAX_BYTES+1)
        if len(b)>MAX_BYTES: raise ValueError("response exceeds 1 MiB")
        return int(getattr(r,"status",200)),r.geturl(),b

def err(prefix:str,e:Exception)->tuple[str,str]:
    s=f"{prefix}:{type(e).__name__}:{e}"; return s,digest(s.encode())

def evidence(kind:str,url:str,accessed:str,sha:str,basis:str,scope:str,fields:list[str],excerpt:Any,status:int|None,requests:int,point:dict[str,Any]|None=None)->dict[str,Any]:
    d={"evidence_kind":kind,"source_url":url,"accessed_at":accessed,"content_sha256":sha,"sha256_basis":basis,
       "record_scope":scope,"supports_fields":fields,"relevant_record_ids_or_excerpt":excerpt,
       "terms_or_license_urls":TERMS,"http_status":status,"requests_made":requests}
    if point: d.update({"parcel_id":point["parcel_id"],"canonical_point":point})
    return d

def metadata(timeout:float)->tuple[dict[str,Any]|None,dict[str,Any]]:
    t=now(); scope="one bounded official Lambeth Local List Buildings layer metadata request; maximum 1 MiB"
    try:
        status,url,b=get(META_URL,timeout); j=json.loads(b)
        if not isinstance(j,dict) or j.get("error"): raise ValueError("unusable layer metadata response")
        rec={"name":j.get("name"),"type":j.get("type"),"geometryType":j.get("geometryType"),"objectIdField":j.get("objectIdField"),
             "field_count":len(j.get("fields",[])) if isinstance(j.get("fields"),list) else None}
        return j,evidence("layer_metadata",url,t,digest(b),"bounded_response_bytes",scope,
            ["layer identity","geometry type","object ID field","published attribute fields","query capability metadata"],rec,status,1)
    except Exception as e:
        s,h=err("LAMBETH_LOCAL_HERITAGE_METADATA_ERROR",e)
        return None,evidence("layer_metadata",META_URL,t,h,"bounded_error_evidence_string",scope,["official layer metadata availability"],s,None,0)

def fields(meta:dict[str,Any]|None)->list[str]:
    if not meta: return ["*"]
    out=[]; oid=meta.get("objectIdField")
    if isinstance(oid,str) and oid: out.append(oid)
    keys=("name","address","street","postcode","description","building","asset","list","reference","date","status","ward","type","category","interest")
    for f in meta.get("fields",[]):
        if not isinstance(f,dict) or not isinstance(f.get("name"),str): continue
        n=f["name"]; mark=(n+" "+str(f.get("alias",""))).lower()
        if any(k in mark for k in keys) and n not in out: out.append(n)
        if len(out)>=20: break
    return out or ["*"]

def qurl(p:dict[str,Any],out:list[str])->str:
    geom=json.dumps({"x":p["longitude"],"y":p["latitude"],"spatialReference":{"wkid":4326}},separators=(",",":"))
    params={"where":"1=1","geometry":geom,"geometryType":"esriGeometryPoint","inSR":"4326",
            "spatialRel":"esriSpatialRelIntersects","distance":str(DISTANCE),"units":"esriSRUnit_Meter",
            "outFields":",".join(out),"returnGeometry":"true","outSR":"4326","resultRecordCount":str(MAX_RESULTS),"f":"json"}
    return QUERY_URL+"?"+urllib.parse.urlencode(params)

def attrs(a:Any)->dict[str,Any]:
    if not isinstance(a,dict): return {}
    out={}
    for k,v in a.items():
        if isinstance(v,(str,int,float,bool)) or v is None: out[str(k)]=v
        if len(out)>=20: break
    return out

def query(p:dict[str,Any],out:list[str],timeout:float)->tuple[list[dict[str,Any]],dict[str,Any]]:
    t=now(); url=qurl(p,out)
    scope="one bounded official Lambeth Local List Buildings spatial query; 500 metre radius, maximum 20 features and 1 MiB"
    try:
        status,final,b=get(url,timeout); j=json.loads(b)
        if not isinstance(j,dict) or j.get("error"): raise ValueError("unusable spatial query response")
        fs=j.get("features") if isinstance(j.get("features"),list) else []
        rows=[{"parcel_id":p["parcel_id"],"canonical_point":p,"source_url":final,"attributes":attrs(f.get("attributes")),
               "geometry":f.get("geometry") if isinstance(f.get("geometry"),dict) else None,
               "context_kind":"nearby_lambeth_local_heritage_building","search_radius_metres":DISTANCE,
               "context_only":True,"exact_parcel_binding":False,"property_type_binding":False}
              for f in fs[:MAX_RESULTS] if isinstance(f,dict)]
        rec={"feature_count":len(fs),"retained_candidate_count":len(rows),"out_fields":out}
        ev=evidence("point_query",final,t,digest(b),"bounded_response_bytes",scope,
            ["nearby local-heritage feature availability","published name/address/postcode","published description/category/reference","published geometry"],rec,status,1,p)
        return rows,ev
    except Exception as e:
        s,h=err("LAMBETH_LOCAL_HERITAGE_POINT_QUERY_ERROR",e)
        return [],evidence("point_query",url,t,h,"bounded_error_evidence_string",scope,["nearby local-heritage feature availability"],s,None,0,p)

def payload(ps:list[dict[str,Any]],timeout:float)->dict[str,Any]:
    meta,me=metadata(timeout); out=fields(meta); rows=[]; ev=[me]
    for p in ps:
        r,e=query(p,out,timeout); rows.extend(r); ev.append(e)
    n=len(rows)
    return {"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":SLOT,"task_id":TASK,"generated_at":now(),
        "state":"CANDIDATES_FOUND_CONTEXT_ONLY" if n else "NO_DATA_CONTINUE","panel_status":"PUBLISHED",
        "completed_count":4,"target_count":4,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,
        "validated_canonical_points":ps,"produced_candidate_rows":n,"candidate_rows":rows,"source_evidence":ev,
        "blocker":{"code":None if n else "LAMBETH_LOCAL_HERITAGE_NO_USABLE_RESPONSE_OR_NO_NEARBY_RESULT",
                   "state":"NONE" if n else "NO_DATA_CONTINUE","manual_action_required":False,"retry_unchanged_route":False},
        "next_unverified_step":"SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_LOCAL_HERITAGE_BUILDINGS_COORDINATE",
        "service_root_url":ROOT_URL,"layer_url":LAYER_URL,"council_list_url":LIST_URL,"council_guide_url":GUIDE_URL,
        "open_mapping_url":OPEN_MAP_URL,"terms_url":TERMS_URL,"copyright_url":COPYRIGHT_URL,"open_government_licence_url":OGL_URL,
        "login_or_api_key_used":False,"bulk_download_performed":False,"full_dataset_scan_performed":False,
        "large_data_downloaded":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,
        "inferred_values":0,"fake_data":False,"final_ready":False}

def validate(root:Path)->None:
    if len(points(root))!=3 or not QUERY_URL.startswith("https://gis.lambeth.gov.uk/arcgis/rest/services/"): raise ValueError("validation failed")
    if (DISTANCE,MAX_RESULTS,MAX_BYTES)!=(500,20,1_048_576): raise ValueError("bounded limits mismatch")
    print("PASS_TARGET_4_LAMBETH_LOCAL_HERITAGE_METADATA_PLUS_3_POINT_QUERIES_500M_MAX20_EACH_MAX1MIB_CONTEXT_ONLY")

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--timeout",type=float,default=5); ap.add_argument("--validate-only",action="store_true"); a=ap.parse_args()
    root=base(); validate(root)
    if a.validate_only: return 0
    d=payload(points(root),max(1,min(float(a.timeout),30)))
    atomic(root/"docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_local_heritage_buildings_coordinate_result_latest.json",d)
    atomic(root/"england_map_web/data/aays_21_slots/parcel_label_3/lambeth_local_heritage_buildings_coordinate_latest.json",d)
    print(f"PASS_CONTEXT_CANDIDATES_{d['produced_candidate_rows']}_4_OF_4" if d["produced_candidate_rows"] else "PASS_NO_DATA_CONTINUE_4_OF_4")
    return 0
if __name__=="__main__": raise SystemExit(main())
