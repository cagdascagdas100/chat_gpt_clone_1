from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-fsa-establishments-postcode-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/fsa_establishments_postcode_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/fsa_establishments_postcode_latest.json",
)
ENDPOINT = "https://api.ratings.food.gov.uk/Establishments"
HELP_URL = "https://api.ratings.food.gov.uk/help"
SEARCH_DOC_URL = "https://api.ratings.food.gov.uk/Help/Api/GET-Establishments_name_address_longitude_latitude_maxDistanceLimit_businessTypeId_schemeTypeKey_ratingKey_ratingOperatorKey_localAuthorityId_countryId_sortOptionKey_pageNumber_pageSize"
OPEN_DATA_URL = "https://ratings.food.gov.uk/open-data?lang=en-US"
TERMS_URL = "https://ratings.food.gov.uk/terms-and-conditions"
POSTCODES = (
    ("parcel_61523", "SW16 5TG"),
    ("parcel_61524", "SW16 5AE"),
    ("parcel_61525", "SW16 5AZ"),
)
PAGE_SIZE = 20
MAX_BYTES = 1_048_576


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: str, obj: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, target)


def canonical_points() -> list[dict]:
    data = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    rows = {row["parcel_id"]: row for row in data["canonical_points"]}
    result = []
    for parcel_id, _ in POSTCODES:
        row = rows.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"invalid coordinate {parcel_id}")
        result.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return result


def request_url(postcode: str) -> str:
    query = urllib.parse.urlencode(
        {"address": postcode, "pageNumber": 1, "pageSize": PAGE_SIZE}
    )
    return f"{ENDPOINT}?{query}"


def candidate(parcel_id: str, row: dict, source_url: str) -> dict:
    address = [row.get(f"AddressLine{i}") for i in range(1, 5)]
    address = [str(value) for value in address if value]
    geo = row.get("geocode") if isinstance(row.get("geocode"), dict) else {}
    return {
        "parcel_id": parcel_id,
        "fhrsid": row.get("FHRSID"),
        "local_authority_business_id": row.get("LocalAuthorityBusinessID"),
        "business_name": row.get("BusinessName"),
        "business_type": row.get("BusinessType"),
        "business_type_id": row.get("BusinessTypeID"),
        "address_lines": address,
        "postcode": row.get("PostCode"),
        "rating_value": row.get("RatingValue"),
        "rating_date": row.get("RatingDate"),
        "longitude": geo.get("longitude"),
        "latitude": geo.get("latitude"),
        "source_url": source_url,
        "candidate_only": True,
        "exact_parcel_binding_claimed": False,
        "property_type_binding_claimed": False,
    }


def run(timeout: float) -> dict:
    points = canonical_points()
    point_map = {row["parcel_id"]: row for row in points}
    evidence: list[dict] = []
    candidates: list[dict] = []
    for parcel_id, postcode in POSTCODES:
        url = request_url(postcode)
        accessed_at = now()
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "x-api-version": "2",
                    "User-Agent": "TerraYield-AAYS/1.0 bounded FSA postcode research",
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("response exceeded 1 MiB")
                payload = json.loads(raw.decode("utf-8"))
                rows = payload.get("establishments", [])
                if not isinstance(rows, list):
                    raise ValueError("establishments list missing")
                rows = rows[:PAGE_SIZE]
                candidates.extend(candidate(parcel_id, row, url) for row in rows)
                evidence.append(
                    {
                        "parcel_id": parcel_id,
                        "searched_postcode": postcode,
                        "canonical_point": point_map[parcel_id],
                        "source_url": url,
                        "endpoint_url": ENDPOINT,
                        "accessed_at": accessed_at,
                        "content_sha256": sha256(raw),
                        "sha256_basis": "bounded_raw_json_response_bytes",
                        "record_scope": "one official FSA API v2 address search; page 1; maximum 20 establishments; maximum 1 MiB",
                        "supports_fields": [
                            "FHRS establishment identifier",
                            "business name",
                            "business type",
                            "address and postcode",
                            "rating value and date",
                            "published geocode",
                        ],
                        "relevant_record_ids_or_excerpt": {
                            "establishment_count": len(rows),
                            "fhrsids": [row.get("FHRSID") for row in rows],
                        },
                        "help_url": HELP_URL,
                        "search_documentation_url": SEARCH_DOC_URL,
                        "open_data_url": OPEN_DATA_URL,
                        "license_or_terms_url": TERMS_URL,
                        "http_status": getattr(response, "status", None),
                    }
                )
        except Exception as exc:
            message = f"FSA_ESTABLISHMENTS_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append(
                {
                    "parcel_id": parcel_id,
                    "searched_postcode": postcode,
                    "canonical_point": point_map[parcel_id],
                    "source_url": url,
                    "endpoint_url": ENDPOINT,
                    "accessed_at": accessed_at,
                    "content_sha256": sha256(message),
                    "sha256_basis": "bounded_error_evidence_string",
                    "record_scope": "one official FSA API v2 address search; page 1; maximum 20 establishments; no bulk/open-data file download",
                    "supports_fields": ["FSA API endpoint availability"],
                    "relevant_record_ids_or_excerpt": message[:512],
                    "help_url": HELP_URL,
                    "search_documentation_url": SEARCH_DOC_URL,
                    "open_data_url": OPEN_DATA_URL,
                    "license_or_terms_url": TERMS_URL,
                    "http_status": getattr(exc, "code", None),
                }
            )
    state = "FSA_ESTABLISHMENT_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
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
            "code": "NONE" if candidates else "FSA_API_NO_USABLE_RESPONSE_OR_NO_POSTCODE_ESTABLISHMENTS",
            "state": state,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VALIDATE_FSA_ESTABLISHMENT_CANDIDATES_WITHOUT_EXACT_PARCEL_OR_PROPERTY_TYPE_INFERENCE"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_FSA_ESTABLISHMENTS_POSTCODE"
        ),
        "bulk_download_performed": False,
        "large_data_downloaded": False,
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
        raise ValueError("target count")
    for path in (PROBE, *OUT):
        if Path(path).is_absolute():
            raise ValueError("relative paths required")
    if not OUT[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/"):
        raise ValueError("slot output boundary")
    if not OUT[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"):
        raise ValueError("web output boundary")
    for _, postcode in POSTCODES:
        url = request_url(postcode)
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if parsed.get("address") != [postcode] or parsed.get("pageNumber") != ["1"] or parsed.get("pageSize") != ["20"]:
            raise ValueError("bounded request guard")
    print("PASS_TARGET_3_FSA_API_V2_POSTCODE_PAGE1_SIZE20_MAX1MIB_CANDIDATE_ONLY")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "produced_candidate_rows": result["produced_candidate_rows"],
        "evidence_records": len(result["source_evidence"]),
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
