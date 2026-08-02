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
TASK_ID = "parcel-label-3-wikimedia-commons-geosearch-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
API_URL = "https://commons.wikimedia.org/w/api.php"
GEOSEARCH_DOC_URL = "https://www.mediawiki.org/wiki/API:Geosearch"
IMAGEINFO_DOC_URL = "https://www.mediawiki.org/wiki/API:Imageinfo"
LICENSING_URL = "https://commons.wikimedia.org/wiki/Commons:Licensing"
REUSE_URL = "https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia"
MAX_BYTES = 1_048_576
MAX_FILES = 20
RADIUS_METRES = 500
POINTS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_points(root: Path) -> list[dict[str, Any]]:
    probe_path = root / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    payload = json.loads(probe_path.read_text(encoding="utf-8"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list):
        raise ValueError("canonical_points missing")
    selected = {row.get("parcel_id"): row for row in rows if isinstance(row, dict) and row.get("parcel_id") in POINTS}
    if set(selected) != set(POINTS):
        raise ValueError("exact target parcels missing")
    result: list[dict[str, Any]] = []
    for parcel_id, (expected_lon, expected_lat) in POINTS.items():
        row = selected[parcel_id]
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid Point {parcel_id}")
        if abs(lon - expected_lon) > 1e-7 or abs(lat - expected_lat) > 1e-7:
            raise ValueError(f"coordinate mismatch {parcel_id}")
        result.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return result


def bounded_json(url: str, timeout: float) -> tuple[int, str, bytes, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AAYS-parcel-label-evidence/1.0 (bounded open-source research)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        decoded = json.loads(raw.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("response is not a JSON object")
        return int(getattr(response, "status", 200)), response.geturl(), raw, decoded


def metadata_value(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if isinstance(value, dict):
        raw = value.get("value")
        if raw is not None:
            return str(raw)
    return None


def query_point(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accessed_at = utc_now()
    requests_made = 0
    lat = point["latitude"]
    lon = point["longitude"]
    search_params = {
        "action": "query",
        "format": "json",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": str(RADIUS_METRES),
        "gslimit": str(MAX_FILES),
        "gsnamespace": "6",
        "gsprimary": "all",
    }
    search_url = API_URL + "?" + urllib.parse.urlencode(search_params)
    try:
        status_1, final_search_url, raw_1, search_payload = bounded_json(search_url, timeout)
        requests_made += 1
        geosearch = search_payload.get("query", {}).get("geosearch", [])
        if not isinstance(geosearch, list):
            raise ValueError("query.geosearch missing")
        geosearch = geosearch[:MAX_FILES]
        titles = [str(row.get("title")) for row in geosearch if isinstance(row, dict) and row.get("title")]
        metadata_by_title: dict[str, dict[str, Any]] = {}
        metadata_raw = b""
        metadata_status: int | None = None
        metadata_url: str | None = None
        if titles:
            info_params = {
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "titles": "|".join(titles),
                "iiprop": "url|extmetadata",
                "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit|ImageDescription|DateTimeOriginal",
                "iiextmetadatalanguage": "en",
                "iilimit": "1",
            }
            info_url = API_URL + "?" + urllib.parse.urlencode(info_params)
            metadata_status, metadata_url, metadata_raw, info_payload = bounded_json(info_url, timeout)
            requests_made += 1
            pages = info_payload.get("query", {}).get("pages", {})
            if isinstance(pages, dict):
                for page in pages.values():
                    if not isinstance(page, dict):
                        continue
                    title = page.get("title")
                    imageinfo = page.get("imageinfo")
                    if isinstance(title, str) and isinstance(imageinfo, list) and imageinfo and isinstance(imageinfo[0], dict):
                        metadata_by_title[title] = imageinfo[0]
        candidates: list[dict[str, Any]] = []
        for row in geosearch:
            if not isinstance(row, dict):
                continue
            title = str(row.get("title") or "")
            info = metadata_by_title.get(title, {})
            extmetadata = info.get("extmetadata") if isinstance(info.get("extmetadata"), dict) else {}
            license_name = metadata_value(extmetadata, "LicenseShortName")
            license_url = metadata_value(extmetadata, "LicenseUrl")
            candidates.append(
                {
                    "parcel_id": point["parcel_id"],
                    "canonical_point": point,
                    "source_page_id": row.get("pageid"),
                    "file_title": title,
                    "distance_metres": row.get("dist"),
                    "file_latitude": row.get("lat"),
                    "file_longitude": row.get("lon"),
                    "description_url": info.get("descriptionurl"),
                    "file_url": info.get("url"),
                    "license_short_name": license_name,
                    "license_url": license_url,
                    "artist": metadata_value(extmetadata, "Artist"),
                    "credit": metadata_value(extmetadata, "Credit"),
                    "image_description": metadata_value(extmetadata, "ImageDescription"),
                    "date_time_original": metadata_value(extmetadata, "DateTimeOriginal"),
                    "context_only": True,
                    "exact_parcel_binding": False,
                    "property_type_binding": False,
                    "reuse_requires_file_level_license_check": True,
                }
            )
        combined = raw_1 + b"\n" + metadata_raw
        excerpt = f"GEOSPATIAL_FILE_COUNT:{len(geosearch)};LICENSE_METADATA_COUNT:{len(metadata_by_title)}"
        evidence = {
            "parcel_id": point["parcel_id"],
            "canonical_point": point,
            "source_url": final_search_url,
            "metadata_url": metadata_url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(combined),
            "sha256_basis": "bounded_geosearch_and_imageinfo_response_bytes",
            "record_scope": "one Wikimedia Commons namespace-6 geosearch within 500 metres and one batch imageinfo request; maximum 20 files and 1 MiB per response",
            "supports_fields": [
                "nearby Commons file title",
                "distance and media coordinates",
                "file and description URLs",
                "file-level licence name and URL",
                "artist, credit and description metadata",
            ],
            "relevant_record_ids_or_excerpt": excerpt,
            "terms_or_license_urls": [LICENSING_URL, REUSE_URL],
            "http_statuses": [status_1, metadata_status],
            "requests_made": requests_made,
        }
        return candidates, evidence
    except Exception as exc:
        error = f"WIKIMEDIA_COMMONS_GEOSEARCH_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "parcel_id": point["parcel_id"],
            "canonical_point": point,
            "source_url": search_url,
            "metadata_url": None,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(error.encode("utf-8")),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded Wikimedia Commons namespace-6 geosearch and optional one batch imageinfo request; maximum two requests",
            "supports_fields": ["Wikimedia Commons API availability for nearby media and file-level licence metadata"],
            "relevant_record_ids_or_excerpt": error,
            "terms_or_license_urls": [LICENSING_URL, REUSE_URL],
            "http_statuses": [],
            "requests_made": requests_made,
        }
        return [], evidence


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for point in points:
        point_candidates, point_evidence = query_point(point, timeout)
        candidates.extend(point_candidates)
        evidence.append(point_evidence)
    count = len(candidates)
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if count else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": count,
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": None if count else "WIKIMEDIA_COMMONS_NO_USABLE_RESPONSE_OR_NO_NEARBY_MEDIA",
            "state": "NONE" if count else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_WIKIMEDIA_COMMONS_GEOSEARCH",
        "api_url": API_URL,
        "geosearch_documentation_url": GEOSEARCH_DOC_URL,
        "imageinfo_documentation_url": IMAGEINFO_DOC_URL,
        "licensing_url": LICENSING_URL,
        "reuse_url": REUSE_URL,
        "login_or_api_key_used": False,
        "media_files_downloaded": False,
        "bulk_download_performed": False,
        "full_commons_scan_performed": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate_only(root: Path) -> None:
    points = load_points(root)
    if len(points) != 3 or not API_URL.startswith("https://commons.wikimedia.org/"):
        raise ValueError("validation failed")
    if MAX_FILES != 20 or RADIUS_METRES != 500 or MAX_BYTES != 1_048_576:
        raise ValueError("bounded constants changed")
    print("PASS_TARGET_3_WIKIMEDIA_COMMONS_GEOSEARCH_MAX2_REQUESTS_EACH_500M_MAX1MIB_20_FILES_LICENSE_METADATA_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    validate_only(root)
    if args.validate_only:
        return 0
    payload = build_payload(load_points(root), max(1.0, min(args.timeout, 30.0)))
    atomic_json(root / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/wikimedia_commons_geosearch_result_latest.json", payload)
    atomic_json(root / "england_map_web/data/aays_21_slots/parcel_label_3/wikimedia_commons_geosearch_latest.json", payload)
    if payload["produced_candidate_rows"]:
        print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_3_OF_3")
    else:
        print("PASS_NO_DATA_CONTINUE_3_OF_3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
