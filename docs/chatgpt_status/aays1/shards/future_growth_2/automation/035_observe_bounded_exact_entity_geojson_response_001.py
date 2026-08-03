#!/usr/bin/env python3
"""Observe one bounded exact Planning Data entity GeoJSON response.

This gate is safe for a network-enabled runner. It records only response
metadata, a SHA-256 digest, and a minimal schema summary. It never persists the
response body, geometry, coordinates, point values, or inferred business rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

EXACT_URL = "https://www.planning.data.gov.uk/entity/12032669504.geojson"
EXPECTED_ENTITY = 12032669504
MAX_BYTES = 262_144
ALLOWED_TYPES = {
    "Feature",
    "FeatureCollection",
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
}


def _entity_values(value: Any) -> list[int]:
    found: list[int] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "entity" and isinstance(item, int):
                found.append(item)
            else:
                found.extend(_entity_values(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_entity_values(item))
    return found


def inspect_payload(*, url: str, status: int, content_type: str, body: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {
        "exact_url_match": url == EXACT_URL,
        "http_status": status,
        "http_200_verified": status == 200,
        "content_type": content_type,
        "content_type_json_compatible": "json" in (content_type or "").lower(),
        "response_byte_count": len(body),
        "response_size_within_limit": 0 < len(body) <= MAX_BYTES,
        "response_sha256": hashlib.sha256(body).hexdigest() if body else None,
        "json_parse_ok": False,
        "top_level_type": None,
        "top_level_type_rfc7946": False,
        "feature_count": None,
        "expected_entity_present": False,
        "response_body_persisted": False,
        "geometry_persisted": False,
        "coordinates_persisted": False,
        "point_persisted": False,
    }
    if not (
        result["exact_url_match"]
        and result["http_200_verified"]
        and result["content_type_json_compatible"]
        and result["response_size_within_limit"]
    ):
        result["observation_verified"] = False
        return result
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        result["observation_verified"] = False
        return result
    result["json_parse_ok"] = True
    if isinstance(payload, dict):
        top_type = payload.get("type")
        result["top_level_type"] = top_type if isinstance(top_type, str) else None
        result["top_level_type_rfc7946"] = top_type in ALLOWED_TYPES
        features = payload.get("features")
        if isinstance(features, list):
            result["feature_count"] = len(features)
    result["expected_entity_present"] = EXPECTED_ENTITY in _entity_values(payload)
    result["observation_verified"] = bool(
        result["json_parse_ok"]
        and result["top_level_type_rfc7946"]
        and result["expected_entity_present"]
    )
    return result


def fetch_exact(timeout_seconds: int) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        EXACT_URL,
        headers={
            "Accept": "application/geo+json, application/json;q=0.9",
            "User-Agent": "AAYS-future-growth-2-bounded-observer/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read(MAX_BYTES + 1)
        return int(response.status), response.headers.get("content-type", ""), body


def validate_manifest(manifest: dict[str, Any]) -> dict[str, bool]:
    roles = {record.get("evidence_role") for record in manifest.get("sources", [])}
    return {
        "official_endpoint_contract_present": "official_endpoint_contract" in roles,
        "official_entity_identity_present": "official_entity_identity" in roles,
        "rfc7946_contract_present": "rfc7946_contract" in roles,
        "direct_runner_probe_present": "direct_runner_probe" in roles,
        "web_channel_observation_present": "web_channel_observation" in roles,
    }


def build_output(*, continuation_key: str, manifest: dict[str, Any], observation: dict[str, Any], error: str | None) -> dict[str, Any]:
    manifest_checks = validate_manifest(manifest)
    manifest_ok = all(manifest_checks.values())
    verified = bool(manifest_ok and observation.get("observation_verified"))
    return {
        "architecture_version": 3,
        "schema_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "task_continuation_key": continuation_key,
        "state": "PUBLISHED" if verified else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED" if verified else "BLOCKED",
        "completed_count": 1 if verified else 0,
        "target_count": 1,
        "progress_percent": 100.0 if verified else 0.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "produced_business_rows": 0,
        "exact_official_entity_geojson_url": EXACT_URL,
        "manifest_checks": manifest_checks,
        "manifest_verified": manifest_ok,
        "observation": observation,
        "network_error": error,
        "response_body_persisted": False,
        "geometry_persisted": False,
        "coordinates_persisted": False,
        "point_persisted": False,
        "fake_data": False,
        "blocker": None if verified else "NETWORK_ENABLED_RUNNER_REQUIRED_FOR_EXACT_ENTITY_GEOJSON_RESPONSE_OBSERVATION",
        "next_unverified_step": "VALIDATE_OBSERVED_ENTITY_GEOJSON_SCHEMA_AND_PROVENANCE" if verified else "RUN_READY_GATE_ON_NETWORK_ENABLED_RUNNER",
    }


def self_test() -> dict[str, Any]:
    feature = {
        "type": "Feature",
        "properties": {"entity": EXPECTED_ENTITY, "dataset": "title-boundary"},
        "geometry": {"type": "MultiPolygon", "coordinates": []},
    }
    collection = {"type": "FeatureCollection", "features": [feature]}
    good = json.dumps(collection, separators=(",", ":")).encode()
    tests: list[tuple[str, bool]] = []
    result = inspect_payload(url=EXACT_URL, status=200, content_type="application/geo+json", body=good)
    tests.append(("valid_feature_collection", result["observation_verified"] is True))
    tests.append(("body_not_persisted", result["response_body_persisted"] is False and "body" not in result))
    tests.append(("hash_recorded", result["response_sha256"] == hashlib.sha256(good).hexdigest()))
    wrong_entity = json.dumps({"type": "Feature", "properties": {"entity": 1}, "geometry": None}).encode()
    tests.append(("wrong_entity_rejected", inspect_payload(url=EXACT_URL, status=200, content_type="application/json", body=wrong_entity)["observation_verified"] is False))
    tests.append(("wrong_url_rejected", inspect_payload(url="https://example.test/x.geojson", status=200, content_type="application/json", body=good)["observation_verified"] is False))
    tests.append(("wrong_status_rejected", inspect_payload(url=EXACT_URL, status=404, content_type="application/json", body=good)["observation_verified"] is False))
    tests.append(("non_json_rejected", inspect_payload(url=EXACT_URL, status=200, content_type="text/plain", body=b"not-json")["observation_verified"] is False))
    tests.append(("oversized_rejected", inspect_payload(url=EXACT_URL, status=200, content_type="application/json", body=b"x" * (MAX_BYTES + 1))["observation_verified"] is False))
    passed = sum(bool(ok) for _, ok in tests)
    return {"tests": [{"name": name, "passed": bool(ok)} for name, ok in tests], "passed": passed, "target": len(tests), "result": f"PASS_{passed}_OF_{len(tests)}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--task-continuation-key")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--fixture-response", type=Path)
    parser.add_argument("--fixture-content-type", default="application/geo+json")
    parser.add_argument("--fixture-status", type=int, default=200)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    if not args.manifest or not args.output or not args.task_continuation_key:
        parser.error("--manifest, --output and --task-continuation-key are required")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    error: str | None = None
    if args.fixture_response:
        body = args.fixture_response.read_bytes()
        status, content_type = args.fixture_status, args.fixture_content_type
    else:
        try:
            status, content_type, body = fetch_exact(args.timeout_seconds)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            status, content_type, body = 0, "", b""
            error = f"{type(exc).__name__}:{exc}"
    observation = inspect_payload(url=EXACT_URL, status=status, content_type=content_type, body=body)
    output = build_output(
        continuation_key=args.task_continuation_key,
        manifest=manifest,
        observation=observation,
        error=error,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
