#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SLOT_ID="future_growth_1"
WORKSTREAM_ID="AAYS_21_SLOT_SAFE_PARALLEL_V1"
TASK_ID="aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID="future-growth-1-20260722-005"
CONTRACT_REVISION=8
COMPLETED_STATE="COMPLETED_SLOT_LOCAL_GEOMETRY_AND_PLANNING_QUERY_SAMPLE"
COMPLETED_STATUS="COMPLETED_REVISION8_QUEUE_REQUEST_PREFLIGHT_CORRECTED_EXACT_ROWS_GEOMETRY_AND_19_QUERIES_NO_SCORE"
BUG_FIX_MARKER="RAW_SHA256_WAS_COMPARED_TO_GIT_BLOB_SHA1"
EXPECTED_SOURCE_SHA_KEYS={"entry_v8","geometry_entry","queue_request_contract_validator","queue_request_contract_selftest","queue_manifest","source_readiness","queue_request_validation","extractor_v2","extractor_v2_selftest","relation_pair_contract_validator","relation_pair_contract_selftest","relation_pair_contract_manifest","relation_pair_contract_validation","query_executor","query_validator","rows_output","relation_output","query_evidence","query_validation"}
EXPECTED_ROW_ACCEPTANCE_KEYS={"schema_revision","semantics","canonical_git_blob_sha1","canonical_sha256","five_rows","row_numbers","parcel_ids","unique_hmlr_ids","positive_areas","no_nearest","business_zero"}
EXPECTED_QUERY_ACCEPTANCE_KEYS={"requests","rows","evidence_rows","promotion_zero","scores_zero","validation_pass","validated_rows","polygon_claim_false"}
EXPECTED_GEOMETRY_ACCEPTANCE_KEYS={"exact_hmlr_parcel_polygons","current_gla_site_polygons","current_polygon_relations_verified","stale_or_completed_rejections","nearest_polygon_fill_used","point_only_promotion_used","scored_business_rows","actual_business_data_rows_written"}
EXPECTED_GEOMETRY_SOURCE_SHA_KEYS={"gla_geojson","relation_builder","candidate_json"}
REQUIRED_SOURCE_STEPS={"queue_request_contract_selftest","queue_request_contract_validation","rows_20_24_extractor_selftest","rows_20_24_extraction","relation_pair_contract_selftest","relation_pair_contract_validation","slot_local_geometry","planning_query_execution","planning_query_validation"}
SHA256_RE=re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_CROSS_SLOT_TOKENS=("height_difference_2","future_growth_2","future_growth_3")
PLANNING_HOST="www.planning.data.gov.uk"
GLA_HOST="gis.london.gov.uk"
HMLR_HOST="use-land-property-data.service.gov.uk"

def load_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise ValueError("runner output must be a JSON object")
    return value

def all_true_exact(value:Any,expected_keys:set[str])->bool:
    return isinstance(value,dict) and set(value)==expected_keys and all(item is True for item in value.values())

def sha256_value(value:Any)->bool:
    return isinstance(value,str) and SHA256_RE.fullmatch(value) is not None

def official_https(url:Any,host:str,path_contains:str|None=None)->bool:
    if not isinstance(url,str): return False
    parsed=urlsplit(url)
    return parsed.scheme=="https" and parsed.hostname==host and (path_contains is None or path_contains in parsed.path)

def query_rows_valid(rows:Any)->bool:
    if not isinstance(rows,list) or len(rows)!=19: return False
    if [r.get("row_no") for r in rows if isinstance(r,dict)]!=list(range(1,20)): return False
    for row in rows:
        if not isinstance(row,dict): return False
        if not official_https(row.get("request_url"),PLANNING_HOST,"/entity.json"): return False
        if not sha256_value(row.get("response_sha256")): return False
        if not isinstance(row.get("response_path"),str) or "future_growth_1" not in row["response_path"]: return False
        if not isinstance(row.get("entity_count"),int) or not 0<=row["entity_count"]<=100: return False
        if row.get("promotion_eligible") is not False or row.get("score") is not None: return False
        if row["entity_count"]==0 and row.get("zero_result_semantics")!="NO_DATA_COVERAGE_NOT_PROOF": return False
        if row["entity_count"]>0 and row.get("zero_result_semantics") not in (None,""): return False
    return True

def hmlr_manifest_valid(value:Any)->bool:
    if not isinstance(value,dict): return False
    records=value.get("records")
    if not isinstance(records,list) or len(records)!=1 or not isinstance(records[0],dict): return False
    record=records[0]; vectors=record.get("vectors")
    if not isinstance(vectors,list) or not vectors: return False
    return all([
        value.get("slot_id")==SLOT_ID,value.get("status")=="READY_HMLR_GML_DOWNLOADED",
        official_https(value.get("download_page"),HMLR_HOST,"/datasets/inspire/download"),
        official_https(value.get("download_page_resolved_url"),HMLR_HOST),
        sha256_value(value.get("download_page_sha256")),value.get("authority_count")==1,
        value.get("prepared_authority_count")==1,value.get("resolve_only") is False,value.get("blocked")==[],
        official_https(record.get("download_link",{}).get("url"),HMLR_HOST),
        official_https(record.get("resolved_url"),HMLR_HOST),
        isinstance(record.get("size_bytes"),int) and record["size_bytes"]>0,sha256_value(record.get("raw_sha256")),
        all(isinstance(v,dict) and isinstance(v.get("size_bytes"),int) and v["size_bytes"]>0 and sha256_value(v.get("sha256")) for v in vectors),
        value.get("nearest_or_fuzzy_authority_match_used") is False,value.get("actual_business_data_rows_written")==0,value.get("final_ready") is False,
    ])

def gla_step_valid(value:Any)->bool:
    if not isinstance(value,dict): return False
    required={"LBBD49/XJ","LBBD64/XE","LBBD72/ZZ","LBBD91/DI"}
    present=set(value.get("current_references_present") or [])
    op=set(value.get("optional_stale_references_present") or [])
    om=set(value.get("optional_stale_references_missing") or [])
    return all([value.get("ok") is True,official_https(value.get("url"),GLA_HOST,"/FeatureServer/101/query"),value.get("http_status")==200,"json" in str(value.get("content_type") or "").lower(),isinstance(value.get("bytes"),int) and value["bytes"]>0,sha256_value(value.get("sha256")),isinstance(value.get("feature_count"),int) and value["feature_count"] in {4,5},set(value.get("current_references_required") or [])==required,present==required,op|om=={"LBBD23"},not(op&om)])

def relation_result_valid(value:Any)->bool:
    if not isinstance(value,dict): return False
    counts=value.get("counts"); gates=value.get("quality_gates")
    if not isinstance(counts,dict) or not isinstance(gates,dict): return False
    return all([counts.get("exact_hmlr_parcel_polygons")==6,counts.get("current_gla_site_polygons")==4,counts.get("current_polygon_relations_verified")==14,counts.get("stale_or_completed_rejections")==1,counts.get("scored_business_rows")==0,counts.get("actual_business_data_rows_written")==0,gates.get("nearest_polygon_fill_used") is False,gates.get("point_only_promotion_used") is False])

def validate(payload:dict[str,Any])->dict[str,Any]:
    source_steps=payload.get("source_steps"); geometry=payload.get("geometry_status")
    query_evidence=payload.get("planning_query_evidence"); query_validation=payload.get("planning_query_validation")
    source_sha=payload.get("source_sha256"); selftest=payload.get("rows_20_24_extractor_selftest")
    relation_selftest=payload.get("relation_pair_contract_selftest"); relation_validation=payload.get("relation_pair_contract_validation")
    queue_selftest=payload.get("queue_request_contract_selftest"); queue_validation=payload.get("queue_request_contract_validation")
    geometry_steps=geometry.get("source_steps") if isinstance(geometry,dict) else None
    geometry_source_sha=geometry.get("source_sha256") if isinstance(geometry,dict) else None
    serialized=json.dumps(payload,ensure_ascii=False,sort_keys=True)
    queue_cases=queue_selftest.get("cases") if isinstance(queue_selftest,dict) else None
    checks={
      "slot_id_exact":payload.get("slot_id")==SLOT_ID,"workstream_exact":payload.get("workstream_id")==WORKSTREAM_ID,
      "task_id_exact":payload.get("task_id")==TASK_ID,"attempt_id_exact":payload.get("attempt_id")==ATTEMPT_ID,
      "contract_revision_exact":payload.get("contract_revision")==CONTRACT_REVISION,"bug_fix_marker_exact":payload.get("revision7_bug_fixed")==BUG_FIX_MARKER,
      "completed_state_exact":payload.get("state")==COMPLETED_STATE,"completed_status_exact":payload.get("status")==COMPLETED_STATUS,
      "no_blocker_on_completed_output":not payload.get("blocker"),
      "queue_selftest_pass_10_of_10":isinstance(queue_selftest,dict) and queue_selftest.get("result")=="10/10 PASS" and isinstance(queue_cases,list) and len(queue_cases)==10 and all(isinstance(c,dict) and c.get("pass") is True for c in queue_cases),
      "queue_validation_pass_22_16_10":isinstance(queue_validation,dict) and queue_validation.get("result")=="PASS" and queue_validation.get("checks_passed")==22 and queue_validation.get("checks_total")==22 and queue_validation.get("source_rows_validated")==16 and queue_validation.get("example_rows_validated")==10,
      "queue_validation_truth_flags_false":isinstance(queue_validation,dict) and queue_validation.get("runner_execution_claimed") is False and queue_validation.get("loader_execution_claimed") is False and queue_validation.get("polygon_relation_claimed") is False and queue_validation.get("business_progress_claimed") is False and queue_validation.get("final_ready") is False,
      "extractor_selftest_pass_6_of_6":isinstance(selftest,dict) and selftest.get("result")=="PASS" and selftest.get("passed")==6 and selftest.get("total")==6,
      "relation_pair_selftest_pass_7_of_7":isinstance(relation_selftest,dict) and relation_selftest.get("result")=="PASS" and relation_selftest.get("passed")==7 and relation_selftest.get("total")==7,
      "relation_pair_validation_pass_15":isinstance(relation_validation,dict) and relation_validation.get("result")=="PASS" and relation_validation.get("pair_rows_validated")==15 and relation_validation.get("current_pairs")==14 and relation_validation.get("stale_pairs")==1 and relation_validation.get("polygon_relation_claimed") is False,
      "row_acceptance_exact_all_true":all_true_exact(payload.get("rows_20_24_acceptance"),EXPECTED_ROW_ACCEPTANCE_KEYS),
      "source_steps_exact":isinstance(source_steps,dict) and set(source_steps)==REQUIRED_SOURCE_STEPS,
      "source_steps_exit_zero":isinstance(source_steps,dict) and all(isinstance(source_steps.get(k),dict) and source_steps[k].get("exit_code")==0 for k in REQUIRED_SOURCE_STEPS),
      "geometry_status_object":isinstance(geometry,dict),"geometry_slot_exact":isinstance(geometry,dict) and geometry.get("slot_id")==SLOT_ID,
      "geometry_completed":isinstance(geometry,dict) and geometry.get("state")=="COMPLETED_SOURCE_GEOMETRY_WAVE",
      "geometry_status_exact":isinstance(geometry,dict) and geometry.get("status")=="COMPLETED_EXACT_OFFICIAL_GEOMETRY_WAVE_SIX_PARCELS_NO_SCORE",
      "geometry_acceptance_exact_all_true":isinstance(geometry,dict) and all_true_exact(geometry.get("acceptance"),EXPECTED_GEOMETRY_ACCEPTANCE_KEYS),
      "geometry_gla_payload_evidence":isinstance(geometry_steps,dict) and gla_step_valid(geometry_steps.get("gla_brownfield")),
      "geometry_hmlr_payload_evidence":isinstance(geometry_steps,dict) and hmlr_manifest_valid(geometry_steps.get("hmlr_source_manifest")),
      "geometry_relation_result_exact":isinstance(geometry,dict) and relation_result_valid(geometry.get("relation_result")),
      "geometry_source_sha_exact":isinstance(geometry_source_sha,dict) and set(geometry_source_sha)==EXPECTED_GEOMETRY_SOURCE_SHA_KEYS and all(sha256_value(v) for v in geometry_source_sha.values()),
      "geometry_truth_flags_false":isinstance(geometry,dict) and geometry.get("fake_data") is False and geometry.get("db_write") is False and geometry.get("migration") is False and geometry.get("production_deploy") is False and geometry.get("final_ready") is False and geometry.get("actual_business_data_rows_written")==0,
      "query_evidence_object":isinstance(query_evidence,dict),"query_manifest_sha_valid":isinstance(query_evidence,dict) and sha256_value(query_evidence.get("manifest_sha256")),
      "query_request_count_19":isinstance(query_evidence,dict) and query_evidence.get("request_count")==19,
      "query_dataset_screens_133":isinstance(query_evidence,dict) and query_evidence.get("dataset_screens")==133,
      "query_network_requests_19":isinstance(query_evidence,dict) and query_evidence.get("network_requests_executed")==19,
      "query_rows_completed_19":isinstance(query_evidence,dict) and query_evidence.get("rows_completed")==19,
      "query_evidence_rows_exact_valid":isinstance(query_evidence,dict) and query_rows_valid(query_evidence.get("rows")),
      "query_evidence_zero_promotion_and_scores":isinstance(query_evidence,dict) and query_evidence.get("promotion_eligible_rows")==0 and query_evidence.get("scores_emitted")==0 and query_evidence.get("dry_run") is False and query_evidence.get("final_ready") is False,
      "query_validation_pass":isinstance(query_validation,dict) and query_validation.get("result")=="PASS",
      "query_validation_rows_19":isinstance(query_validation,dict) and query_validation.get("rows_validated")==19,
      "query_validation_polygon_claim_false":isinstance(query_validation,dict) and query_validation.get("polygon_relation_claimed") is False,
      "query_acceptance_exact_all_true":all_true_exact(payload.get("planning_query_acceptance"),EXPECTED_QUERY_ACCEPTANCE_KEYS),
      "canonical_rows_exact_5":payload.get("canonical_rows_20_24_extracted")==5,"official_site_polygons_exact_4":payload.get("official_site_polygons_downloaded")==4,
      "exact_hmlr_polygons_exact_6":payload.get("exact_hmlr_parcel_polygons")==6,"verified_relations_exact_14":payload.get("verified_polygon_relations")==14,
      "planning_requests_exact_19":payload.get("planning_query_requests_executed")==19,"planning_rows_validated_exact_19":payload.get("planning_query_rows_validated")==19,
      "promoted_rows_zero":payload.get("source_wave_parcel_rows_promoted")==0,"scored_rows_zero":payload.get("scored_business_rows")==0,
      "business_rows_zero":payload.get("actual_business_data_rows_written")==0,
      "source_sha_keys_exact":isinstance(source_sha,dict) and set(source_sha)==EXPECTED_SOURCE_SHA_KEYS,
      "source_sha_values_valid":isinstance(source_sha,dict) and all(sha256_value(v) for v in source_sha.values()),
      "final_ready_false":payload.get("final_ready") is False,"fake_data_false":payload.get("fake_data") is False,
      "db_write_false":payload.get("db_write") is False,"migration_false":payload.get("migration") is False,
      "production_deploy_false":payload.get("production_deploy") is False,
      "no_cross_slot_token":not any(t in serialized for t in FORBIDDEN_CROSS_SLOT_TOKENS),
      "next_step_exact":payload.get("next_unverified_step")=="BUILD_ROWS_20_24_CANDIDATES_AND_FULL_30761_FACTOR_MATRIX",
    }
    failed=[k for k,v in checks.items() if not v]
    return {"schema_version":2,"slot_id":SLOT_ID,"validation_kind":"REVISION8_RUNNER_OUTPUT_FAIL_CLOSED_ACCEPTANCE","result":"PASS" if not failed else "FAIL","checks_passed":sum(checks.values()),"checks_total":len(checks),"checks":checks,"failed_checks":failed,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("runner_output",type=Path); p.add_argument("--output",type=Path); args=p.parse_args()
    try: result=validate(load_json(args.runner_output))
    except Exception as exc: result={"schema_version":2,"slot_id":SLOT_ID,"validation_kind":"REVISION8_RUNNER_OUTPUT_FAIL_CLOSED_ACCEPTANCE","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"json_load":False},"failed_checks":[f"json_load:{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
