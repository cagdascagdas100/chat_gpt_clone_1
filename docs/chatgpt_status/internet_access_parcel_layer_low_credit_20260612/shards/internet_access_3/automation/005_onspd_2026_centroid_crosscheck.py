#!/usr/bin/env python3
"""Cross-check internet_access_3 postcode proxies against ONSPD May 2026.

This worker is evidence-only:
- it selects a deterministic distributed sample from existing postcode proxies;
- it queries the official ONS hosted table by exact postcode;
- it measures parcel-centroid to postcode-centroid distance;
- it never creates a postcode, parcel score, measured-speed claim, or confidence uplift.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
TASK_ID = "aays1-internet-access-3-onspd-2026-centroid-crosscheck-20260722"
SHARD_START = 61523
SHARD_END = 92283
DEFAULT_SAMPLE_SIZE = 96
DEFAULT_ROWS = "england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json"
DEFAULT_REGISTRY = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_3/source_snapshots/003_onspd_may_2026_registry_latest.json"
)
DEFAULT_OUTPUT_ROOT = "england_map_web/data/aays_21_slots/internet_access_3"
DEFAULT_RUNNER_OUTPUT = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_3/runner_outputs/004_onspd_2026_centroid_crosscheck_latest.json"
)
REQUIRED_SERVICE_FIELDS = {
    "pcd7", "pcds", "dointr", "doterm", "east1m", "north1m",
    "gridind", "lat", "long", "lad25cd", "oa21cd", "lsoa21cd", "msoa21cd",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--rows", default=DEFAULT_ROWS)
    parser.add_argument("--source-registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--runner-output", default=DEFAULT_RUNNER_OUTPUT)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--query-timeout", type=int, default=90)
    parser.add_argument("--batch-size", type=int, default=40)
    return parser.parse_args()


def find_repo_root(explicit: Path | None) -> Path:
    if explicit:
        root = explicit.expanduser().resolve()
        if not (root / "england_map_web").exists():
            raise FileNotFoundError(f"invalid repo root: {root}")
        return root
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found; pass --repo-root")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def normalize_postcode(value: Any) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"\s+", "", str(value)).upper()
    if not re.fullmatch(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}", normalized):
        return None
    return normalized


def postcode_area(postcode: str) -> str:
    match = re.match(r"^([A-Z]{1,2})", postcode)
    if not match:
        raise ValueError(f"postcode area missing: {postcode}")
    return match.group(1)


def as_float(value: Any) -> float | None:
    if value in (None, "", "null", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def haversine_metres(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius = 6_371_008.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def distance_bucket(distance_m: float | None) -> str:
    if distance_m is None:
        return "COORDINATE_DISTANCE_UNAVAILABLE"
    if distance_m <= 100:
        return "WITHIN_100M_POSTCODE_CENTROID"
    if distance_m <= 250:
        return "WITHIN_250M_POSTCODE_CENTROID"
    if distance_m <= 500:
        return "WITHIN_500M_POSTCODE_CENTROID"
    if distance_m <= 1000:
        return "WITHIN_1KM_POSTCODE_CENTROID"
    return "OVER_1KM_FROM_POSTCODE_CENTROID_REVIEW_REQUIRED"


def deterministic_sample(rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    eligible = [
        row for row in rows
        if SHARD_START <= int(row.get("row_no", -1)) <= SHARD_END
        and row.get("internet_status") in {
            "verified_existing_postcode_proxy",
            "official_2026_postcode_proxy_sample",
        }
        and normalize_postcode(row.get("postcode"))
        and as_float(row.get("parcel_centroid_lon")) is not None
        and as_float(row.get("parcel_centroid_lat")) is not None
    ]
    eligible.sort(key=lambda row: int(row["row_no"]))
    if not eligible or size <= 0:
        return []
    if len(eligible) <= size:
        return eligible
    indexes = [round(i * (len(eligible) - 1) / (size - 1)) for i in range(size)]
    selected: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index in indexes:
        row_no = int(eligible[index]["row_no"])
        if row_no not in seen:
            seen.add(row_no)
            selected.append(eligible[index])
    return selected


def request_json(url: str, params: dict[str, str], timeout: int, post: bool = False) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(params).encode("utf-8")
    headers = {"User-Agent": "TerraYield-AAYS-internet-access-3/1.0"}
    if post:
        request = urllib.request.Request(url, data=encoded, headers=headers, method="POST")
    else:
        separator = "&" if "?" in url else "?"
        request = urllib.request.Request(url + separator + encoded.decode("utf-8"), headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("official service returned non-object JSON")
    if payload.get("error"):
        raise RuntimeError(f"official service error: {payload['error']}")
    return payload


def fetch_service_schema(feature_service_url: str, timeout: int) -> dict[str, Any]:
    payload = request_json(feature_service_url, {"f": "json"}, timeout)
    fields = {
        str(item.get("name"))
        for item in payload.get("fields", [])
        if isinstance(item, dict) and item.get("name")
    }
    return {
        "service_name": payload.get("name"),
        "max_record_count": payload.get("maxRecordCount"),
        "last_edit_date": (payload.get("editingInfo") or {}).get("lastEditDate"),
        "data_last_edit_date": (payload.get("editingInfo") or {}).get("dataLastEditDate"),
        "available_fields": sorted(fields),
        "missing_required_fields": sorted(REQUIRED_SERVICE_FIELDS - fields),
    }


def fetch_records(query_url: str, postcodes: list[str], batch_size: int, timeout: int) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    records: dict[str, dict[str, Any]] = {}
    audits: list[dict[str, Any]] = []
    out_fields = ",".join(sorted(REQUIRED_SERVICE_FIELDS))
    for offset in range(0, len(postcodes), batch_size):
        batch = postcodes[offset:offset + batch_size]
        quoted = ",".join("'" + postcode.replace("'", "''") + "'" for postcode in batch)
        where = f"pcd7 IN ({quoted})"
        payload = request_json(
            query_url,
            {
                "f": "json",
                "where": where,
                "outFields": out_fields,
                "returnGeometry": "false",
                "resultRecordCount": "1000",
                "orderByFields": "pcd7 ASC",
            },
            timeout,
            post=True,
        )
        found = 0
        for feature in payload.get("features", []):
            attributes = (feature or {}).get("attributes") or {}
            postcode = normalize_postcode(attributes.get("pcd7") or attributes.get("pcds"))
            if postcode:
                records[postcode] = attributes
                found += 1
        audits.append({
            "batch_start": offset,
            "target_count": len(batch),
            "found_count": found,
            "exceeded_transfer_limit": bool(payload.get("exceededTransferLimit")),
        })
    return records, audits


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def update_web_feed(output_root: Path, candidates: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    feed_path = output_root / "operation_feed_latest.json"
    feed = load_json(feed_path) if feed_path.exists() else {"schema_version": 1, "slot_id": SLOT_ID, "operations": []}
    operations = list(feed.get("operations") or [])
    next_sequence = max([int(item.get("sequence", 0)) for item in operations] or [0]) + 1
    operations.append({
        "sequence": next_sequence,
        "status": "PASS" if summary["validation"]["passed"] else "BLOCKED",
        "operation": "ONSPD_MAY_2026_SERVICE_SCHEMA_READBACK",
        "detail": (
            f"Exact-postcode service batches={len(summary['source_validation']['query_batches'])}; "
            f"schema_missing={len(summary['source_validation']['schema']['missing_required_fields'])}."
        ),
    })
    next_sequence += 1
    for candidate in candidates:
        operations.append({
            "sequence": next_sequence,
            "status": "PASS" if candidate["onspd_postcode_found"] else "NO_DATA",
            "operation": "ONSPD_POSTCODE_CENTROID_CROSSCHECK",
            "row_no": candidate["row_no"],
            "parcel_id": candidate["canonical_program_parcel_id"],
            "postcode": candidate["postcode"],
            "detail": (
                f"{candidate['postcode_status']}; distance_m={candidate['parcel_to_postcode_centroid_distance_m']}; "
                f"{candidate['distance_bucket']}; confidence_not_raised"
            ),
        })
        next_sequence += 1
    feed.update({
        "updated_at": summary["updated_at"],
        "display_mode": "line_by_line",
        "final_ready": False,
        "operations": operations,
        "safety": {
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        },
    })
    atomic_write_json(feed_path, feed)


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(args.repo_root)
    rows_path = repo_root / args.rows
    registry_path = repo_root / args.source_registry
    output_root = repo_root / args.output_root
    runner_output_path = repo_root / args.runner_output

    rows = load_json(rows_path)
    registry = load_json(registry_path)
    if not isinstance(rows, list) or len(rows) != 30761:
        raise ValueError("internet_access_3 migrated rows are missing or have the wrong count")

    sample = deterministic_sample(rows, args.sample_size)
    if not sample:
        raise ValueError("no eligible postcode proxy rows available for ONSPD crosscheck")

    service_url = str(registry["feature_service_url"])
    query_url = str(registry["query_url"])
    schema = fetch_service_schema(service_url, args.query_timeout)
    target_postcodes = sorted({normalize_postcode(row.get("postcode")) for row in sample} - {None})
    official, batch_audits = fetch_records(
        query_url, list(target_postcodes), max(1, args.batch_size), args.query_timeout
    )

    candidates: list[dict[str, Any]] = []
    distances: list[float] = []
    found_count = 0
    terminated_count = 0
    for row in sample:
        postcode = normalize_postcode(row.get("postcode"))
        record = official.get(postcode or "")
        parcel_lon = as_float(row.get("parcel_centroid_lon"))
        parcel_lat = as_float(row.get("parcel_centroid_lat"))
        ons_lon = as_float(record.get("long")) if record else None
        ons_lat = as_float(record.get("lat")) if record else None
        distance = (
            round(haversine_metres(parcel_lon, parcel_lat, ons_lon, ons_lat), 2)
            if None not in (parcel_lon, parcel_lat, ons_lon, ons_lat)
            else None
        )
        if distance is not None:
            distances.append(distance)
        doterm = str(record.get("doterm") or "").strip() if record else ""
        status = "ONSPD_NOT_FOUND"
        if record:
            found_count += 1
            if doterm:
                terminated_count += 1
                status = "ONSPD_TERMINATED_POSTCODE_FOUND"
            else:
                status = "ONSPD_CURRENT_POSTCODE_FOUND"
        candidates.append({
            "row_no": int(row["row_no"]),
            "canonical_program_parcel_id": row.get("canonical_program_parcel_id"),
            "hmlr_inspire_id": row.get("hmlr_inspire_id"),
            "postcode": postcode,
            "postcode_area": postcode_area(postcode) if postcode else None,
            "onspd_postcode_found": record is not None,
            "postcode_status": status,
            "onspd_dointr": record.get("dointr") if record else None,
            "onspd_doterm": record.get("doterm") if record else None,
            "onspd_gridind": record.get("gridind") if record else None,
            "onspd_lad25cd": record.get("lad25cd") if record else None,
            "onspd_oa21cd": record.get("oa21cd") if record else None,
            "onspd_lsoa21cd": record.get("lsoa21cd") if record else None,
            "onspd_msoa21cd": record.get("msoa21cd") if record else None,
            "parcel_centroid_lon": parcel_lon,
            "parcel_centroid_lat": parcel_lat,
            "postcode_centroid_lon": ons_lon,
            "postcode_centroid_lat": ons_lat,
            "parcel_to_postcode_centroid_distance_m": distance,
            "distance_bucket": distance_bucket(distance),
            "parcel_relation_promoted": False,
            "confidence_raised": False,
            "source_accuracy_score": 96 if record else 0,
            "parcel_relation_accuracy_ceiling": 50,
            "evidence_semantics": "POSTCODE_CENTROID_CROSSCHECK_ONLY",
            "blockers": [
                "POSTCODE_CENTROID_IS_NOT_ADDRESS_OR_PARCEL_PROOF",
                "UPRN_OR_ADDRESS_RELATION_NOT_ESTABLISHED",
            ],
        })

    schema_missing = schema["missing_required_fields"]
    query_errors = [
        audit for audit in batch_audits if audit["exceeded_transfer_limit"]
    ]
    passed = not schema_missing and not query_errors
    summary = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if passed else "blocked",
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "source_validation": {
            "dataset": registry["dataset"],
            "snapshot_date": registry["snapshot_date"],
            "feature_service_url": service_url,
            "schema": schema,
            "query_batches": batch_audits,
        },
        "result": {
            "sample_rows_requested": args.sample_size,
            "sample_rows_selected": len(sample),
            "unique_postcodes_queried": len(target_postcodes),
            "onspd_exact_postcodes_found": found_count,
            "onspd_postcodes_missing": len(sample) - found_count,
            "terminated_postcodes_found": terminated_count,
            "distance_available_count": len(distances),
            "median_distance_m": round(statistics.median(distances), 2) if distances else None,
            "p95_distance_m": round(percentile(distances, 0.95), 2) if distances else None,
            "maximum_distance_m": round(max(distances), 2) if distances else None,
            "parcel_relations_promoted": 0,
            "confidence_uplifts": 0,
            "new_postcode_matches_created": 0,
            "quality_scores_created": 0,
            "actual_business_data_rows_written": 0,
        },
        "validation": {
            "passed": passed,
            "missing_required_service_fields": schema_missing,
            "transfer_limit_batches": query_errors,
            "blockers": [
                "PARCEL_TO_POSTCODE_RELATION_REMAINS_PROXY",
                "UPRN_OR_ADDRESS_RELATION_NOT_ESTABLISHED",
            ],
        },
        "output_semantics": "POSTCODE_CENTROID_CROSSCHECK_ONLY",
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": "ESTABLISH_INDEPENDENT_PARCEL_TO_UPRN_OR_ADDRESS_RELATION_OR_RETAIN_PROXY",
    }

    atomic_write_json(output_root / "onspd_2026_postcode_centroid_candidates_latest.json", candidates)
    atomic_write_json(output_root / "onspd_2026_postcode_centroid_validation_latest.json", summary)
    atomic_write_json(runner_output_path, summary)
    update_web_feed(output_root, candidates, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({
            "task_id": TASK_ID,
            "slot_id": SLOT_ID,
            "state": "exception",
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }, ensure_ascii=False, indent=2), file=__import__("sys").stderr)
        raise
