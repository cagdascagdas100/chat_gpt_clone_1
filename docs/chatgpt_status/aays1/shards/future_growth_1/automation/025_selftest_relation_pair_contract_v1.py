#!/usr/bin/env python3
"""Offline fixtures for exact relation-pair contract validator."""
from __future__ import annotations
import copy, importlib.util, json
from pathlib import Path


def load():
    p=Path(__file__).with_name("024_validate_relation_pair_contract_v1.py")
    s=importlib.util.spec_from_file_location("relation_validator",p)
    if s is None or s.loader is None: raise RuntimeError("load failed")
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def main():
    m=load()
    manifest=json.loads(Path(__file__).parents[1].joinpath("validation/032_revision8_relation_pair_contract_20260722.json").read_text())
    base={"candidates":[]}
    for row in manifest["pairs"]:
        base["candidates"].append({**row,"future_growth_score":None,"scorable":False,"site_geometry_verified":False,"parcel_polygon_verified":False})
    fixtures=[("exact",base,"PASS")]
    missing=copy.deepcopy(base); missing["candidates"].pop(); fixtures.append(("missing_pair",missing,"FAIL"))
    duplicate=copy.deepcopy(base); duplicate["candidates"][-1]=copy.deepcopy(duplicate["candidates"][0]); fixtures.append(("duplicate_pair",duplicate,"FAIL"))
    stale=copy.deepcopy(base); stale["candidates"][4]["source_current"]=True; fixtures.append(("stale_promoted",stale,"FAIL"))
    distance=copy.deepcopy(base); distance["candidates"][0]["point_distance_m"]+=0.1; fixtures.append(("distance_changed",distance,"FAIL"))
    score=copy.deepcopy(base); score["candidates"][0]["future_growth_score"]=1; fixtures.append(("score_present",score,"FAIL"))
    polygon=copy.deepcopy(base); polygon["candidates"][0]["site_geometry_verified"]=True; fixtures.append(("premature_polygon",polygon,"FAIL"))
    results=[]
    for name,payload,expected in fixtures:
        actual=m.validate(manifest,payload)["result"]
        results.append({"name":name,"expected":expected,"actual":actual,"result":actual==expected})
    passed=sum(x["result"] for x in results)
    print(json.dumps({"schema_version":1,"slot_id":"future_growth_1","result":"PASS" if passed==len(results) else "FAIL","passed":passed,"total":len(results),"cases":results,"actual_business_data_rows_written":0,"final_ready":False}))
    return 0 if passed==len(results) else 2


if __name__=="__main__": raise SystemExit(main())
