#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

INPUT = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
MANIFEST = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_controlled_parking_zone_point_containment_source_manifest_20260804.json")
OUTPUTS = [
    pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_controlled_parking_zone_point_containment_result_latest.json"),
    pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/lambeth_controlled_parking_zone_point_containment_latest.json"),
]
LAYER_ROOTS = [
    "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethControlledParkingZones/MapServer/0",
    "https://gis.lambeth.gov.uk/arcgis/rest/services/STATICLambethControlledParkingZones/MapServer/0",
]
ALLOWED_HOST = "gis.lambeth.gov.uk"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_METADATA_REQUESTS = 2
MAX_POINT_REQUESTS = 3

def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",",":"), sort_keys=True)

def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temporary = pathlib.Path(handle.name)
    temporary.replace(path)

def safe_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or (parsed.hostname or "").casefold() != ALLOWED_HOST or parsed.username or parsed.password or parsed.fragment:
        raise RuntimeError(f"UNSAFE_OR_UNTRUSTED_URL:{url}")
    return url

def fetch(url: str, timeout: int, accept: str) -> tuple[bytes,str,int]:
    safe_url(url)
    request=urllib.request.Request(url,headers={"User-Agent":"AAYS-parcel-label-3/1.0","Accept":accept})
    with urllib.request.urlopen(request,timeout=timeout) as response:
        final_url=response.geturl()
        safe_url(final_url)
        body=bytearray()
        while True:
            remaining=MAX_RESPONSE_BYTES-len(body)+1
            chunk=response.read(min(1024*1024,remaining))
            if not chunk:
                break
            body.extend(chunk)
            if len(body)>MAX_RESPONSE_BYTES:
                raise RuntimeError(f"RESPONSE_TOO_LARGE:{len(body)}:{MAX_RESPONSE_BYTES}")
        return bytes(body),final_url,int(getattr(response,"status",200))

def load_manifest() -> dict[str,Any]:
    payload=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("service_roots") != LAYER_ROOTS:
        raise RuntimeError("WRONG_MANIFEST_SERVICE_ROOTS")
    if payload.get("harvest_guid") != "e9996e9dbf4a4729bc5116ea56fe6b57_4":
        raise RuntimeError("WRONG_MANIFEST_HARVEST_GUID")
    if len(payload.get("target_uprns",[])) != 3:
        raise RuntimeError("SOURCE_MANIFEST_TARGET_COUNT")
    sources=payload.get("sources",[])
    if len(sources)<5:
        raise RuntimeError("SOURCE_MANIFEST_INCOMPLETE")
    for source in sources:
        excerpt=source.get("retained_excerpt","")
        if not excerpt or sha256_bytes(excerpt.encode("utf-8")) != source.get("retained_excerpt_sha256"):
            raise RuntimeError("MANIFEST_EXCERPT_SHA_MISMATCH")
    return payload

def load_rows() -> list[dict[str,Any]]:
    payload=json.loads(INPUT.read_text(encoding="utf-8"))
    records=payload.get("records",[])
    manifest=load_manifest()
    target_uprns=set(manifest["target_uprns"])
    if len(records)!=3:
        raise RuntimeError(f"EXPECTED_3_INPUT_ROWS:{len(records)}")
    rows=[]
    for record in records:
        required=("parcel_id","UPRN","FULLADDRESS","POSTCODE","longitude","latitude")
        if not record.get("exact_uprn_bound") or any(field not in record for field in required):
            raise RuntimeError("INVALID_INPUT_ROW")
        row={field:record[field] for field in required}
        row["UPRN"]=str(row["UPRN"])
        row["exact_uprn_bound"]=True
        if row["UPRN"] not in target_uprns:
            raise RuntimeError(f"UPRN_NOT_IN_MANIFEST:{row['UPRN']}")
        rows.append(row)
    if len({row["UPRN"] for row in rows})!=3:
        raise RuntimeError("INPUT_UPRNS_NOT_UNIQUE")
    return rows

def point_on_segment(px:float,py:float,x1:float,y1:float,x2:float,y2:float,eps:float=1e-12)->bool:
    cross=(px-x1)*(y2-y1)-(py-y1)*(x2-x1)
    if abs(cross)>eps:
        return False
    return min(x1,x2)-eps<=px<=max(x1,x2)+eps and min(y1,y2)-eps<=py<=max(y1,y2)+eps

def ring_contains_or_touches(ring:list[list[float]], point:tuple[float,float])->bool:
    px,py=point
    inside=False
    if len(ring)<4:
        return False
    for i in range(len(ring)-1):
        x1,y1=ring[i][:2]
        x2,y2=ring[i+1][:2]
        if point_on_segment(px,py,x1,y1,x2,y2):
            return True
        if (y1>py)!=(y2>py):
            x_at_y=(x2-x1)*(py-y1)/(y2-y1)+x1
            if px < x_at_y:
                inside=not inside
    return inside

def polygon_covers(coords:list[Any], point:tuple[float,float])->bool:
    if not coords or not ring_contains_or_touches(coords[0],point):
        return False
    for hole in coords[1:]:
        if ring_contains_or_touches(hole,point):
            return False
    return True

def geometry_covers(geometry:dict[str,Any], point:tuple[float,float])->bool:
    gtype=geometry.get("type")
    coords=geometry.get("coordinates")
    if gtype=="Polygon" and isinstance(coords,list):
        return polygon_covers(coords,point)
    if gtype=="MultiPolygon" and isinstance(coords,list):
        return any(polygon_covers(poly,point) for poly in coords)
    return False

def metadata_url(root:str)->str:
    return root+"?"+urllib.parse.urlencode({"f":"json"})

def discover_layer(timeout:int,evidence:dict[str,Any])->str:
    errors=[]
    for root in LAYER_ROOTS:
        evidence["metadata_request_count"]+=1
        url=metadata_url(root)
        try:
            body,final_url,status=fetch(url,timeout,"application/json")
            payload=json.loads(body)
            if payload.get("type")!="Feature Layer":
                raise RuntimeError("NOT_FEATURE_LAYER")
            if payload.get("geometryType")!="esriGeometryPolygon":
                raise RuntimeError("NOT_POLYGON_LAYER")
            field_names={str(field.get("name","")).upper() for field in payload.get("fields",[]) if isinstance(field,dict)}
            if "NAME" not in field_names or "HOURS" not in field_names:
                raise RuntimeError("REQUIRED_FIELDS_MISSING")
            evidence["metadata_response_count"]+=1
            evidence["metadata_requests"].append({
                "layer_root":root,"request_url":url,"final_url":final_url,"http_status":status,
                "bytes":len(body),"response_sha256":sha256_bytes(body),
                "geometry_type":payload.get("geometryType"),"field_names":sorted(field_names),"state":"RESPONSE"
            })
            return root
        except Exception as exc:
            error=f"{type(exc).__name__}:{exc}"
            errors.append(error)
            evidence["metadata_requests"].append({"layer_root":root,"request_url":url,"state":"ERROR","error":error})
    raise RuntimeError("ALL_LAYER_METADATA_ENDPOINTS_FAILED:"+"|".join(errors))

def query_url(root:str,row:dict[str,Any])->str:
    params={
        "where":"1=1",
        "geometry":f"{float(row['longitude']):.15f},{float(row['latitude']):.15f}",
        "geometryType":"esriGeometryPoint",
        "inSR":"4326",
        "spatialRel":"esriSpatialRelIntersects",
        "outFields":"OBJECTID,NAME,HOURS,CODE,CODE_1",
        "returnGeometry":"true",
        "outSR":"4326",
        "f":"geojson",
    }
    return root+"/query?"+urllib.parse.urlencode(params)

def selected_properties(properties:dict[str,Any])->dict[str,Any]:
    allowed=("OBJECTID","NAME","HOURS","CODE","CODE_1")
    return {key:properties.get(key) for key in allowed if key in properties}

def parse_candidates(body:bytes,row:dict[str,Any])->tuple[list[dict[str,Any]],int]:
    payload=json.loads(body)
    features=payload.get("features")
    if payload.get("type")!="FeatureCollection" or not isinstance(features,list):
        raise RuntimeError("NOT_GEOJSON_FEATURE_COLLECTION")
    point=(float(row["longitude"]),float(row["latitude"]))
    candidates=[]
    for index,feature in enumerate(features,1):
        if not isinstance(feature,dict) or not isinstance(feature.get("geometry"),dict):
            continue
        geometry=feature["geometry"]
        if not geometry_covers(geometry,point):
            continue
        properties=feature.get("properties")
        if not isinstance(properties,dict):
            properties={}
        name=str(properties.get("NAME") or "").strip()
        if not name:
            continue
        raw_attributes=canonical_json(properties)
        raw_geometry=canonical_json(geometry)
        candidates.append({
            "feature_id":feature.get("id"),
            "feature_index":index,
            "official_cpz_name":name,
            "official_cpz_hours":properties.get("HOURS"),
            "official_cpz_code":properties.get("CODE_1",properties.get("CODE")),
            "retained_official_attributes":selected_properties(properties),
            "raw_attributes_sha256":sha256_bytes(raw_attributes.encode("utf-8")),
            "geometry_sha256":sha256_bytes(raw_geometry.encode("utf-8")),
            "geometry":geometry,
        })
    return candidates,len(features)

def synthetic_feature(row:dict[str,Any],idx:int,offset:float=0.0)->dict[str,Any]:
    lon=float(row["longitude"])+offset
    lat=float(row["latitude"])+offset
    d=0.00008
    ring=[[lon-d,lat-d],[lon+d,lat-d],[lon+d,lat+d],[lon-d,lat+d],[lon-d,lat-d]]
    return {
        "type":"Feature","id":idx,
        "properties":{"OBJECTID":idx,"NAME":f"CPZ-{idx}","HOURS":"Mon-Fri 08:30-18:30","CODE_1":chr(64+idx)},
        "geometry":{"type":"Polygon","coordinates":[ring]},
    }

def run(rows:list[dict[str,Any]],timeout:int,synthetic:bool=False,ambiguous:bool=False)->tuple[dict[str,Any],list[dict[str,Any]],int]:
    evidence={
        "accessed_at":now(),"layer_roots":LAYER_ROOTS,"metadata_request_count":0,
        "metadata_response_count":0,"metadata_requests":[],"point_query_count":0,"point_queries":[]
    }
    if synthetic:
        selected_root=LAYER_ROOTS[0]
        evidence["selected_layer_root"]=selected_root
    else:
        try:
            selected_root=discover_layer(timeout,evidence)
            evidence["selected_layer_root"]=selected_root
        except Exception as exc:
            error=f"{type(exc).__name__}:{exc}"
            evidence["discovery_error"]=error
            return evidence,[{
                **row,"source_url":LAYER_ROOTS[0],"candidate_count":0,"state":"NO_DATA",
                "reason":error,"inferred":False
            } for row in rows],0
    records=[]
    matched=0
    for idx,row in enumerate(rows,1):
        url=query_url(selected_root,row)
        evidence["point_query_count"]+=1
        try:
            if synthetic:
                features=[synthetic_feature(row,idx)]
                if ambiguous and idx==2:
                    features.append(synthetic_feature(row,100+idx,offset=0.00001))
                body=canonical_json({"type":"FeatureCollection","features":features}).encode("utf-8")
                final_url=url
                status=200
            else:
                body,final_url,status=fetch(url,timeout,"application/geo+json,application/json;q=0.9")
            candidates,returned=parse_candidates(body,row)
            evidence["point_queries"].append({
                "UPRN":row["UPRN"],"request_url":url,"final_url":final_url,"http_status":status,
                "bytes":len(body),"response_sha256":sha256_bytes(body),
                "returned_feature_count":returned,"point_covering_candidate_count":len(candidates),"state":"RESPONSE"
            })
            output={**row,"source_url":final_url,"layer_root":selected_root,"candidate_count":len(candidates),"inferred":False}
            if len(candidates)==1:
                output.update({
                    "state":"MATCHED_UNIQUE_LAMBETH_CONTROLLED_PARKING_ZONE_POLYGON",
                    "official_controlled_parking_zone":True,
                    **candidates[0],
                })
                matched+=1
            elif len(candidates)>1:
                output.update({
                    "state":"NO_DATA",
                    "reason":"AMBIGUOUS_MULTIPLE_POINT_CONTAINING_CONTROLLED_PARKING_ZONE_POLYGONS",
                    "candidate_geometry_sha256":[candidate["geometry_sha256"] for candidate in candidates]
                })
            else:
                output.update({"state":"NO_DATA","reason":"NO_POINT_CONTAINING_CONTROLLED_PARKING_ZONE_POLYGON"})
        except Exception as exc:
            error=f"{type(exc).__name__}:{exc}"
            evidence["point_queries"].append({"UPRN":row["UPRN"],"request_url":url,"state":"ERROR","error":error})
            output={**row,"source_url":selected_root+"/query","layer_root":selected_root,"candidate_count":0,"state":"NO_DATA","reason":error,"inferred":False}
        records.append(output)
    return evidence,records,matched

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--timeout",type=int,default=20)
    parser.add_argument("--validate-only",action="store_true")
    parser.add_argument("--synthetic-test",action="store_true")
    parser.add_argument("--synthetic-ambiguous-test",action="store_true")
    args=parser.parse_args()
    if not 1<=args.timeout<=300:
        raise RuntimeError("INVALID_TIMEOUT")
    rows=load_rows()
    if args.validate_only:
        print(json.dumps({
            "valid":True,"input_count":3,"target_uprns":[row["UPRN"] for row in rows],
            "layer_roots":LAYER_ROOTS,"resource_class":"network",
            "metadata_request_limit":MAX_METADATA_REQUESTS,"point_query_limit":MAX_POINT_REQUESTS,
            "max_response_bytes":MAX_RESPONSE_BYTES,"write_paths":[str(path) for path in OUTPUTS]
        },sort_keys=True))
        return 0
    synthetic=args.synthetic_test or args.synthetic_ambiguous_test
    evidence,records,matched=run(rows,args.timeout,synthetic=synthetic,ambiguous=args.synthetic_ambiguous_test)
    if args.synthetic_test:
        counts=[record["candidate_count"] for record in records]
        names=[record.get("official_cpz_name") for record in records]
        if matched!=3 or counts!=[1,1,1] or names!=["CPZ-1","CPZ-2","CPZ-3"]:
            raise RuntimeError(f"SYNTHETIC_UNIQUE_FAILED:{matched}:{counts}:{names}")
        print(json.dumps({"valid":True,"matched_rows":matched,"candidate_counts":counts,"cpz_names":names},sort_keys=True))
        return 0
    if args.synthetic_ambiguous_test:
        states=[record["state"] for record in records]
        if matched!=2 or states[1]!="NO_DATA" or records[1].get("reason")!="AMBIGUOUS_MULTIPLE_POINT_CONTAINING_CONTROLLED_PARKING_ZONE_POLYGONS":
            raise RuntimeError(f"SYNTHETIC_AMBIGUOUS_FAILED:{matched}:{states}")
        print(json.dumps({"valid":True,"matched_rows":matched,"ambiguous_state":states[1]},sort_keys=True))
        return 0
    state="PUBLISHED" if matched else "NO_DATA_CONTINUE"
    result={
        "schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3",
        "task_id":"parcel-label-3-lambeth-controlled-parking-zone-point-containment-v1-20260804",
        "state":state,"panel_status":"PUBLISHED","completed_count":len(records),"target_count":3,
        "previous_percent":0.0,"progress_percent":round(len(records)/3*100,6),
        "percent_increase":round(len(records)/3*100,6),
        "matched_unique_controlled_parking_zone_rows":matched,"evidence_records":len(records),
        "source_evidence":evidence,"records":records,"unknown_attributes_promoted_to_label":False,
        "fake_data":False,"large_raw_files_committed":False,"generated_at":now()
    }
    text=canonical_json(result)+"\n"
    for output in OUTPUTS:
        atomic_write(output,text)
    print(json.dumps({
        "completed_count":len(records),"target_count":3,
        "matched_unique_controlled_parking_zone_rows":matched,
        "state":state,"output_sha256":sha256_bytes(text.encode("utf-8"))
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
