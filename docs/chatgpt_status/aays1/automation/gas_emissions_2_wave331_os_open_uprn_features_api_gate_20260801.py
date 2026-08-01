#!/usr/bin/env python3
"""Wave331 OS Open UPRN Features API authentication and result-limit gate."""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_IDS = {
    "canonical_wave330",
    "canonical_parcel_sample",
    "os_features_overview",
    "os_features_data_available",
    "os_features_getfeature",
    "os_features_getcapabilities",
    "os_features_authentication",
    "os_api_project_getting_started",
    "os_rate_limiting",
    "os_plans",
    "os_features_filtering",
    "runtime_auth_dns_probe",
}
SAMPLES = {"parcel_30762", "parcel_30763", "parcel_30764"}
AUTH_METHODS = ["api_key_query", "api_key_header", "oauth2"]
OUTPUT_FORMATS = ["GML32", "GML3", "GML2", "GEOJSON"]
SRS = ["EPSG:27700", "EPSG:4326", "EPSG:3857"]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_json(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value


def build(fixture: dict) -> dict:
    if (fixture.get("slot_id"), fixture.get("wave")) != ("gas_emissions_2", 331):
        raise ValueError("slot/wave mismatch")
    context = fixture["canonical_context"]
    samples = fixture["canonical_samples"]
    assessment = fixture["features_api_assessment"]
    manifest = fixture["source_evidence_manifest"]

    if context.get("wave330_remote_readback") != "PASS":
        raise ValueError("Wave330 readback gate failed")
    if context.get("continuation_key") != "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec":
        raise ValueError("continuation mismatch")
    if context.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")

    if {row.get("parcel_id") for row in samples} != SAMPLES:
        raise ValueError("sample set mismatch")
    if any(row.get("geometry_type") != "Point" or row.get("uprn") is not None for row in samples):
        raise ValueError("sample identity gate failed")

    required_true = (
        "open_uprn_supported",
        "authentication_required",
        "api_project_required",
        "bbox_supported",
        "count_supported",
        "start_index_supported",
        "result_type_hits_supported",
        "open_data_transactions_unlimited",
        "point_or_coordinate_guessing_forbidden",
    )
    required_false = (
        "credential_present",
        "dns_resolution_succeeded",
        "get_capabilities_bytes_acquired",
        "authenticated_request_performed",
        "anonymous_request_succeeded",
        "bbox_query_performed",
        "enfield_subset_acquired",
        "coordinate_collision_audit_performed",
    )
    if any(assessment.get(key) is not True for key in required_true):
        raise ValueError("positive API gate failed")
    if any(assessment.get(key) is not False for key in required_false):
        raise ValueError("negative API gate failed")
    if assessment.get("feature_type_name") != "OpenUPRN_Address":
        raise ValueError("feature type mismatch")
    if assessment.get("authentication_methods") != AUTH_METHODS:
        raise ValueError("auth methods mismatch")
    if assessment.get("max_features_per_response") != 100 or assessment.get("default_count") != 100:
        raise ValueError("response limit mismatch")
    if assessment.get("output_formats") != OUTPUT_FORMATS or assessment.get("supported_srs") != SRS:
        raise ValueError("format/SRS mismatch")
    if assessment.get("runtime_hosts_probed") != ["api.os.uk", "docs.os.uk", "osdatahub.os.uk"]:
        raise ValueError("runtime host set mismatch")
    if assessment.get("runtime_dns_results") != ["EAI_AGAIN", "EAI_AGAIN", "EAI_AGAIN"]:
        raise ValueError("runtime DNS result mismatch")
    if assessment.get("credential_environment_variables_checked") != 6:
        raise ValueError("credential probe mismatch")

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
        "wave": 331,
        "state": "NO_DATA_CONTINUE",
        "decision": "OS_OPEN_UPRN_FEATURES_API_AUTH_AND_LIMIT_GATE_NO_DATA_CONTINUE",
        "decision_reason": (
            "Official OS documentation proves that OpenUPRN_Address is available through the OS Features API and can be queried with WFS BBOX, count, startIndex and resultType=hits. "
            "Every OS API request requires an OS Data Hub API project and API key or OAuth2 token; the execution environment contains none of the six checked credential variables. "
            "The endpoint also remains unreachable from the execution environment because api.os.uk, docs.os.uk and osdatahub.os.uk all return EAI_AGAIN. "
            "The response maximum is 100 features, so a complete Enfield extract would require authenticated pagination. No capabilities, query response, subset, coordinate collision audit or parcel binding was produced."
        ),
        "canonical_context": context,
        "canonical_samples": samples,
        "features_api_assessment": assessment,
        "source_count": len(manifest),
        "source_evidence_manifest": [by_id[key] for key in sorted(by_id)],
        "resolved_blockers": [
            "OS_OPEN_UPRN_FEATURES_API_AVAILABILITY_UNKNOWN",
            "OS_OPEN_UPRN_FEATURE_TYPE_NAME_UNKNOWN",
            "OS_FEATURES_API_AUTHENTICATION_REQUIREMENT_UNKNOWN",
            "OS_FEATURES_API_BBOX_PARAMETER_SUPPORT_UNKNOWN",
            "OS_FEATURES_API_SINGLE_RESPONSE_LIMIT_UNKNOWN",
            "OS_FEATURES_API_PAGINATION_SUPPORT_UNKNOWN",
            "OS_OPEN_DATA_FEATURE_TRANSACTION_PLAN_UNKNOWN",
        ],
        "remaining_blocker": (
            "OS_FEATURES_API_PROJECT_KEY_OR_OAUTH2_TOKEN_ABSENT;"
            "EXECUTION_ENVIRONMENT_DNS_EGRESS_FAILURE_FOR_API_OS_UK_DOCS_OS_UK_OSDATAHUB_OS_UK;"
            "OS_FEATURES_API_GETCAPABILITIES_AND_OPENUPRN_ADDRESS_BBOX_RESPONSE_BYTES_NOT_ACQUIRED;"
            "OS_FEATURES_API_MAX_100_FEATURES_PER_RESPONSE_REQUIRES_AUTHENTICATED_PAGINATION;"
            "AUTHORITATIVE_ENFIELD_SUBSET_NOT_ACQUIRED;"
            "OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;"
            "CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": (
            "OS_FEATURES_API_AUTHORISED_KEY_OR_DOWNLOAD_EGRESS_RECOVERY_AND_BOUNDED_SAMPLE_QUERY_OR_NO_DATA_CONTINUE"
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
        "open_uprn_supported": True,
        "feature_type_name": "OpenUPRN_Address",
        "authentication_required": True,
        "authentication_methods": AUTH_METHODS,
        "api_project_required": True,
        "bbox_supported": True,
        "bbox_axis_order": "bottom-left y,bottom-left x,top-right y,top-right x",
        "count_supported": True,
        "default_count": 100,
        "max_features_per_response": 100,
        "start_index_supported": True,
        "result_type_hits_supported": True,
        "output_formats": OUTPUT_FORMATS,
        "supported_srs": SRS,
        "open_data_transactions_unlimited": True,
        "point_or_coordinate_guessing_forbidden": True,
        "credential_environment_variables_checked": 6,
        "credential_present": False,
        "runtime_hosts_probed": ["api.os.uk", "docs.os.uk", "osdatahub.os.uk"],
        "runtime_dns_results": ["EAI_AGAIN", "EAI_AGAIN", "EAI_AGAIN"],
        "dns_resolution_succeeded": False,
        "get_capabilities_bytes_acquired": False,
        "authenticated_request_performed": False,
        "anonymous_request_succeeded": False,
        "bbox_query_performed": False,
        "enfield_subset_acquired": False,
        "coordinate_collision_audit_performed": False,
    }
    fixture = {
        "slot_id": "gas_emissions_2",
        "wave": 331,
        "canonical_context": {
            "wave330_remote_readback": "PASS",
            "continuation_key": "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec",
            "slot_partition": {"start": 30762, "end": 61522, "count": 30761},
        },
        "canonical_samples": [
            {"parcel_id": parcel_id, "geometry_type": "Point", "uprn": None}
            for parcel_id in sorted(SAMPLES)
        ],
        "features_api_assessment": assessment,
        "source_evidence_manifest": manifest,
    }
    assert build(fixture)["source_count"] == 12
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
