from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-openstreetmap-core-map-v1-20260802"
API_URL = "https://api.openstreetmap.org/api/0.6/map"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/openstreetmap_core_map_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/openstreetmap_core_map_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024
MAX_CANDIDATES = 10
HALF_SIZE_METERS = 25.0
REQUEST_SPACING_SECONDS = 1.2
USER_AGENT = "TerraYield-AAYS/parcel_label_3 bounded public-source research"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def validate_relative(path: str) -> None:
    p = Path(path)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"non-relative path: {path}")


def validate_contract() -> str:
    validate_relative(PROBE)
    for path in OUTPUTS:
        validate_relative(path)
    if not API_URL.startswith("https://api.openstreetmap.org/api/0.6/map"):
        raise ValueError("unexpected OpenStreetMap core API URL")
    if MAX_BYTES != 1024 * 1024 or MAX_CANDIDATES != 10 or HALF_SIZE_METERS != 25.0:
        raise ValueError("bounded constants changed")
    return "PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_OPENSTREETMAP_CORE_MAP_25M_MAX10_MAX1MIB"


def read_points(root: Path) -> list[dict[str, Any]]:
    payload = json.loads((root / PROBE).read_text(encoding="utf-8"))
    by_id = {row.get("parcel_id"): row for row in payload.get("canonical_points", [])}
    points: list[dict[str, Any]] = []
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row:
            raise ValueError(f"missing canonical point: {parcel_id}")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid point metadata: {parcel_id}")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        points.append({"parcel_id": parcel_id, "longitude": float(lon), "latitude": float(lat)})
    return points


def bbox_for(lon: float, lat: float) -> tuple[float, float, float, float]:
    lat_delta = HALF_SIZE_METERS / 111_320.0
    lon_scale = max(0.1, math.cos(math.radians(lat)))
    lon_delta = HALF_SIZE_METERS / (111_320.0 * lon_scale)
    return lon - lon_delta, lat - lat_delta, lon + lon_delta, lat + lat_delta


def build_url(lon: float, lat: float) -> str:
    left, bottom, right, top = bbox_for(lon, lat)
    bbox = f"{left:.7f},{bottom:.7f},{right:.7f},{top:.7f}"
    return API_URL + "?" + urllib.parse.urlencode({"bbox": bbox}, safe=",")


def parse_candidates(raw: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(raw)
    candidates: list[dict[str, Any]] = []
    for element in root:
        if element.tag not in {"node", "way", "relation"}:
            continue
        tags = {
            tag.attrib.get("k", ""): tag.attrib.get("v", "")
            for tag in element.findall("tag")
            if tag.attrib.get("k")
        }
        if "building" not in tags and "building:part" not in tags:
            continue
        candidates.append(
            {
                "osm_type": element.tag,
                "osm_id": element.attrib.get("id"),
                "tags": tags,
            }
        )
        if len(candidates) >= MAX_CANDIDATES:
            break
    return candidates


def fetch_once(url: str, timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accessed_at = now()
    evidence: dict[str, Any] = {
        "source_url": url,
        "accessed_at": accessed_at,
        "query_sha256": sha256(url),
        "record_scope": "one approximately 25m OpenStreetMap core API map bbox; retain max 10 building/building:part candidates; max 1 MiB",
        "proven_fields": ["query URL", "access time", "query SHA-256"],
    }
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/xml"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            evidence["http_status"] = getattr(response, "status", None)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB bound")
        evidence["content_sha256"] = sha256(raw)
        evidence["sha256_basis"] = "bounded_raw_response"
        candidates = parse_candidates(raw)
        evidence["candidate_count"] = len(candidates)
        evidence["relevant_record_ids_or_excerpt"] = [
            f"{row['osm_type']}/{row['osm_id']}" for row in candidates
        ]
        evidence["proven_fields"] += ["HTTP status", "raw-response SHA-256", "OSM element ids", "raw OSM tags"]
        return candidates, evidence
    except Exception as exc:
        error_text = f"OPENSTREETMAP_CORE_MAP_ERROR:{type(exc).__name__}:{exc}"
        evidence.update(
            {
                "http_status": getattr(exc, "code", None),
                "content_sha256": sha256(error_text),
                "sha256_basis": "bounded_error_evidence_string",
                "relevant_record_ids_or_excerpt": error_text[:500],
                "candidate_count": 0,
            }
        )
        return [], evidence


def run(root: Path, timeout: float) -> dict[str, Any]:
    points = read_points(root)
    source_candidates: list[dict[str, Any]] = []
    source_evidence: list[dict[str, Any]] = []
    for index, point in enumerate(points):
        if index:
            time.sleep(REQUEST_SPACING_SECONDS)
        url = build_url(point["longitude"], point["latitude"])
        candidates, evidence = fetch_once(url, timeout)
        evidence["parcel_id"] = point["parcel_id"]
        source_evidence.append(evidence)
        for candidate in candidates:
            source_candidates.append({"parcel_id": point["parcel_id"], **candidate})
    state = "DATA_CANDIDATES" if source_candidates else "NO_DATA_CONTINUE"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": len(points),
        "target_count": len(IDS),
        "previous_percent": 0.0,
        "progress_percent": len(points) / len(IDS) * 100.0,
        "percent_increase": len(points) / len(IDS) * 100.0,
        "validated_canonical_points": [point["parcel_id"] for point in points],
        "produced_candidate_rows": len(source_candidates),
        "source_candidates": source_candidates,
        "source_evidence": source_evidence,
        "blocker": {
            "code": None if source_candidates else "OPENSTREETMAP_CORE_MAP_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OPENSTREETMAP_CORE_MAP",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write_json(root / output, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    validation = validate_contract()
    if args.validate_only:
        print(validation)
        return 0
    payload = run(Path(args.root), args.timeout)
    print(json.dumps({
        "state": payload["state"],
        "completed_count": payload["completed_count"],
        "target_count": payload["target_count"],
        "produced_candidate_rows": payload["produced_candidate_rows"],
        "evidence_records": len(payload["source_evidence"]),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
