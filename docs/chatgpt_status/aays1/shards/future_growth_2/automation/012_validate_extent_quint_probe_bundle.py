#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode,urlparse
CONT="5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462"
ALLOWED={"services.arcgis.com","www.planning.data.gov.uk","gis2.london.gov.uk","gis.lambeth.gov.uk"}
def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def dt(v):
 x=datetime.fromisoformat(v.replace("Z","+00:00"));assert x.tzinfo is not None
def params(r,x):
 p={"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects"};p.update(x);return urlencode(p)
def jobs(m):
 a=[]
 def add(x):x["job_no"]=len(a)+1;a.append(x)
 for typ in ("META","COUNT","IDS","ATTR","GEOM","EXTENT"):
  for r in m["rows"]:
   for lid,name in r["layers"]:
    root=f"{r['service']}/{lid}"
    if typ=="META":u=root+"?f=pjson";qt="ARCGIS_CHILD_METADATA_JSON"
    elif typ=="COUNT":u=root+"/query?"+params(r,{"returnCountOnly":"true"});qt="ARCGIS_POINT_INTERSECTION_COUNT"
    elif typ=="IDS":u=root+"/query?"+params(r,{"returnIdsOnly":"true"});qt="ARCGIS_POINT_INTERSECTION_OBJECT_IDS"
    elif typ=="ATTR":u=root+"/query?"+params(r,{"outFields":"*","returnGeometry":"false"});qt="ARCGIS_POINT_INTERSECTION_ATTRIBUTES"
    elif typ=="GEOM":u=root+"/query?"+params(r,{"outFields":"*","returnGeometry":"true","outSR":"4326"});qt="ARCGIS_POINT_INTERSECTION_GEOMETRY"
    else:u=root+"/query?"+params(r,{"returnExtentOnly":"true","outSR":"4326"});qt="ARCGIS_POINT_INTERSECTION_EXTENT"
    add({"job_id":f"{typ}_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":qt,"url":u})
 for r in m["rows"]:
  for ds in m["planning_datasets"]:
   p=[("latitude",str(r["lat"])),("longitude",str(r["lon"])),("dataset",ds),("field","name"),("field","dataset"),("field","reference"),("field","entity"),("field","quality"),("limit","100")]
   add({"job_id":f"PD_{r['row_no']}_{ds.upper().replace('-','_')}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"PLANNING_DATA_COORDINATE_QUERY","url":"https://www.planning.data.gov.uk/entity.json?"+urlencode(p)})
 for r in m["rows"]:
  for pref,root in [("GLA_OA","https://gis2.london.gov.uk/server/rest/services/apps/planning_data_map_02/MapServer/103"),("LAMBETH_BLR","https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBrownfieldLandRegister/MapServer/2")]:
   add({"job_id":f"{pref}_{r['row_no']}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"REGIONAL_OR_PRIMARY_GEOMETRY_QUERY","url":root+"/query?"+params(r,{"outFields":"*","returnGeometry":"true","outSR":"4326"})})
 return a
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--data",type=Path,required=True);ap.add_argument("--results",type=Path);z=ap.parse_args();d=load(z.data);parts={q["name"]:load(z.data.parent/q["path"]) for q in d["parts"]};m=parts["manifest"];jj=jobs(m)
 assert d["continuation_key"]==CONT and [r["row_no"] for r in m["rows"]]==[30762,46142,61522]
 assert len(jj)==210 and len({x["job_id"] for x in jj})==210 and [x["job_no"] for x in jj]==list(range(1,211))
 assert all(urlparse(x["url"]).scheme=="https" and urlparse(x["url"]).hostname in ALLOWED for x in jj)
 kinds={}
 for x in jj:kinds[x["query_type"]]=kinds.get(x["query_type"],0)+1
 assert kinds=={"ARCGIS_CHILD_METADATA_JSON":30,"ARCGIS_POINT_INTERSECTION_COUNT":30,"ARCGIS_POINT_INTERSECTION_OBJECT_IDS":30,"ARCGIS_POINT_INTERSECTION_ATTRIBUTES":30,"ARCGIS_POINT_INTERSECTION_GEOMETRY":30,"ARCGIS_POINT_INTERSECTION_EXTENT":30,"PLANNING_DATA_COORDINATE_QUERY":24,"REGIONAL_OR_PRIMARY_GEOMETRY_QUERY":6}
 assert len(parts["quint_consistency"]["quint_probe_gates"])==30 and len(parts["geometry_gates"]["geometry_verification_gates"])==30 and len(parts["extent_gates"]["extent_verification_gates"])==30 and len(parts["replay_gates"]["replay_integrity_gates"])==30
 assert len(parts["sources"]["official_sources"])==16 and sum(x.get("new",False) for x in parts["sources"]["official_sources"])==d["new_unique_official_source_pages"]==5
 assert len(parts["standards"]["standards"])==10 and sum(len(x["fields"]) for x in parts["standards"]["standards"])==40
 g=parts["guards"];assert len(g["temporal_guards"])==24 and len(g["conflict_gates"])==24 and len(g["system_validations"])==11
 total=3+210+210+30+30+30+30+48+40+24+24+11;assert total==690==d["batch_operations_total"]
 assert d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0 and d["business_coverage_pct"]==0
 if z.results:
  r=load(z.results);assert r["continuation_key"]==CONT and r["result_count"]==210;rr=r["results"];assert len(rr)==210 and len({x["job_id"] for x in rr})==210
  jm={x["job_id"]:x for x in jj};rm={x["job_id"]:x for x in rr}
  for x in rr:
   j=jm[x["job_id"]];assert x["request_url"]==j["url"] and x["request_url_sha256"]==sha(x["request_url"]) and x["raw_sha256"]==sha(x.get("raw_body",""));dt(x["fetched_at_utc"]);assert x.get("future_growth_score") is None and x.get("confidence_pct")==0 and x.get("data_status")=="NO_DATA"
  pieces="\n".join("|".join([x["job_id"],x["request_url_sha256"],x["raw_sha256"],x["fetched_at_utc"]]) for x in sorted(rr,key=lambda y:y["job_id"]));assert r["result_chain_sha256"]==sha(pieces)
  for q in parts["quint_consistency"]["quint_probe_gates"]:
   vals=[rm[q[k]].get("record_count") for k in ("count_job_id","ids_job_id","attributes_job_id","geometry_job_id","extent_job_id")];assert all(v is not None for v in vals) and len(set(vals))==1
   meta=rm[q["metadata_job_id"]];assert meta.get("supports_returning_query_extent") is True
  for q in parts["geometry_gates"]["geometry_verification_gates"]:
   x=rm[q["geometry_job_id"]];assert x.get("record_count",0)==0 or x.get("geometry_feature_count")==x["record_count"]
  for q in parts["extent_gates"]["extent_verification_gates"]:
   x=rm[q["extent_job_id"]];assert x.get("record_count",0)==0 or (x.get("extent_present") is True and x.get("point_within_extent") is True)
 print(json.dumps({"validator":"PASS","operations":690,"network_jobs":210,"new_source_pages":5,"results_validated":210 if z.results else 0},separators=(",",":")))
if __name__=="__main__":
 try:main()
 except Exception as e:print(json.dumps({"validator":"FAIL","error":str(e)},separators=(",",":")),file=sys.stderr);raise
