#!/usr/bin/env python3
"""Validate future_growth_2 Batch 015 triple-probe plan-event bundle and optional live results."""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse

ALLOWED_HOSTS={"services.arcgis.com","www.planning.data.gov.uk","gis2.london.gov.uk","gis.lambeth.gov.uk"}

def load(p:Path): return json.loads(p.read_text(encoding="utf-8"))
def sha(v:str)->str: return hashlib.sha256(v.encode("utf-8")).hexdigest()
def parse_time(v:str):
    dt=datetime.fromisoformat(v.replace("Z","+00:00"))
    assert dt.tzinfo is not None

def build_jobs(d):
    jobs=[]; n=1
    for r in d["rows"]:
        for lid,name in r["layers"]:
            jobs.append({"job_no":n,"job_id":f"META_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"ARCGIS_CHILD_METADATA_JSON","probe_family":f"LAYER_{r['row_no']}_{lid}","subject":f"{name} (layer {lid}) metadata","url":f"{r['service']}/{lid}?f=pjson","binding_policy":"METADATA_ONLY_NOT_INTERSECTION_RAW_HASH_REQUIRED"}); n+=1
    for r in d["rows"]:
        for lid,name in r["layers"]:
            q=urlencode({"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects","returnCountOnly":"true"})
            jobs.append({"job_no":n,"job_id":f"COUNT_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"ARCGIS_POINT_INTERSECTION_COUNT","probe_family":f"LAYER_{r['row_no']}_{lid}","subject":f"{name} (layer {lid}) count","url":f"{r['service']}/{lid}/query?{q}","binding_policy":"COUNT_IDS_FEATURE_THREE_WAY_MATCH_REQUIRED"}); n+=1
    for r in d["rows"]:
        for lid,name in r["layers"]:
            q=urlencode({"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects","returnIdsOnly":"true"})
            jobs.append({"job_no":n,"job_id":f"IDS_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"ARCGIS_POINT_INTERSECTION_OBJECT_IDS","probe_family":f"LAYER_{r['row_no']}_{lid}","subject":f"{name} (layer {lid}) object ids","url":f"{r['service']}/{lid}/query?{q}","binding_policy":"COUNT_IDS_FEATURE_THREE_WAY_MATCH_REQUIRED"}); n+=1
    for r in d["rows"]:
        for lid,name in r["layers"]:
            q=urlencode({"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects","outFields":"*","returnGeometry":"false"})
            jobs.append({"job_no":n,"job_id":f"FEATURE_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"ARCGIS_POINT_INTERSECTION_FEATURES","probe_family":f"LAYER_{r['row_no']}_{lid}","subject":f"{name} (layer {lid}) attributes","url":f"{r['service']}/{lid}/query?{q}","binding_policy":"COUNT_IDS_FEATURE_THREE_WAY_MATCH_PRIMARY_CROSSCHECK_REQUIRED"}); n+=1
    for r in d["rows"]:
        for ds in d["planning_datasets"]:
            pairs=[("latitude",str(r["lat"])),("longitude",str(r["lon"])),("dataset",ds),("field","name"),("field","dataset"),("field","reference"),("field","entity"),("field","quality"),("limit","100")]
            jobs.append({"job_no":n,"job_id":f"PD_{r['row_no']}_{ds.upper().replace('-','_')}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":"PLANNING_DATA_COORDINATE_QUERY","probe_family":f"PD_{r['row_no']}_{ds}","subject":ds,"url":"https://www.planning.data.gov.uk/entity.json?"+urlencode(pairs),"binding_policy":"DATASET_SPECIFIC_ZERO_NOT_GLOBAL_NEGATIVE_RAW_HASH_REQUIRED"}); n+=1
    for r in d["rows"]:
        for prefix,subject,base,type_,policy in [
            ("GLA_OA","GLA Opportunity Areas","https://gis2.london.gov.uk/server/rest/services/apps/planning_data_map_02/MapServer/103","REGIONAL_INDICATIVE_POINT_QUERY","INDICATIVE_BOUNDARY_BOROUGH_CONFIRMATION_REQUIRED"),
            ("LAMBETH_BLR","Lambeth Brownfield Register","https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBrownfieldLandRegister/MapServer/2","PRIMARY_COUNCIL_BROWNFIELD_QUERY","NON_LAMBETH_ROWS_CONTROL_PRIMARY_POLYGON_CROSSCHECK_REQUIRED")]:
            q=urlencode({"f":"json","where":"1=1","geometry":f"{r['lon']},{r['lat']}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects","outFields":"*","returnGeometry":"false"})
            jobs.append({"job_no":n,"job_id":f"{prefix}_{r['row_no']}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"query_type":type_,"probe_family":f"{prefix}_{r['row_no']}","subject":subject,"url":f"{base}/query?{q}","binding_policy":policy}); n+=1
    return jobs

def chain_for(results):
    pieces=[]
    for x in sorted(results,key=lambda z:z["job_id"]):
        pieces.append("|".join([x["job_id"],x["request_url_sha256"],x["raw_sha256"],x["fetched_at_utc"]]))
    return sha("\n".join(pieces))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,default=Path("official_triple_probe_plan_event_bundle_batch_015_20260723.json"))
    ap.add_argument("--results",type=Path)
    a=ap.parse_args(); root=load(a.data); b=a.data.parent
    parts={p["name"]:load(b/p["path"]) for p in root["parts"]}
    d={**root,**parts["manifest"],**parts["sources"],**parts["standards"],**parts["guards"]}
    d["triple_probe_gates"]=[]; d["replay_integrity_gates"]=[]
    for row in d["rows"]:
        for lid,name in row["layers"]:
            d["triple_probe_gates"].append({"code":f"TRIPLE_{row['row_no']}_{lid}","row_no":row["row_no"],"parcel_id":row["parcel_id"],"lpa":row["lpa"],"subject":f"{name} (layer {lid})","metadata_job_id":f"META_{row['row_no']}_{lid}","count_job_id":f"COUNT_{row['row_no']}_{lid}","ids_job_id":f"IDS_{row['row_no']}_{lid}","feature_job_id":f"FEATURE_{row['row_no']}_{lid}"})
            d["replay_integrity_gates"].append({"code":f"REPLAY_{row['row_no']}_{lid}","required_jobs":[f"META_{row['row_no']}_{lid}",f"COUNT_{row['row_no']}_{lid}",f"IDS_{row['row_no']}_{lid}",f"FEATURE_{row['row_no']}_{lid}"]})
    jobs=build_jobs(d)
    assert d["continuation_key"]=="5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462"
    assert [r["row_no"] for r in d["rows"]]==[30762,46142,61522]
    assert len(jobs)==150 and len({j["job_id"] for j in jobs})==150 and [j["job_no"] for j in jobs]==list(range(1,151))
    for j in jobs:
        u=urlparse(j["url"]); assert u.scheme=="https" and u.hostname in ALLOWED_HOSTS
        assert j["parcel_id"]==f"parcel_{j['row_no']}"
    kinds={}
    for j in jobs: kinds[j["query_type"]]=kinds.get(j["query_type"],0)+1
    assert kinds=={"ARCGIS_CHILD_METADATA_JSON":30,"ARCGIS_POINT_INTERSECTION_COUNT":30,"ARCGIS_POINT_INTERSECTION_OBJECT_IDS":30,"ARCGIS_POINT_INTERSECTION_FEATURES":30,"PLANNING_DATA_COORDINATE_QUERY":24,"REGIONAL_INDICATIVE_POINT_QUERY":3,"PRIMARY_COUNCIL_BROWNFIELD_QUERY":3}
    assert len(d["triple_probe_gates"])==30 and len(d["replay_integrity_gates"])==30
    assert len(d["official_sources"])==16 and sum(1 for s in d["official_sources"] if s.get("new"))==d["new_unique_official_source_pages"]==5
    assert len(d["standards"])==10 and sum(len(s["fields"]) for s in d["standards"])==40
    assert len(d["temporal_guards"])==24 and len(d["conflict_gates"])==24 and len(d["system_validations"])==11
    total=3+150+150+30+30+48+40+24+24+11
    assert total==510==d["batch_operations_total"]
    assert d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0 and d["business_coverage_pct"]==0.0
    if a.results:
        r=load(a.results)
        assert r["continuation_key"]==d["continuation_key"] and r["result_count"]==150
        rr=r["results"]; assert len(rr)==150 and len({x["job_id"] for x in rr})==150
        jm={j["job_id"]:j for j in jobs}; rm={x["job_id"]:x for x in rr}
        for x in rr:
            j=jm[x["job_id"]]
            assert x["request_url"]==j["url"]
            assert x["request_url_sha256"]==sha(x["request_url"])
            assert x["raw_sha256"]==sha(x.get("raw_body",""))
            parse_time(x["fetched_at_utc"])
            assert "http_status" in x and "content_type" in x
            assert x.get("future_growth_score") is None and x.get("confidence_pct")==0 and x.get("data_status")=="NO_DATA"
        assert r["result_chain_sha256"]==chain_for(rr)
        for g in d["triple_probe_gates"]:
            c,i,f=rm[g["count_job_id"]],rm[g["ids_job_id"]],rm[g["feature_job_id"]]
            if all(x.get("json_parse_ok") and not x.get("api_error") for x in (c,i,f)):
                cv=c.get("record_count"); iv=i.get("record_count"); fv=f.get("record_count")
                if None not in (cv,iv,fv): assert cv==iv==fv,(g["code"],cv,iv,fv)
        for g in d["replay_integrity_gates"]:
            assert all(job_id in rm for job_id in g["required_jobs"])
    print(json.dumps({"validator":"PASS","operations":total,"network_jobs":len(jobs),"new_source_pages":5,"results_validated":150 if a.results else 0},separators=(",",":")))

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(json.dumps({"validator":"FAIL","error":str(exc)},separators=(",",":")),file=sys.stderr)
        raise
