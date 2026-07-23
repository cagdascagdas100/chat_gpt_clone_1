#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse

CONT="5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462"
ALLOWED={"services.arcgis.com","www.planning.data.gov.uk","gis2.london.gov.uk","gis.lambeth.gov.uk"}

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def dt(v):
    x=datetime.fromisoformat(v.replace("Z","+00:00")); assert x.tzinfo is not None
def norm_ids(a): return sorted(set(a or []), key=lambda x:(str(type(x)),str(x)))
def qp(r,x):
    p={"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects"}
    p.update(x); return urlencode(p)

def jobs(m):
    a=[]
    def add(x): x["job_no"]=len(a)+1; a.append(x)
    for typ in ("META","COUNT","IDS","ATTR","GEOM4326","GEOM27700","EXTENT"):
        for r in m["rows"]:
            for lid,name in r["layers"]:
                root=f"{r['service']}/{lid}"
                if typ=="META": u=root+"?f=pjson"; qt="ARCGIS_CHILD_METADATA_JSON"
                elif typ=="COUNT": u=root+"/query?"+qp(r,{"returnCountOnly":"true"}); qt="ARCGIS_POINT_INTERSECTION_COUNT"
                elif typ=="IDS": u=root+"/query?"+qp(r,{"returnIdsOnly":"true"}); qt="ARCGIS_POINT_INTERSECTION_OBJECT_IDS"
                elif typ=="ATTR": u=root+"/query?"+qp(r,{"outFields":"*","returnGeometry":"false"}); qt="ARCGIS_POINT_INTERSECTION_ATTRIBUTES"
                elif typ=="GEOM4326": u=root+"/query?"+qp(r,{"outFields":"*","returnGeometry":"true","outSR":"4326"}); qt="ARCGIS_POINT_INTERSECTION_GEOMETRY_WGS84"
                elif typ=="GEOM27700": u=root+"/query?"+qp(r,{"outFields":"*","returnGeometry":"true","outSR":"27700"}); qt="ARCGIS_POINT_INTERSECTION_GEOMETRY_BNG"
                else: u=root+"/query?"+qp(r,{"returnExtentOnly":"true","outSR":"4326"}); qt="ARCGIS_POINT_INTERSECTION_EXTENT"
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
            root=f"{r['service']}/{lid}"; b=f"{r['row_no']}_{lid}"
            add({"job_id":f"IDREPLAY_{b}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"DYNAMIC_OBJECT_ID_REPLAY","url":None,"root":root,"dependency_job_id":f"IDS_{b}"})
            add({"job_id":f"PAGE_{b}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"DYNAMIC_ORDERED_FIRST_WINDOW","url":None,"root":root,"ids_dependency_job_id":f"IDS_{b}","metadata_dependency_job_id":f"META_{b}"})
            add({"job_id":f"CHAIN_{b}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"DYNAMIC_FULL_PAGE_CHAIN","url":None,"root":root,"ids_dependency_job_id":f"IDS_{b}","metadata_dependency_job_id":f"META_{b}"})
    return a

def replay_url(j,ids):
    ids=norm_ids(ids); p={"f":"json","outFields":"*","returnGeometry":"true","outSR":"4326"}
    if ids: p["objectIds"]=",".join(map(str,ids))
    else: p["where"]="1=0"
    return j["root"]+"/query?"+urlencode(p)

def page_plan(j,ids,meta):
    ids=norm_ids(ids); oid=meta.get("object_id_field"); mx=meta.get("max_record_count")
    assert isinstance(oid,str) and oid
    assert isinstance(mx,int) and mx>0
    assert meta.get("supports_pagination") is True and meta.get("supports_order_by") is True
    size=min(mx,1000)
    offsets=list(range(0,len(ids),size)) if ids else [0]
    urls=[]
    for off in offsets:
        p={"f":"json","outFields":"*","returnGeometry":"true","outSR":"4326","orderByFields":f"{oid} ASC","resultOffset":str(off),"resultRecordCount":str(size)}
        if ids: p["objectIds"]=",".join(map(str,ids))
        else: p["where"]="1=0"
        urls.append((j["root"]+"/query?"+urlencode(p),off,size))
    return urls

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--results",type=Path)
    z=ap.parse_args(); d=load(z.data); parts={q["name"]:load(z.data.parent/q["path"]) for q in d["parts"]}; m=parts["manifest"]; jj=jobs(m)
    assert d["continuation_key"]==CONT and [r["row_no"] for r in m["rows"]]==[30762,46142,61522]
    assert len(jj)==330 and len({x["job_id"] for x in jj})==330 and [x["job_no"] for x in jj]==list(range(1,331))
    assert sum(x["query_type"]=="DYNAMIC_OBJECT_ID_REPLAY" for x in jj)==30
    assert sum(x["query_type"]=="DYNAMIC_ORDERED_FIRST_WINDOW" for x in jj)==30
    assert sum(x["query_type"]=="DYNAMIC_FULL_PAGE_CHAIN" for x in jj)==30
    assert all(x["url"] is None or (urlparse(x["url"]).scheme=="https" and urlparse(x["url"]).hostname in ALLOWED) for x in jj)
    s=parts["sources"]["official_sources"]; assert len(s)==16 and sum(x.get("new",False) for x in s)==d["new_unique_official_source_pages"]==5
    assert len(parts["standards"]["standards"])==10 and sum(len(x["fields"]) for x in parts["standards"]["standards"])==40
    g=parts["gates"]; assert len(g["generated_layer_gate_families"])==11 and len(g["temporal_guards"])==24 and len(g["conflict_gates"])==24 and len(g["system_validations"])==11
    total=3+330+330+30*11+48+40+24+24+11
    assert total==1140==d["batch_operations_total"]
    assert d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0 and d["business_coverage_pct"]==0
    if z.results:
        r=load(z.results); assert r["continuation_key"]==CONT and r["result_count"]==330
        rr=r["results"]; assert len(rr)==330 and len({x["job_id"] for x in rr})==330
        jm={x["job_id"]:x for x in jj}; rm={x["job_id"]:x for x in rr}
        for x in rr:
            j=jm[x["job_id"]]
            if j["query_type"]=="DYNAMIC_OBJECT_ID_REPLAY":
                exp=replay_url(j,rm[j["dependency_job_id"]].get("feature_ids",[])); assert x["request_url"]==exp
            elif j["query_type"]=="DYNAMIC_ORDERED_FIRST_WINDOW":
                plan=page_plan(j,rm[j["ids_dependency_job_id"]].get("feature_ids",[]),rm[j["metadata_dependency_job_id"]])
                exp,off,size=plan[0]; assert x["request_url"]==exp and x.get("result_offset")==off and x.get("requested_window_size")==size
            elif j["query_type"]=="DYNAMIC_FULL_PAGE_CHAIN":
                plan=page_plan(j,rm[j["ids_dependency_job_id"]].get("feature_ids",[]),rm[j["metadata_dependency_job_id"]])
                assert x["request_url"]==j["root"]+"/query"
                subs=x.get("subrequests",[]); assert len(subs)==len(plan)==x.get("page_count")
                for sub,(u,off,size) in zip(subs,plan):
                    assert sub["request_url"]==u and sub["result_offset"]==off and sub["requested_window_size"]==size
                    assert sub["request_url_sha256"]==sha(u) and sub["raw_sha256"]==sha(sub.get("raw_body","")); dt(sub["fetched_at_utc"])
                    assert sub.get("exceeded_transfer_limit") is not True
                canonical=json.dumps(subs,separators=(",",":"),sort_keys=True)
                assert x["raw_body"]==canonical and x["raw_sha256"]==sha(canonical)
            else:
                assert x["request_url"]==j["url"]
            assert x["request_url_sha256"]==sha(x["request_url"]) and x["raw_sha256"]==sha(x.get("raw_body","")); dt(x["fetched_at_utc"])
            assert x.get("future_growth_score") is None and x.get("confidence_pct")==0 and x.get("data_status")=="NO_DATA"
        pieces="\n".join("|".join([x["job_id"],x["request_url_sha256"],x["raw_sha256"],x["fetched_at_utc"]]) for x in sorted(rr,key=lambda y:y["job_id"]))
        assert r["result_chain_sha256"]==sha(pieces)
        for row in m["rows"]:
            for lid,name in row["layers"]:
                b=f"{row['row_no']}_{lid}"
                keys={"count":f"COUNT_{b}","ids":f"IDS_{b}","attr":f"ATTR_{b}","wgs":f"GEOM4326_{b}","bng":f"GEOM27700_{b}","extent":f"EXTENT_{b}","replay":f"IDREPLAY_{b}","page":f"PAGE_{b}","chain":f"CHAIN_{b}","meta":f"META_{b}"}
                meta=rm[keys["meta"]]; ids0=norm_ids(rm[keys["ids"]].get("feature_ids",[]))
                assert meta.get("supports_pagination") is True and meta.get("supports_order_by") is True and meta.get("object_id_field") and isinstance(meta.get("max_record_count"),int) and meta["max_record_count"]>0
                vals=[rm[keys[k]].get("record_count") for k in ("count","ids","attr","wgs","bng","extent","replay","chain")]
                assert all(v is not None for v in vals) and len(set(vals))==1
                assert norm_ids(rm[keys["wgs"]].get("feature_ids",[]))==norm_ids(rm[keys["bng"]].get("feature_ids",[]))
                assert norm_ids(rm[keys["replay"]].get("feature_ids",[]))==ids0
                page_ids=norm_ids(rm[keys["page"]].get("feature_ids",[]))
                assert page_ids==ids0[:rm[keys["page"]]["requested_window_size"]]
                chain=rm[keys["chain"]]; assert norm_ids(chain.get("feature_ids",[]))==ids0
                flat=[]; offsets=[]
                for sub in chain["subrequests"]:
                    flat.extend(sub.get("feature_ids",[])); offsets.append(sub["result_offset"])
                assert len(flat)==len(set(map(str,flat))) and norm_ids(flat)==ids0
                size=chain["subrequests"][0]["requested_window_size"]
                assert offsets==([0] if not ids0 else list(range(0,len(ids0),size)))
                for k in ("attr","wgs","bng","replay","page","chain"):
                    assert rm[keys[k]].get("exceeded_transfer_limit") is not True
        print(json.dumps({"validator":"PASS","operations":1140,"logical_jobs":330,"new_source_pages":5,"results_validated":330},separators=(",",":")))
    else:
        print(json.dumps({"validator":"PASS","operations":1140,"logical_jobs":330,"new_source_pages":5,"results_validated":0},separators=(",",":")))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"validator":"FAIL","error":str(e)},separators=(",",":")),file=sys.stderr); raise
