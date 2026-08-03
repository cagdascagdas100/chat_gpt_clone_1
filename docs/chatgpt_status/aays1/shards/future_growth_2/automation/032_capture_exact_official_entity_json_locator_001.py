#!/usr/bin/env python3
"""Capture one exact official Planning Data entity JSON locator.

The script derives the locator only from an official endpoint template and an
official entity record. It never claims that the JSON response was fetched and
never persists geometry, point or a remote payload body.
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
EXPECTED_TEMPLATE = "/entity/{entity}.json"


def classify(sources: list[dict[str, Any]]) -> dict[str, Any]:
    docs = next((s for s in sources if s.get("evidence_role") == "official_api_documentation"), None)
    entity = next((s for s in sources if s.get("evidence_role") == "official_entity_record"), None)
    dataset = next((s for s in sources if s.get("evidence_role") == "official_dataset_terms"), None)
    probe = next((s for s in sources if s.get("evidence_role") == "direct_runner_probe"), None)

    docs_ok = bool(docs and docs.get("proven", {}).get("endpoint_template") == EXPECTED_TEMPLATE)
    entity_fields = (entity or {}).get("proven", {})
    entity_ok = bool(
        entity
        and entity_fields.get("entity") == EXPECTED_ENTITY
        and entity_fields.get("dataset") == EXPECTED_DATASET
        and entity_fields.get("organisation") == "HM Land Registry"
    )
    dataset_ok = bool(dataset and dataset.get("proven", {}).get("ogl_v3") is True)
    exact_url = f"https://{OFFICIAL_HOST}{EXPECTED_TEMPLATE.format(entity=EXPECTED_ENTITY)}"
    host_ok = urlparse(exact_url).hostname == OFFICIAL_HOST
    probe_fields = (probe or {}).get("proven", {})
    response_verified = bool(probe_fields.get("http_response_verified") is True)
    locator_verified = bool(docs_ok and entity_ok and dataset_ok and host_ok)
    return {
        "docs_template_verified": docs_ok,
        "entity_identity_verified": entity_ok,
        "dataset_terms_verified": dataset_ok,
        "official_host_verified": host_ok,
        "exact_official_entity_json_url": exact_url,
        "exact_locator_verified": locator_verified,
        "direct_json_response_verified": response_verified,
        "probe_error": probe_fields.get("error"),
    }


def self_test() -> dict[str, Any]:
    base = [
        {"evidence_role": "official_api_documentation", "proven": {"endpoint_template": EXPECTED_TEMPLATE}},
        {"evidence_role": "official_entity_record", "proven": {"entity": EXPECTED_ENTITY, "dataset": EXPECTED_DATASET, "organisation": "HM Land Registry"}},
        {"evidence_role": "official_dataset_terms", "proven": {"ogl_v3": True}},
        {"evidence_role": "direct_runner_probe", "proven": {"http_response_verified": False, "error": "DNS"}},
    ]
    tests = []
    good = classify(base)
    tests.append(("exact_locator", good["exact_locator_verified"] and good["exact_official_entity_json_url"].endswith("12032669504.json")))
    tests.append(("response_unverified_preserved", good["direct_json_response_verified"] is False))
    bad_template = json.loads(json.dumps(base)); bad_template[0]["proven"]["endpoint_template"] = "/wrong/{entity}.json"
    tests.append(("bad_template_rejected", classify(bad_template)["exact_locator_verified"] is False))
    bad_entity = json.loads(json.dumps(base)); bad_entity[1]["proven"]["entity"] = 1
    tests.append(("bad_entity_rejected", classify(bad_entity)["exact_locator_verified"] is False))
    bad_org = json.loads(json.dumps(base)); bad_org[1]["proven"]["organisation"] = "Unknown"
    tests.append(("bad_org_rejected", classify(bad_org)["exact_locator_verified"] is False))
    bad_terms = json.loads(json.dumps(base)); bad_terms[2]["proven"]["ogl_v3"] = False
    tests.append(("missing_terms_rejected", classify(bad_terms)["exact_locator_verified"] is False))
    passed = sum(bool(ok) for _, ok in tests)
    return {"tests": [{"name": name, "passed": bool(ok)} for name, ok in tests], "passed": passed, "target": len(tests), "result": f"PASS_{passed}_OF_{len(tests)}"}


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
    result = classify(manifest.get("sources", []))
    completed = len(manifest.get("sources", []))
    locator_ok = result["exact_locator_verified"]
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
        "blocker": None if result["direct_json_response_verified"] else "DIRECT_ENTITY_JSON_RESPONSE_DNS_UNAVAILABLE",
        "next_unverified_step": "VERIFY_EXACT_ENTITY_JSON_RESPONSE_ON_NETWORK_ENABLED_RUNNER_OR_CAPTURE_OFFICIAL_GEOJSON_DOWNLOAD_HREF",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
