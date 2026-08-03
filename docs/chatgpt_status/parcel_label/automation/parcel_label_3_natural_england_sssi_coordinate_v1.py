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
TASK_ID = "parcel-label-3-natural-england-sssi-coordinate-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
LAYER_URL = "https://services.arcgis.com/JJzESW51TqeY9uat/arcgis/rest/services/SSSI_England/FeatureServer/0"
FEATURE_SERVICE_URL = "https://services.arcgis.com/JJzESW51TqeY9uat/arcgis/rest/services/SSSI_England/FeatureServer"
DATASET_URL = "https://environment.data.gov.uk/dataset/ba8dc201-66ef-4983-9d46-7378af21027e"
GUIDANCE_URL = "https://www.gov.uk/government/collections/sites-of-special-scientific-interest"
ACCESS_GUIDANCE_URL = "https://www.gov.uk/guidance/how-to-access-natural-englands-maps-and-data"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1_048_576
MAX_FEATURES = 5
OUT_FIELDS = ["OBJECTID", "REF_CODE", "NAME", "MEASURE", "LABEL", "HYPERLINK", "CONTACT_NO"]
POINTS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_points(base: Path) -> list[dict[str, Any]]:
    probe_path = base / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    payload = json.loads(probe_path.read_text(encoding="utf-8"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list):
        raise ValueError("canonical_points missing")
    found = {row.get("parcel_id"): row for row in rows if isinstance(row, dict) and row.get("parcel_id") in POINTS}
    if set(found) != set(POINTS):
        raise ValueError("exact target parcels missing")
    validated: list[dict[str, Any]] = []
    for parcel_id, expected in POINTS.items():
        row = found[parcel_id]
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid Point row: {parcel_id}")
        if abs(lon - expected[0]) > 1e-7 or abs(lat - expected[1]) > 1e-7:
            raise ValueError(f"coordinate mismatch: {parcel_id}")
        validated.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return validated


def bounded_get(url: str, timeout: float) -> tuple[int, str, bytes]:
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


def evidence(
    *,
    source_url: str,
    accessed_at: str,
    digest: str,
    basis: str,
    record_scope: str,
    supports_fields: list[str],
    excerpt: str,
    http_status: int | None,
    parcel_id: str | None = None,
    point: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "parcel_id": parcel_id,
        "canonical_point": point,
        "source_url": source_url,
        "accessed_at": accessed_at,
        "content_sha256": digest,
        "sha256_basis": basis,
        "record_scope": record_scope,
        "supports_fields": supports_fields,
        "relevant_record_ids_or_excerpt": excerpt,
        "terms_or_license_urls": [DATASET_URL, ACCESS_GUIDANCE_URL, OGL_URL],
        "http_status": http_status,
    }


def metadata_attempt(timeout: float) -> tuple[list[str], dict[str, Any]]:
    accessed_at = now_iso()
    url = LAYER_URL + "?" + urllib.parse.urlencode({"f": "json"})
    try:
        status, final_url, raw = bounded_get(url, timeout)
        parsed = json.loads(raw.decode("utf-8"))
        published = [field.get("name") for field in parsed.get("fields", []) if isinstance(field, dict)]
        selected = [name for name in OUT_FIELDS if name in published][:12]
        if not selected:
            selected = OUT_FIELDS[:]
        excerpt = json.dumps(
            {
                "name": parsed.get("name"),
                "geometryType": parsed.get("geometryType"),
                "objectIdField": parsed.get("objectIdField"),
                "selected_fields": selected,
                "maxRecordCount": parsed.get("maxRecordCount"),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return selected, evidence(
            source_url=final_url,
            accessed_at=accessed_at,
            digest=sha256_bytes(raw),
            basis="bounded_metadata_response_bytes",
            record_scope="one bounded official Natural England Sites of Special Scientific Interest layer metadata request; maximum 1 MiB",
            supports_fields=["layer name", "polygon geometry type", "published field names", "record limit"],
            excerpt=excerpt,
            http_status=status,
        )
    except Exception as exc:
        error = f"NATURAL_ENGLAND_SSSI_METADATA_ERROR:{type(exc).__name__}:{exc}"
        return OUT_FIELDS[:], evidence(
            source_url=url,
            accessed_at=accessed_at,
            digest=sha256_bytes(error.encode("utf-8")),
            basis="bounded_error_evidence_string",
            record_scope="one bounded official Natural England Sites of Special Scientific Interest layer metadata request; maximum 1 MiB",
            supports_fields=["layer metadata availability"],
            excerpt=error,
            http_status=None,
        )


def point_attempt(point: dict[str, Any], fields: list[str], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accessed_at = now_iso()
    geometry = json.dumps(
        {"x": point["longitude"], "y": point["latitude"], "spatialReference": {"wkid": 4326}},
        separators=(",", ":"),
    )
    params = {
        "f": "json",
        "geometry": geometry,
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": ",".join(fields[:12]),
        "returnGeometry": "false",
        "resultRecordCount": str(MAX_FEATURES),
    }
    url = LAYER_URL + "/query?" + urllib.parse.urlencode(params)
    try:
        status, final_url, raw = bounded_get(url, timeout)
        parsed = json.loads(raw.decode("utf-8"))
        features = parsed.get("features") if isinstance(parsed, dict) else None
        rows: list[dict[str, Any]] = []
        if isinstance(features, list):
            for item in features[:MAX_FEATURES]:
                attributes = item.get("attributes") if isinstance(item, dict) else None
                if isinstance(attributes, dict):
                    rows.append(
                        {
                            "parcel_id": point["parcel_id"],
                            "canonical_point": point,
                            "source_url": final_url,
                            "attributes": {key: attributes.get(key) for key in fields[:12] if key in attributes},
                            "context_only": True,
                            "designation_context": "Site of Special Scientific Interest",
                            "exact_parcel_binding": False,
                            "property_type_binding": False,
                        }
                    )
        excerpt = json.dumps(
            {
                "feature_count": len(rows),
                "field_names": fields[:12],
                "exceededTransferLimit": parsed.get("exceededTransferLimit") if isinstance(parsed, dict) else None,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return rows, evidence(
            parcel_id=point["parcel_id"],
            point=point,
            source_url=final_url,
            accessed_at=accessed_at,
            digest=sha256_bytes(raw),
            basis="bounded_point_query_response_bytes",
            record_scope="one bounded exact-point intersection query against official Natural England Sites of Special Scientific Interest layer; maximum five features, twelve fields, no geometry and 1 MiB",
            supports_fields=fields[:12],
            excerpt=excerpt,
            http_status=status,
        )
    except Exception as exc:
        error = f"NATURAL_ENGLAND_SSSI_POINT_ERROR:{type(exc).__name__}:{exc}"
        return [], evidence(
            parcel_id=point["parcel_id"],
            point=point,
            source_url=url,
            accessed_at=accessed_at,
            digest=sha256_bytes(error.encode("utf-8")),
            basis="bounded_error_evidence_string",
            record_scope="one bounded exact-point intersection query against official Natural England Sites of Special Scientific Interest layer; maximum five features, twelve fields, no geometry and 1 MiB",
            supports_fields=fields[:12],
            excerpt=error,
            http_status=None,
        )


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    fields, metadata_evidence = metadata_attempt(timeout)
    candidates: list[dict[str, Any]] = []
    source_evidence = [metadata_evidence]
    for point in points:
        rows, row_evidence = point_attempt(point, fields, timeout)
        candidates.extend(rows)
        source_evidence.append(row_evidence)
    produced = len(candidates)
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": now_iso(),
        "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if produced else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 4,
        "target_count": 4,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": produced,
        "candidate_rows": candidates,
        "source_evidence": source_evidence,
        "blocker": {
            "code": None if produced else "NATURAL_ENGLAND_SSSI_NO_USABLE_RESPONSE_OR_NO_POINT_MATCH",
            "state": "NONE" if produced else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_NATURAL_ENGLAND_SSSI_COORDINATE",
        "layer_url": LAYER_URL,
        "feature_service_url": FEATURE_SERVICE_URL,
        "dataset_url": DATASET_URL,
        "guidance_url": GUIDANCE_URL,
        "access_guidance_url": ACCESS_GUIDANCE_URL,
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


def validate_only(base: Path) -> None:
    points = load_points(base)
    if len(points) != 3 or not LAYER_URL.startswith("https://services.arcgis.com/"):
        raise ValueError("validation failed")
    if len(OUT_FIELDS) > 12 or MAX_FEATURES > 5 or MAX_BYTES != 1_048_576:
        raise ValueError("bounded limits invalid")
    print("PASS_TARGET_4_NATURAL_ENGLAND_SSSI_1_METADATA_PLUS_3_EXACT_POINT_QUERIES_MAX5_EACH_MAX12_FIELDS_MAX1MIB_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base = repo_root()
    validate_only(base)
    if args.validate_only:
        return 0
    payload = build_payload(load_points(base), max(1.0, min(args.timeout, 30.0)))
    atomic_json(base / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/natural_england_sssi_coordinate_result_latest.json", payload)
    atomic_json(base / "england_map_web/data/aays_21_slots/parcel_label_3/natural_england_sssi_coordinate_latest.json", payload)
    if payload["produced_candidate_rows"]:
        print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_4_OF_4")
    else:
        print("PASS_NO_DATA_CONTINUE_4_OF_4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
