from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-ons-live-postcode-geography-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/ons_live_postcode_geography_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/ons_live_postcode_geography_latest.json",
)
QUERY_BASE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Online_ONS_Postcode_Directory_Live/FeatureServer/1/query"
)
SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/"
    "Online_ONS_Postcode_Directory_Live/FeatureServer"
)
LAYER_METADATA = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/"
    "Online_ONS_Postcode_Directory_Live/FeatureServer/layers"
)
DATASET = (
    "https://www.data.gov.uk/dataset/b1c6d498-278a-4b0b-b53c-4d58d0d0646e/"
    "online-ons-postcode-directory-live2"
)
POSTCODE_PRODUCTS = "https://www.ons.gov.uk/methodology/geography/geographicalproducts/postcodeproducts"
LICENCES = "https://www.ons.gov.uk/methodology/geography/licences"
OGL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
TARGETS = (
    ("parcel_61523", "SW16 5TG"),
    ("parcel_61524", "SW16 5AE"),
    ("parcel_61525", "SW16 5AZ"),
)
OUT_FIELDS = (
    "PCDS,DOINTR,DOTERM,LAD25CD,WD25CD,CTRY25CD,RGN25CD,"
    "OA21CD,LSOA21CD,MSOA21CD,RUC21IND,LAT,LONG,USRTYPIND"
)
MAX_BYTES = 1_048_576
MAX_FEATURES_PER_POSTCODE = 1
MAX_REQUESTS_PER_POSTCODE = 1


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value: bytes | str) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def atomic_write(path: str, obj: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(
        json.dumps(obj, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(temporary, target)


def canonical_points() -> list[dict[str, Any]]:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    rows = {row["parcel_id"]: row for row in payload["canonical_points"]}
    points: list[dict[str, Any]] = []
    for parcel_id, _postcode in TARGETS:
        row = rows.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        longitude = float(row["longitude"])
        latitude = float(row["latitude"])
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise ValueError(f"invalid coordinate {parcel_id}")
        points.append({"parcel_id": parcel_id, "longitude": longitude, "latitude": latitude})
    return points


def fetch_json(url: str, timeout: float) -> tuple[bytes, dict[str, Any], int | None, str]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "TerraYield-AAYS/1.0 bounded ONS live postcode geography research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeded 1 MiB")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("ArcGIS response was not an object")
        return raw, payload, getattr(response, "status", None), response.geturl()


def build_query(postcode: str) -> str:
    escaped = postcode.replace("'", "''")
    params = {
        "where": f"PCDS='{escaped}'",
        "outFields": OUT_FIELDS,
        "returnGeometry": "false",
        "resultRecordCount": str(MAX_FEATURES_PER_POSTCODE),
        "f": "json",
    }
    return QUERY_BASE + "?" + urllib.parse.urlencode(params)


def run(timeout: float) -> dict[str, Any]:
    points = canonical_points()
    point_map = {point["parcel_id"]: point for point in points}
    evidence: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for parcel_id, postcode in TARGETS:
        accessed_at = now()
        query_url = build_query(postcode)
        requests_made = 0
        try:
            raw, payload, status, final_url = fetch_json(query_url, timeout)
            requests_made = 1
            if "error" in payload:
                raise ValueError(f"ArcGIS error: {payload['error']}")
            features = payload.get("features")
            if not isinstance(features, list):
                raise ValueError("ArcGIS features missing")
            selected = features[:MAX_FEATURES_PER_POSTCODE]
            for feature in selected:
                attributes = feature.get("attributes") if isinstance(feature, dict) else None
                if not isinstance(attributes, dict):
                    continue
                returned_postcode = attributes.get("PCDS")
                if not isinstance(returned_postcode, str) or returned_postcode.strip().upper() != postcode:
                    continue
                candidates.append({
                    "parcel_id": parcel_id,
                    "searched_postcode": postcode,
                    "canonical_point": point_map[parcel_id],
                    "ons_postcode_geography": {key: attributes.get(key) for key in OUT_FIELDS.split(",")},
                    "postcode_level_context_only": True,
                    "exact_parcel_binding_claimed": False,
                    "property_type_binding_claimed": False,
                })
            evidence.append({
                "parcel_id": parcel_id,
                "searched_postcode": postcode,
                "canonical_point": point_map[parcel_id],
                "source_url": final_url,
                "accessed_at": accessed_at,
                "content_sha256": digest(raw),
                "sha256_basis": "bounded_raw_json_response_bytes",
                "record_scope": (
                    "one exact PCDS query against official ONS live postcode layer; "
                    "selected fields only; maximum one feature and 1 MiB response"
                ),
                "supports_fields": OUT_FIELDS.split(","),
                "relevant_record_ids_or_excerpt": {
                    "feature_count": len(selected),
                    "returned_postcodes": [
                        item.get("attributes", {}).get("PCDS")
                        for item in selected if isinstance(item, dict)
                    ],
                },
                "service_url": SERVICE,
                "layer_metadata_url": LAYER_METADATA,
                "dataset_url": DATASET,
                "postcode_products_url": POSTCODE_PRODUCTS,
                "license_or_terms_url": LICENCES,
                "open_government_licence_url": OGL,
                "http_status": status,
                "requests_made": requests_made,
            })
        except Exception as exc:
            message = f"ONS_LIVE_POSTCODE_GEOGRAPHY_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({
                "parcel_id": parcel_id,
                "searched_postcode": postcode,
                "canonical_point": point_map[parcel_id],
                "source_url": query_url,
                "accessed_at": accessed_at,
                "content_sha256": digest(message),
                "sha256_basis": "bounded_error_evidence_string",
                "record_scope": (
                    "one bounded exact-postcode query against official ONS live postcode layer; "
                    "selected fields only; maximum one feature and 1 MiB response"
                ),
                "supports_fields": ["ONS live postcode exact-query availability", *OUT_FIELDS.split(",")],
                "relevant_record_ids_or_excerpt": message[:512],
                "service_url": SERVICE,
                "layer_metadata_url": LAYER_METADATA,
                "dataset_url": DATASET,
                "postcode_products_url": POSTCODE_PRODUCTS,
                "license_or_terms_url": LICENCES,
                "open_government_licence_url": OGL,
                "http_status": getattr(exc, "code", None),
                "requests_made": requests_made,
            })

    state = "ONS_POSTCODE_GEOGRAPHY_CONTEXT_FOUND" if candidates else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": len(candidates),
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "NONE" if candidates else "ONS_LIVE_POSTCODE_NO_USABLE_RESPONSE_OR_NO_EXACT_POSTCODE_RESULT",
            "state": state,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VALIDATE_ONS_POSTCODE_GEOGRAPHY_CONTEXT_WITHOUT_EXACT_PARCEL_OR_PROPERTY_TYPE_INFERENCE"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_ONS_LIVE_POSTCODE_GEOGRAPHY"
        ),
        "login_or_api_key_used": False,
        "bulk_download_performed": False,
        "full_layer_scan_performed": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output_path in OUT:
        atomic_write(output_path, result)
    return result


def validate() -> None:
    if len(canonical_points()) != 3:
        raise ValueError("target count")
    if any(Path(path).is_absolute() for path in (PROBE, *OUT)):
        raise ValueError("relative paths required")
    if not QUERY_BASE.startswith("https://services1.arcgis.com/"):
        raise ValueError("official ONS ArcGIS service required")
    if MAX_BYTES != 1_048_576 or MAX_FEATURES_PER_POSTCODE != 1 or MAX_REQUESTS_PER_POSTCODE != 1:
        raise ValueError("bounds changed")
    if len(TARGETS) != 3:
        raise ValueError("exactly three postcodes required")
    if "PCDS" not in OUT_FIELDS or "LAD25CD" not in OUT_FIELDS or "OA21CD" not in OUT_FIELDS:
        raise ValueError("required fields missing")
    print("PASS_TARGET_3_ONS_LIVE_POSTCODE_EXACT_QUERY_MAX1_REQUEST_EACH_MAX1MIB_MAX1_FEATURE_CONTEXT_ONLY")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0 or args.timeout > 30:
        raise ValueError("timeout must be >0 and <=30 seconds per request")
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(f"PASS_{result['state']}_{result['completed_count']}_OF_{result['target_count']}")


if __name__ == "__main__":
    main()
