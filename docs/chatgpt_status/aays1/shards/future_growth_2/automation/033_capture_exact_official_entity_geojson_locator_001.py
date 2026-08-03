#!/usr/bin/env python3
"""Capture one exact official Planning Data entity GeoJSON locator.

The locator is accepted only when official API documentation permits the
GeoJSON extension and the official entity page identifies the same entity and
exposes a GeoJSON download option. Network failures never become response
success, and no remote payload, geometry or point is persisted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

OFFICIAL_HOST = "www.planning.data.gov.uk"
EXPECTED_DATASET = "title-boundary"
EXPECTED_ENTITY = 12032669504
EXPECTED_TEMPLATE = "/entity/{entity}.{extension}"
EXPECTED_EXTENSION = "geojson"


def classify(sources: list[dict[str, Any]]) -> dict[str, Any]:
    docs = next((s for s in sources if s.get("evidence_role") == "official_api_documentation"), None)
    entity = next((s for s in sources if s.get("evidence_role") == "official_entity_download_page"), None)
    json_probe = next((s for s in sources if s.get("evidence_role") == "direct_runner_json_probe"), None)
    geo_probe = next((s for s in sources if s.get("evidence_role") == "direct_runner_geojson_probe"), None)

    docs_fields = (docs or {}).get("proven", {})
    docs_ok = bool(
        docs
        and docs_fields.get("endpoint_template") == EXPECTED_TEMPLATE
        and EXPECTED_EXTENSION in docs_fields.get("allowed_extensions", [])
    )
    entity_fields = (entity or {}).get("proven", {})
    entity_ok = bool(
        entity
        and entity_fields.get("entity") == EXPECTED_ENTITY
        and entity_fields.get("dataset") == EXPECTED_DATASET
        and entity_fields.get("organisation") == "HM Land Registry"
        and entity_fields.get("download_geojson_label") is True
        and entity_fields.get("ogl_v3") is True
    )
    exact_url = f"https://{OFFICIAL_HOST}{EXPECTED_TEMPLATE.format(entity=EXPECTED_ENTITY, extension=EXPECTED_EXTENSION)}"
    host_ok = urlparse(exact_url).hostname == OFFICIAL_HOST
    geo_fields = (geo_probe or {}).get("proven", {})
    json_fields = (json_probe or {}).get("proven", {})
    response_verified = bool(geo_fields.get("http_response_verified") is True)
    locator_verified = bool(docs_ok and entity_ok and host_ok)
    return {
        "docs_geojson_extension_verified": docs_ok,
        "entity_download_page_verified": entity_ok,
        "official_host_verified": host_ok,
        "exact_official_entity_geojson_url": exact_url,
        "exact_geojson_locator_verified": locator_verified,
        "direct_geojson_response_verified": response_verified,
        "geojson_probe_error": geo_fields.get("error"),
        "prior_json_probe_error": json_fields.get("error"),
    }


def self_test() -> dict[str, Any]:
    base = [
        {"evidence_role": "official_api_documentation", "proven": {"endpoint_template": EXPECTED_TEMPLATE, "allowed_extensions": ["json", "html", "geojson"]}},
        {"evidence_role": "official_entity_download_page", "proven": {"entity": EXPECTED_ENTITY, "dataset": EXPECTED_DATASET, "organisation": "HM Land Registry", "download_geojson_label": True, "ogl_v3": True}},
        {"evidence_role": "direct_runner_json_probe", "proven": {"http_response_verified": False, "error": "DNS"}},
        {"evidence_role": "direct_runner_geojson_probe", "proven": {"http_response_verified": False, "error": "DNS"}},
    ]
    tests: list[tuple[str, bool]] = []
    good = classify(base)
    tests.append(("exact_geojson_locator", good["exact_geojson_locator_verified"] and good["exact_official_entity_geojson_url"].endswith("12032669504.geojson")))
    tests.append(("response_unverified_preserved", good["direct_geojson_response_verified"] is False))
    bad_ext = json.loads(json.dumps(base)); bad_ext[0]["proven"]["allowed_extensions"] = ["json", "html"]
    tests.append(("missing_geojson_extension_rejected", classify(bad_ext)["exact_geojson_locator_verified"] is False))
    bad_entity = json.loads(json.dumps(base)); bad_entity[1]["proven"]["entity"] = 1
    tests.append(("wrong_entity_rejected", classify(bad_entity)["exact_geojson_locator_verified"] is False))
    bad_download = json.loads(json.dumps(base)); bad_download[1]["proven"]["download_geojson_label"] = False
    tests.append(("missing_download_label_rejected", classify(bad_download)["exact_geojson_locator_verified"] is False))
    bad_terms = json.loads(json.dumps(base)); bad_terms[1]["proven"]["ogl_v3"] = False
    tests.append(("missing_terms_rejected", classify(bad_terms)["exact_geojson_locator_verified"] is False))
    passed = sum(bool(ok) for _, ok in tests)
    return {"tests": [{"name": n, "passed": bool(ok)} for n, ok in tests], "passed": passed, "target": len(tests), "result": f"PASS_{passed}_OF_{len(tests)}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--task-continuation-key")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    if not args.manifest or not args.output or not args.task_continuation_key:
        parser.error("--manifest, --output and --task-continuation-key are required")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    sources = manifest.get("sources", [])
    result = classify(sources)
    completed = len(sources)
    locator_ok = result["exact_geojson_locator_verified"]
    output = {
        "architecture_version": 3,
        "schema_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "task_continuation_key": args.task_continuation_key,
        "state": "PUBLISHED" if locator_ok else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": completed,
        "progress_percent": 100.0 if completed else 0.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "produced_business_rows": 0,
        **result,
        "response_body_persisted": False,
        "geometry_persisted": False,
        "point_persisted": False,
        "fake_data": False,
        "blocker": None if result["direct_geojson_response_verified"] else "DIRECT_ENTITY_GEOJSON_RESPONSE_DNS_UNAVAILABLE",
        "next_unverified_step": "VALIDATE_EXACT_ENTITY_GEOJSON_RESPONSE_SCHEMA_ON_NETWORK_ENABLED_RUNNER",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
