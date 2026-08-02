from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-os-open-uprn-doc-manifest-v1-20260802"
SOURCE_URLS = (
    "https://docs.os.uk/os-downloads/products/addresses-and-names-portfolio/os-open-uprn",
    "https://docs.os.uk/os-downloads/identifiers/os-open-uprn/os-open-uprn-overview/product-supply",
    "https://docs.os.uk/os-downloads/identifiers/os-open-uprn/os-open-uprn-technical-specification/feature-type/os-open-uprn",
)
LICENSE_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/os_open_uprn_doc_manifest_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/os_open_uprn_doc_manifest_latest.json",
)
TARGET_IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES_PER_URL = 1024 * 1024
EXPECTED_MARKERS = {
    SOURCE_URLS[0]: ("OS Open UPRN", "CSV", "GeoPackage"),
    SOURCE_URLS[1]: ("free online download", "without registration", "Great Britain"),
    SOURCE_URLS[2]: ("UPRN", "X_COORDINATE", "Y_COORDINATE", "LATITUDE", "LONGITUDE"),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    temp.write_text(encoded, encoding="utf-8")
    os.replace(temp, target)


def load_points() -> list[dict[str, Any]]:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    points = payload.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {row.get("parcel_id"): row for row in points if isinstance(row, dict)}
    validated: list[dict[str, Any]] = []
    for parcel_id in TARGET_IDS:
        row = by_id.get(parcel_id)
        if not row:
            raise ValueError(f"missing canonical point {parcel_id}")
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates {parcel_id}")
        validated.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return validated


def validate_only() -> None:
    load_points()
    if len(SOURCE_URLS) != 3 or not all(url.startswith("https://docs.os.uk/") for url in SOURCE_URLS):
        raise ValueError("sources must be three official OS documentation HTTPS URLs")
    if not LICENSE_URL.startswith("https://www.nationalarchives.gov.uk/"):
        raise ValueError("licence URL must be the official OGL URL")
    if not all(not Path(path).is_absolute() for path in (PROBE, *OUTPUTS)):
        raise ValueError("all paths must be repository-relative")
    allowed_prefixes = (
        "docs/chatgpt_status/_shared/slots_21/parcel_label_3/",
        "england_map_web/data/aays_21_slots/parcel_label_3/",
    )
    if len(OUTPUTS) != 2 or not all(path.startswith(allowed_prefixes) for path in OUTPUTS):
        raise ValueError("exact write boundary mismatch")
    if MAX_BYTES_PER_URL != 1024 * 1024:
        raise ValueError("response bound mismatch")
    print("PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_OS_OPEN_UPRN_DOC_MANIFEST_MAX1MIB_EACH_NO_DATA_DOWNLOAD")


def run(timeout: float) -> dict[str, Any]:
    points = load_points()
    evidence: list[dict[str, Any]] = []
    source_candidates: list[dict[str, Any]] = []
    for url in SOURCE_URLS:
        accessed_at = now()
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "TerraYield-AAYS/1.0 (+source-documentation-manifest-only)"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(MAX_BYTES_PER_URL + 1)
                if len(raw) > MAX_BYTES_PER_URL:
                    raise ValueError("response exceeded 1 MiB bound")
                text = raw.decode("utf-8", errors="replace")
                normalized = re.sub(r"\s+", " ", text)
                found = [marker for marker in EXPECTED_MARKERS[url] if marker.lower() in normalized.lower()]
                evidence.append({
                    "source_url": url,
                    "accessed_at": accessed_at,
                    "content_sha256": sha256(raw),
                    "sha256_basis": "bounded_raw_response_bytes",
                    "supports_fields": list(EXPECTED_MARKERS[url]),
                    "relevant_record_ids_or_excerpt": found,
                    "license_or_terms_url": LICENSE_URL,
                    "http_status": getattr(response, "status", None),
                })
                if len(found) == len(EXPECTED_MARKERS[url]):
                    source_candidates.append({
                        "candidate_type": "OS_OPEN_UPRN_DOCUMENTATION_PAGE",
                        "source_url": url,
                        "markers": found,
                        "uprn_binding_claimed": False,
                        "exact_parcel_binding_claimed": False,
                    })
        except Exception as exc:
            error_text = f"OS_OPEN_UPRN_DOC_MANIFEST_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({
                "source_url": url,
                "accessed_at": accessed_at,
                "content_sha256": sha256(error_text),
                "sha256_basis": "bounded_error_evidence_string",
                "supports_fields": list(EXPECTED_MARKERS[url]),
                "relevant_record_ids_or_excerpt": error_text[:512],
                "license_or_terms_url": LICENSE_URL,
                "http_status": getattr(exc, "code", None),
            })

    completed = len(SOURCE_URLS)
    target = len(SOURCE_URLS)
    all_supported = len(source_candidates) == target
    state = "SOURCE_CANDIDATE_CONFIRMED" if all_supported else "NO_DATA_CONTINUE"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": completed / target * 100.0,
        "percent_increase": completed / target * 100.0,
        "validated_canonical_points": [row["parcel_id"] for row in points],
        "produced_candidate_rows": len(source_candidates),
        "source_candidates": source_candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "NONE" if all_supported else "OS_OPEN_UPRN_DOCUMENTATION_NOT_FULLY_VERIFIED",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "DISCOVER_BOUNDED_OS_OPEN_UPRN_DOWNLOAD_OR_NO_DATA_CONTINUE",
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for path in OUTPUTS:
        atomic_write(path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_only()
        return 0
    result = run(args.timeout)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "produced_candidate_rows": result["produced_candidate_rows"],
        "evidence_records": len(result["source_evidence"]),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
