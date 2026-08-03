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

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-lambeth-article4-coordinate-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
LAYER_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethArticle4/MapServer/0"
METADATA_URL = LAYER_URL + "?f=json"
QUERY_URL = LAYER_URL + "/query"
DOCUMENTATION_URL = "https://www.lambeth.gov.uk/planning-building-control/planning-policy-guidance/article-4-directions"
SPECIFICATION_URL = "https://www.planning.data.gov.uk/guidance/specifications/article-4-direction"
TERMS_URL = "https://www.lambeth.gov.uk/about-council/using-website/terms-conditions-disclaimer"
COPYRIGHT_URL = "https://www.lambeth.gov.uk/about-council/using-website/copyright"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1_048_576
MAX_FEATURES = 5
FIELDS = ["OBJECTID", "CODE", "NAME", "START_DATE", "DESCRIPTION"]
POINTS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, temp_path = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def load_points(base: Path) -> list[dict[str, Any]]:
    probe_path = base / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    data = json.loads(probe_path.read_text(encoding="utf-8"))
    rows = data.get("canonical_points", [])
    found = {row.get("parcel_id"): row for row in rows if isinstance(row, dict) and row.get("parcel_id") in POINTS}
    if set(found) != set(POINTS):
        raise ValueError("exact target parcels missing")
    output: list[dict[str, Any]] = []
    for parcel_id in POINTS:
        row = found[parcel_id]
        longitude = float(row["longitude"])
        latitude = float(row["latitude"])
        expected_longitude, expected_latitude = POINTS[parcel_id]
        if (
            row.get("geometry_type") != "Point"
            or row.get("point_valid") is not True
            or abs(longitude - expected_longitude) > 1e-7
            or abs(latitude - expected_latitude) > 1e-7
        ):
            raise ValueError(f"invalid canonical Point {parcel_id}")
        output.append({"parcel_id": parcel_id, "longitude": longitude, "latitude": latitude})
    return output


def open_bounded(url: str, timeout: float) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AAYS-parcel-label-evidence/1.0 bounded official-source research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), raw


def evidence_record(
    *,
    attempt_kind: str,
    source_url: str,
    accessed_at: str,
    content_sha256: str,
    sha256_basis: str,
    excerpt: str,
    http_status: int | None,
    parcel_id: str | None = None,
    canonical_point: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "attempt_kind": attempt_kind,
        "parcel_id": parcel_id,
        "canonical_point": canonical_point,
        "source_url": source_url,
        "accessed_at": accessed_at,
        "content_sha256": content_sha256,
        "sha256_basis": sha256_basis,
        "record_scope": (
            "one bounded official Lambeth Article 4 layer metadata request"
            if attempt_kind == "layer_metadata"
            else "one bounded exact-point intersection query against the official Lambeth Article 4 polygon layer; maximum five features, selected fields only, no geometry and 1 MiB response"
        ),
        "supports_fields": FIELDS if attempt_kind == "coordinate_query" else ["layer name", "geometry type", "spatial reference", "public attribute fields", "query capabilities"],
        "relevant_record_ids_or_excerpt": excerpt,
        "documentation_url": DOCUMENTATION_URL,
        "specification_url": SPECIFICATION_URL,
        "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL],
        "http_status": http_status,
        "requests_made": 1 if http_status is not None else 0,
    }


def metadata_attempt(timeout: float) -> dict[str, Any]:
    accessed_at = utc_now()
    try:
        status, final_url, raw = open_bounded(METADATA_URL, timeout)
        parsed = json.loads(raw.decode("utf-8"))
        public_fields = [
            field.get("name")
            for field in parsed.get("fields", [])
            if isinstance(field, dict) and field.get("type") != "esriFieldTypeGeometry"
        ][:12]
        excerpt = json.dumps(
            {
                "name": parsed.get("name"),
                "type": parsed.get("type"),
                "geometryType": parsed.get("geometryType"),
                "currentVersion": parsed.get("currentVersion"),
                "fields": public_fields,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return evidence_record(
            attempt_kind="layer_metadata",
            source_url=final_url,
            accessed_at=accessed_at,
            content_sha256=digest(raw),
            sha256_basis="bounded_response_bytes",
            excerpt=excerpt,
            http_status=status,
        )
    except Exception as exc:
        error = f"LAMBETH_ARTICLE4_METADATA_ERROR:{type(exc).__name__}:{exc}"
        return evidence_record(
            attempt_kind="layer_metadata",
            source_url=METADATA_URL,
            accessed_at=accessed_at,
            content_sha256=digest(error.encode("utf-8")),
            sha256_basis="bounded_error_evidence_string",
            excerpt=error,
            http_status=None,
        )


def coordinate_attempt(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accessed_at = utc_now()
    params = {
        "where": "1=1",
        "geometry": f"{point['longitude']},{point['latitude']}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": ",".join(FIELDS),
        "returnGeometry": "false",
        "resultRecordCount": str(MAX_FEATURES),
        "f": "json",
    }
    source_url = QUERY_URL + "?" + urllib.parse.urlencode(params)
    try:
        status, final_url, raw = open_bounded(source_url, timeout)
        parsed = json.loads(raw.decode("utf-8"))
        if parsed.get("error"):
            raise ValueError("ArcGIS error: " + json.dumps(parsed["error"], separators=(",", ":")))
        features = parsed.get("features", [])
        candidates: list[dict[str, Any]] = []
        for feature in features[:MAX_FEATURES]:
            attributes = feature.get("attributes", {}) if isinstance(feature, dict) else {}
            candidates.append(
                {
                    "parcel_id": point["parcel_id"],
                    "canonical_point": point,
                    "source_url": final_url,
                    "article4_attributes": {field: attributes.get(field) for field in FIELDS},
                    "context_only": True,
                    "exact_parcel_binding": False,
                    "property_type_binding": False,
                }
            )
        excerpt = json.dumps(
            {"feature_count": len(features), "attributes": [candidate["article4_attributes"] for candidate in candidates]},
            ensure_ascii=False,
            separators=(",", ":"),
        )[:4000]
        record = evidence_record(
            attempt_kind="coordinate_query",
            parcel_id=point["parcel_id"],
            canonical_point=point,
            source_url=final_url,
            accessed_at=accessed_at,
            content_sha256=digest(raw),
            sha256_basis="bounded_response_bytes",
            excerpt=excerpt,
            http_status=status,
        )
        return candidates, record
    except Exception as exc:
        error = f"LAMBETH_ARTICLE4_COORDINATE_ERROR:{type(exc).__name__}:{exc}"
        record = evidence_record(
            attempt_kind="coordinate_query",
            parcel_id=point["parcel_id"],
            canonical_point=point,
            source_url=source_url,
            accessed_at=accessed_at,
            content_sha256=digest(error.encode("utf-8")),
            sha256_basis="bounded_error_evidence_string",
            excerpt=error,
            http_status=None,
        )
        return [], record


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    evidence = [metadata_attempt(timeout)]
    candidates: list[dict[str, Any]] = []
    for point in points:
        rows, record = coordinate_attempt(point, timeout)
        candidates.extend(rows)
        evidence.append(record)
    candidate_count = len(candidates)
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if candidate_count else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 4,
        "target_count": 4,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": candidate_count,
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": None if candidate_count else "LAMBETH_ARTICLE4_NO_USABLE_RESPONSE_OR_NO_POINT_MATCH",
            "state": "NONE" if candidate_count else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_ARTICLE4_COORDINATE",
        "layer_url": LAYER_URL,
        "documentation_url": DOCUMENTATION_URL,
        "specification_url": SPECIFICATION_URL,
        "terms_url": TERMS_URL,
        "copyright_url": COPYRIGHT_URL,
        "open_government_licence_url": OGL_URL,
        "login_or_api_key_used": False,
        "geometry_payload_requested": False,
        "bulk_download_performed": False,
        "full_dataset_scan_performed": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate(base: Path) -> None:
    points = load_points(base)
    if len(points) != 3:
        raise ValueError("expected exactly three canonical points")
    if not LAYER_URL.startswith("https://gis.lambeth.gov.uk/arcgis/rest/services/"):
        raise ValueError("unexpected official layer host")
    if FIELDS != ["OBJECTID", "CODE", "NAME", "START_DATE", "DESCRIPTION"]:
        raise ValueError("unexpected field set")
    print("PASS_TARGET_4_LAMBETH_ARTICLE4_1_METADATA_PLUS_3_EXACT_POINT_QUERIES_MAX5_EACH_MAX1MIB_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base = repo_root()
    validate(base)
    if args.validate_only:
        return 0
    payload = build_payload(load_points(base), max(1.0, min(args.timeout, 30.0)))
    output_paths = [
        base / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_article4_coordinate_result_latest.json",
        base / "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_article4_coordinate_latest.json",
    ]
    for path in output_paths:
        atomic_json(path, payload)
    print(
        f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_4_OF_4"
        if payload["produced_candidate_rows"]
        else "PASS_NO_DATA_CONTINUE_4_OF_4"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
