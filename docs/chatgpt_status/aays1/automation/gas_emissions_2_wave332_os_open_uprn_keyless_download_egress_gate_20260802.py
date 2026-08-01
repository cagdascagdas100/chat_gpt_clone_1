#!/usr/bin/env python3
"""Wave332 OS Open UPRN keyless download egress fail-closed gate."""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_IDS = {
    "canonical_wave331",
    "canonical_parcel_sample",
    "os_downloads_technical_spec",
    "os_download_opendata_product",
    "os_downloads_getting_started",
    "os_downloads_overview",
    "os_arcgis_open_uprn_item",
    "public_open_client_example",
    "runtime_keyless_download_probe",
    "repository_serial_egress_search",
}
SAMPLES = {"parcel_30762", "parcel_30763", "parcel_30764"}

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_json(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value

def build(fixture: dict) -> dict:
    if (fixture.get("slot_id"), fixture.get("wave")) != ("gas_emissions_2", 332):
        raise ValueError("slot/wave mismatch")
    context = fixture["canonical_context"]
    samples = fixture["canonical_samples"]
    assessment = fixture["keyless_download_assessment"]
    manifest = fixture["source_evidence_manifest"]

    if context.get("wave331_remote_readback") != "PASS":
        raise ValueError("Wave331 readback gate failed")
    if context.get("continuation_key") != "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec":
        raise ValueError("continuation mismatch")
    if context.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")
    if {row.get("parcel_id") for row in samples} != SAMPLES:
        raise ValueError("sample set mismatch")
    if any(row.get("geometry_type") != "Point" or row.get("uprn") is not None for row in samples):
        raise ValueError("sample identity gate failed")

    required_true = (
        "premium_data_package_key_required",
        "historical_public_client_example_found",
        "point_or_coordinate_guessing_forbidden",
    )
    required_false = (
        "open_data_download_api_key_required",
        "credential_present",
        "dns_resolution_succeeded",
        "product_details_bytes_acquired",
        "download_list_bytes_acquired",
        "redirect_headers_acquired",
        "redirect_object_host_discovered",
        "current_archive_filename_verified",
        "content_length_verified",
        "etag_verified",
        "last_modified_verified",
        "archive_bytes_acquired",
        "sanctioned_existing_serial_egress_workflow_found",
        "historical_filename_currently_authoritative",
        "enfield_subset_acquired",
        "coordinate_collision_audit_performed",
    )
    if any(assessment.get(key) is not True for key in required_true):
        raise ValueError("positive gate failed")
    if any(assessment.get(key) is not False for key in required_false):
        raise ValueError("negative gate failed")
    if assessment.get("product_id") != "OpenUPRN" or assessment.get("area") != "GB":
        raise ValueError("product gate failed")
    if assessment.get("formats") != ["CSV", "GeoPackage"]:
        raise ValueError("format gate failed")
    if assessment.get("metadata_success_http_code") != 200 or assessment.get("single_match_redirect_http_code") != 307:
        raise ValueError("HTTP contract mismatch")
    if assessment.get("credential_environment_variables_checked") != 6:
        raise ValueError("credential probe mismatch")
    if assessment.get("runtime_hosts_probed") != ["api.os.uk", "docs.os.uk", "osdatahub.os.uk"]:
        raise ValueError("runtime host set mismatch")
    if assessment.get("runtime_dns_results") != ["EAI_AGAIN", "EAI_AGAIN", "EAI_AGAIN"]:
        raise ValueError("runtime DNS result mismatch")
    if assessment.get("open_data_requests_probed") != 3 or assessment.get("repository_search_queries") != 3:
        raise ValueError("probe count mismatch")

    by_id = {}
    for source in manifest:
        source_id = source.get("source_id")
        excerpt = source.get("relevant_excerpt")
        if not source_id or not excerpt:
            raise ValueError("source id/excerpt missing")
        if source.get("excerpt_sha256") != sha256_text(excerpt):
            raise ValueError(f"source hash mismatch: {source_id}")
        for key in ("publisher", "source_url", "accessed_at", "hash_scope", "supports_fields", "license_or_terms_url"):
            if not source.get(key):
                raise ValueError(f"source field missing: {source_id}:{key}")
        by_id[source_id] = source
    if set(by_id) != SOURCE_IDS:
        raise ValueError("source set mismatch")

    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 332,
        "state": "NO_DATA_CONTINUE",
        "decision": "OS_OPEN_UPRN_KEYLESS_DOWNLOAD_EGRESS_GATE_NO_DATA_CONTINUE",
        "decision_reason": (
            "Official OS documentation proves that the OpenData Downloads API path for OpenUPRN does not require an API key, "
            "while Premium data packages and the alternative Features API do require credentials. The official endpoint contract "
            "returns JSON metadata with HTTP 200 or an HTTP 307 redirect when one file matches. Three keyless OpenUPRN requests "
            "could not reach that contract because api.os.uk, docs.os.uk and osdatahub.os.uk all returned EAI_AGAIN in the execution "
            "environment. No metadata, redirect header, object host, current filename or archive byte was acquired. A public 2024 "
            "client example confirms endpoint usage but its historical filename is not current authoritative evidence. No parcel binding is promoted."
        ),
        "canonical_context": context,
        "canonical_samples": samples,
        "keyless_download_assessment": assessment,
        "source_count": len(manifest),
        "source_evidence_manifest": [by_id[key] for key in sorted(by_id)],
        "resolved_blockers": [
            "OS_OPEN_UPRN_BULK_DOWNLOAD_AUTHENTICATION_REQUIREMENT_UNKNOWN",
            "OS_OPEN_UPRN_BULK_DOWNLOAD_ENDPOINT_CONTRACT_UNKNOWN",
            "OS_OPEN_UPRN_BULK_DOWNLOAD_REDIRECT_BEHAVIOUR_UNKNOWN",
            "OS_OPEN_UPRN_PRODUCT_ID_AND_GB_FILTER_UNKNOWN",
            "FEATURES_API_KEY_REQUIRED_BUT_KEYLESS_BULK_ALTERNATIVE_UNKNOWN",
        ],
        "remaining_blocker": (
            "EXECUTION_ENVIRONMENT_DNS_EGRESS_FAILURE_FOR_API_OS_UK_DOCS_OS_UK_OSDATAHUB_OS_UK;"
            "OS_DOWNLOADS_API_OPENUPRN_PRODUCT_DETAILS_METADATA_AND_REDIRECT_HEADERS_NOT_ACQUIRED;"
            "OS_OPEN_UPRN_CURRENT_ARCHIVE_FILENAME_CONTENT_LENGTH_ETAG_LAST_MODIFIED_AND_OBJECT_HOST_UNVERIFIED;"
            "SANCTIONED_EXISTING_SERIAL_EGRESS_WORKFLOW_NOT_DISCOVERED;"
            "AUTHORITATIVE_ENFIELD_SUBSET_NOT_ACQUIRED;"
            "OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;"
            "CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": (
            "OS_DOWNLOADS_API_REDIRECT_OBJECT_HOST_DISCOVERY_VIA_EXTERNAL_EGRESS_OR_PUBLIC_ARCHIVE_BYTE_RECEIPT_OR_NO_DATA_CONTINUE"
        ),
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "fake_data": False,
        "final_ready": False,
    }

def self_test() -> None:
    excerpt = "x"
    manifest = [{
        "source_id": source_id, "publisher": "x", "source_url": "x", "accessed_at": "x",
        "hash_scope": "x", "relevant_excerpt": excerpt, "excerpt_sha256": sha256_text(excerpt),
        "supports_fields": ["x"], "license_or_terms_url": "x"
    } for source_id in SOURCE_IDS]
    assessment = {
        "product_id":"OpenUPRN","open_data_download_api_key_required":False,
        "premium_data_package_key_required":True,"area":"GB","formats":["CSV","GeoPackage"],
        "metadata_endpoint":"x","redirect_endpoint":"x","metadata_success_http_code":200,
        "single_match_redirect_http_code":307,"credential_environment_variables_checked":6,
        "credential_present":False,"runtime_hosts_probed":["api.os.uk","docs.os.uk","osdatahub.os.uk"],
        "runtime_dns_results":["EAI_AGAIN","EAI_AGAIN","EAI_AGAIN"],"dns_resolution_succeeded":False,
        "open_data_requests_probed":3,"product_details_bytes_acquired":False,
        "download_list_bytes_acquired":False,"redirect_headers_acquired":False,
        "redirect_object_host_discovered":False,"current_archive_filename_verified":False,
        "content_length_verified":False,"etag_verified":False,"last_modified_verified":False,
        "archive_bytes_acquired":False,"repository_search_queries":3,
        "sanctioned_existing_serial_egress_workflow_found":False,
        "historical_public_client_example_found":True,"historical_filename_currently_authoritative":False,
        "enfield_subset_acquired":False,"coordinate_collision_audit_performed":False,
        "point_or_coordinate_guessing_forbidden":True,
    }
    fixture = {
        "slot_id":"gas_emissions_2","wave":332,
        "canonical_context":{"wave331_remote_readback":"PASS","continuation_key":"f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec","slot_partition":{"start":30762,"end":61522,"count":30761}},
        "canonical_samples":[{"parcel_id":p,"geometry_type":"Point","uprn":None} for p in sorted(SAMPLES)],
        "keyless_download_assessment":assessment,"source_evidence_manifest":manifest,
    }
    assert build(fixture)["source_count"] == 10
    print("SELF_TEST_PASS")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    result = build(load_json(args.fixture))
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    print("DECISION=" + result["decision"])
    print("BUSINESS_ROWS_PRODUCED=0")
    print("PARCEL_ROWS_BOUND=0")

if __name__ == "__main__":
    main()
