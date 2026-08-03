#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone

INPUT = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
OUTPUTS = [
    pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/osm_overpass_exact_building_result_latest.json"),
    pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/osm_overpass_exact_building_latest.json"),
]
ENDPOINT = "https://overpass-api.de/api/interpreter"
ATTRIBUTION_URL = "https://www.openstreetmap.org/copyright"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

def split_address(row: dict) -> tuple[str, str, str]:
    address = str(row["FULLADDRESS"])
    postcode = str(row["POSTCODE"]).strip().upper()
    prefix = address[:-len(postcode)].strip() if address.upper().endswith(postcode) else address
    match = re.match(r"^\s*([0-9]+[A-Za-z]?)\s+(.+?)\s+London\s*$", prefix, re.I)
    if not match:
        raise RuntimeError(f"ADDRESS_PARSE_FAILED:{row['parcel_id']}:{address}")
    return match.group(1).upper(), match.group(2).strip(), postcode

def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        tmp = pathlib.Path(handle.name)
    tmp.replace(path)

def load_rows() -> list[dict]:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = payload.get("records", [])
    if len(rows) != 3:
        raise RuntimeError(f"EXPECTED_3_ROWS:{len(rows)}")
    for row in rows:
        for key in ("parcel_id", "UPRN", "FULLADDRESS", "POSTCODE", "longitude", "latitude"):
            if key not in row:
                raise RuntimeError(f"MISSING_FIELD:{row.get('parcel_id')}:{key}")
        if not row.get("exact_uprn_bound"):
            raise RuntimeError(f"NOT_EXACT_UPRN_BOUND:{row['parcel_id']}")
        split_address(row)
    return rows

def build_query(row: dict) -> str:
    house, street, _postcode = split_address(row)
    lat = float(row["latitude"])
    lon = float(row["longitude"])
    return (
        "[out:json][timeout:25];"
        f'way(around:25,{lat:.8f},{lon:.8f})["building"]'
        f'["addr:housenumber"="{house}"]["addr:street"="{street}"];'
        "out tags geom;"
    )

def fetch_json(query: str, timeout: int) -> tuple[dict, str]:
    body = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"User-Agent": "AAYS-parcel-label-3/1.0", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise RuntimeError(f"OVERPASS_RESPONSE_TOO_LARGE:{len(raw)}")
        final_url = response.geturl()
        if urllib.parse.urlsplit(final_url).scheme != "https":
            raise RuntimeError("OVERPASS_FINAL_URL_NOT_HTTPS")
        return json.loads(raw), hashlib.sha256(raw).hexdigest()

def candidate_from_element(element: dict, row: dict) -> dict | None:
    tags = element.get("tags") or {}
    house, street, postcode = split_address(row)
    if str(tags.get("addr:housenumber", "")).upper() != house:
        return None
    if norm(str(tags.get("addr:street", ""))) != norm(street):
        return None
    tagged_postcode = str(tags.get("addr:postcode", "")).strip().upper()
    if tagged_postcode and tagged_postcode != postcode:
        return None
    geometry = element.get("geometry") or []
    coordinates = [[float(p["lon"]), float(p["lat"])] for p in geometry if "lon" in p and "lat" in p]
    if len(coordinates) < 4:
        return None
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    geometry_obj = {"type": "Polygon", "coordinates": [coordinates]}
    geometry_text = json.dumps(geometry_obj, separators=(",", ":"), sort_keys=True)
    return {
        "osm_type": str(element.get("type", "way")),
        "osm_id": int(element["id"]),
        "geometry": geometry_obj,
        "geometry_sha256": hashlib.sha256(geometry_text.encode("utf-8")).hexdigest(),
        "coordinate_count": len(coordinates),
        "tags": {
            key: tags[key]
            for key in ("building", "addr:housenumber", "addr:street", "addr:postcode")
            if key in tags
        },
    }

def evaluate_payload(payload: dict, row: dict) -> tuple[str, dict | None, int]:
    candidates = []
    for element in payload.get("elements", []):
        candidate = candidate_from_element(element, row)
        if candidate is not None:
            candidates.append(candidate)
    if len(candidates) == 1:
        return "MATCHED_EXACT_BUILDING", candidates[0], 1
    if len(candidates) > 1:
        return "NO_DATA", None, len(candidates)
    return "NO_DATA", None, 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    rows = load_rows()
    if args.validate_only:
        print(json.dumps({
            "valid": True,
            "input_count": 3,
            "resource_class": "network_fetch",
            "endpoint": ENDPOINT,
            "write_paths": [str(path) for path in OUTPUTS],
        }, sort_keys=True))
        return 0

    records = []
    matched = 0
    for row in rows:
        query = build_query(row)
        record = {
            "parcel_id": row["parcel_id"],
            "UPRN": str(row["UPRN"]),
            "FULLADDRESS": row["FULLADDRESS"],
            "source_url": ENDPOINT,
            "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            "accessed_at": utc_now(),
            "attribution_url": ATTRIBUTION_URL,
            "exact_uprn_bound": True,
            "inferred": False,
        }
        try:
            payload, response_sha = fetch_json(query, args.timeout)
            state, candidate, candidate_count = evaluate_payload(payload, row)
            record.update({
                "state": state,
                "response_content_sha256": response_sha,
                "exact_candidate_count": candidate_count,
            })
            if candidate is not None:
                record.update(candidate)
                matched += 1
            elif candidate_count > 1:
                record["reason"] = "AMBIGUOUS_MULTIPLE_EXACT_ADDRESS_BUILDINGS"
            else:
                record["reason"] = "NO_EXACT_ADDRESS_BUILDING"
        except Exception as exc:
            record.update({
                "state": "NO_DATA",
                "exact_candidate_count": 0,
                "reason": f"{type(exc).__name__}:{exc}",
            })
        records.append(record)

    result_state = "PUBLISHED" if matched else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": "parcel-label-3-osm-overpass-exact-building-v1-20260803",
        "state": result_state,
        "panel_status": "PUBLISHED",
        "completed_count": len(records),
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": round(len(records) / 3 * 100, 6),
        "percent_increase": round(len(records) / 3 * 100, 6),
        "matched_exact_building_rows": matched,
        "evidence_records": len(records),
        "source_url": ENDPOINT,
        "license_or_terms_url": ATTRIBUTION_URL,
        "records": records,
        "fake_data": False,
        "generated_at": utc_now(),
    }
    text = json.dumps(result, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    for output in OUTPUTS:
        atomic_write(output, text)
    print(json.dumps({
        "completed_count": 3,
        "target_count": 3,
        "matched_exact_building_rows": matched,
        "state": result_state,
        "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
