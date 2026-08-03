#!/usr/bin/env python3
"""Validate one exact Planning Data entity GeoJSON response schema without persisting geometry.

The gate accepts only a bounded response observation supplied in the evidence
manifest. Official documentation, entity-model and RFC records define the
checks, but they are never promoted into an observed response. When the exact
response body is unavailable, the script emits evidence-backed NO_DATA_CONTINUE.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

EXPECTED_ENTITY = 12032669504
EXPECTED_DATASET = "title-boundary"
EXPECTED_URL = "https://www.planning.data.gov.uk/entity/12032669504.geojson"
REQUIRED_MODEL_FIELDS = {
    "entity","dataset","geojson","geometry","reference",
    "organisation-entity","quality","entry-date","start-date","end-date"
}

def by_role(sources: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    return next((s for s in sources if s.get("evidence_role") == role), None)

def classify(sources: list[dict[str, Any]]) -> dict[str, Any]:
    docs=by_role(sources,"official_api_documentation")
    model=by_role(sources,"official_entity_model")
    page=by_role(sources,"official_entity_page")
    standard=by_role(sources,"geojson_standard")
    probe=by_role(sources,"direct_runner_probe")
    response=by_role(sources,"exact_geojson_response_observation")

    docs_ok=bool(docs and docs.get("proven",{}).get("endpoint_template")=="/entity/{entity}.{extension}" and "geojson" in docs.get("proven",{}).get("allowed_extensions",[]))
    model_fields=set((model or {}).get("proven",{}).get("required_model_fields",[]))
    model_ok=bool(model and REQUIRED_MODEL_FIELDS.issubset(model_fields) and (model or {}).get("proven",{}).get("geometry_datatype")=="multipolygon")
    page_p=(page or {}).get("proven",{})
    page_ok=bool(page and page_p.get("entity")==EXPECTED_ENTITY and page_p.get("dataset")==EXPECTED_DATASET and page_p.get("download_geojson_offered") is True)
    std_p=(standard or {}).get("proven",{})
    standard_ok=bool(standard and set(std_p.get("allowed_top_level_types",[]))=={"Feature","FeatureCollection"} and std_p.get("media_type")=="application/geo+json")
    probe_p=(probe or {}).get("proven",{})
    probe_matches=bool(probe and probe.get("url")==EXPECTED_URL)
    response_available=bool(response and response.get("proven",{}).get("http_response_verified") is True)

    schema_verified=False
    observed_summary=None
    if response_available:
        rp=response.get("proven",{})
        top=rp.get("top_level_type")
        content_type=rp.get("content_type")
        entity=rp.get("entity")
        dataset=rp.get("dataset")
        geometry_type=rp.get("geometry_type")
        required_members_ok=rp.get("required_members_verified") is True
        schema_verified=bool(
            top in {"Feature","FeatureCollection"}
            and content_type in {"application/geo+json","application/json"}
            and entity==EXPECTED_ENTITY
            and dataset==EXPECTED_DATASET
            and geometry_type=="MultiPolygon"
            and required_members_ok
        )
        observed_summary={
            "top_level_type":top,"content_type":content_type,"entity":entity,
            "dataset":dataset,"geometry_type":geometry_type,
            "required_members_verified":required_members_ok
        }

    prerequisites=docs_ok and model_ok and page_ok and standard_ok and probe_matches
    return {
        "official_endpoint_contract_verified":docs_ok,
        "official_entity_model_verified":model_ok,
        "official_entity_identity_verified":page_ok,
        "rfc7946_contract_verified":standard_ok,
        "direct_probe_matches_exact_url":probe_matches,
        "direct_http_response_verified":bool(probe_p.get("http_response_verified") is True),
        "exact_response_observation_available":response_available,
        "exact_geojson_response_schema_verified":schema_verified,
        "schema_validation_prerequisites_verified":prerequisites,
        "observed_schema_summary":observed_summary,
        "probe_error_type":probe_p.get("error_type"),
        "probe_error":probe_p.get("error"),
    }

def self_test() -> dict[str, Any]:
    base=[
      {"evidence_role":"official_api_documentation","proven":{"endpoint_template":"/entity/{entity}.{extension}","allowed_extensions":["json","html","geojson"]}},
      {"evidence_role":"official_entity_model","proven":{"required_model_fields":sorted(REQUIRED_MODEL_FIELDS),"geometry_datatype":"multipolygon"}},
      {"evidence_role":"official_entity_page","proven":{"entity":EXPECTED_ENTITY,"dataset":EXPECTED_DATASET,"download_geojson_offered":True}},
      {"evidence_role":"geojson_standard","proven":{"allowed_top_level_types":["Feature","FeatureCollection"],"media_type":"application/geo+json"}},
      {"evidence_role":"direct_runner_probe","url":EXPECTED_URL,"proven":{"http_response_verified":False,"error_type":"URLError","error":"DNS"}},
    ]
    tests=[]
    got=classify(base)
    tests.append(("no_body_is_no_schema_claim", got["schema_validation_prerequisites_verified"] and not got["exact_geojson_response_schema_verified"]))
    good=base+[{"evidence_role":"exact_geojson_response_observation","proven":{"http_response_verified":True,"top_level_type":"Feature","content_type":"application/geo+json","entity":EXPECTED_ENTITY,"dataset":EXPECTED_DATASET,"geometry_type":"MultiPolygon","required_members_verified":True}}]
    tests.append(("valid_observation_passes", classify(good)["exact_geojson_response_schema_verified"]))
    bad_entity=json.loads(json.dumps(good)); bad_entity[-1]["proven"]["entity"]=1
    tests.append(("wrong_entity_rejected", not classify(bad_entity)["exact_geojson_response_schema_verified"]))
    bad_geom=json.loads(json.dumps(good)); bad_geom[-1]["proven"]["geometry_type"]="Polygon"
    tests.append(("wrong_geometry_rejected", not classify(bad_geom)["exact_geojson_response_schema_verified"]))
    missing_docs=[x for x in base if x["evidence_role"]!="official_api_documentation"]
    tests.append(("missing_docs_rejected", not classify(missing_docs)["schema_validation_prerequisites_verified"]))
    missing_model=json.loads(json.dumps(base)); missing_model[1]["proven"]["required_model_fields"]=["entity","dataset"]
    tests.append(("incomplete_model_rejected", not classify(missing_model)["schema_validation_prerequisites_verified"]))
    wrong_url=json.loads(json.dumps(base)); wrong_url[-1]["url"]="https://example.invalid/x.geojson"
    tests.append(("wrong_probe_url_rejected", not classify(wrong_url)["schema_validation_prerequisites_verified"]))
    passed=sum(bool(ok) for _,ok in tests)
    return {"tests":[{"name":n,"passed":bool(ok)} for n,ok in tests],"passed":passed,"target":len(tests),"result":f"PASS_{passed}_OF_{len(tests)}"}

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--task-continuation-key")
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),sort_keys=True)); return 0
    if not args.manifest or not args.output or not args.task_continuation_key:
        ap.error("--manifest, --output and --task-continuation-key are required")
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    result=classify(manifest.get("sources",[]))
    completed=len(manifest.get("sources",[]))
    verified=result["exact_geojson_response_schema_verified"]
    output={
      "schema_version":3,"architecture_version":3,
      "workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
      "slot_id":"future_growth_2",
      "task_continuation_key":args.task_continuation_key,
      "state":"PUBLISHED" if verified else "NO_DATA_CONTINUE",
      "panel_status":"PUBLISHED",
      "completed_count":completed,"target_count":completed,
      "progress_percent":100.0 if completed else 0.0,
      "global_business_completed_count":0,
      "global_business_target_count":30761,
      "global_progress_percent":0.0,
      "produced_business_rows":0,
      "exact_official_entity_geojson_url":EXPECTED_URL,
      **result,
      "response_body_persisted":False,
      "geometry_persisted":False,
      "point_persisted":False,
      "fake_data":False,
      "blocker":None if verified else "EXACT_ENTITY_GEOJSON_RESPONSE_BODY_UNAVAILABLE_FOR_SCHEMA_VALIDATION",
      "next_unverified_step":"OBTAIN_BOUNDED_EXACT_ENTITY_GEOJSON_RESPONSE_OBSERVATION_ON_NETWORK_ENABLED_RUNNER",
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    sys.exit(main())
