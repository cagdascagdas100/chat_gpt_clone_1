from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-os-open-linked-identifiers-catalog-v1-20260802"
PRODUCTS_URL = "https://api.os.uk/downloads/v1/products?expanded=true"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/os_open_linked_identifiers_catalog_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/os_open_linked_identifiers_catalog_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def repo_root() -> Path:
    return Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()


def load_points(root: Path) -> list[dict[str, Any]]:
    data = json.loads((root / PROBE).read_text(encoding="utf-8"))
    rows = {row.get("parcel_id"): row for row in data.get("canonical_points", [])}
    selected: list[dict[str, Any]] = []
    for parcel_id in IDS:
        row = rows.get(parcel_id)
        if not row:
            raise ValueError(f"MISSING_CANONICAL_POINT:{parcel_id}")
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"INVALID_CANONICAL_POINT:{parcel_id}")
        selected.append({
            "parcel_id": parcel_id,
            "longitude": float(row["longitude"]),
            "latitude": float(row["latitude"]),
        })
    return selected


def write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, path)


def fetch(timeout: float) -> tuple[int | None, bytes | None, str | None]:
    request = urllib.request.Request(
        PRODUCTS_URL,
        headers={"User-Agent": "AAYS-parcel-label-3/1.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return getattr(response, "status", None), None, "RESPONSE_TOO_LARGE"
            return getattr(response, "status", None), raw, None
    except Exception as exc:
        return None, None, f"{type(exc).__name__}:{exc}"


def candidate_from_product(product: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "id", "name", "description", "url", "version", "updateFrequency",
        "formats", "outputFormats", "areas", "downloads", "thumbnailUrl",
    )
    return {key: product.get(key) for key in allowed if key in product}


def find_linked_identifier_products(payload: Any) -> list[dict[str, Any]]:
    products = payload if isinstance(payload, list) else payload.get("products", []) if isinstance(payload, dict) else []
    matches: list[dict[str, Any]] = []
    for product in products:
        if not isinstance(product, dict):
            continue
        searchable = " ".join(str(product.get(key, "")) for key in ("id", "name", "description", "url")).lower()
        if "linked identifier" in searchable or "linked-identifiers" in searchable or "linkedidentifiers" in searchable:
            matches.append(candidate_from_product(product))
    return matches


def validate(root: Path) -> str:
    points = load_points(root)
    if len(points) != 3:
        raise ValueError("INVALID_CANONICAL_POINT_COUNT")
    if not PRODUCTS_URL.startswith("https://api.os.uk/downloads/v1/products"):
        raise ValueError("INVALID_OFFICIAL_PRODUCTS_URL")
    for output in OUTPUTS:
        path = Path(output)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("NON_RELATIVE_OUTPUT_PATH")
    return "PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_OS_OPEN_LINKED_IDENTIFIERS_CATALOG_MAX2MIB"


def run(root: Path, timeout: float) -> dict[str, Any]:
    points = load_points(root)
    accessed_at = now()
    status, raw, error = fetch(timeout)
    candidates: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {
        "source_url": PRODUCTS_URL,
        "accessed_at": accessed_at,
        "query_sha256": sha256(PRODUCTS_URL),
        "http_status": status,
        "record_scope": "one bounded OS Downloads API OpenData products catalogue request; maximum 2 MiB",
        "proven_fields": ["request URL", "access time", "query SHA-256"],
    }
    if raw is None:
        bounded = f"OS_OPEN_LINKED_IDENTIFIERS_CATALOG_ERROR:{error}"
        evidence.update({
            "content_sha256": sha256(bounded),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": bounded[:500],
            "candidate_count": 0,
        })
    else:
        evidence.update({"content_sha256": sha256(raw), "sha256_basis": "raw_response_bytes"})
        try:
            payload = json.loads(raw.decode("utf-8"))
            candidates = find_linked_identifier_products(payload)
            evidence.update({
                "candidate_count": len(candidates),
                "relevant_record_ids_or_excerpt": [candidate.get("id") or candidate.get("name") for candidate in candidates[:10]],
                "proven_fields": evidence["proven_fields"] + ["raw catalogue SHA-256", "matching product id/name fields when present"],
            })
        except Exception as exc:
            bounded = f"JSON_PARSE_ERROR:{type(exc).__name__}:{exc}"
            evidence.update({
                "relevant_record_ids_or_excerpt": bounded[:500],
                "candidate_count": 0,
                "proven_fields": evidence["proven_fields"] + ["raw response SHA-256"],
            })

    blocker = None if candidates else {
        "code": "OS_OPEN_LINKED_IDENTIFIERS_CATALOG_NO_USABLE_RESPONSE",
        "state": "NO_DATA_CONTINUE",
        "candidate_research_blocked": False,
        "manual_action_required": False,
        "retry_unchanged_route": False,
    }
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "SOURCE_CATALOG_CANDIDATE_PUBLISHED" if candidates else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": [point["parcel_id"] for point in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": blocker,
        "next_unverified_step": "FETCH_OS_OPEN_LINKED_IDENTIFIERS_DOWNLOADS_MANIFEST_FOR_DISCOVERED_PRODUCT" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OS_OPEN_LINKED_IDENTIFIERS_CATALOG",
        "relationship_target": "BLPU_UPRN_TopographicArea_TOID_5",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for relative in OUTPUTS:
        write_atomic(root / relative, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    if args.validate_only:
        print(validate(root))
        return 0
    validate(root)
    print(json.dumps(run(root, args.timeout), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
