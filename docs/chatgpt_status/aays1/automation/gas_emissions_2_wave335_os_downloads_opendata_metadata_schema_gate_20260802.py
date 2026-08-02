#!/usr/bin/env python3
"""Wave335 OS Downloads API OpenData metadata schema/checksum support fail-closed gate."""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_IDS = {
    "canonical_wave334",
    "canonical_parcel_sample",
    "os_downloads_api_technical_spec",
    "os_download_opendata_contract",
    "os_automating_opendata_downloads",
    "os_data_hub_open_uprn",
    "os_official_python_client",
    "cran_osdatahub_r_client",
    "open_api_response_example",
    "runtime_metadata_dns_probe",
}
SAMPLES = {"parcel_30762", "parcel_30763", "parcel_30764"}
PROVEN_METADATA_FIELDS = ["md5", "size", "url", "format", "area", "fileName"]

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_json(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value

def build(fixture: dict) -> dict:
    if (fixture.get("slot_id"), fixture.get("wave")) != ("gas_emissions_2", 335):
        raise ValueError("slot/wave mismatch")
    context = fixture["canonical_context"]
    samples = fixture["canonical_samples"]
    assessment = fixture["metadata_schema_assessment"]
    manifest = fixture["source_evidence_manifest"]

    if context.get("wave334_remote_readback") != "PASS":
        raise ValueError("Wave334 readback gate failed")
    if context.get("continuation_key") != "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec":
        raise ValueError("continuation mismatch")
    if context.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")

    if {row.get("parcel_id") for row in samples} != SAMPLES:
        raise ValueError("sample set mismatch")
    if any(row.get("geometry_type") != "Point" or row.get("uprn") is not None for row in samples):
        raise ValueError("sample identity gate failed")

    required_true = (
        "opendata_api_key_not_required",
        "metadata_list_http_200_documented",
        "single_match_redirect_http_307_documented",
        "file_name_filter_supported",
        "format_filter_supported",
        "subformat_filter_supported",
        "area_filter_supported",
        "redirect_filter_supported",
        "md5_checksum_field_supported",
        "size_field_supported",
        "download_url_field_supported",
        "point_or_coordinate_guessing_forbidden",
    )
    required_false = (
        "official_openapi_schema_artifact_acquired",
        "current_open_uprn_metadata_bytes_acquired",
        "current_open_uprn_file_name_verified",
        "current_open_uprn_size_verified",
        "current_open_uprn_md5_verified",
        "current_open_uprn_object_url_verified",
        "enfield_subset_acquired",
        "coordinate_collision_audit_performed",
    )
    if any(assessment.get(key) is not True for key in required_true):
        raise ValueError("positive schema gate failed")
    if any(assessment.get(key) is not False for key in required_false):
        raise ValueError("negative schema gate failed")
    if assessment.get("proven_metadata_fields") != PROVEN_METADATA_FIELDS:
        raise ValueError("metadata field set mismatch")
    if assessment.get("runtime_hosts_probed") != ["api.os.uk", "docs.os.uk", "osdatahub.os.uk"]:
        raise ValueError("runtime host set mismatch")
    if assessment.get("runtime_dns_results") != [
        "EAI_AGAIN_OR_UNRESOLVED",
        "EAI_AGAIN_OR_UNRESOLVED",
        "EAI_AGAIN_OR_UNRESOLVED",
    ]:
        raise ValueError("runtime DNS result mismatch")
    if assessment.get("direct_http_codes") != [0, 0, 0] or assessment.get("direct_response_bytes") != [0, 0, 0]:
        raise ValueError("runtime request receipt mismatch")

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
        "wave": 335,
        "state": "NO_DATA_CONTINUE",
        "decision": "OS_DOWNLOADS_API_OPENDATA_METADATA_SCHEMA_AND_MD5_SUPPORT_NO_DATA_CONTINUE",
        "decision_reason": (
            "Official OS documentation proves the keyless OpenData endpoint, HTTP 200 metadata-list and HTTP 307 single-match redirect contracts, "
            "and the fileName, format, subformat, area and redirect filters. Open OS clients and reproducible response examples prove a common "
            "download-file metadata object containing md5, size, url, format, area and fileName, and the R client verifies downloaded bytes against md5. "
            "However, no official OpenAPI schema artifact or live current OpenUPRN metadata response was acquired because api.os.uk, docs.os.uk and "
            "osdatahub.os.uk remain unresolved in the execution environment. Therefore current filename, size, MD5 and object URL remain unverified; "
            "no Enfield subset, coordinate collision audit or exact parcel binding is promoted."
        ),
        "canonical_context": context,
        "canonical_samples": samples,
        "metadata_schema_assessment": assessment,
        "source_count": len(manifest),
        "source_evidence_manifest": [by_id[key] for key in sorted(by_id)],
        "resolved_blockers": [
            "OS_DOWNLOADS_API_OPENDATA_AUTHENTICATION_REQUIREMENT_UNKNOWN",
            "OS_DOWNLOADS_API_METADATA_HTTP_CONTRACT_UNKNOWN",
            "OS_DOWNLOADS_API_REDIRECT_HTTP_CONTRACT_UNKNOWN",
            "OS_DOWNLOADS_API_COMMON_FILE_METADATA_FIELDS_UNKNOWN",
            "OS_DOWNLOADS_API_MD5_CHECKSUM_FIELD_SUPPORT_UNKNOWN",
            "OS_DOWNLOADS_API_SIZE_FIELD_SUPPORT_UNKNOWN",
        ],
        "remaining_blocker": (
            "OFFICIAL_OS_DOWNLOADS_OPENAPI_SCHEMA_ARTIFACT_NOT_ACQUIRED;"
            "CURRENT_OPENUPRN_METADATA_RESPONSE_BYTES_NOT_ACQUIRED;"
            "CURRENT_OPENUPRN_FILENAME_SIZE_MD5_AND_OBJECT_URL_UNVERIFIED;"
            "EXECUTION_ENVIRONMENT_DNS_EGRESS_FAILURE_FOR_API_OS_UK_DOCS_OS_UK_OSDATAHUB_OS_UK;"
            "AUTHORITATIVE_ENFIELD_SUBSET_NOT_ACQUIRED;"
            "OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;"
            "CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": (
            "OS_DOWNLOADS_API_OFFICIAL_OPENAPI_SCHEMA_OR_LIVE_OPENUPRN_METADATA_RECEIPT_ACQUISITION_OR_NO_DATA_CONTINUE"
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
    manifest = [
        {
            "source_id": source_id,
            "publisher": "x",
            "source_url": "x",
            "accessed_at": "x",
            "hash_scope": "x",
            "relevant_excerpt": excerpt,
            "excerpt_sha256": sha256_text(excerpt),
            "supports_fields": ["x"],
            "license_or_terms_url": "x",
        }
        for source_id in SOURCE_IDS
    ]
    assessment = {
        "opendata_api_key_not_required": True,
        "metadata_list_http_200_documented": True,
        "single_match_redirect_http_307_documented": True,
        "file_name_filter_supported": True,
        "format_filter_supported": True,
        "subformat_filter_supported": True,
        "area_filter_supported": True,
        "redirect_filter_supported": True,
        "proven_metadata_fields": PROVEN_METADATA_FIELDS,
        "md5_checksum_field_supported": True,
        "size_field_supported": True,
        "download_url_field_supported": True,
        "official_openapi_schema_artifact_acquired": False,
        "current_open_uprn_metadata_bytes_acquired": False,
        "current_open_uprn_file_name_verified": False,
        "current_open_uprn_size_verified": False,
        "current_open_uprn_md5_verified": False,
        "current_open_uprn_object_url_verified": False,
        "runtime_hosts_probed": ["api.os.uk", "docs.os.uk", "osdatahub.os.uk"],
        "runtime_dns_results": ["EAI_AGAIN_OR_UNRESOLVED"] * 3,
        "direct_http_codes": [0, 0, 0],
        "direct_response_bytes": [0, 0, 0],
        "enfield_subset_acquired": False,
        "coordinate_collision_audit_performed": False,
        "point_or_coordinate_guessing_forbidden": True,
    }
    fixture = {
        "slot_id": "gas_emissions_2",
        "wave": 335,
        "canonical_context": {
            "wave334_remote_readback": "PASS",
            "continuation_key": "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec",
            "slot_partition": {"start": 30762, "end": 61522, "count": 30761},
        },
        "canonical_samples": [
            {"parcel_id": parcel_id, "geometry_type": "Point", "uprn": None}
            for parcel_id in sorted(SAMPLES)
        ],
        "metadata_schema_assessment": assessment,
        "source_evidence_manifest": manifest,
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
    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    print("DECISION=" + result["decision"])
    print("BUSINESS_ROWS_PRODUCED=0")
    print("PARCEL_ROWS_BOUND=0")

if __name__ == "__main__":
    main()
