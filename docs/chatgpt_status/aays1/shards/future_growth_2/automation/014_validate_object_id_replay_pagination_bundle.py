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
def qp(r,x):
 p={"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects"};p.update(x);return urlencode(p)
def jobs(m):
 a=[]
 def add(x):x["job_no"]=len(a)+1;a.append(x)
 for typ in ("META","COUNT","IDS","ATTR","GEOM4326","GEOM27700","EXTENT"):
  for r in m["rows"]:
   for lid,name in r["layers"]:
    root=f"{r['service']}/{lid}"
    if typ=="META":u=root+"?f=pjson";qt="ARCGIS_CHILD_METADATA_JSON"
    elif typ=="COUNT":u=root+"/query?"+qp(r,{"returnCountOnly":"true"});qt="ARCGIS_POINT_INTERSECTION_COUNT"
    elif typ=="IDS":u=root+"/query?"+qp(r,{"returnIdsOnly":"true"});qt="ARCGIS_POINT_INTERSECTION_OBJECT_IDS"
    elif typ=="ATTR":u=root+"/query?"+qp(r,{"outFields":"*","returnGeometry":"false"});qt="ARCGIS_POINT_INTERSECTION_ATTRIBUTES"
    elif typ=="GEOM4326":u=root+"/query?"+qp(r,{"outFields":"*","returnGeometry":"true","outSR":"4326"});qt="ARCGIS_POINT_INTERSECTION_GEOMETRY_WGS84"
    elif typ=="GEOM27700":u=root+"/query?"+qp(r,{"outFields":"*","returnGeometry":"true","outSR":"27700"});qt="ARCGIS_POINT_INTERSECTION_GEOMETRY_BNG"
    else:u=root+"/query?"+qp(r,{"returnExtentOnly":"true","outSR":"4326"});qt="ARCGIS_POINT_INTERSECTION_EXTENT"
    add({"job_id":f"{typ}_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":qt,"url":u,"root":root})
 for r in m["rows"]:
  for ds in m["planning_datasets"]:
   p=[("latitude",str(r["lat"])),("longitude",str(r["lon"])),("dataset",ds),("field","name"),("field","dataset"),("field","reference"),("field","entity"),("field","quality"),("limit","100")]
   add({"job_id":f"PD_{r['row_no']}_{ds.upper().replace('-','_')}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"PLANNING_DATA_COORDINATE_QUERY","url":"https://www.planning.data.gov.uk/entity.json?"+urlencode(p)})
 for r in m["rows"]:
  for pref,root in [("GLA_OA","https://gis2.london.gov.uk/server/rest/services/apps/planning_data_map_02/MapServer/103"),("LAMBETH_BLR","https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBrownfieldLandRegister/MapServer/2")]:
   add({"job_id":f"{pref}_{r['row_no']}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"REGIONAL_OR_PRIMARY_GEOMETRY_QUERY","url":root+"/query?"+qp(r,{"outFields":"*","returnGeometry":"true","outSR":"4326"})})
 for r in m["rows"]:
  for lid,name in r["layers"]:
   add({"job_id":f"IDREPLAY_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"DYNAMIC_OBJECT_ID_REPLAY","url":None,"root":f"{r['service']}/{lid}","dependency_job_id":f"IDS_{r['row_no']}_{lid}"})
 return a
def expected_replay_url(j,ids):
 ids=sorted(set(ids or []),key=lambda x:(str(type(x)),str(x)))
 p={"f":"json","outFields":"*","returnGeometry":"true","outSR":"4326"}
 if ids:p["objectIds"]=",".join(map(str,ids))
 else:p["where"]="1=0"
 return j["root"]+"/query?"+urlencode(p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--data",type=Path,required=True);ap.add_argument("--results",type=Path);z=ap.parse_args();d=load(z.data);parts={q["name"]:load(z.data.parent/q["path"]) for q in d["parts"]};m=parts["manifest"];jj=jobs(m)
 assert d["continuation_key"]==CONT and [r["row_no"] for r in m["rows"]]==[30762,46142,61522]
 assert len(jj)==270 and len({x["job_id"] for x in jj})==270 and [x["job_no"] for x in jj]==list(range(1,271))
 assert sum(x["query_type"]=="DYNAMIC_OBJECT_ID_REPLAY" for x in jj)==30
 assert all(x["url"] is None or (urlparse(x["url"]).scheme=="https" and urlparse(x["url"]).hostname in ALLOWED) for x in jj)
 s=parts["sources"]["official_sources"];assert len(s)==16 and sum(x.get("new",False) for x in s)==d["new_unique_official_source_pages"]==5
 assert len(parts["standards"]["standards"])==10 and sum(len(x["fields"]) for x in parts["standards"]["standards"])==40
 g=parts["gates"]
 assert g["generated_layer_gate_families"]==["SEPT_PROBE_CONSISTENCY","GEOMETRY_WGS84_VERIFICATION","GEOMETRY_BNG_VERIFICATION","CRS_EQUIVALENCE","OBJECT_ID_REPLAY_VERIFICATION","TRANSFER_LIMIT_VERIFICATION","REPLAY_HASH_INTEGRITY"]
 assert len(g["temporal_guards"])==24 and len(g["conflict_gates"])==24 and len(g["system_validations"])==11
 total=3+270+270+30*7+48+40+24+24+11;assert total==900==d["batch_operations_total"]
 assert d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0 and d["business_coverage_pct"]==0
 if z.results:
  r=load(z.results);assert r["continuation_key"]==CONT and r["result_count"]==270;rr=r["results"];assert len(rr)==270 and len({x["job_id"] for x in rr})==270
  jm={x["job_id"]:x for x in jj};rm={x["job_id"]:x for x in rr}
  for x in rr:
   j=jm[x["job_id"]]
   if j["query_type"]=="DYNAMIC_OBJECT_ID_REPLAY":
    dep=rm[j["dependency_job_id"]];exp=expected_replay_url(j,dep.get("feature_ids",[]));assert x["request_url"]==exp
   else:assert x["request_url"]==j["url"]
   assert x["request_url_sha256"]==sha(x["request_url"]) and x["raw_sha256"]==sha(x.get("raw_body",""));dt(x["fetched_at_utc"]);assert x.get("future_growth_score") is None and x.get("confidence_pct")==0 and x.get("data_status")=="NO_DATA"
  pieces="\n".join("|".join([x["job_id"],x["request_url_sha256"],x["raw_sha256"],x["fetched_at_utc"]]) for x in sorted(rr,key=lambda y:y["job_id"]));assert r["result_chain_sha256"]==sha(pieces)
  for row in m["rows"]:
   for lid,name in row["layers"]:
    b=f"{row['row_no']}_{lid}";keys={"count":f"COUNT_{b}","ids":f"IDS_{b}","attr":f"ATTR_{b}","wgs":f"GEOM4326_{b}","bng":f"GEOM27700_{b}","extent":f"EXTENT_{b}","replay":f"IDREPLAY_{b}"}
    vals=[rm[keys[k]].get("record_count") for k in ("count","ids","attr","wgs","bng","extent","replay")];assert all(v is not None for v in vals) and len(set(vals))==1
    a=rm[keys["wgs"]];c=rm[keys["bng"]];replay=rm[keys["replay"]];idsr=rm[keys["ids"]]
    assert a.get("record_count",0)==0 or (a.get("geometry_feature_count")==a["record_count"] and a.get("spatial_reference_wkid")==4326)
    assert c.get("record_count",0)==0 or (c.get("geometry_feature_count")==c["record_count"] and c.get("spatial_reference_wkid")==27700)
    assert sorted(map(str,a.get("feature_ids",[])))==sorted(map(str,c.get("feature_ids",[])))
    assert sorted(map(str,idsr.get("feature_ids",[])))==sorted(map(str,replay.get("feature_ids",[])))
    for k in ("attr","wgs","bng","replay"):assert rm[keys[k]].get("exceeded_transfer_limit") is not True
 print(json.dumps({"validator":"PASS","operations":900,"network_templates":270,"new_source_pages":5,"results_validated":270 if z.results else 0},separators=(",",":")))
if __name__=="__main__":
 try:main()
 except Exception as e:print(json.dumps({"validator":"FAIL","error":str(e)},separators=(",",":")),file=sys.stderr);raise
