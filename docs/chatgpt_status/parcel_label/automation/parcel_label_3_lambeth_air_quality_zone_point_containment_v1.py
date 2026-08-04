#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from typing import Any
from shapely.geometry import Point, mapping, shape

INPUT=pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
MANIFEST=pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_air_quality_zone_point_containment_source_manifest_20260804.json")
OUTPUTS=[
 pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_air_quality_zone_point_containment_result_latest.json"),
 pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/lambeth_air_quality_zone_point_containment_latest.json"),
]
SERVICE_ROOTS=["https://gis.lambeth.gov.uk/arcgis/rest/services/LambethAirQualityZone/MapServer"]
ALLOWED_HOST="gis.lambeth.gov.uk"; MAX_RESPONSE_BYTES=8*1024*1024
ATTRIBUTE_HINTS=("objectid","air","quality","aqma","zone","name","type","status","pollut","date","year","reference","ref")

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def sha256_bytes(data): return hashlib.sha256(data).hexdigest()
def canonical_json(value): return json.dumps(value,ensure_ascii=False,separators=(",",":"),sort_keys=True)
def atomic_write(path,text):
 path.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as h: h.write(text); tmp=pathlib.Path(h.name)
 tmp.replace(path)
def safe_url(url):
 p=urllib.parse.urlsplit(url)
 if p.scheme!="https" or (p.hostname or "").casefold()!=ALLOWED_HOST or p.username or p.password or p.fragment: raise RuntimeError(f"UNSAFE_OR_UNTRUSTED_URL:{url}")
 return url
def fetch(url,timeout,accept):
 safe_url(url); req=urllib.request.Request(url,headers={"User-Agent":"AAYS-parcel-label-3/1.0","Accept":accept})
 with urllib.request.urlopen(req,timeout=timeout) as r:
  final=r.geturl(); safe_url(final); body=bytearray()
  while True:
   chunk=r.read(min(1024*1024,MAX_RESPONSE_BYTES-len(body)+1))
   if not chunk: break
   body.extend(chunk)
   if len(body)>MAX_RESPONSE_BYTES: raise RuntimeError(f"RESPONSE_TOO_LARGE:{len(body)}:{MAX_RESPONSE_BYTES}")
  return bytes(body),final,int(getattr(r,"status",200))
def load_manifest():
 p=json.loads(MANIFEST.read_text(encoding="utf-8"))
 if p.get("service_roots")!=SERVICE_ROOTS: raise RuntimeError("WRONG_MANIFEST_SERVICE_ROOTS")
 if len(p.get("target_uprns",[]))!=3: raise RuntimeError("SOURCE_MANIFEST_TARGET_COUNT")
 if len(p.get("sources",[]))<6: raise RuntimeError("SOURCE_MANIFEST_INCOMPLETE")
 d=p.get("designation_evidence",{})
 if d.get("official_label")!="Lambeth Air Quality Management Area" or d.get("pollutants")!=["NO2","PM10"] or not d.get("borough_wide_statement"): raise RuntimeError("WRONG_DESIGNATION_EVIDENCE")
 for s in p["sources"]:
  e=s.get("retained_excerpt","")
  if not e or sha256_bytes(e.encode())!=s.get("retained_excerpt_sha256"): raise RuntimeError("MANIFEST_EXCERPT_SHA_MISMATCH")
 return p
def load_rows():
 p=json.loads(INPUT.read_text(encoding="utf-8")); records=p.get("records",[]); m=load_manifest(); targets=set(m["target_uprns"])
 if len(records)!=3: raise RuntimeError(f"EXPECTED_3_INPUT_ROWS:{len(records)}")
 out=[]
 for r in records:
  req=("parcel_id","UPRN","FULLADDRESS","POSTCODE","longitude","latitude")
  if not r.get("exact_uprn_bound") or any(k not in r for k in req): raise RuntimeError("INVALID_INPUT_ROW")
  row={k:r[k] for k in req}; row["UPRN"]=str(row["UPRN"]); row["exact_uprn_bound"]=True
  if row["UPRN"] not in targets: raise RuntimeError(f"UPRN_NOT_IN_MANIFEST:{row['UPRN']}")
  out.append(row)
 if len({r["UPRN"] for r in out})!=3: raise RuntimeError("INPUT_UPRNS_NOT_UNIQUE")
 return out
def discover_layer(timeout,evidence):
 errors=[]
 for root in SERVICE_ROOTS:
  url=root+"?"+urllib.parse.urlencode({"f":"json"}); evidence["metadata_attempt_count"]+=1
  try:
   body,final,status=fetch(url,timeout,"application/json"); p=json.loads(body); layers=p.get("layers",[])
   ranked=sorted([x for x in layers if isinstance(x,dict) and isinstance(x.get("id"),int)],key=lambda x:(0 if all(t in str(x.get("name","")).casefold() for t in ("air","quality")) else 1,int(x["id"])))
   if not ranked: raise RuntimeError("SERVICE_METADATA_HAS_NO_VALID_LAYER")
   s=ranked[0]; evidence["metadata_response_count"]+=1
   evidence["metadata_requests"].append({"service_root":root,"request_url":url,"final_url":final,"http_status":status,"bytes":len(body),"response_sha256":sha256_bytes(body),"layer_count":len(layers),"selected_layer_id":int(s["id"]),"selected_layer_name":str(s.get("name","")),"state":"RESPONSE"})
   return root,int(s["id"]),str(s.get("name",""))
  except Exception as exc:
   err=f"{type(exc).__name__}:{exc}"; errors.append(err); evidence["metadata_requests"].append({"service_root":root,"request_url":url,"state":"ERROR","error":err})
 raise RuntimeError("ALL_SERVICE_METADATA_ENDPOINTS_FAILED:"+"|".join(errors))
def query_url(root,layer,row):
 params={"where":"1=1","geometry":f"{float(row['longitude']):.12f},{float(row['latitude']):.12f}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects","outFields":"*","returnGeometry":"true","outSR":"4326","f":"geojson"}
 return f"{root}/{layer}/query?"+urllib.parse.urlencode(params)
def retained_attributes(props):
 out={}
 for k in sorted(props):
  v=props[k]
  if any(h in str(k).casefold() for h in ATTRIBUTE_HINTS) and (isinstance(v,(str,int,float,bool)) or v is None): out[str(k)]=v
  if len(out)>=24: break
 return out
def parse_geojson(body,row):
 p=json.loads(body); features=p.get("features")
 if p.get("type")!="FeatureCollection" or not isinstance(features,list): raise RuntimeError("NOT_GEOJSON_FEATURE_COLLECTION")
 point=Point(float(row["longitude"]),float(row["latitude"])); candidates=[]
 for i,f in enumerate(features,1):
  if not isinstance(f,dict) or not f.get("geometry"): continue
  g=shape(f["geometry"])
  if g.is_empty or g.geom_type not in {"Polygon","MultiPolygon"}: continue
  if not g.is_valid: g=g.buffer(0)
  if g.is_empty or not g.covers(point): continue
  props=f.get("properties") if isinstance(f.get("properties"),dict) else {}; gv=mapping(g)
  candidates.append({"feature_id":f.get("id"),"feature_index":i,"geometry":gv,"geometry_sha256":sha256_bytes(canonical_json(gv).encode()),"retained_official_attributes":retained_attributes(props),"raw_attributes_sha256":sha256_bytes(canonical_json(props).encode())})
 return candidates,len(features)
def synthetic_feature(row,fid,offset=0.0):
 lon=float(row["longitude"])+offset; lat=float(row["latitude"])+offset; d=0.00008
 ring=[[lon-d,lat-d],[lon+d,lat-d],[lon+d,lat+d],[lon-d,lat+d],[lon-d,lat-d]]
 return {"type":"Feature","id":fid,"properties":{"OBJECTID":fid,"ZONE_NAME":"Lambeth Air Quality Zone","POLLUTANTS":"NO2, PM10"},"geometry":{"type":"Polygon","coordinates":[ring]}}
def run(rows,timeout,synthetic=False,ambiguous=False):
 ev={"accessed_at":now(),"service_roots":SERVICE_ROOTS,"metadata_attempt_count":0,"metadata_response_count":0,"metadata_requests":[],"point_query_count":0,"point_queries":[]}
 if synthetic: root,layer,name=SERVICE_ROOTS[0],0,"Synthetic Lambeth Air Quality Zone"
 else:
  try: root,layer,name=discover_layer(timeout,ev)
  except Exception as exc:
   err=f"{type(exc).__name__}:{exc}"; ev["discovery_error"]=err
   return ev,[{**r,"source_url":SERVICE_ROOTS[0],"candidate_count":0,"state":"NO_DATA","reason":err,"inferred":False} for r in rows],0
 ev.update({"selected_service_root":root,"selected_layer_id":layer,"selected_layer_name":name}); records=[]; matched=0
 for idx,row in enumerate(rows,1):
  url=query_url(root,layer,row); ev["point_query_count"]+=1
  try:
   if synthetic:
    feats=[synthetic_feature(row,idx)]
    if ambiguous and idx==2: feats.append(synthetic_feature(row,100+idx,0.00001))
    body=canonical_json({"type":"FeatureCollection","features":feats}).encode(); final=url; status=200
   else: body,final,status=fetch(url,timeout,"application/geo+json,application/json;q=0.9")
   candidates,returned=parse_geojson(body,row); ev["point_queries"].append({"UPRN":row["UPRN"],"request_url":url,"final_url":final,"http_status":status,"bytes":len(body),"response_sha256":sha256_bytes(body),"returned_feature_count":returned,"point_covering_candidate_count":len(candidates),"state":"RESPONSE"})
   out={**row,"source_url":final,"service_root":root,"layer_id":layer,"layer_name":name,"candidate_count":len(candidates),"inferred":False}
   if len(candidates)==1:
    out.update({"state":"MATCHED_UNIQUE_LAMBETH_AIR_QUALITY_ZONE_POLYGON","official_air_quality_management_area":True,"official_air_quality_management_area_label":"Lambeth Air Quality Management Area","official_aqma_pollutants":["NO2","PM10"],**candidates[0]}); matched+=1
   elif len(candidates)>1: out.update({"state":"NO_DATA","reason":"AMBIGUOUS_MULTIPLE_POINT_CONTAINING_AIR_QUALITY_ZONE_POLYGONS","candidate_geometry_sha256":[c["geometry_sha256"] for c in candidates]})
   else: out.update({"state":"NO_DATA","reason":"NO_POINT_CONTAINING_AIR_QUALITY_ZONE_POLYGON"})
  except Exception as exc:
   err=f"{type(exc).__name__}:{exc}"; ev["point_queries"].append({"UPRN":row["UPRN"],"request_url":url,"state":"ERROR","error":err}); out={**row,"source_url":f"{root}/{layer}/query","service_root":root,"layer_id":layer,"layer_name":name,"candidate_count":0,"state":"NO_DATA","reason":err,"inferred":False}
  records.append(out)
 return ev,records,matched
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--timeout",type=int,default=20); ap.add_argument("--validate-only",action="store_true"); ap.add_argument("--synthetic-test",action="store_true"); ap.add_argument("--synthetic-ambiguous-test",action="store_true"); args=ap.parse_args()
 if not 1<=args.timeout<=300: raise RuntimeError("INVALID_TIMEOUT")
 rows=load_rows()
 if args.validate_only:
  print(json.dumps({"valid":True,"input_count":3,"target_uprns":[r["UPRN"] for r in rows],"service_roots":SERVICE_ROOTS,"resource_class":"network","metadata_request_limit":1,"point_query_limit":3,"max_response_bytes":MAX_RESPONSE_BYTES,"write_paths":[str(p) for p in OUTPUTS]},sort_keys=True)); return 0
 synthetic=args.synthetic_test or args.synthetic_ambiguous_test; ev,records,matched=run(rows,args.timeout,synthetic,args.synthetic_ambiguous_test)
 if args.synthetic_test:
  counts=[r["candidate_count"] for r in records]; pollutants=[r.get("official_aqma_pollutants") for r in records]
  if matched!=3 or counts!=[1,1,1] or pollutants!=[["NO2","PM10"]]*3: raise RuntimeError(f"SYNTHETIC_UNIQUE_FAILED:{matched}:{counts}:{pollutants}")
  print(json.dumps({"valid":True,"matched_rows":matched,"candidate_counts":counts,"point_query_count":ev["point_query_count"],"pollutants":pollutants},sort_keys=True)); return 0
 if args.synthetic_ambiguous_test:
  states=[r["state"] for r in records]
  if matched!=2 or states[1]!="NO_DATA" or records[1].get("reason")!="AMBIGUOUS_MULTIPLE_POINT_CONTAINING_AIR_QUALITY_ZONE_POLYGONS": raise RuntimeError(f"SYNTHETIC_AMBIGUOUS_FAILED:{matched}:{states}")
  print(json.dumps({"valid":True,"matched_rows":matched,"ambiguous_state":states[1],"point_query_count":ev["point_query_count"]},sort_keys=True)); return 0
 state="PUBLISHED" if matched else "NO_DATA_CONTINUE"
 result={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":"parcel-label-3-lambeth-air-quality-zone-point-containment-v1-20260804","state":state,"panel_status":"PUBLISHED","completed_count":len(records),"target_count":3,"previous_percent":0.0,"progress_percent":round(len(records)/3*100,6),"percent_increase":round(len(records)/3*100,6),"matched_unique_air_quality_zone_rows":matched,"evidence_records":len(records),"source_evidence":ev,"records":records,"unknown_attributes_promoted_to_label":False,"fake_data":False,"large_raw_files_committed":False,"generated_at":now()}
 text=canonical_json(result)+"\n"
 for p in OUTPUTS: atomic_write(p,text)
 print(json.dumps({"completed_count":len(records),"target_count":3,"matched_unique_air_quality_zone_rows":matched,"state":state,"output_sha256":sha256_bytes(text.encode())},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
