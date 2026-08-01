#!/usr/bin/env python3
"""Wave333 OS Open UPRN public archive/object-host receipt fail-closed gate."""
import argparse, hashlib, json
from pathlib import Path

SOURCE_IDS = {
    "canonical_wave332",
    "canonical_parcel_sample",
    "os_data_hub_open_uprn",
    "os_download_opendata_contract",
    "os_download_automation_guide",
    "os_arcgis_link_surface",
    "data_gov_link_surface",
    "cadcorp_access_controlled_surface",
    "public_historical_client_example",
    "runtime_public_archive_search_probe",
}
SAMPLES = {"parcel_30762", "parcel_30763", "parcel_30764"}

def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def load(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be object")
    return value

def build(fixture: dict) -> dict:
    if (fixture.get("slot_id"), fixture.get("wave")) != ("gas_emissions_2", 333):
        raise ValueError("slot/wave")
    context = fixture["canonical_context"]
    samples = fixture["canonical_samples"]
    assessment = fixture["public_archive_assessment"]
    manifest = fixture["source_evidence_manifest"]
    if context.get("wave332_remote_readback") != "PASS":
        raise ValueError("wave332 readback")
    if context.get("continuation_key") != "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec":
        raise ValueError("continuation")
    if context.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition")
    if {r.get("parcel_id") for r in samples} != SAMPLES:
        raise ValueError("sample set")
    if any(r.get("geometry_type") != "Point" or r.get("uprn") is not None for r in samples):
        raise ValueError("sample identity")
    true_keys = (
        "official_version_june_2026",
        "official_redirect_contract_verified",
        "arcgis_points_to_os_api",
        "data_gov_is_link_only",
        "cadcorp_surface_access_controlled",
        "historical_filename_not_current_authority",
        "point_or_coordinate_guessing_forbidden",
    )
    false_keys = (
        "current_redirect_object_host_found",
        "current_archive_filename_found",
        "current_archive_size_found",
        "current_archive_checksum_found",
        "public_current_full_gb_archive_found",
        "public_archive_byte_receipt_acquired",
        "official_archive_byte_receipt_acquired",
        "enfield_subset_acquired",
        "coordinate_collision_audit_performed",
    )
    if any(assessment.get(k) is not True for k in true_keys):
        raise ValueError("positive gate")
    if any(assessment.get(k) is not False for k in false_keys):
        raise ValueError("negative gate")
    if assessment.get("official_direct_download_links_checked") != 2:
        raise ValueError("download links")
    if assessment.get("link_only_catalog_surfaces_checked") != 3:
        raise ValueError("link surfaces")
    if assessment.get("public_archive_search_queries") != 10:
        raise ValueError("search count")
    by_id = {}
    for source in manifest:
        sid, excerpt = source.get("source_id"), source.get("relevant_excerpt")
        if not sid or not excerpt or source.get("excerpt_sha256") != sha(excerpt):
            raise ValueError("source hash")
        for key in ("publisher","source_url","accessed_at","hash_scope","supports_fields","license_or_terms_url"):
            if not source.get(key):
                raise ValueError(f"source field {sid}:{key}")
        by_id[sid] = source
    if set(by_id) != SOURCE_IDS:
        raise ValueError("source set")
    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 333,
        "state": "NO_DATA_CONTINUE",
        "decision": "OS_OPEN_UPRN_REDIRECT_OBJECT_HOST_AND_PUBLIC_ARCHIVE_RECEIPT_NO_DATA_CONTINUE",
        "decision_reason": (
            "Official OS, ArcGIS and data.gov surfaces confirm the current June 2026 product and direct OS API links, but expose no current redirect object host, archive filename, size or checksum. "
            "The Cadcorp surface uses current OS data but requires service credentials, and the public client filename is historical rather than current authoritative metadata. "
            "Ten bounded public-search queries found no byte-bearing, current, full-GB OpenUPRN archive mirror. No archive bytes, Enfield subset, collision audit or parcel binding were produced."
        ),
        "canonical_context": context,
        "canonical_samples": samples,
        "public_archive_assessment": assessment,
        "source_count": len(manifest),
        "source_evidence_manifest": [by_id[k] for k in sorted(by_id)],
        "resolved_blockers": [
            "OS_DOWNLOADS_API_REDIRECT_OBJECT_HOST_PUBLICLY_INDEXED_UNKNOWN",
            "OS_OPEN_UPRN_PUBLIC_CURRENT_FULL_GB_ARCHIVE_MIRROR_UNKNOWN",
            "ARCGIS_OPEN_UPRN_SURFACE_BYTE_BEARING_UNKNOWN",
            "DATA_GOV_OPEN_UPRN_SURFACE_BYTE_BEARING_UNKNOWN",
            "CADCORP_OPEN_UPRN_SURFACE_ACCESS_MODE_UNKNOWN",
            "PUBLIC_CLIENT_FILENAME_CURRENT_AUTHORITY_UNKNOWN",
        ],
        "remaining_blocker": (
            "CURRENT_OS_OPEN_UPRN_REDIRECT_OBJECT_HOST_NOT_PUBLICLY_SURFACED;"
            "CURRENT_OS_OPEN_UPRN_ARCHIVE_FILENAME_SIZE_CHECKSUM_AND_OBJECT_URL_UNVERIFIED;"
            "PUBLIC_CURRENT_FULL_GB_BYTE_BEARING_ARCHIVE_MIRROR_NOT_FOUND;"
            "CADCORP_DATA_SURFACE_REQUIRES_SERVICE_CREDENTIALS;"
            "EXECUTION_ENVIRONMENT_DNS_EGRESS_FAILURE_FOR_API_OS_UK_PERSISTS;"
            "AUTHORITATIVE_ENFIELD_SUBSET_NOT_ACQUIRED;"
            "OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;"
            "CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": "OS_OPEN_UPRN_JUNE_2026_RELEASE_NOTE_FEATURE_COUNT_AND_ARCHIVE_CHECKSUM_DISCOVERY_OR_NO_DATA_CONTINUE",
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
        "source_id": sid, "publisher":"x", "source_url":"x", "accessed_at":"x",
        "hash_scope":"x", "relevant_excerpt":excerpt, "excerpt_sha256":sha(excerpt),
        "supports_fields":["x"], "license_or_terms_url":"x"
    } for sid in SOURCE_IDS]
    assessment = {
        "official_version_june_2026":True,
        "official_redirect_contract_verified":True,
        "official_direct_download_links_checked":2,
        "arcgis_points_to_os_api":True,
        "data_gov_is_link_only":True,
        "cadcorp_surface_access_controlled":True,
        "historical_filename_not_current_authority":True,
        "point_or_coordinate_guessing_forbidden":True,
        "link_only_catalog_surfaces_checked":3,
        "public_archive_search_queries":10,
        "current_redirect_object_host_found":False,
        "current_archive_filename_found":False,
        "current_archive_size_found":False,
        "current_archive_checksum_found":False,
        "public_current_full_gb_archive_found":False,
        "public_archive_byte_receipt_acquired":False,
        "official_archive_byte_receipt_acquired":False,
        "enfield_subset_acquired":False,
        "coordinate_collision_audit_performed":False,
    }
    fixture = {
        "slot_id":"gas_emissions_2","wave":333,
        "canonical_context":{"wave332_remote_readback":"PASS","continuation_key":"f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec","slot_partition":{"start":30762,"end":61522,"count":30761}},
        "canonical_samples":[{"parcel_id":p,"geometry_type":"Point","uprn":None} for p in sorted(SAMPLES)],
        "public_archive_assessment":assessment,
        "source_evidence_manifest":manifest,
    }
    assert build(fixture)["source_count"] == 10
    print("SELF_TEST_PASS")

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--fixture"); parser.add_argument("--output"); parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        self_test(); return
    result=build(load(args.fixture))
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
    print("DECISION="+result["decision"]); print("BUSINESS_ROWS_PRODUCED=0"); print("PARCEL_ROWS_BOUND=0")
if __name__ == "__main__": main()
