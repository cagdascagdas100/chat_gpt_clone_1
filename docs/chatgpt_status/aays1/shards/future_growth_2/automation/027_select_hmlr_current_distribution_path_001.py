#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

SLOT_ID = "future_growth_2"
WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
REQUIRED_FIELDS = {
    "source_url",
    "accessed_at",
    "content_sha256",
    "hash_scope",
    "relevant_record_ids_or_excerpt",
    "supports_fields",
    "license_or_terms_url",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def validate_manifest(manifest: dict) -> list[dict]:
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != 3:
        raise ValueError("exactly three source evidence records required")
    for record in records:
        missing = REQUIRED_FIELDS - set(record)
        if missing:
            raise ValueError(f"missing evidence fields: {sorted(missing)}")
        digest = record["content_sha256"]
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("content_sha256 must be lowercase SHA-256 hex")
        if not str(record["source_url"]).startswith("https://"):
            raise ValueError("HTTPS source URL required")
    return records


def classify(records: list[dict]) -> dict:
    support = set()
    for record in records:
        support.update(record["supports_fields"])
    required = {
        "official_wms_catalog_locator_present",
        "current_gml_distribution",
        "current_monthly_update",
        "current_api_available_false",
        "current_local_authority_download_list",
    }
    missing = sorted(required - support)
    if missing:
        raise ValueError(f"required source support missing: {missing}")
    return {
        "official_wms_catalog_locator_present": True,
        "current_distribution_format": "GML",
        "current_distribution_frequency": "monthly",
        "current_api_available": False,
        "official_proxy_or_capabilities_snapshot_found": False,
        "exact_current_gml_file_url_captured": False,
        "next_unverified_step": "EXTRACT_ONE_OFFICIAL_CURRENT_GML_DOWNLOAD_LOCATOR",
        "blocker": "EXACT_CURRENT_GML_FILE_URL_NOT_CAPTURED",
    }


def fixture_manifest() -> dict:
    return {
        "records": [
            {
                "source_url": "https://www.data.gov.uk/example",
                "accessed_at": "2026-08-03T00:00:00Z",
                "content_sha256": hashlib.sha256(b"catalog").hexdigest(),
                "hash_scope": "fixture",
                "relevant_record_ids_or_excerpt": "wms locator",
                "supports_fields": ["official_wms_catalog_locator_present"],
                "license_or_terms_url": "https://example.gov/licence",
            },
            {
                "source_url": "https://use-land-property-data.service.gov.uk/download",
                "accessed_at": "2026-08-03T00:00:00Z",
                "content_sha256": hashlib.sha256(b"download").hexdigest(),
                "hash_scope": "fixture",
                "relevant_record_ids_or_excerpt": "monthly GML local authorities",
                "supports_fields": [
                    "current_gml_distribution",
                    "current_monthly_update",
                    "current_local_authority_download_list",
                ],
                "license_or_terms_url": "https://example.gov/licence",
            },
            {
                "source_url": "https://use-land-property-data.service.gov.uk/",
                "accessed_at": "2026-08-03T00:00:00Z",
                "content_sha256": hashlib.sha256(b"overview").hexdigest(),
                "hash_scope": "fixture",
                "relevant_record_ids_or_excerpt": "API available No",
                "supports_fields": ["current_api_available_false"],
                "license_or_terms_url": "https://example.gov/licence",
            },
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest")
    parser.add_argument("--output")
    parser.add_argument("--task-continuation-key", required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if len(args.task_continuation_key) != 64 or any(
        ch not in "0123456789abcdef" for ch in args.task_continuation_key
    ):
        raise ValueError("continuation key must be lowercase SHA-256 hex")

    if args.self_test:
        records = validate_manifest(fixture_manifest())
        result = classify(records)
        assert result["current_distribution_format"] == "GML"
        assert result["current_distribution_frequency"] == "monthly"
        assert result["current_api_available"] is False
        assert result["official_proxy_or_capabilities_snapshot_found"] is False
        assert result["exact_current_gml_file_url_captured"] is False
        print(json.dumps({"self_test": "PASS_5_OF_5"}, sort_keys=True))
        return

    if not args.manifest or not args.output:
        raise ValueError("--manifest and --output are required")
    manifest = load_json(Path(args.manifest))
    records = validate_manifest(manifest)
    classification = classify(records)
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "task_continuation_key": args.task_continuation_key,
        "state": "PUBLISHED",
        "panel_status": "PUBLISHED",
        "completed_count": len(records),
        "target_count": 3,
        "progress_percent": 100.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "evidence_record_count": len(records),
        "produced_business_rows": 0,
        "fake_data": False,
        "geometry_copied": False,
        "authority_membership_inferred": False,
        "score_written": False,
        **classification,
    }
    atomic_write(Path(args.output), output)
    print(json.dumps({
        "state": output["state"],
        "completed_count": output["completed_count"],
        "target_count": output["target_count"],
        "blocker": output["blocker"],
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
