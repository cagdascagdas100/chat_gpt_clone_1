#!/usr/bin/env python3
from __future__ import annotations
import copy, importlib.util, json
from pathlib import Path

def load():
    path=Path(__file__).with_name("022_validate_revision8_runner_output_v1.py")
    spec=importlib.util.spec_from_file_location("validator_v8",path)
    module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module); return module

def valid_hmlr(m):
    return {"schema_version":2,"slot_id":m.SLOT_ID,"status":"READY_HMLR_GML_DOWNLOADED","download_page":"https://use-land-property-data.service.gov.uk/datasets/inspire/download","download_page_resolved_url":"https://use-land-property-data.service.gov.uk/datasets/inspire/download","download_page_sha256":"b"*64,"authority_count":1,"prepared_authority_count":1,"resolve_only":False,"records":[{"download_link":{"url":"https://use-land-property-data.service.gov.uk/download/barking.gml"},"resolved_url":"https://use-land-property-data.service.gov.uk/download/barking.gml","size_bytes":100,"raw_sha256":"c"*64,"vectors":[{"path":"x.gml","size_bytes":90,"sha256":"d"*64}]}],"blocked":[],"nearest_or_fuzzy_authority_match_used":False,"actual_business_data_rows_written":0,"final_ready":False}

def valid_geometry(m):
    return {"slot_id":m.SLOT_ID,"state":"COMPLETED_SOURCE_GEOMETRY_WAVE","status":"COMPLETED_EXACT_OFFICIAL_GEOMETRY_WAVE_SIX_PARCELS_NO_SCORE","acceptance":{k:True for k in m.EXPECTED_GEOMETRY_ACCEPTANCE_KEYS},"source_steps":{"gla_brownfield":{"ok":True,"url":"https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/FeatureServer/101/query?f=geojson","http_status":200,"content_type":"application/geo+json","bytes":1000,"sha256":"e"*64,"feature_count":5,"current_references_required":["LBBD49/XJ","LBBD64/XE","LBBD72/ZZ","LBBD91/DI"],"current_references_present":["LBBD49/XJ","LBBD64/XE","LBBD72/ZZ","LBBD91/DI"],"optional_stale_references_present":["LBBD23"],"optional_stale_references_missing":[]},"hmlr_preparer_execution":{"exit_code":0},"hmlr_source_manifest":valid_hmlr(m),"relation_builder_execution":{"exit_code":0}},"relation_result":{"counts":{"exact_hmlr_parcel_polygons":6,"current_gla_site_polygons":4,"current_polygon_relations_verified":14,"stale_or_completed_rejections":1,"scored_business_rows":0,"actual_business_data_rows_written":0},"quality_gates":{"nearest_polygon_fill_used":False,"point_only_promotion_used":False}},"source_sha256":{k:"f"*64 for k in m.EXPECTED_GEOMETRY_SOURCE_SHA_KEYS},"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def valid_query_rows():
    return [{"row_no":i,"request_url":f"https://www.planning.data.gov.uk/entity.json?row={i}","response_path":f"docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/row_{i:05d}.json","response_sha256":"1"*64,"entity_count":0,"zero_result_semantics":"NO_DATA_COVERAGE_NOT_PROOF","promotion_eligible":False,"score":None} for i in range(1,20)]

def valid_payload(m):
    return {"schema_version":8,"workstream_id":m.WORKSTREAM_ID,"slot_id":m.SLOT_ID,"task_id":m.TASK_ID,"attempt_id":m.ATTEMPT_ID,"contract_revision":m.CONTRACT_REVISION,"revision7_bug_fixed":m.BUG_FIX_MARKER,"state":m.COMPLETED_STATE,"status":m.COMPLETED_STATUS,"source_steps":{k:{"exit_code":0} for k in m.REQUIRED_SOURCE_STEPS},"queue_request_contract_selftest":{"result":"10/10 PASS","cases":[{"name":f"c{i}","pass":True} for i in range(10)]},"queue_request_contract_validation":{"result":"PASS","checks_passed":22,"checks_total":22,"source_rows_validated":16,"example_rows_validated":10,"runner_execution_claimed":False,"loader_execution_claimed":False,"polygon_relation_claimed":False,"business_progress_claimed":False,"final_ready":False},"rows_20_24_extractor_selftest":{"result":"PASS","passed":6,"total":6},"relation_pair_contract_selftest":{"result":"PASS","passed":7,"total":7},"relation_pair_contract_validation":{"result":"PASS","pair_rows_validated":15,"current_pairs":14,"stale_pairs":1,"polygon_relation_claimed":False},"rows_20_24_acceptance":{k:True for k in m.EXPECTED_ROW_ACCEPTANCE_KEYS},"geometry_status":valid_geometry(m),"planning_query_evidence":{"manifest_sha256":"2"*64,"request_count":19,"dataset_screens":133,"dry_run":False,"network_requests_executed":19,"rows_completed":19,"rows":valid_query_rows(),"promotion_eligible_rows":0,"scores_emitted":0,"final_ready":False},"planning_query_validation":{"result":"PASS","rows_validated":19,"polygon_relation_claimed":False},"planning_query_acceptance":{k:True for k in m.EXPECTED_QUERY_ACCEPTANCE_KEYS},"canonical_rows_20_24_extracted":5,"official_site_polygons_downloaded":4,"exact_hmlr_parcel_polygons":6,"verified_polygon_relations":14,"planning_query_requests_executed":19,"planning_query_rows_validated":19,"source_wave_parcel_rows_promoted":0,"scored_business_rows":0,"actual_business_data_rows_written":0,"source_sha256":{k:"a"*64 for k in m.EXPECTED_SOURCE_SHA_KEYS},"next_unverified_step":"BUILD_ROWS_20_24_CANDIDATES_AND_FULL_30761_FACTOR_MATRIX","final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def main():
    m=load(); base=valid_payload(m); fixtures=[("exact_output",base,"PASS")]
    def add(name,fn):
        p=copy.deepcopy(base); fn(p); fixtures.append((name,p,"FAIL"))
    add("old_completion_status",lambda p:p.__setitem__("status","COMPLETED_REVISION8_CORRECTED_EXACT_ROWS_GEOMETRY_AND_19_QUERIES_NO_SCORE"))
    add("missing_queue_preflight_step",lambda p:p["source_steps"].pop("queue_request_contract_validation"))
    add("queue_selftest_incomplete",lambda p:p["queue_request_contract_selftest"].__setitem__("result","9/10 PASS"))
    add("queue_gate_count_wrong",lambda p:p["queue_request_contract_validation"].__setitem__("checks_passed",21))
    add("forty_char_source_sha",lambda p:p["source_sha256"].__setitem__("entry_v8","0"*40))
    add("gla_wrong_host",lambda p:p["geometry_status"]["source_steps"]["gla_brownfield"].__setitem__("url","https://example.com/query"))
    add("gla_missing_current_site",lambda p:p["geometry_status"]["source_steps"]["gla_brownfield"]["current_references_present"].pop())
    add("hmlr_empty_payload",lambda p:p["geometry_status"]["source_steps"]["hmlr_source_manifest"]["records"][0].__setitem__("size_bytes",0))
    add("hmlr_wrong_host",lambda p:p["geometry_status"]["source_steps"]["hmlr_source_manifest"]["records"][0].__setitem__("resolved_url","https://example.com/file.gml"))
    add("relation_count_13",lambda p:p["geometry_status"]["relation_result"]["counts"].__setitem__("current_polygon_relations_verified",13))
    add("point_only_promotion",lambda p:p["geometry_status"]["relation_result"]["quality_gates"].__setitem__("point_only_promotion_used",True))
    add("query_wrong_host",lambda p:p["planning_query_evidence"]["rows"][0].__setitem__("request_url","https://example.com/entity.json"))
    add("query_missing_sha",lambda p:p["planning_query_evidence"]["rows"][0].__setitem__("response_sha256","bad"))
    add("zero_result_semantics_missing",lambda p:p["planning_query_evidence"]["rows"][0].__setitem__("zero_result_semantics",None))
    add("query_promotion_claim",lambda p:p["planning_query_evidence"]["rows"][0].__setitem__("promotion_eligible",True))
    add("business_row_claim",lambda p:p.__setitem__("actual_business_data_rows_written",1))
    add("cross_slot_token",lambda p:p.__setitem__("note","future_growth_2"))
    results=[{"name":n,"expected":e,"actual":m.validate(p)["result"],"result":m.validate(p)["result"]==e} for n,p,e in fixtures]
    passed=sum(x["result"] for x in results)
    print(json.dumps({"schema_version":2,"slot_id":"future_growth_1","result":"PASS" if passed==len(results) else "FAIL","passed":passed,"total":len(results),"cases":results,"actual_business_data_rows_written":0,"final_ready":False},ensure_ascii=False))
    return 0 if passed==len(results) else 2
if __name__=="__main__": raise SystemExit(main())
