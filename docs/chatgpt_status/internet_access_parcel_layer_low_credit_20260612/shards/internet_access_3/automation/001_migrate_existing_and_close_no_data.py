#!/usr/bin/env python3
"""Build the internet_access_3 shard from canonical parcel rows and existing verified internet proxy rows.

This task is deliberately conservative:
- It migrates only existing repository evidence from program_layer_matrix/internet.geojson.
- It does not invent postcodes, coverage values, scores, providers, or measured speeds.
- Canonical rows without an existing verified record are retained as explicit NO_DATA rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from collections import Counter
from typing import Any, Iterable

SLOT_ID = "internet_access_3"
SHARD_START = 61523
SHARD_END = 92283
SHARD_COUNT = 30761
CANONICAL_COUNT = 92283
EXPECTED_EXISTING_COUNT = 33785
TASK_ID = "aays1-internet-access-3-migrate-existing-then-no-data-20260722"
CALCULATION_VERSION = "legacy-postcode-proxy-migration-v1-score-deferred"

LEGACY_PERCENT_KEYS = {
    "gigabit": "gigabit_available_pct",
    "ufbb100": "ultrafast_or_100mbps_available_pct",
    "sfbb": "superfast_30mbps_available_pct",
    "unable30": "decent_broadband_unavailable_pct",
    "full_fibre": "full_fibre_available_pct",
    "provider_count": "provider_count",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument(
        "--canonical-source",
        default="england_map_web/data/program_layer_matrix/security.geojson",
    )
    parser.add_argument(
        "--internet-source",
        default="england_map_web/data/program_layer_matrix/internet.geojson",
    )
    parser.add_argument(
        "--output-root",
        default="england_map_web/data/aays_21_slots/internet_access_3",
    )
    parser.add_argument(
        "--runner-output",
        default=(
            "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
            "shards/internet_access_3/runner_outputs/"
            "001_migration_and_no_data_latest.json"
        ),
    )
    return parser.parse_args()


def find_repo_root(explicit: Path | None) -> Path:
    if explicit:
        root = explicit.expanduser().resolve()
        if not (root / "england_map_web").exists():
            raise FileNotFoundError(f"repo root does not contain england_map_web: {root}")
        return root
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found; pass --repo-root")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_feature_collection(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError(f"not a GeoJSON FeatureCollection: {path}")
    return payload["features"]


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


def as_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc


def parse_percentage(value: str) -> float | None:
    clean = value.strip()
    if clean.endswith("%"):
        clean = clean[:-1].strip()
    if not clean or clean.lower() in {"none", "null", "n/a", "na"}:
        return None
    try:
        number = float(clean)
    except ValueError:
        return None
    if not 0.0 <= number <= 100.0:
        return None
    return number


def parse_legacy_value(raw: Any) -> tuple[dict[str, Any], list[str]]:
    parsed: dict[str, Any] = {
        "postcode": None,
        "internet_quality_band": None,
        "gigabit_available_pct": None,
        "ultrafast_or_100mbps_available_pct": None,
        "superfast_30mbps_available_pct": None,
        "decent_broadband_unavailable_pct": None,
        "full_fibre_available_pct": None,
        "provider_count": None,
    }
    errors: list[str] = []
    if not isinstance(raw, str) or not raw.strip():
        return parsed, ["LEGACY_VALUE_MISSING"]

    parts = [part.strip() for part in raw.split(";") if part.strip()]
    if not parts:
        return parsed, ["LEGACY_VALUE_EMPTY"]
    parsed["internet_quality_band"] = parts[0]

    for part in parts[1:]:
        if "=" not in part:
            errors.append(f"UNPARSED_SEGMENT:{part}")
            continue
        key, value = [item.strip() for item in part.split("=", 1)]
        key_lower = key.lower()
        if key_lower == "postcode":
            normalized = re.sub(r"\s+", "", value).upper()
            if normalized:
                parsed["postcode"] = normalized
            else:
                errors.append("POSTCODE_EMPTY")
            continue
        target = LEGACY_PERCENT_KEYS.get(key_lower)
        if not target:
            continue
        if target == "provider_count":
            try:
                parsed[target] = int(value)
            except ValueError:
                errors.append("PROVIDER_COUNT_INVALID")
            continue
        number = parse_percentage(value)
        if number is None:
            errors.append(f"PERCENT_INVALID:{key_lower}")
        else:
            parsed[target] = number

    required = [
        "postcode",
        "gigabit_available_pct",
        "ultrafast_or_100mbps_available_pct",
        "superfast_30mbps_available_pct",
    ]
    for field in required:
        if parsed[field] is None:
            errors.append(f"REQUIRED_FIELD_MISSING:{field}")
    return parsed, sorted(set(errors))


def unique_index(
    features: Iterable[dict[str, Any]], field: str, label: str
) -> tuple[dict[int, dict[str, Any]], list[int]]:
    index: dict[int, dict[str, Any]] = {}
    duplicates: list[int] = []
    for feature in features:
        props = feature.get("properties") or {}
        key = as_int(props.get(field), f"{label}.{field}")
        if key in index:
            duplicates.append(key)
        else:
            index[key] = feature
    return index, sorted(set(duplicates))


def canonical_identity(props: dict[str, Any], geometry: Any) -> dict[str, Any]:
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
    lon = props.get("hmlr_lon")
    lat = props.get("hmlr_lat")
    if isinstance(coordinates, list) and len(coordinates) >= 2:
        lon = coordinates[0] if lon is None else lon
        lat = coordinates[1] if lat is None else lat
    return {
        "canonical_program_parcel_id": props.get("parcel_id"),
        "row_no": as_int(props.get("row_no"), "canonical.row_no"),
        "hmlr_inspire_id": props.get("hmlr_inspire_id"),
        "parcel_centroid_lon": lon,
        "parcel_centroid_lat": lat,
        "london_authority": props.get("london_authority"),
    }


def migrated_properties(
    canonical_feature: dict[str, Any],
    existing_feature: dict[str, Any] | None,
    internet_source_sha256: str,
    canonical_source_sha256: str,
) -> tuple[dict[str, Any], list[str]]:
    canonical_props = canonical_feature.get("properties") or {}
    geometry = canonical_feature.get("geometry")
    output = canonical_identity(canonical_props, geometry)
    output.update(
        {
            "slot_id": SLOT_ID,
            "internet_availability_quality_percent": None,
            "source_snapshot_date": None,
            "source_url": None,
            "source_file_sha256": internet_source_sha256,
            "canonical_source_file_sha256": canonical_source_sha256,
            "calculation_version": CALCULATION_VERSION,
            "topic_id": "internet",
        }
    )

    if existing_feature is None:
        output.update(
            {
                "internet_status": "no_data",
                "postcode": None,
                "source_level": "NO_DATA",
                "gigabit_available_pct": None,
                "ultrafast_or_100mbps_available_pct": None,
                "superfast_30mbps_available_pct": None,
                "decent_broadband_unavailable_pct": None,
                "full_fibre_available_pct": None,
                "provider_count": None,
                "internet_quality_band": None,
                "internet_match_method": "NO_EXISTING_VERIFIED_ROW_AT_SOURCE_READBACK",
                "internet_match_confidence": 0,
                "internet_accuracy": "0/4",
                "legacy_internet_level_value": None,
                "legacy_matrix_color": None,
                "calculation_explanation": (
                    "No matching row exists in the verified repository internet GeoJSON. "
                    "No postcode, coverage percentage, quality score, or provider value was fabricated."
                ),
                "blockers": ["VERIFIED_POSTCODE_OR_PREMISE_MATCH_NOT_ESTABLISHED"],
            }
        )
        return output, []

    existing_props = existing_feature.get("properties") or {}
    raw_value = existing_props.get("internet_level_value")
    parsed, parse_errors = parse_legacy_value(raw_value)
    legacy_accuracy = str(existing_props.get("internet_level_accuracy") or "2/4")
    confidence = 50 if legacy_accuracy.strip() == "2/4" and not parse_errors else 0
    output.update(parsed)
    output.update(
        {
            "internet_status": (
                "verified_existing_postcode_proxy" if not parse_errors else "legacy_record_parse_blocked"
            ),
            "source_level": "POSTCODE_PROXY",
            "internet_match_method": "EXISTING_PROGRAM_LAYER_MATRIX_ROW_NO",
            "internet_match_confidence": confidence,
            "internet_accuracy": legacy_accuracy,
            "legacy_internet_level_value": raw_value,
            "legacy_matrix_color": existing_props.get("matrix_color"),
            "calculation_explanation": (
                "Existing postcode-level Ofcom coverage proxy migrated without creating a new score. "
                "The 50 confidence value is a mechanical conversion of the legacy 2/4 accuracy label; "
                "it is not a new measurement or source validation."
                if not parse_errors
                else "Existing legacy row preserved, but required structured fields could not be parsed; no score was created."
            ),
            "blockers": ["QUALITY_SCORE_DEFERRED_UNTIL_VERIFIED_CALCULATION_VERSION"]
            + parse_errors,
        }
    )
    return output, parse_errors


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(args.repo_root)
    canonical_path = repo_root / args.canonical_source
    internet_path = repo_root / args.internet_source
    output_root = repo_root / args.output_root
    runner_output_path = repo_root / args.runner_output

    canonical_sha = sha256_file(canonical_path)
    internet_sha = sha256_file(internet_path)
    canonical_features = load_feature_collection(canonical_path)
    existing_features = load_feature_collection(internet_path)

    canonical_by_row, canonical_duplicate_rows = unique_index(canonical_features, "row_no", "canonical")
    existing_by_row, existing_duplicate_rows = unique_index(existing_features, "row_no", "internet")

    expected_rows = list(range(SHARD_START, SHARD_END + 1))
    missing_canonical_rows = [row for row in expected_rows if row not in canonical_by_row]
    shard_features: list[dict[str, Any]] = []
    shard_rows: list[dict[str, Any]] = []
    parse_failures: list[dict[str, Any]] = []
    matched_count = 0
    no_data_count = 0

    for row_no in expected_rows:
        canonical_feature = canonical_by_row.get(row_no)
        if canonical_feature is None:
            continue
        existing_feature = existing_by_row.get(row_no)
        props, parse_errors = migrated_properties(
            canonical_feature,
            existing_feature,
            internet_sha,
            canonical_sha,
        )
        if existing_feature is None:
            no_data_count += 1
        else:
            matched_count += 1
        if parse_errors:
            parse_failures.append({"row_no": row_no, "errors": parse_errors})
        shard_rows.append(props)
        shard_features.append(
            {
                "type": "Feature",
                "geometry": canonical_feature.get("geometry"),
                "properties": props,
            }
        )

    parcel_ids = [row.get("canonical_program_parcel_id") for row in shard_rows]
    parcel_id_counts = Counter(value for value in parcel_ids if value is not None)
    duplicate_parcel_ids = sorted(value for value, count in parcel_id_counts.items() if count > 1)

    blockers: list[str] = []
    if len(canonical_features) != CANONICAL_COUNT:
        blockers.append(f"CANONICAL_FEATURE_COUNT_MISMATCH:{len(canonical_features)}")
    if len(existing_features) != EXPECTED_EXISTING_COUNT:
        blockers.append(f"EXISTING_INTERNET_FEATURE_COUNT_MISMATCH:{len(existing_features)}")
    if canonical_duplicate_rows:
        blockers.append(f"CANONICAL_DUPLICATE_ROWS:{len(canonical_duplicate_rows)}")
    if existing_duplicate_rows:
        blockers.append(f"EXISTING_INTERNET_DUPLICATE_ROWS:{len(existing_duplicate_rows)}")
    if missing_canonical_rows:
        blockers.append(f"SHARD_CANONICAL_GAPS:{len(missing_canonical_rows)}")
    if len(shard_rows) != SHARD_COUNT:
        blockers.append(f"SHARD_ROW_COUNT_MISMATCH:{len(shard_rows)}")
    if duplicate_parcel_ids:
        blockers.append(f"SHARD_DUPLICATE_PARCEL_IDS:{len(duplicate_parcel_ids)}")
    if matched_count + no_data_count != SHARD_COUNT:
        blockers.append("MATCHED_PLUS_NO_DATA_COUNT_MISMATCH")
    if parse_failures:
        blockers.append(f"LEGACY_PARSE_FAILURES:{len(parse_failures)}")

    summary = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if not blockers else "blocked",
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "parcel_partition": {
            "start": SHARD_START,
            "end": SHARD_END,
            "count": SHARD_COUNT,
            "canonical_count": CANONICAL_COUNT,
        },
        "source_evidence": {
            "canonical_source": args.canonical_source,
            "canonical_source_sha256": canonical_sha,
            "canonical_feature_count": len(canonical_features),
            "internet_source": args.internet_source,
            "internet_source_sha256": internet_sha,
            "internet_feature_count": len(existing_features),
            "source_level": "POSTCODE_PROXY_OR_NO_DATA",
        },
        "result": {
            "shard_rows_written": len(shard_rows),
            "matched_existing_rows": matched_count,
            "no_data_rows": no_data_count,
            "legacy_parse_failures": len(parse_failures),
            "quality_scores_created": 0,
            "new_postcode_matches_created": 0,
            "actual_business_data_rows_written": len(shard_rows),
        },
        "validation": {
            "canonical_duplicate_rows": canonical_duplicate_rows[:100],
            "existing_duplicate_rows": existing_duplicate_rows[:100],
            "missing_canonical_rows": missing_canonical_rows[:100],
            "duplicate_parcel_ids": duplicate_parcel_ids[:100],
            "parse_failure_examples": parse_failures[:100],
            "blockers": blockers,
            "passed": not blockers,
        },
        "output_semantics": "POSTCODE_LEVEL_PROXY_OR_NO_DATA",
        "first_unverified_step_after_run": (
            "VERIFY_POSTCODE_SCHEMA_AND_RUN_DIRECT_OR_SPATIAL_GAP_MATCHING"
            if not blockers
            else "REPAIR_MIGRATION_VALIDATION_BLOCKERS"
        ),
    }

    atomic_write_json(output_root / "internet_rows_latest.json", shard_rows)
    atomic_write_json(
        output_root / "internet_rows_latest.geojson",
        {"type": "FeatureCollection", "features": shard_features},
    )
    atomic_write_json(output_root / "migration_validation_latest.json", summary)
    atomic_write_json(runner_output_path, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        error = {
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
        }
        print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
