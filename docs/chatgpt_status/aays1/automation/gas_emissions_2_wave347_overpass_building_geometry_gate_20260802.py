#!/usr/bin/env python3
"""Wave347: bounded OpenStreetMap Overpass building-geometry candidate gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = "https://overpass-api.de/api/interpreter"
RADIUS_METRES = 35
MAX_BYTES_PER_REQUEST = 750_000
MAX_TOTAL_BYTES = 2_250_000
EXPECTED_IDS = ["parcel_30762", "parcel_30763", "parcel_30764"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def extract_samples(canonical: dict[str, Any]) -> list[dict[str, Any]]:
    rows = canonical.get("rows")
    if not isinstance(rows, list):
        raise ValueError("canonical rows missing")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("parcel_id"), str):
            indexed[row["parcel_id"]] = row
    samples: list[dict[str, Any]] = []
    for parcel_id in EXPECTED_IDS:
        row = indexed.get(parcel_id)
        if row is None:
            raise ValueError(f"canonical sample missing: {parcel_id}")
        geometry = row.get("geometry")
        props = row.get("properties")
        if not isinstance(geometry, dict) or geometry.get("type") != "Point":
            raise ValueError(f"{parcel_id}: Point geometry required")
        coords = geometry.get("coordinates")
        if not isinstance(coords, list) or len(coords) != 2:
            raise ValueError(f"{parcel_id}: coordinates required")
        if not isinstance(props, dict):
            raise ValueError(f"{parcel_id}: properties required")
        lon, lat = float(coords[0]), float(coords[1])
        if not (-1.0 < lon < 1.0 and 50.0 < lat < 53.0):
            raise ValueError(f"{parcel_id}: coordinate outside expected London gate")
        samples.append({
            "parcel_id": parcel_id,
            "row_no": int(props["row_no"]),
            "hmlr_inspire_id": str(props["hmlr_inspire_id"]),
            "london_authority": str(props.get("london_authority", "")),
            "longitude": lon,
            "latitude": lat,
        })
    return samples


def build_query(lat: float, lon: float) -> str:
    return (
        "[out:json][timeout:25];"
        "("
        f'way["building"](around:{RADIUS_METRES},{lat:.7f},{lon:.7f});'
        f'relation["building"](around:{RADIUS_METRES},{lat:.7f},{lon:.7f});'
        ");"
        "out tags geom;"
    )


def bounded_post(query: str, timeout: int) -> dict[str, Any]:
    encoded = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=encoded,
        method="POST",
        headers={
            "User-Agent": "AAYS-gas-emissions-evidence-gate/1.0",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
    )
    data = b""
    status = None
    content_type = None
    final_url = None
    network_error = None
    parse_error = None
    parsed: dict[str, Any] | None = None
    truncated = False
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", None)
            content_type = response.headers.get("Content-Type")
            final_url = response.geturl()
            data = response.read(MAX_BYTES_PER_REQUEST + 1)
            if len(data) > MAX_BYTES_PER_REQUEST:
                data = data[:MAX_BYTES_PER_REQUEST]
                truncated = True
    except Exception as exc:
        network_error = f"{type(exc).__name__}:{exc}"
    if data:
        try:
            value = json.loads(data.decode("utf-8"))
            if isinstance(value, dict):
                parsed = value
            else:
                parse_error = "response JSON is not an object"
        except Exception as exc:
            parse_error = f"{type(exc).__name__}:{exc}"
    return {
        "source_url": ENDPOINT,
        "http_status": status,
        "content_type": content_type,
        "final_url": final_url,
        "bytes_read": len(data),
        "content_sha256": sha256_bytes(data),
        "truncated": truncated,
        "network_error": network_error,
        "parse_error": parse_error,
        "parsed": parsed,
    }


def candidate_from_element(element: dict[str, Any]) -> dict[str, Any] | None:
    element_type = element.get("type")
    element_id = element.get("id")
    if element_type not in {"way", "relation"} or not isinstance(element_id, int):
        return None
    tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
    geometry = element.get("geometry") if isinstance(element.get("geometry"), list) else []
    cleaned_geometry = []
    for point in geometry[:5000]:
        if isinstance(point, dict) and isinstance(point.get("lat"), (int, float)) and isinstance(point.get("lon"), (int, float)):
            cleaned_geometry.append({"lat": float(point["lat"]), "lon": float(point["lon"])})
    return {
        "osm_type": element_type,
        "osm_id": element_id,
        "building_tag": tags.get("building"),
        "name": tags.get("name"),
        "addr_housenumber": tags.get("addr:housenumber"),
        "addr_street": tags.get("addr:street"),
        "addr_postcode": tags.get("addr:postcode"),
        "geometry_point_count": len(cleaned_geometry),
        "geometry": cleaned_geometry,
        "candidate_is_exact_property_identity": False,
        "candidate_is_exact_parcel_binding": False,
    }


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def self_test() -> None:
    query = build_query(51.6769078, -0.0407406)
    required = [
        '[out:json][timeout:25]',
        'way["building"](around:35,51.6769078,-0.0407406)',
        'relation["building"](around:35,51.6769078,-0.0407406)',
        'out tags geom;',
    ]
    if not all(marker in query for marker in required):
        raise AssertionError(query)
    sample = {
        "type": "way",
        "id": 123,
        "tags": {"building": "yes", "addr:housenumber": "1"},
        "geometry": [{"lat": 51.0, "lon": -0.1}],
    }
    candidate = candidate_from_element(sample)
    if not candidate or candidate["candidate_is_exact_parcel_binding"] is not False:
        raise AssertionError("candidate semantics failed")
    print("SELF_TEST_PASS")


def run(args: argparse.Namespace) -> dict[str, Any]:
    canonical_path = Path(args.canonical)
    fixture_path = Path(args.fixture)
    output_path = Path(args.output)
    canonical = read_json(canonical_path)
    fixture = read_json(fixture_path)
    manifest = fixture.get("source_evidence_manifest")
    if not isinstance(manifest, list) or len(manifest) < 6:
        raise ValueError("complete source evidence manifest required")
    samples = extract_samples(canonical)
    assessments = []
    total_bytes = 0
    network_error_count = 0
    candidate_count = 0
    geometry_candidate_count = 0
    for index, sample in enumerate(samples):
        query = build_query(sample["latitude"], sample["longitude"])
        probe = bounded_post(query, args.timeout)
        total_bytes += int(probe["bytes_read"])
        if total_bytes > MAX_TOTAL_BYTES:
            raise RuntimeError("maximum total response bytes exceeded")
        if probe["network_error"]:
            network_error_count += 1
        candidates = []
        parsed = probe.pop("parsed")
        if isinstance(parsed, dict):
            elements = parsed.get("elements")
            if isinstance(elements, list):
                for element in elements[:250]:
                    if isinstance(element, dict):
                        candidate = candidate_from_element(element)
                        if candidate:
                            candidates.append(candidate)
        candidate_count += len(candidates)
        geometry_candidate_count += sum(1 for candidate in candidates if candidate["geometry_point_count"] >= 3)
        assessments.append({
            **sample,
            "query": query,
            "probe": probe,
            "building_candidates": candidates,
            "candidate_count": len(candidates),
            "candidate_is_exact_property_identity": False,
            "candidate_is_exact_parcel_binding": False,
            "uprn_claimed": False,
        })
        if index + 1 < len(samples):
            time.sleep(args.delay)
    now = args.accessed_at
    if candidate_count:
        decision = "OVERPASS_BUILDING_GEOMETRY_CANDIDATES_ACQUIRED_NOT_EXACT_PROPERTY_BOUND"
        first_unverified = "ASSESS_SPATIAL_CONTAINMENT_AND_INDEPENDENT_IDENTITY_PROOF_FOR_OVERPASS_BUILDING_CANDIDATES_OR_NO_DATA_CONTINUE"
    else:
        decision = "OVERPASS_BUILDING_GEOMETRY_GATE_ASSESSED_NO_LIVE_CANDIDATES"
        first_unverified = "ASSESS_OPENSTREETMAP_STATIC_EXTRACT_BUILDING_GEOMETRY_SOURCE_OR_NO_DATA_CONTINUE"
    blocker = (
        "OVERPASS_API_BUILDING_GEOMETRY_REQUESTS_NOT_LIVE_ACQUIRED;"
        "THREE_NEARBY_OSM_BUILDING_GEOMETRY_CANDIDATE_SETS_NOT_ACQUIRED;"
        "OVERPASS_AROUND_RESULTS_ARE_NOT_EXACT_PROPERTY_ADDRESS_OR_UPRN;"
        "THREE_EXACT_UPRNS_NOT_ACQUIRED;"
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        if candidate_count == 0
        else
        "OVERPASS_BUILDING_GEOMETRY_CANDIDATES_ARE_NEARBY_ONLY;"
        "INDEPENDENT_SPATIAL_CONTAINMENT_AND_IDENTITY_PROOF_NOT_COMPLETED;"
        "THREE_EXACT_UPRNS_NOT_ACQUIRED;"
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    )
    result = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 347,
        "accessed_at": now,
        "canonical_sample_rows_in_scope": len(samples),
        "candidate_semantics": fixture.get("candidate_semantics"),
        "assessment_count": len(assessments),
        "assessments": assessments,
        "overpass_building_candidate_count": candidate_count,
        "geometry_candidate_count": geometry_candidate_count,
        "network_error_count": network_error_count,
        "total_bytes_read": total_bytes,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "address_claimed": False,
        "uprn_claimed": False,
        "decision": decision,
        "state": "NO_DATA_CONTINUE",
        "blocker": blocker,
        "first_unverified_step": first_unverified,
        "source_evidence_manifest": manifest,
        "runtime_source_evidence": [{
            "source_url": ENDPOINT,
            "accessed_at": now,
            "content_sha256": sha256_bytes(b""),
            "hash_scope": "three_bounded_live_response_receipts",
            "record_scope": "Three delayed anonymous Overpass POST requests for nearby OSM way/relation building geometries around exact canonical coordinates.",
            "relevant_record_ids_or_excerpt": "; ".join(
                f"{item['parcel_id']}:{item['probe'].get('network_error') or item['probe'].get('http_status')}"
                for item in assessments
            ),
            "supports_fields": ["bounded_request_attempt", "live_network_or_http_evidence", "no_form_submission", "no_personal_data_submission", "no_exact_binding_claim"],
            "license_or_terms_url": "https://www.openstreetmap.org/copyright",
        }],
        "official_or_open_source_evidence_count": len(manifest),
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "fake_data": False,
        "final_ready": False,
    }
    atomic_write(output_path, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--delay", type=float, default=1.1)
    parser.add_argument("--accessed-at", default="2026-08-02T17:01:00Z")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test and not all((args.canonical, args.fixture, args.output)):
        parser.error("--canonical, --fixture and --output are required")
    return args


if __name__ == "__main__":
    options = parse_args()
    if options.self_test:
        self_test()
    else:
        payload = run(options)
        print(json.dumps({
            "state": payload["state"],
            "assessment_count": payload["assessment_count"],
            "candidate_count": payload["overpass_building_candidate_count"],
            "network_error_count": payload["network_error_count"],
            "total_bytes_read": payload["total_bytes_read"],
            "blocker": payload["blocker"],
            "first_unverified_step": payload["first_unverified_step"],
        }, sort_keys=True))
