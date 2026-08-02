#!/usr/bin/env python3
"""Wave345: bounded reverse-postcode assessment for three canonical parcel samples."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_BYTES_PER_REQUEST = 500_000
MAX_TOTAL_BYTES = 1_500_000
EXPECTED_SAMPLE_IDS = ["parcel_30762", "parcel_30763", "parcel_30764"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        tmp.write("\n")
        tmp_name = tmp.name
    os.replace(tmp_name, path)


def extract_samples(canonical: dict[str, Any]) -> list[dict[str, Any]]:
    rows = canonical.get("rows", [])
    by_id = {row.get("parcel_id"): row for row in rows}
    samples: list[dict[str, Any]] = []
    for parcel_id in EXPECTED_SAMPLE_IDS:
        row = by_id.get(parcel_id)
        if not row:
            raise ValueError(f"missing canonical sample: {parcel_id}")
        props = row.get("properties", {})
        geom = row.get("geometry", {})
        coords = geom.get("coordinates", [])
        if geom.get("type") != "Point" or len(coords) != 2:
            raise ValueError(f"invalid point geometry: {parcel_id}")
        lon, lat = float(coords[0]), float(coords[1])
        samples.append({
            "parcel_id": parcel_id,
            "row_no": props.get("row_no"),
            "hmlr_inspire_id": str(props.get("hmlr_inspire_id")),
            "longitude": lon,
            "latitude": lat,
            "london_authority": props.get("london_authority"),
        })
    return samples


def endpoint_for(sample: dict[str, Any]) -> str:
    query = urllib.parse.urlencode({
        "lon": sample["longitude"],
        "lat": sample["latitude"],
        "limit": 1,
        "radius": 1000,
    })
    return f"https://api.postcodes.io/postcodes?{query}"


def bounded_fetch(url: str, timeout: int, remaining: int) -> dict[str, Any]:
    limit = max(0, min(MAX_BYTES_PER_REQUEST, remaining))
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "AAYS-wave345/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(limit + 1)
            truncated = len(data) > limit
            data = data[:limit]
            parsed: Any = None
            parse_error: str | None = None
            try:
                parsed = json.loads(data)
            except Exception as exc:
                parse_error = f"{type(exc).__name__}:{exc}"
            return {
                "source_url": url,
                "final_url": response.geturl(),
                "http_status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "bytes_read": len(data),
                "content_sha256": sha256_bytes(data),
                "truncated": truncated,
                "json": parsed,
                "parse_error": parse_error,
                "network_error": None,
            }
    except Exception as exc:
        return {
            "source_url": url,
            "final_url": None,
            "http_status": getattr(exc, "code", None),
            "content_type": None,
            "bytes_read": 0,
            "content_sha256": sha256_bytes(b""),
            "truncated": False,
            "json": None,
            "parse_error": None,
            "network_error": f"{type(exc).__name__}:{exc}",
        }


def parse_candidate(result: dict[str, Any]) -> dict[str, Any] | None:
    payload = result.get("json")
    if not isinstance(payload, dict) or payload.get("status") != 200:
        return None
    rows = payload.get("result")
    if not isinstance(rows, list) or not rows:
        return None
    row = rows[0]
    if not isinstance(row, dict):
        return None
    postcode = row.get("postcode")
    distance = row.get("distance")
    if not isinstance(postcode, str) or not postcode.strip():
        return None
    return {
        "postcode": postcode.strip(),
        "distance_metres": float(distance) if isinstance(distance, (int, float)) else None,
        "longitude": row.get("longitude"),
        "latitude": row.get("latitude"),
        "admin_district": row.get("admin_district"),
        "region": row.get("region"),
        "quality": row.get("quality"),
    }


def self_test() -> None:
    canonical = {
        "rows": [
            {"parcel_id": "parcel_30762", "geometry": {"type": "Point", "coordinates": [-0.04, 51.67]}, "properties": {"row_no": 30762, "hmlr_inspire_id": "46058185", "london_authority": "Enfield"}},
            {"parcel_id": "parcel_30763", "geometry": {"type": "Point", "coordinates": [-0.05, 51.67]}, "properties": {"row_no": 30763, "hmlr_inspire_id": "46037757", "london_authority": "Enfield"}},
            {"parcel_id": "parcel_30764", "geometry": {"type": "Point", "coordinates": [-0.048, 51.678]}, "properties": {"row_no": 30764, "hmlr_inspire_id": "45981756", "london_authority": "Enfield"}},
        ]
    }
    samples = extract_samples(canonical)
    assert len(samples) == 3
    assert "lon=" in endpoint_for(samples[0]) and "lat=" in endpoint_for(samples[0])
    candidate = parse_candidate({"json": {"status": 200, "result": [{"postcode": "EN3 6AA", "distance": 15.5}]}})
    assert candidate and candidate["postcode"] == "EN3 6AA" and candidate["distance_metres"] == 15.5
    assert parse_candidate({"json": {"status": 200, "result": []}}) is None
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.canonical or not args.fixture or not args.output:
        parser.error("--canonical, --fixture and --output are required unless --self-test is used")

    canonical_bytes = args.canonical.read_bytes()
    fixture_bytes = args.fixture.read_bytes()
    canonical = json.loads(canonical_bytes)
    fixture = json.loads(fixture_bytes)
    manifest = fixture.get("source_evidence_manifest", [])
    if len(manifest) != 5:
        raise SystemExit("fixture must contain exactly five source evidence records")
    samples = extract_samples(canonical)

    total_bytes = 0
    assessments: list[dict[str, Any]] = []
    for sample in samples:
        url = endpoint_for(sample)
        probe = bounded_fetch(url, args.timeout, MAX_TOTAL_BYTES - total_bytes)
        total_bytes += probe["bytes_read"]
        candidate = parse_candidate(probe)
        assessments.append({
            **sample,
            "request_url": url,
            "probe": {k: v for k, v in probe.items() if k != "json"},
            "nearest_postcode_candidate": candidate,
            "candidate_is_exact_property_identity": False,
            "candidate_is_exact_parcel_binding": False,
        })

    candidate_count = sum(1 for row in assessments if row["nearest_postcode_candidate"])
    network_error_count = sum(1 for row in assessments if row["probe"]["network_error"])
    blocker_parts: list[str] = []
    if network_error_count:
        blocker_parts.append("POSTCODES_IO_REVERSE_GEOCODE_REQUESTS_NOT_LIVE_ACQUIRED")
    if candidate_count < 3:
        blocker_parts.append("THREE_NEAREST_POSTCODE_CANDIDATES_NOT_ACQUIRED")
    blocker_parts.extend([
        "NEAREST_POSTCODE_IS_NOT_EXACT_PROPERTY_ADDRESS_OR_UPRN",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    output = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 345,
        "accessed_at": utc_now(),
        "state": "NO_DATA_CONTINUE",
        "decision": "NEAREST_POSTCODE_CANDIDATE_GATE_ASSESSED_NO_EXACT_PROPERTY_BINDING",
        "blocker": ";".join(blocker_parts),
        "first_unverified_step": "ASSESS_OPEN_ADDRESS_OR_BUILDING_IDENTIFIER_SOURCE_FOR_THREE_CANONICAL_COORDINATES_OR_NO_DATA_CONTINUE",
        "fake_data": False,
        "final_ready": False,
        "canonical_sample_rows_in_scope": 3,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "canonical_sha256": sha256_bytes(canonical_bytes),
        "fixture_sha256": sha256_bytes(fixture_bytes),
        "source_evidence_manifest": manifest,
        "official_or_open_source_evidence_count": len(manifest),
        "assessment_count": len(assessments),
        "nearest_postcode_candidate_count": candidate_count,
        "network_error_count": network_error_count,
        "total_bytes_read": total_bytes,
        "max_total_bytes": MAX_TOTAL_BYTES,
        "assessments": assessments,
        "address_claimed": False,
        "uprn_claimed": False,
        "parcel_binding_claimed": False,
    }
    atomic_json(args.output, output)


if __name__ == "__main__":
    main()
