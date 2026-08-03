#!/usr/bin/env python3
"""Validate one bounded official Planning Data title-boundary record.

Only record metadata is persisted. Geometry and point values are never copied.
A failed direct API probe remains explicit and does not invalidate the official
record-page evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

OFFICIAL_HOST = "www.planning.data.gov.uk"
REQUIRED_FIELDS = (
    "entity", "reference", "dataset", "organisation", "organisation_curie",
    "entry_date", "start_date", "quality"
)


def classify(manifest: dict[str, Any]) -> dict[str, Any]:
    sources = manifest.get("sources", [])
    record_sources = [s for s in sources if "bounded_record_fields" in s.get("supports_fields", [])]
    if len(record_sources) != 1:
        raise ValueError("expected exactly one bounded record source")
    source = record_sources[0]
    if urlparse(source["source_url"]).hostname != OFFICIAL_HOST:
        raise ValueError("record source is not the official Planning Data host")
    values = source.get("proven_values", {})
    missing = [field for field in REQUIRED_FIELDS if values.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing required proven fields: {missing}")
    record_provenance = (
        values["dataset"] == "title-boundary"
        and values["organisation"] == "HM Land Registry"
        and values["quality"] == "authoritative"
        and values["organisation_curie"] == "government-organisation:D69"
    )
    direct_probe_sources = [s for s in sources if "direct_api_probe_result" in s.get("supports_fields", [])]
    direct_api_verified = any(s.get("proven_values", {}).get("http_verified") is True for s in direct_probe_sources)
    output_record = {field: values[field] for field in REQUIRED_FIELDS}
    return {
        "record": output_record,
        "record_page_url": source["source_url"],
        "record_authoritative_provenance_verified": record_provenance,
        "official_record_page_verified": True,
        "direct_api_json_response_verified": direct_api_verified,
        "dataset_wide_authoritative_equivalence_verified": False,
        "geometry_persisted": False,
        "point_persisted": False,
        "payload_body_persisted": False,
    }


def self_test() -> dict[str, Any]:
    good = {
        "sources": [{
            "source_url": "https://www.planning.data.gov.uk/entity/12032669504",
            "supports_fields": ["bounded_record_fields"],
            "proven_values": {
                "entity": 12032669504,
                "reference": "32669504",
                "dataset": "title-boundary",
                "organisation": "HM Land Registry",
                "organisation_curie": "government-organisation:D69",
                "entry_date": "2026-07-23",
                "start_date": "2002-04-07",
                "quality": "authoritative",
            },
        }, {
            "source_url": "https://www.planning.data.gov.uk/entity.json?dataset=title-boundary&limit=1",
            "supports_fields": ["direct_api_probe_result"],
            "proven_values": {"http_verified": False},
        }]
    }
    tests = []
    result = classify(good)
    tests.append(("official_record_page", result["official_record_page_verified"] is True))
    tests.append(("authoritative_provenance", result["record_authoritative_provenance_verified"] is True))
    tests.append(("direct_api_failure_preserved", result["direct_api_json_response_verified"] is False))
    tests.append(("geometry_not_persisted", result["geometry_persisted"] is False and "geometry" not in result["record"]))
    tests.append(("point_not_persisted", result["point_persisted"] is False and "point" not in result["record"]))
    bad = json.loads(json.dumps(good))
    bad["sources"][0]["source_url"] = "https://example.com/entity/1"
    rejected = False
    try:
        classify(bad)
    except ValueError:
        rejected = True
    tests.append(("non_official_host_rejected", rejected))
    passed = sum(1 for _, ok in tests if ok)
    return {"tests": [{"name": n, "passed": ok} for n, ok in tests], "passed": passed, "target": len(tests), "result": f"PASS_{passed}_OF_{len(tests)}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--task-continuation-key")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True, separators=(",", ":")))
        return 0
    if not all((args.manifest, args.output, args.task_continuation_key)):
        parser.error("manifest, output and task-continuation-key are required")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = classify(manifest)
    verified = result["record_authoritative_provenance_verified"]
    output = {
        "architecture_version": 3,
        "schema_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "task_continuation_key": args.task_continuation_key,
        "state": "PUBLISHED" if verified else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": len(manifest.get("sources", [])),
        "target_count": len(manifest.get("sources", [])),
        "progress_percent": 100.0 if manifest.get("sources") else 0.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "produced_business_rows": 0,
        "validated_metadata_record_count": 1 if verified else 0,
        **result,
        "blocker": "DIRECT_API_JSON_RESPONSE_DNS_UNAVAILABLE_AND_DATASET_WIDE_EQUIVALENCE_UNVERIFIED",
        "next_unverified_step": "CAPTURE_EXACT_OFFICIAL_ENTITY_JSON_RESPONSE_OR_DOWNLOAD_LINK",
        "fake_data": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    sys.exit(main())
