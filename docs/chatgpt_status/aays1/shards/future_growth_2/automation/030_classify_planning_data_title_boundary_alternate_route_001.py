#!/usr/bin/env python3
"""Classify the official Planning Data title-boundary alternate route from bounded evidence."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

OFFICIAL_HOSTS={"planning.data.gov.uk","www.planning.data.gov.uk"}
JSON_PATH="/entity.json"
GEOJSON_PATH="/entity.geojson"

def classify(manifest: dict) -> dict:
    sources=manifest.get("sources") or []
    fields=set()
    for src in sources:
        fields.update(src.get("supports_fields") or [])
    urls=[src.get("source_url","") for src in sources]
    official_hosts=all(urlparse(u).hostname in OFFICIAL_HOSTS for u in urls if u)
    dataset_ok="dataset_identity_title_boundary" in fields
    ogl_ok="open_government_licence" in fields
    docs_ok={"official_api_documentation","entity_api_route","dataset_filter"}.issubset(fields)
    json_urls=[u for u in urls if urlparse(u).path==JSON_PATH and parse_qs(urlparse(u).query).get("dataset")==["title-boundary"]]
    geojson_urls=[u for u in urls if urlparse(u).path==GEOJSON_PATH and parse_qs(urlparse(u).query).get("dataset")==["title-boundary"]]
    origin_caution="origin_caution_not_fully_authoritative" in fields
    route_found=bool(official_hosts and dataset_ok and ogl_ok and docs_ok and json_urls and geojson_urls and origin_caution)
    return {
      "alternate_route_found":route_found,
      "route_class":"OFFICIAL_GOVERNMENT_OPEN_DERIVED_ALTERNATE_ROUTE" if route_found else None,
      "exact_json_route":json_urls[0] if json_urls else None,
      "exact_geojson_route":geojson_urls[0] if geojson_urls else None,
      "official_host_verified":official_hosts,
      "open_government_licence_verified":ogl_ok,
      "official_api_documented":docs_ok,
      "origin_caution_preserved":origin_caution,
      "authoritative_hmlr_equivalence_verified":False,
      "direct_runner_network_availability_verified":False,
      "payload_body_persisted":False,
      "geometry_persisted":False,
      "business_rows_produced":0,
      "fake_data":False,
    }

def self_test():
    base={"sources":[
      {"source_url":"https://www.planning.data.gov.uk/dataset/title-boundary","supports_fields":["dataset_identity_title_boundary","open_government_licence","origin_caution_not_fully_authoritative"]},
      {"source_url":"https://www.planning.data.gov.uk/docs","supports_fields":["official_api_documentation","entity_api_route","dataset_filter"]},
      {"source_url":"https://www.planning.data.gov.uk/entity.json?dataset=title-boundary","supports_fields":[]},
      {"source_url":"https://www.planning.data.gov.uk/entity.geojson?dataset=title-boundary","supports_fields":[]},
    ]}
    tests=[]
    good=classify(base); tests.append({"name":"valid_route","passed":good["alternate_route_found"] and not good["authoritative_hmlr_equivalence_verified"]})
    bad=json.loads(json.dumps(base)); bad["sources"][0]["supports_fields"].remove("open_government_licence"); tests.append({"name":"ogl_required","passed":not classify(bad)["alternate_route_found"]})
    bad=json.loads(json.dumps(base)); bad["sources"][2]["source_url"]="https://example.com/entity.json?dataset=title-boundary"; tests.append({"name":"official_host_required","passed":not classify(bad)["alternate_route_found"]})
    bad=json.loads(json.dumps(base)); bad["sources"]=bad["sources"][:-1]; tests.append({"name":"both_routes_required","passed":not classify(bad)["alternate_route_found"]})
    tests.append({"name":"no_payload_or_geometry","passed":not good["payload_body_persisted"] and not good["geometry_persisted"] and good["business_rows_produced"]==0})
    passed=sum(t["passed"] for t in tests)
    return {"tests":tests,"passed":passed,"target":len(tests),"result":f"PASS_{passed}_OF_{len(tests)}"}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--manifest",type=Path); p.add_argument("--output",type=Path); p.add_argument("--task-continuation-key"); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),sort_keys=True)); return 0
    if not all((a.manifest,a.output,a.task_continuation_key)): p.error("manifest, output, and task-continuation-key required")
    m=json.loads(a.manifest.read_text()); c=classify(m); target=len(m.get("sources") or []); completed=target
    state="PUBLISHED" if c["alternate_route_found"] else "NO_DATA_CONTINUE"
    blocker="DIRECT_RUNNER_DNS_UNAVAILABLE_AND_ALTERNATE_ROUTE_NOT_AUTHORITATIVE_EQUIVALENT" if c["alternate_route_found"] else "OFFICIAL_ALTERNATE_ROUTE_NOT_FOUND"
    out={"schema_version":3,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"future_growth_2","task_continuation_key":a.task_continuation_key,"state":state,"panel_status":"PUBLISHED","completed_count":completed,"target_count":target,"progress_percent":100.0 if target else 0.0,"global_business_completed_count":0,"global_business_target_count":30761,"global_progress_percent":0.0,"produced_business_rows":0,**c,"blocker":blocker,"next_unverified_step":"VALIDATE_ONE_BOUNDED_TITLE_BOUNDARY_API_RECORD_ON_NETWORK_ENABLED_RUNNER" if c["alternate_route_found"] else "DISCOVER_ANOTHER_OFFICIAL_OR_OPEN_ALTERNATE_ROUTE"}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n")
    return 0
if __name__=="__main__": sys.exit(main())
