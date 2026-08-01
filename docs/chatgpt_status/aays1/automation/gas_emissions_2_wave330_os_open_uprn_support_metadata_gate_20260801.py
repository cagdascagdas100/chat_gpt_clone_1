#!/usr/bin/env python3
"""Wave330 OS Open UPRN support metadata fail-closed gate."""
import argparse, hashlib, json
from pathlib import Path

SOURCES={"canonical_wave329","canonical_parcel_sample","os_data_hub_open_uprn","os_open_uprn_product_landing","os_download_docs_landing","os_open_uprn_technical_spec","os_open_uprn_feature_type","os_open_uprn_product_supply","os_open_uprn_release_notes","os_addressbase_publication_dates","os_open_uprn_known_issues","runtime_support_and_runner_probe"}
SAMPLES={"parcel_30762","parcel_30763","parcel_30764"}
ATTRS=["UPRN","X_COORDINATE","Y_COORDINATE","LATITUDE","LONGITUDE"]

def h(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def load(p):
    v=json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise ValueError("object required")
    return v

def build(v):
    if (v.get("slot_id"),v.get("wave"))!=("gas_emissions_2",330): raise ValueError("slot/wave")
    c,s,a,m=v["canonical_context"],v["canonical_samples"],v["support_metadata_assessment"],v["source_evidence_manifest"]
    if c.get("wave329_remote_readback")!="PASS" or c.get("slot_partition")!={"start":30762,"end":61522,"count":30761}: raise ValueError("canonical gate")
    if {x.get("parcel_id") for x in s}!=SAMPLES or any(x.get("geometry_type")!="Point" or x.get("uprn") is not None for x in s): raise ValueError("sample gate")
    if a.get("product_version_date")!="June 2026" or a.get("epoch_number")!=128 or a.get("epoch_publication_date")!="2026-06-25": raise ValueError("version gate")
    if a.get("formats")!=["CSV","GeoPackage"] or a.get("coverage")!="Great Britain" or a.get("core_attributes")!=ATTRS: raise ValueError("schema gate")
    true_keys=("csv_headers_embedded","full_supply_only","no_live_known_data_issue")
    false_keys=("aoi_available","change_only_available","product_specific_downloads_page_found","standalone_header_file_found","standalone_data_dictionary_found","standalone_checksum_manifest_found","standalone_content_length_found","standalone_archive_filename_found","june_2026_release_note_found","june_2026_feature_count_found","sanctioned_existing_serial_egress_runner_found","metadata_bytes_acquired","bounded_header_bytes_acquired","archive_bytes_acquired","enfield_subset_acquired","collision_audit_performed")
    if any(a.get(k) is not True for k in true_keys) or any(a.get(k) is not False for k in false_keys): raise ValueError("support gate")
    if a.get("repository_runner_search_queries")!=3: raise ValueError("runner gate")
    by={}
    for x in m:
        sid,e=x.get("source_id"),x.get("relevant_excerpt")
        if not sid or not e or x.get("excerpt_sha256")!=h(e): raise ValueError("source hash")
        if any(not x.get(k) for k in ("publisher","source_url","accessed_at","hash_scope","supports_fields","license_or_terms_url")): raise ValueError("source fields")
        by[sid]=x
    if set(by)!=SOURCES: raise ValueError("source set")
    return {
        "schema_version":1,"slot_id":"gas_emissions_2","wave":330,"state":"NO_DATA_CONTINUE",
        "decision":"OS_OPEN_UPRN_SUPPORT_METADATA_PARTIAL_NO_DATA_CONTINUE",
        "decision_reason":"Official OS support surfaces prove the June 2026 product version, Epoch 128 publication date, full-GB CSV/GeoPackage supply and five-field schema. They do not surface a standalone header, data dictionary, checksum manifest, content length, archive filename or June 2026 feature count. CSV headers are embedded in the unavailable full file, repository search found no sanctioned serial egress runner, and zero metadata/header/archive bytes were acquired. No identity or parcel binding is promoted.",
        "canonical_context":c,"canonical_samples":s,"support_metadata_assessment":a,
        "source_count":len(m),"source_evidence_manifest":[by[k] for k in sorted(by)],
        "resolved_blockers":["OS_OPEN_UPRN_PRODUCT_VERSION_DATE_UNKNOWN","OS_OPEN_UPRN_SCHEMA_FIELDS_UNKNOWN","OS_OPEN_UPRN_SUPPORT_FILE_SURFACE_UNKNOWN","OS_OPEN_UPRN_EPOCH_128_PUBLICATION_DATE_UNKNOWN","OS_OPEN_UPRN_LIVE_KNOWN_ISSUE_STATE_UNKNOWN"],
        "remaining_blocker":"OS_OPEN_UPRN_PRODUCT_SPECIFIC_DOWNLOADS_SUPPORT_PAGE_NOT_SURFACED;STANDALONE_HEADER_DATA_DICTIONARY_CHECKSUM_CONTENT_LENGTH_AND_ARCHIVE_FILENAME_NOT_PUBLISHED_ON_AUDITED_OFFICIAL_SURFACES;JUNE_2026_RELEASE_NOTE_AND_FEATURE_COUNT_NOT_SURFACED;EXECUTION_ENVIRONMENT_DNS_EGRESS_FAILURE_PERSISTS;SANCTIONED_EXISTING_SERIAL_EGRESS_RUNNER_NOT_DISCOVERED;OS_OPEN_UPRN_METADATA_HEADER_ARCHIVE_BYTES_NOT_ACQUIRED;OS_OPEN_UPRN_ENFIELD_SUBSET_NOT_ACQUIRED;OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
        "first_unverified_step":"OS_OPEN_UPRN_FEATURES_API_ENFIELD_BBOX_AUTHENTICATION_AND_RESULT_LIMIT_GATE_OR_NO_DATA_CONTINUE",
        "business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,
        "previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,"fake_data":False,"final_ready":False
    }

def selftest():
    e="x"
    m=[{"source_id":i,"publisher":"x","source_url":"x","accessed_at":"x","hash_scope":"x","relevant_excerpt":e,"excerpt_sha256":h(e),"supports_fields":["x"],"license_or_terms_url":"x"} for i in SOURCES]
    a={"product_version_date":"June 2026","epoch_number":128,"epoch_publication_date":"2026-06-25","epoch_data_cut_date":"2026-05-22","formats":["CSV","GeoPackage"],"coverage":"Great Britain","core_attributes":ATTRS,"csv_headers_embedded":True,"full_supply_only":True,"aoi_available":False,"change_only_available":False,"product_specific_downloads_page_found":False,"standalone_header_file_found":False,"standalone_data_dictionary_found":False,"standalone_checksum_manifest_found":False,"standalone_content_length_found":False,"standalone_archive_filename_found":False,"june_2026_release_note_found":False,"june_2026_feature_count_found":False,"no_live_known_data_issue":True,"repository_runner_search_queries":3,"sanctioned_existing_serial_egress_runner_found":False,"metadata_bytes_acquired":False,"bounded_header_bytes_acquired":False,"archive_bytes_acquired":False,"enfield_subset_acquired":False,"collision_audit_performed":False}
    v={"slot_id":"gas_emissions_2","wave":330,"canonical_context":{"wave329_remote_readback":"PASS","slot_partition":{"start":30762,"end":61522,"count":30761}},"canonical_samples":[{"parcel_id":i,"geometry_type":"Point","uprn":None} for i in sorted(SAMPLES)],"support_metadata_assessment":a,"source_evidence_manifest":m}
    assert build(v)["source_count"]==12
    print("SELF_TEST_PASS")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--fixture"); p.add_argument("--output"); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: selftest(); return
    o=build(load(a.fixture)); Path(a.output).write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
    print("DECISION="+o["decision"]); print("BUSINESS_ROWS_PRODUCED=0"); print("PARCEL_ROWS_BOUND=0")
if __name__=="__main__": main()
