#!/usr/bin/env python3
"""Wave334 OS Open UPRN June 2026 release receipt fail-closed gate."""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_IDS = {
    "canonical_wave333",
    "canonical_parcel_sample",
    "os_data_hub_open_uprn",
    "os_addressbase_publication_dates",
    "os_open_uprn_release_notes_index",
    "os_addressbase_release_notes_index",
    "os_open_uprn_november_2025_release_note",
    "os_addressbase_january_2026_epoch124",
    "os_downloads_api_overview",
    "os_download_opendata_contract",
    "runtime_release_note_checksum_probe",
}
SAMPLES = {"parcel_30762", "parcel_30763", "parcel_30764"}
CONTINUATION = "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec"

def h(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_json(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be object")
    return value

def build(fixture: dict) -> dict:
    if (fixture.get("slot_id"), fixture.get("wave")) != ("gas_emissions_2", 334):
        raise ValueError("slot/wave mismatch")
    context = fixture["canonical_context"]
    samples = fixture["canonical_samples"]
    assessment = fixture["release_receipt_assessment"]
    manifest = fixture["source_evidence_manifest"]

    if context.get("wave333_remote_readback") != "PASS":
        raise ValueError("Wave333 readback gate failed")
    if context.get("continuation_key") != CONTINUATION:
        raise ValueError("continuation mismatch")
    if context.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")

    if {row.get("parcel_id") for row in samples} != SAMPLES:
        raise ValueError("sample set mismatch")
    if any(row.get("geometry_type") != "Point" or row.get("uprn") is not None for row in samples):
        raise ValueError("sample identity gate failed")

    required_true = ("historical_feature_count_pattern_verified", "point_or_coordinate_guessing_forbidden")
    required_false = (
        "june_2026_open_uprn_release_note_found",
        "epoch_128_addressbase_release_note_found",
        "june_2026_feature_count_found",
        "current_archive_checksum_found",
        "current_archive_filename_found",
        "current_archive_size_found",
        "current_metadata_bytes_acquired",
        "enfield_subset_acquired",
        "coordinate_collision_audit_performed",
    )
    if any(assessment.get(k) is not True for k in required_true):
        raise ValueError("positive receipt gate failed")
    if any(assessment.get(k) is not False for k in required_false):
        raise ValueError("negative receipt gate failed")
    if assessment.get("official_version_date") != "June 2026":
        raise ValueError("version mismatch")
    if (assessment.get("epoch_number"), assessment.get("epoch_publication_date"), assessment.get("epoch_data_cut_date")) != (128, "2026-06-25", "2026-05-22"):
        raise ValueError("epoch mismatch")
    if assessment.get("open_uprn_release_notes_latest_visible_epoch") != 125:
        raise ValueError("OpenUPRN index mismatch")
    if assessment.get("addressbase_release_notes_latest_visible_epoch") != 125:
        raise ValueError("AddressBase index mismatch")
    if assessment.get("historical_november_2025_feature_count") != 41386550:
        raise ValueError("historical November count mismatch")
    if assessment.get("historical_epoch_124_feature_count") != 41431031:
        raise ValueError("historical Epoch124 count mismatch")
    if assessment.get("direct_urls_probed") != 3 or assessment.get("bounded_search_queries") != 8:
        raise ValueError("probe count mismatch")
    if assessment.get("direct_http_codes") != [0, 0, 0] or assessment.get("direct_response_bytes") != [0, 0, 0]:
        raise ValueError("direct response mismatch")
    if assessment.get("runtime_hosts_probed") != ["docs.os.uk", "api.os.uk", "osdatahub.os.uk"]:
        raise ValueError("host set mismatch")

    by_id = {}
    for source in manifest:
        sid = source.get("source_id")
        excerpt = source.get("relevant_excerpt")
        if not sid or not excerpt:
            raise ValueError("source id/excerpt missing")
        if source.get("excerpt_sha256") != h(excerpt):
            raise ValueError("source hash mismatch: " + str(sid))
        for key in ("publisher","source_url","accessed_at","hash_scope","supports_fields","license_or_terms_url"):
            if not source.get(key):
                raise ValueError("source field missing: " + str(sid) + ":" + key)
        by_id[sid] = source
    if set(by_id) != SOURCE_IDS:
        raise ValueError("source set mismatch")

    return {
        "schema_version":1,
        "slot_id":"gas_emissions_2",
        "wave":334,
        "state":"NO_DATA_CONTINUE",
        "decision":"OS_OPEN_UPRN_JUNE_2026_RELEASE_NOTE_FEATURE_COUNT_AND_CHECKSUM_NO_DATA_CONTINUE",
        "decision_reason":(
            "Official OS surfaces prove the June 2026 product version and Epoch 128 publication on 25 June 2026. "
            "The visible OS Open UPRN and AddressBase release-note indexes stop at February 2026 Epoch 125, while historical notes prove where feature counts are normally published. "
            "Eight bounded searches and three direct runtime probes produced no June 2026 release-note URL, Epoch 128 feature count, archive filename, size, checksum or metadata bytes. "
            "No Enfield subset, coordinate collision audit or exact parcel binding is promoted."
        ),
        "canonical_context":context,
        "canonical_samples":samples,
        "release_receipt_assessment":assessment,
        "source_count":len(manifest),
        "source_evidence_manifest":[by_id[k] for k in sorted(by_id)],
        "resolved_blockers":[
            "OS_OPEN_UPRN_EPOCH_128_PUBLICATION_DATE_UNKNOWN",
            "OS_OPEN_UPRN_RELEASE_NOTE_FEATURE_COUNT_LOCATION_UNKNOWN",
            "OS_OPEN_UPRN_RELEASE_NOTE_INDEX_LATEST_VISIBLE_ENTRY_UNKNOWN",
            "ADDRESSBASE_RELEASE_NOTE_INDEX_LATEST_VISIBLE_EPOCH_UNKNOWN",
            "HISTORICAL_FEATURE_COUNT_PATTERN_UNKNOWN",
        ],
        "remaining_blocker":(
            "JUNE_2026_OS_OPEN_UPRN_RELEASE_NOTE_NOT_SURFACED_ON_OFFICIAL_INDEX;"
            "EPOCH_128_ADDRESSBASE_RELEASE_NOTE_NOT_SURFACED;"
            "CURRENT_OS_OPEN_UPRN_FEATURE_COUNT_UNVERIFIED;"
            "CURRENT_OS_OPEN_UPRN_ARCHIVE_FILENAME_SIZE_CHECKSUM_AND_OBJECT_URL_UNVERIFIED;"
            "EXECUTION_ENVIRONMENT_DNS_EGRESS_FAILURE_FOR_DOCS_OS_UK_API_OS_UK_OSDATAHUB_OS_UK;"
            "AUTHORITATIVE_ENFIELD_SUBSET_NOT_ACQUIRED;"
            "OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;"
            "CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step":"OS_DOWNLOADS_API_OPENDATA_FILE_METADATA_SCHEMA_FIELDS_AND_CHECKSUM_SUPPORT_GATE_OR_NO_DATA_CONTINUE",
        "business_rows_produced":0,
        "parcel_rows_bound":0,
        "completed_count":0,
        "target_count":30761,
        "previous_percent":0.0,
        "current_percent":0.0,
        "percent_increase":0.0,
        "fake_data":False,
        "final_ready":False,
    }

def self_test() -> None:
    excerpt = "x"
    manifest = [{
        "source_id":sid,
        "publisher":"x",
        "source_url":"x",
        "accessed_at":"x",
        "hash_scope":"x",
        "relevant_excerpt":excerpt,
        "excerpt_sha256":h(excerpt),
        "supports_fields":["x"],
        "license_or_terms_url":"x",
    } for sid in SOURCE_IDS]
    assessment = {
        "official_version_date":"June 2026",
        "epoch_number":128,
        "epoch_publication_date":"2026-06-25",
        "epoch_data_cut_date":"2026-05-22",
        "open_uprn_release_notes_latest_visible":"February 2026",
        "open_uprn_release_notes_latest_visible_epoch":125,
        "addressbase_release_notes_latest_visible_epoch":125,
        "historical_feature_count_pattern_verified":True,
        "historical_november_2025_feature_count":41386550,
        "historical_epoch_124_feature_count":41431031,
        "june_2026_open_uprn_release_note_found":False,
        "epoch_128_addressbase_release_note_found":False,
        "june_2026_feature_count_found":False,
        "current_archive_checksum_found":False,
        "current_archive_filename_found":False,
        "current_archive_size_found":False,
        "current_metadata_bytes_acquired":False,
        "direct_urls_probed":3,
        "direct_http_codes":[0,0,0],
        "direct_response_bytes":[0,0,0],
        "runtime_hosts_probed":["docs.os.uk","api.os.uk","osdatahub.os.uk"],
        "runtime_dns_results":["EAI_AGAIN_OR_UNRESOLVED"]*3,
        "bounded_search_queries":8,
        "point_or_coordinate_guessing_forbidden":True,
        "enfield_subset_acquired":False,
        "coordinate_collision_audit_performed":False,
    }
    fixture = {
        "slot_id":"gas_emissions_2",
        "wave":334,
        "canonical_context":{
            "wave333_remote_readback":"PASS",
            "continuation_key":CONTINUATION,
            "slot_partition":{"start":30762,"end":61522,"count":30761},
        },
        "canonical_samples":[{"parcel_id":p,"geometry_type":"Point","uprn":None} for p in sorted(SAMPLES)],
        "release_receipt_assessment":assessment,
        "source_evidence_manifest":manifest,
    }
    assert build(fixture)["source_count"] == 11
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
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",",":")), encoding="utf-8")
    print("DECISION=" + result["decision"])
    print("BUSINESS_ROWS_PRODUCED=0")
    print("PARCEL_ROWS_BOUND=0")

if __name__ == "__main__":
    main()
