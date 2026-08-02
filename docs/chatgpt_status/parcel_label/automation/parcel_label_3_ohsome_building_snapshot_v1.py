from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-ohsome-building-snapshot-v1-20260802"
ENDPOINT = "https://api.ohsome.org/v1/elements/geometry"
DOC_URL = "https://docs.ohsome.org/ohsome-api/stable/endpoints.html"
FILTER_DOC_URL = "https://docs.ohsome.org/ohsome-api/v1/filter.html"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/ohsome_building_snapshot_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/ohsome_building_snapshot_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024
MAX_CANDIDATES = 10
RADIUS_METERS = 25.0
REQUEST_SPACING_SECONDS = 1.2
FILTER = "building=* and geometry:polygon"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def load_points(root: Path) -> list[dict[str, Any]]:
    data = json.loads((root / PROBE).read_text(encoding="utf-8"))
    points = {p.get("parcel_id"): p for p in data.get("canonical_points", [])}
    selected: list[dict[str, Any]] = []
    for parcel_id in IDS:
        p = points.get(parcel_id)
        if not p or p.get("geometry_type") != "Point" or p.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon = float(p["longitude"])
        lat = float(p["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"invalid coordinate: {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return selected


def bbox_around(lon: float, lat: float) -> str:
    lat_delta = RADIUS_METERS / 111_320.0
    lon_delta = RADIUS_METERS / (111_320.0 * max(math.cos(math.radians(lat)), 0.1))
    return f"{lon-lon_delta:.7f},{lat-lat_delta:.7f},{lon+lon_delta:.7f},{lat+lat_delta:.7f}"


def build_url(lon: float, lat: float) -> str:
    params = {
        "bboxes": bbox_around(lon, lat),
        "filter": FILTER,
        "time": "latest",
        "properties": "tags,metadata",
        "clipGeometry": "false",
    }
    return ENDPOINT + "?" + urllib.parse.urlencode(params)


def fetch(url: str, timeout: float) -> tuple[int | None, bytes | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS/parcel-label-evidence"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                return int(response.status), None, "ResponseTooLarge"
            return int(response.status), body, None
    except Exception as exc:  # fail closed and preserve bounded technical evidence
        return None, None, type(exc).__name__


def validate() -> None:
    assert not Path(PROBE).is_absolute()
    assert all(not Path(p).is_absolute() for p in OUTPUTS)
    assert ENDPOINT.startswith("https://api.ohsome.org/")
    assert MAX_BYTES == 1024 * 1024
    assert MAX_CANDIDATES == 10
    assert RADIUS_METERS == 25.0
    assert FILTER == "building=* and geometry:polygon"
    print("PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_OHSOME_BUILDING_SNAPSHOT_25M_MAX10_MAX1MIB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate()
        return 0

    root = Path.cwd()
    points = load_points(root)
    evidence: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for index, point in enumerate(points):
        if index:
            time.sleep(REQUEST_SPACING_SECONDS)
        url = build_url(point["longitude"], point["latitude"])
        accessed_at = now()
        status, body, error = fetch(url, args.timeout)
        record: dict[str, Any] = {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": sha256(url),
            "record_scope": "one approximately 25m bbox ohsome latest OSM building polygon extraction; retain max 10 candidates",
            "proven_fields": ["query URL", "access time", "query SHA-256"],
            "http_status": status,
        }
        if body is None:
            marker = f"OHSOME_BUILDING_SNAPSHOT_ERROR:{error}"
            record.update({
                "content_sha256": sha256(marker),
                "sha256_basis": "bounded_error_evidence_string",
                "relevant_record_ids_or_excerpt": marker,
                "candidate_count": 0,
            })
        else:
            record["content_sha256"] = sha256(body)
            record["sha256_basis"] = "raw_response_bytes"
            try:
                payload = json.loads(body.decode("utf-8"))
                features = payload.get("features", []) if isinstance(payload, dict) else []
                for feature in features[:MAX_CANDIDATES]:
                    props = feature.get("properties") if isinstance(feature, dict) else None
                    props = props if isinstance(props, dict) else {}
                    candidate = {
                        "parcel_id": point["parcel_id"],
                        "osm_id": props.get("@osmId"),
                        "osm_type": props.get("@osmType"),
                        "timestamp": props.get("@timestamp"),
                        "building": props.get("building"),
                        "name": props.get("name"),
                        "addr_housenumber": props.get("addr:housenumber"),
                        "addr_street": props.get("addr:street"),
                        "source_candidate_only": True,
                    }
                    candidates.append(candidate)
                ids = [str(c.get("osm_id")) for c in candidates if c.get("parcel_id") == point["parcel_id"] and c.get("osm_id")]
                record["relevant_record_ids_or_excerpt"] = ids[:MAX_CANDIDATES]
                record["candidate_count"] = len(features[:MAX_CANDIDATES])
                record["proven_fields"] += ["raw-response SHA-256", "returned OSM candidate fields"]
            except Exception as exc:
                record["relevant_record_ids_or_excerpt"] = f"OHSOME_BUILDING_SNAPSHOT_PARSE_ERROR:{type(exc).__name__}"
                record["candidate_count"] = 0
        evidence.append(record)

    completed = len(evidence)
    target = len(points)
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "CANDIDATES_FOUND_CONTINUE" if candidates else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": completed / target * 100.0,
        "percent_increase": completed / target * 100.0,
        "validated_canonical_points": list(IDS),
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "OHSOME_BUILDING_SNAPSHOT_NO_USABLE_RESPONSE" if not candidates else None,
            "state": "NO_DATA_CONTINUE" if not candidates else "CANDIDATES_FOUND_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OHSOME_BUILDING_SNAPSHOT",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write(root / output, result)
    print(json.dumps({"state": result["state"], "completed": f"{completed}/{target}", "candidates": len(candidates)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
