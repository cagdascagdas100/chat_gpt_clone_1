#!/usr/bin/env python3
"""Validate future_growth_2 Batch 016 geometry quad-probe bundle and optional results."""
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode,urlparse
CONTINUATION="5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462"
ALLOWED={"services.arcgis.com","www.planning.data.gov.uk","gis2.london.gov.uk","gis.lambeth.gov.uk"}
def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def dt(v):
 x=datetime.fromisoformat(v.replace("Z","+00:00"));assert x.tzinfo is not None
def jobs(d):
 a=[];n=1
 def add(x):
  nonlocal n;x["job_no"]=n;n+=1;a.append(x)
 for typ in ("META","COUNT","IDS","ATTR","GEOM"):
  for r in d["rows"]:
   for lid,name in r["layers"]:
    root=f"{r['service']}/{lid}"
    if typ=="META":u=root+"?f=pjson";q="ARCGIS_CHILD_METADATA_JSON"
    else:
     p={"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects"}
     if typ=="COUNT":p["returnCountOnly"]="true";q="ARCGIS_POINT_INTERSECTION_COUNT"
     elif typ=="IDS":p["returnIdsOnly"]="true";q="ARCGIS_POINT_INTERSECTION_OBJECT_IDS"
     elif typ=="ATTR":p.update({"outFields":"*","returnGeometry":"false"});q="ARCGIS_POINT_INTERSECTION_ATTRIBUTES"
     else:p.update({"outFields":"*","returnGeometry":"true","outSR":"4326"});q="ARCGIS_POINT_INTERSECTION_GEOMETRY"
     u=root+"/query?"+urlencode(p)
    add({"job_id":f"{typ}_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":q,"url":u})
 for r in d["rows"]:
  for ds in d["planning_datasets"]:
   p=[("latitude",str(r["lat"])),("longitude",str(r["lon"])),("dataset",ds),("field","name"),("field","dataset"),("field","reference"),("field","entity"),("field","quality"),("limit","100")]
   add({"job_id":f"PD_{r['row_no']}_{ds.upper().replace('-','_')}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"PLANNING_DATA_COORDINATE_QUERY","url":"https://www.planning.data.gov.uk/entity.json?"+urlencode(p)})
 for r in d["rows"]:
  for pref,root,qt in [("GLA_OA","https://gis2.london.gov.uk/server/rest/services/apps/planning_data_map_02/MapServer/103","REGIONAL_INDICATIVE_POINT_QUERY"),("LAMBETH_BLR","https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBrownfieldLandRegister/MapServer/2","PRIMARY_COUNCIL_BROWNFIELD_QUERY")]:
   p={"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects","outFields":"*","returnGeometry":"true","outSR":"4326"}
   add({"job_id":f"{pref}_{r['row_no']}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":qt,"url":root+"/query?"+urlencode(p)})
 return a
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--data",type=Path,required=True);ap.add_argument("--results",type=Path);z=ap.parse_args();d=load(z.data);parts={p["name"]:load(z.data.parent/p["path"]) for p in d["parts"]};m=parts["manifest"];jj=jobs(m)
 assert d["continuation_key"]==CONTINUATION and [r["row_no"] for r in m["rows"]]==[30762,46142,61522]
 assert len(jj)==180 and len({x["job_id"] for x in jj})==180 and [x["job_no"] for x in jj]==list(range(1,181))
 assert all(urlparse(x["url"]).scheme=="https" and urlparse(x["url"]).hostname in ALLOWED for x in jj)
 kinds={};[kinds.__setitem__(x["query_type"],kinds.get(x["query_type"],0)+1) for x in jj]
 assert kinds=={"ARCGIS_CHILD_METADATA_JSON":30,"ARCGIS_POINT_INTERSECTION_COUNT":30,"ARCGIS_POINT_INTERSECTION_OBJECT_IDS":30,"ARCGIS_POINT_INTERSECTION_ATTRIBUTES":30,"ARCGIS_POINT_INTERSECTION_GEOMETRY":30,"PLANNING_DATA_COORDINATE_QUERY":24,"REGIONAL_INDICATIVE_POINT_QUERY":3,"PRIMARY_COUNCIL_BROWNFIELD_QUERY":3}
 assert len(parts["quad_consistency"]["quad_probe_gates"])==30 and len(parts["geometry_gates"]["geometry_verification_gates"])==30 and len(parts["replay_gates"]["replay_integrity_gates"])==30
 assert len(parts["sources"]["official_sources"])==16 and sum(x.get("new",False) for x in parts["sources"]["official_sources"])==d["new_unique_official_source_pages"]==5
 assert len(parts["standards"]["standards"])==10 and sum(len(x["fields"]) for x in parts["standards"]["standards"])==40
 g=parts["guards"];assert len(g["temporal_guards"])==24 and len(g["conflict_gates"])==24 and len(g["system_validations"])==11
 total=3+180+180+30+30+30+48+40+24+24+11;assert total==600==d["batch_operations_total"]
 assert d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0 and d["business_coverage_pct"]==0
 if z.results:
  r=load(z.results);assert r["continuation_key"]==CONTINUATION and r["result_count"]==180;rr=r["results"];assert len(rr)==180 and len({x["job_id"] for x in rr})==180
  jm={x["job_id"]:x for x in jj};rm={x["job_id"]:x for x in rr}
  for x in rr:
   j=jm[x["job_id"]];assert x["request_url"]==j["url"] and x["request_url_sha256"]==sha(x["request_url"]) and x["raw_sha256"]==sha(x.get("raw_body",""));dt(x["fetched_at_utc"]);assert x.get("future_growth_score") is None and x.get("confidence_pct")==0 and x.get("data_status")=="NO_DATA"
  pieces="\n".join("|".join([x["job_id"],x["request_url_sha256"],x["raw_sha256"],x["fetched_at_utc"]]) for x in sorted(rr,key=lambda y:y["job_id"]));assert r["result_chain_sha256"]==sha(pieces)
  for q in parts["quad_consistency"]["quad_probe_gates"]:
   vals=[rm[q[k]].get("record_count") for k in ("count_job_id","ids_job_id","attributes_job_id","geometry_job_id")];assert all(v is not None for v in vals) and len(set(vals))==1
  for q in parts["geometry_gates"]["geometry_verification_gates"]:
   x=rm[q["geometry_job_id"]];assert x.get("record_count",0)==0 or x.get("geometry_feature_count")==x["record_count"]
 print(json.dumps({"validator":"PASS","operations":600,"network_jobs":180,"new_source_pages":5,"results_validated":180 if z.results else 0},separators=(",",":")))
if __name__=="__main__":
 try:main()
 except Exception as e:print(json.dumps({"validator":"FAIL","error":str(e)},separators=(",",":")),file=sys.stderr);raise
