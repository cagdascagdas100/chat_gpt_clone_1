#!/usr/bin/env python3
"""Preview-only ONS postcode-centroid verifier for internet_access_1."""
from __future__ import annotations
import argparse,json,math,sys,urllib.parse,urllib.request
from pathlib import Path

ONS_QUERY_URL="https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/Online_ONS_Postcode_Directory_Live/FeatureServer/1/query"

def compact(v:str)->str:return "".join(v.upper().split())
def spaced(v:str)->str:
    v=compact(v)
    if len(v)<5:raise ValueError(f"invalid postcode: {v!r}")
    return f"{v[:-3]} {v[-3:]}"
def distance_m(a,b,c,d):
    r=6371008.8;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return r*2*math.atan2(math.sqrt(x),math.sqrt(1-x))
def classify(d):
    if d<=100:return "STRONG_OFFICIAL_ONS_CENTROID_CORROBORATION"
    if d<=250:return "SUPPORTED_OFFICIAL_ONS_CENTROID_CORROBORATION"
    if d<=300:return "BORDERLINE_OFFICIAL_ONS_CENTROID_REVIEW"
    return "OUTSIDE_300M_MANUAL_REVIEW"
def query(pc,timeout):
    where=f"PCDS='{spaced(pc).replace(chr(39),chr(39)*2)}'"
    q=urllib.parse.urlencode({"f":"json","where":where,"outFields":"PCDS,LAT,LONG,LAD25CD","returnGeometry":"false"})
    req=urllib.request.Request(f"{ONS_QUERY_URL}?{q}",headers={"User-Agent":"AAYS-internet-access-1/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as response:data=json.load(response)
    if data.get("error"):raise RuntimeError(data["error"])
    features=data.get("features") or []
    if len(features)!=1:raise RuntimeError(f"expected one ONS row, got {len(features)}")
    a=features[0]["attributes"]
    return {"postcode":compact(a["PCDS"]),"lat":float(a["LAT"]),"lon":float(a["LONG"]),"lad_code":a.get("LAD25CD"),"source_level":"OFFICIAL_ONS_POSTCODE_CENTROID"}
def fixture(path):
    obj=json.loads(path.read_text(encoding="utf-8"));obj=obj.get("postcodes",obj)
    return {compact(k):v for k,v in obj.items()}
def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True,type=Path);p.add_argument("--output",required=True,type=Path);p.add_argument("--fixture",type=Path);p.add_argument("--timeout",type=int,default=20);a=p.parse_args()
    src=json.loads(a.input.read_text(encoding="utf-8"));rows=src.get("rows") or src.get("sample_rows")
    if not isinstance(rows,list):raise ValueError("input must contain rows or sample_rows")
    fx=fixture(a.fixture) if a.fixture else None;cache={};results=[];failures=[]
    for row in rows:
        pc=compact(str(row.get("postcode","")))
        try:
            if pc not in cache:
                if fx is not None:
                    if pc not in fx:raise KeyError(f"fixture missing {pc}")
                    cache[pc]={**fx[pc],"postcode":pc,"source_level":"FIXTURE_ONLY"}
                else:cache[pc]=query(pc,a.timeout)
            o=cache[pc];d=round(distance_m(float(row["parcel_lat"]),float(row["parcel_lon"]),float(o["lat"]),float(o["lon"])),1)
            results.append({"row_no":row.get("row_no"),"parcel_id":row.get("parcel_id"),"postcode":pc,"ons_lat":float(o["lat"]),"ons_lon":float(o["lon"]),"distance_m":d,"join_confidence_class":classify(d),"source_level":o["source_level"],"internet_accuracy_changed":False})
        except Exception as e:failures.append({"row_no":row.get("row_no"),"parcel_id":row.get("parcel_id"),"postcode":pc,"error":f"{type(e).__name__}: {e}"})
    out={"schema_version":1,"slot_id":"internet_access_1","status":"PASS" if not failures else "PARTIAL_FAIL_CLOSED","official_ons_rows":len(results) if fx is None else 0,"fixture_rows":len(results) if fx is not None else 0,"failed_rows":len(failures),"results":results,"failures":failures,"internet_accuracy_upgraded_rows":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return 0 if not failures else 2
if __name__=="__main__":sys.exit(main())
