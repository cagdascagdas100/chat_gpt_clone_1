#!/usr/bin/env python3
"""Validate bounded Planning Data entity GeoJSON observation schema and provenance."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any

EXACT_URL = "https://www.planning.data.gov.uk/entity/12032669504.geojson"
EXPECTED_CONTINUATION = "aae4cb4e9436625e9055f30175593257a6342598982c54e4632a2014661b2ba6"
ALLOWED_TYPES = {"Feature", "FeatureCollection"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")

def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def role_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("evidence_role")): item for item in manifest.get("sources", []) if isinstance(item, dict)}

def validate(observed: dict[str, Any], receipt: dict[str, Any], manifest: dict[str, Any],
             observed_sha: str, receipt_sha: str) -> dict[str, bool]:
    o = observed.get("observation", {})
    roles = role_map(manifest)
    official = roles.get("official_exact_entity_geojson_bounded_observation", {}).get("proven", {})
    run = roles.get("github_hosted_workflow_run", {}).get("proven", {})
    artifact = roles.get("github_hosted_bounded_artifact", {}).get("proven", {})
    checks = {
        "observed_schema_v3": observed.get("schema_version") == 3 and observed.get("architecture_version") == 3,
        "observed_terminal_published": observed.get("state") == "PUBLISHED" and observed.get("panel_status") == "PUBLISHED",
        "observed_progress_exact": observed.get("completed_count") == 1 and observed.get("target_count") == 1 and observed.get("progress_percent") == 100.0,
        "exact_url_verified": observed.get("exact_official_entity_geojson_url") == EXACT_URL and o.get("exact_url_match") is True,
        "http_and_json_verified": o.get("http_status") == 200 and o.get("http_200_verified") is True and o.get("content_type_json_compatible") is True and o.get("json_parse_ok") is True,
        "bounded_size_verified": isinstance(o.get("response_byte_count"), int) and 0 < o["response_byte_count"] <= 262144 and o.get("response_size_within_limit") is True,
        "response_hash_valid": isinstance(o.get("response_sha256"), str) and HEX64.fullmatch(o["response_sha256"]) is not None,
        "rfc7946_type_verified": o.get("top_level_type") in ALLOWED_TYPES and o.get("top_level_type_rfc7946") is True,
        "entity_and_observation_verified": o.get("expected_entity_present") is True and o.get("observation_verified") is True,
        "no_network_error": observed.get("network_error") is None and observed.get("blocker") is None,
        "no_sensitive_payload_persisted": all(observed.get(k) is False for k in ("response_body_persisted","geometry_persisted","coordinates_persisted","point_persisted")) and all(o.get(k) is False for k in ("response_body_persisted","geometry_persisted","coordinates_persisted","point_persisted")),
        "no_business_rows_or_fake_data": observed.get("produced_business_rows") == 0 and observed.get("fake_data") is False,
        "receipt_matches_output": receipt.get("output_sha256") == observed_sha and receipt.get("result_state") == "PUBLISHED" and receipt.get("runner") == "github-hosted-ubuntu-latest",
        "receipt_continuation_matches": receipt.get("continuation_key") == EXPECTED_CONTINUATION == observed.get("task_continuation_key"),
        "manifest_three_roles": manifest.get("source_record_count") == 3 and set(roles) == {"official_exact_entity_geojson_bounded_observation","github_hosted_workflow_run","github_hosted_bounded_artifact"},
        "official_proven_matches": official.get("http_status") == o.get("http_status") and official.get("response_sha256") == o.get("response_sha256") and official.get("response_byte_count") == o.get("response_byte_count") and official.get("top_level_type") == o.get("top_level_type") and official.get("expected_entity_present") is True,
        "run_matches_receipt": str(run.get("run_id")) == str(receipt.get("github_run_id")) and run.get("conclusion") == "success" and run.get("status") == "completed",
        "artifact_hash_chain_matches": artifact.get("output_sha256") == observed_sha and artifact.get("execution_receipt_sha256") == receipt_sha and artifact.get("expired") is False,
        "manifest_licence_present": roles["official_exact_entity_geojson_bounded_observation"].get("terms_url") == "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    }
    return checks

def build_output(continuation_key: str, observed_path: Path, receipt_path: Path, manifest_path: Path) -> dict[str, Any]:
    observed=json.loads(observed_path.read_text())
    receipt=json.loads(receipt_path.read_text())
    manifest=json.loads(manifest_path.read_text())
    observed_sha=sha256_path(observed_path); receipt_sha=sha256_path(receipt_path); manifest_sha=sha256_path(manifest_path)
    checks=validate(observed, receipt, manifest, observed_sha, receipt_sha)
    verified=all(checks.values())
    return {
        "architecture_version":3,"schema_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id":"future_growth_2","task_continuation_key":continuation_key,
        "state":"PUBLISHED" if verified else "NO_DATA_CONTINUE",
        "panel_status":"PUBLISHED" if verified else "BLOCKED",
        "completed_count":1 if verified else 0,"target_count":1,"progress_percent":100.0 if verified else 0.0,
        "global_business_completed_count":0,"global_business_target_count":30761,"global_progress_percent":0.0,
        "produced_business_rows":0,"fake_data":False,"schema_provenance_verified":verified,
        "checks":checks,"observed_output_sha256":observed_sha,"hosted_execution_receipt_sha256":receipt_sha,
        "hosted_source_manifest_sha256":manifest_sha,"response_body_persisted":False,"geometry_persisted":False,
        "coordinates_persisted":False,"point_persisted":False,
        "blocker":None if verified else "OBSERVED_ENTITY_GEOJSON_SCHEMA_OR_PROVENANCE_VALIDATION_FAILED",
        "next_unverified_step":"CREATE_TESTED_TITLE_BOUNDARY_ENTITY_TO_PARCEL_LINKAGE_GATE" if verified else "REVIEW_FAILED_SCHEMA_PROVENANCE_CHECKS",
    }

def self_test() -> dict[str, Any]:
    observed={"architecture_version":3,"schema_version":3,"state":"PUBLISHED","panel_status":"PUBLISHED","completed_count":1,"target_count":1,"progress_percent":100.0,"exact_official_entity_geojson_url":EXACT_URL,"network_error":None,"blocker":None,"task_continuation_key":EXPECTED_CONTINUATION,"produced_business_rows":0,"fake_data":False,"response_body_persisted":False,"geometry_persisted":False,"coordinates_persisted":False,"point_persisted":False,"observation":{"exact_url_match":True,"http_status":200,"http_200_verified":True,"content_type_json_compatible":True,"json_parse_ok":True,"response_byte_count":467,"response_size_within_limit":True,"response_sha256":"a"*64,"top_level_type":"Feature","top_level_type_rfc7946":True,"expected_entity_present":True,"observation_verified":True,"response_body_persisted":False,"geometry_persisted":False,"coordinates_persisted":False,"point_persisted":False}}
    obs_sha="b"*64; rec_sha="c"*64
    receipt={"output_sha256":obs_sha,"result_state":"PUBLISHED","runner":"github-hosted-ubuntu-latest","continuation_key":EXPECTED_CONTINUATION,"github_run_id":"1"}
    manifest={"source_record_count":3,"sources":[
      {"evidence_role":"official_exact_entity_geojson_bounded_observation","terms_url":"https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/","proven":{"http_status":200,"response_sha256":"a"*64,"response_byte_count":467,"top_level_type":"Feature","expected_entity_present":True}},
      {"evidence_role":"github_hosted_workflow_run","proven":{"run_id":1,"conclusion":"success","status":"completed"}},
      {"evidence_role":"github_hosted_bounded_artifact","proven":{"output_sha256":obs_sha,"execution_receipt_sha256":rec_sha,"expired":False}}]}
    checks=validate(observed,receipt,manifest,obs_sha,rec_sha)
    tests=[("valid_fixture_all_checks",all(checks.values()))]
    bad=json.loads(json.dumps(observed)); bad["observation"]["http_status"]=404
    tests.append(("bad_http_rejected",not all(validate(bad,receipt,manifest,obs_sha,rec_sha).values())))
    bad=json.loads(json.dumps(observed)); bad["response_body_persisted"]=True
    tests.append(("body_persistence_rejected",not all(validate(bad,receipt,manifest,obs_sha,rec_sha).values())))
    bad_receipt=dict(receipt); bad_receipt["output_sha256"]="d"*64
    tests.append(("output_hash_mismatch_rejected",not all(validate(observed,bad_receipt,manifest,obs_sha,rec_sha).values())))
    bad_manifest=json.loads(json.dumps(manifest)); bad_manifest["sources"][2]["proven"]["execution_receipt_sha256"]="e"*64
    tests.append(("receipt_hash_mismatch_rejected",not all(validate(observed,receipt,bad_manifest,obs_sha,rec_sha).values())))
    bad=json.loads(json.dumps(observed)); bad["observation"]["top_level_type"]="Polygon"
    tests.append(("unexpected_top_type_rejected",not all(validate(bad,receipt,manifest,obs_sha,rec_sha).values())))
    bad=json.loads(json.dumps(observed)); bad["observation"]["expected_entity_present"]=False
    tests.append(("missing_entity_rejected",not all(validate(bad,receipt,manifest,obs_sha,rec_sha).values())))
    bad=json.loads(json.dumps(observed)); bad["fake_data"]=True
    tests.append(("fake_data_rejected",not all(validate(bad,receipt,manifest,obs_sha,rec_sha).values())))
    passed=sum(1 for _,ok in tests if ok)
    return {"tests":[{"name":n,"passed":ok} for n,ok in tests],"passed":passed,"target":len(tests),"result":f"PASS_{passed}_OF_{len(tests)}"}

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--observed-output",type=Path); p.add_argument("--execution-receipt",type=Path)
    p.add_argument("--source-manifest",type=Path); p.add_argument("--output",type=Path)
    p.add_argument("--task-continuation-key"); p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),sort_keys=True)); return 0
    if not all([a.observed_output,a.execution_receipt,a.source_manifest,a.output,a.task_continuation_key]):
        p.error("all input/output arguments are required")
    output=build_output(a.task_continuation_key,a.observed_output,a.execution_receipt,a.source_manifest)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(output,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if output["schema_provenance_verified"] else 2
if __name__=="__main__": sys.exit(main())
