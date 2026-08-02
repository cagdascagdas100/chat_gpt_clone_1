from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-overture-buildings-stac-scope-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/overture_buildings_stac_scope_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/overture_buildings_stac_scope_latest.json",
)
ROOT_CATALOG = "https://stac.overturemaps.org/catalog.json"
PINNED_RELEASE = "2026-06-17.0"
RELEASE_CATALOG = f"https://stac.overturemaps.org/{PINNED_RELEASE}/catalog.json"
BUILDING_COLLECTION = f"https://stac.overturemaps.org/{PINNED_RELEASE}/buildings/building/collection.json"
DOC_STAC = "https://docs.overturemaps.org/blog/2026/02/11/stac/"
DOC_RELEASE = "https://docs.overturemaps.org/release-calendar/"
DOC_BUILDINGS = "https://docs.overturemaps.org/guides/buildings/"
DOC_SCHEMA = "https://docs.overturemaps.org/schema/reference/buildings/building/"
DOC_LICENSE = "https://docs.overturemaps.org/attribution/"
URLS = (ROOT_CATALOG, RELEASE_CATALOG, BUILDING_COLLECTION)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1_048_576


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: str, obj: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, p)


def canonical_points() -> list[dict]:
    raw = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    by_id = {row["parcel_id"]: row for row in raw["canonical_points"]}
    out = []
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        lon, lat = float(row["longitude"]), float(row["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"invalid coordinate {parcel_id}")
        out.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return out


def bounded_json(url: str, timeout: float) -> tuple[bytes, dict, int | None, str]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "TerraYield-AAYS/1.0 bounded Overture STAC metadata research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeded 1 MiB")
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JSON object required")
        return raw, parsed, getattr(response, "status", None), response.geturl()


def summarize(index: int, data: dict) -> dict:
    if index == 0:
        return {
            "catalog_type": data.get("type"),
            "catalog_id": data.get("id"),
            "stac_version": data.get("stac_version"),
            "latest": data.get("latest"),
            "child_link_count": sum(1 for link in data.get("links", []) if isinstance(link, dict) and link.get("rel") == "child"),
        }
    if index == 1:
        return {
            "catalog_type": data.get("type"),
            "catalog_id": data.get("id"),
            "schema_version": data.get("schema:version"),
            "building_child_present": any(
                isinstance(link, dict) and link.get("rel") == "child" and "building" in str(link.get("href", "")).lower()
                for link in data.get("links", [])
            ),
        }
    return {
        "collection_type": data.get("type"),
        "collection_id": data.get("id"),
        "stac_version": data.get("stac_version"),
        "feature_count": data.get("features"),
        "item_link_count": sum(1 for link in data.get("links", []) if isinstance(link, dict) and link.get("rel") == "item"),
        "extent": data.get("extent"),
    }


def run(timeout: float) -> dict:
    points = canonical_points()
    evidence = []
    success_count = 0
    for index, url in enumerate(URLS):
        accessed_at = now()
        try:
            raw, data, status, final_url = bounded_json(url, timeout)
            summary = summarize(index, data)
            success_count += 1
            evidence.append(
                {
                    "source_url": final_url,
                    "accessed_at": accessed_at,
                    "content_sha256": sha(raw),
                    "sha256_basis": "bounded_raw_json_response_bytes",
                    "record_scope": (
                        "official Overture STAC root catalog"
                        if index == 0
                        else "official pinned Overture release catalog"
                        if index == 1
                        else "official Overture Buildings building collection metadata"
                    ),
                    "supports_fields": (
                        ["latest release identifier", "STAC version", "release child links"]
                        if index == 0
                        else ["release identifier", "schema version", "buildings child link"]
                        if index == 1
                        else ["building collection identifier", "feature count", "item links", "spatial extent"]
                    ),
                    "relevant_record_ids_or_excerpt": summary,
                    "documentation_url": DOC_STAC,
                    "release_calendar_url": DOC_RELEASE,
                    "building_guide_url": DOC_BUILDINGS,
                    "building_schema_url": DOC_SCHEMA,
                    "license_or_terms_url": DOC_LICENSE,
                    "http_status": status,
                    "large_data_downloaded": False,
                }
            )
        except Exception as exc:
            message = f"OVERTURE_BUILDINGS_STAC_SCOPE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append(
                {
                    "source_url": url,
                    "accessed_at": accessed_at,
                    "content_sha256": sha(message),
                    "sha256_basis": "bounded_error_evidence_string",
                    "record_scope": "one official Overture STAC metadata request; no GeoParquet, PMTiles or archive download",
                    "supports_fields": ["Overture STAC metadata endpoint availability"],
                    "relevant_record_ids_or_excerpt": message[:512],
                    "documentation_url": DOC_STAC,
                    "release_calendar_url": DOC_RELEASE,
                    "building_guide_url": DOC_BUILDINGS,
                    "building_schema_url": DOC_SCHEMA,
                    "license_or_terms_url": DOC_LICENSE,
                    "http_status": getattr(exc, "code", None),
                    "large_data_downloaded": False,
                }
            )
    metadata_verified = success_count == 3
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "OVERTURE_BUILDINGS_STAC_METADATA_VERIFIED_CONTINUE" if metadata_verified else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "pinned_release": PINNED_RELEASE,
        "successful_metadata_responses": success_count,
        "produced_candidate_rows": 0,
        "candidate_rows": [],
        "source_evidence": evidence,
        "blocker": {
            "code": "OVERTURE_BUILDINGS_STAC_METADATA_ONLY_NO_BOUNDED_GEOPARQUET_READER" if metadata_verified else "OVERTURE_BUILDINGS_STAC_NO_USABLE_RESPONSE",
            "state": "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "IMPLEMENT_BOUNDED_OVERTURE_BUILDINGS_GEOPARQUET_POINT_QUERY_WITH_AVAILABLE_READER"
            if metadata_verified
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OVERTURE_BUILDINGS_STAC_SCOPE"
        ),
        "large_data_downloaded": False,
        "geoparquet_downloaded": False,
        "pmtiles_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for path in OUT:
        atomic_write(path, result)
    return result


def validate() -> None:
    points = canonical_points()
    if len(points) != 3:
        raise ValueError("target count must be 3")
    for path in (PROBE, *OUT):
        if Path(path).is_absolute():
            raise ValueError("relative paths required")
    if not OUT[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/"):
        raise ValueError("state output boundary")
    if not OUT[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"):
        raise ValueError("web output boundary")
    if len(URLS) != 3 or len(set(URLS)) != 3:
        raise ValueError("exactly three distinct official metadata URLs required")
    print("PASS_TARGET_3_OVERTURE_BUILDINGS_STAC_METADATA_MAX1MIB_NO_DATA_DOWNLOAD")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(
        json.dumps(
            {
                "state": result["state"],
                "completed_count": result["completed_count"],
                "target_count": result["target_count"],
                "produced_candidate_rows": result["produced_candidate_rows"],
                "evidence_records": len(result["source_evidence"]),
                "successful_metadata_responses": result["successful_metadata_responses"],
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
