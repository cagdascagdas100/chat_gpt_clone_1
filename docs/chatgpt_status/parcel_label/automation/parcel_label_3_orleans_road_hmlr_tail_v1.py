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

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-orleans-road-hmlr-tail-v1-20260801"
CONTINUATION_KEY = "3d687c73352401fba113a4994158012f5c4a172e9297a063cd14fc6b7435c55b"
SOURCE_URL = "https://landregistry.data.gov.uk/data/ppi/transaction-record.json"
LICENSE_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
BASELINE_PATH = "england_map_web/data/aays_21_slots/parcel_label_3/progress_rows_latest.json"
WRITE_PATHS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/orleans_road_hmlr_tail_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/orleans_road_hmlr_tail_latest.json",
)
TARGET_COUNT = 6
EXPECTED_BASELINE_SCHEMA = 110
EXPECTED_PUBLISHED_COUNT = 25
EXPECTED_SOURCE_COUNT = 31

TYPE_MAP = {
    "detached": "D",
    "semi-detached": "S",
    "terraced": "T",
    "flat-maisonette": "F",
    "other": "O",
}
TENURE_MAP = {"freehold": "H", "leasehold": "L"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + ".part")
    part.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(part, path)


def unwrap(value: Any) -> Any:
    if isinstance(value, list):
        return unwrap(value[0]) if value else None
    if isinstance(value, dict):
        for key in ("_value", "value", "label", "notation"):
            if key in value:
                return unwrap(value[key])
        return value
    return value


def tail_token(value: Any) -> str:
    raw = str(unwrap(value) or "").strip()
    return raw.rstrip("/").split("/")[-1].lower()


def norm_text(value: Any) -> str:
    return " ".join(str(unwrap(value) or "").upper().split())


def parse_date(value: Any) -> str:
    text = str(unwrap(value) or "").strip()
    return text[:10]


def parse_int(value: Any) -> int | None:
    raw = unwrap(value)
    try:
        return int(str(raw).replace(",", ""))
    except (TypeError, ValueError):
        return None


def nested(item: dict[str, Any], *keys: str) -> Any:
    value: Any = item
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return unwrap(value)


def baseline_key(row: list[Any]) -> tuple[str, int, str, str, str]:
    return (
        str(row[5]),
        int(row[6]),
        norm_text(row[2]),
        norm_text(row[7]),
        norm_text(row[8]),
    )


def load_baseline(repo: Path) -> tuple[dict[str, Any], set[tuple[str, int, str, str, str]]]:
    payload = json.loads((repo / BASELINE_PATH).read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != EXPECTED_BASELINE_SCHEMA:
        raise ValueError("BASELINE_SCHEMA_NOT_110")
    if "WAVE110_ORLEANS_ROAD_25" not in str(payload.get("state")):
        raise ValueError("BASELINE_STATE_NOT_WAVE110_ORLEANS")
    rows = payload.get("progress_rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_PUBLISHED_COUNT:
        raise ValueError("BASELINE_PUBLISHED_COUNT_NOT_25")
    source = ((payload.get("road_sources") or {}).get("o") or [])
    if len(source) < 2 or int(source[1]) != EXPECTED_SOURCE_COUNT:
        raise ValueError("BASELINE_SOURCE_COUNT_NOT_31")
    return payload, {baseline_key(row) for row in rows}


def build_url() -> str:
    params = {
        "propertyAddress.street": "ORLEANS ROAD",
        "_pageSize": "2000",
    }
    return SOURCE_URL + "?" + urllib.parse.urlencode(params)


def fetch(url: str, timeout: int) -> tuple[bytes, int]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-3/1.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), int(response.status)


def extract_items(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    candidates = [payload.get("items"), nested(payload, "result", "items")]
    for value in candidates:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def normalize_item(item: dict[str, Any]) -> dict[str, Any] | None:
    address = item.get("propertyAddress") or {}
    if not isinstance(address, dict):
        address = {}
    street = norm_text(address.get("street") or item.get("propertyAddressStreet"))
    postcode = norm_text(address.get("postcode") or item.get("propertyAddressPostcode"))
    if street != "ORLEANS ROAD" or not postcode.startswith("SE19"):
        return None
    date = parse_date(item.get("transactionDate"))
    price = parse_int(item.get("pricePaid"))
    transaction_id = norm_text(item.get("transactionId"))
    paon = norm_text(address.get("paon") or item.get("propertyAddressPaon"))
    saon = norm_text(address.get("saon") or item.get("propertyAddressSaon"))
    property_type = TYPE_MAP.get(tail_token(item.get("propertyType")), "U")
    tenure = TENURE_MAP.get(tail_token(item.get("estateType")), "U")
    if not all((date, price is not None, transaction_id, paon)):
        return None
    address_text = ", ".join(part for part in (saon, paon, "ORLEANS ROAD", postcode) if part)
    key = (date, int(price), postcode, property_type, tenure)
    return {
        "transaction_id": transaction_id,
        "address": address_text,
        "postcode": postcode,
        "sale_date": date,
        "price_gbp": int(price),
        "property_type": property_type,
        "tenure": tenure,
        "dedupe_key": key,
        "candidate_only": True,
        "exact_uprn_bound": False,
        "address_coordinate_inferred": False,
    }


def run(repo: Path, timeout: int) -> dict[str, Any]:
    baseline, existing = load_baseline(repo)
    url = build_url()
    evidence: dict[str, Any] = {
        "source_url": url,
        "accessed_at": utc_now(),
        "http_status": None,
        "content_sha256": None,
        "supports_fields": [
            "transactionId", "pricePaid", "transactionDate", "propertyType",
            "estateType", "propertyAddress.paon", "propertyAddress.saon",
            "propertyAddress.street", "propertyAddress.postcode",
        ],
        "relevant_record_ids_or_excerpt": [],
        "license_or_terms_url": LICENSE_URL,
    }
    records: list[dict[str, Any]] = []
    state = "NO_DATA_CONTINUE"
    completed_count = 0
    try:
        body, status = fetch(url, timeout)
        completed_count = TARGET_COUNT
        evidence["http_status"] = status
        evidence["content_sha256"] = sha256_bytes(body)
        payload = json.loads(body.decode("utf-8"))
        normalized = []
        seen_ids = set()
        for item in extract_items(payload):
            row = normalize_item(item)
            if row is None or row["transaction_id"] in seen_ids:
                continue
            seen_ids.add(row["transaction_id"])
            normalized.append(row)
        normalized.sort(key=lambda r: (r["sale_date"], r["transaction_id"]), reverse=True)
        tail = [r for r in normalized if tuple(r["dedupe_key"]) not in existing]
        records = tail[:TARGET_COUNT]
        for row in records:
            row.pop("dedupe_key", None)
        evidence["relevant_record_ids_or_excerpt"] = [r["transaction_id"] for r in records]
        if len(records) == TARGET_COUNT:
            state = "PUBLISHED_CANDIDATE_ONLY"
        elif not records:
            evidence["relevant_record_ids_or_excerpt"] = "NO_UNPUBLISHED_COMPLETE_ORLEANS_SE19_RECORDS"
    except Exception as exc:
        completed_count = TARGET_COUNT
        error_text = f"HMLR_API_FETCH_ERROR:{type(exc).__name__}"
        evidence["content_sha256"] = sha256_bytes(error_text.encode("utf-8"))
        evidence["sha256_basis"] = "bounded_error_evidence_string"
        evidence["relevant_record_ids_or_excerpt"] = error_text

    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION_KEY,
        "generated_at": utc_now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": completed_count,
        "target_count": TARGET_COUNT,
        "previous_percent": 0.0,
        "progress_percent": round(100.0 * completed_count / TARGET_COUNT, 4),
        "percent_increase": round(100.0 * completed_count / TARGET_COUNT, 4),
        "produced_rows": len(records),
        "baseline": {
            "schema_version": baseline.get("schema_version"),
            "published_rows": EXPECTED_PUBLISHED_COUNT,
            "source_reported_rows": EXPECTED_SOURCE_COUNT,
            "baseline_blob_sha": "592b57f94ad418d29aa6949891f929fb0df87186",
        },
        "records": records,
        "source_evidence": [evidence],
        "blocker": None if len(records) == TARGET_COUNT else {
            "code": "HMLR_LINKED_DATA_TAIL_NOT_EXACTLY_6",
            "state": "NO_DATA_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_UNPUBLISHED_OFFICIAL_OR_FREE_CANDIDATE_BATCH",
        "fake_data": False,
        "final_ready": False,
    }


def validate_only() -> dict[str, Any]:
    assert TARGET_COUNT == EXPECTED_SOURCE_COUNT - EXPECTED_PUBLISHED_COUNT
    assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in WRITE_PATHS)
    assert urllib.parse.urlparse(build_url()).hostname == "landregistry.data.gov.uk"
    return {
        "state": "VALIDATED",
        "target_count": TARGET_COUNT,
        "baseline_count": EXPECTED_PUBLISHED_COUNT,
        "source_count": EXPECTED_SOURCE_COUNT,
        "write_paths": list(WRITE_PATHS),
        "resource_class": "network_fetch",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        print(json.dumps(validate_only(), ensure_ascii=False))
        return 0
    repo = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
    result = run(repo, args.timeout)
    for rel in WRITE_PATHS:
        atomic_json(repo / rel, result)
    print(json.dumps({"state": result["state"], "completed_count": result["completed_count"], "produced_rows": result["produced_rows"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
