#!/usr/bin/env python3
"""Alias-safe wrapper for the height_difference_3 resumable artefact validator.

The canonical extractor permits an official HMLR INSPIRE identity to appear in
multiple London-authority compatibility rows only when all copies have the same
source coordinate and are linked to one canonical primary row. The original
resume validator rejected every repeated INSPIRE identity, including these
validated authority-overlap aliases. This wrapper preserves all original
fail-closed checks while replacing only that inconsistent registry rule.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

BASE_NAME = "025_validate_resumable_targeted_sources.py"
ROW_START = 61523
ROW_END = 92283
CANONICAL_COUNT = 92283
TOLERANCE = 1e-7
ALLOWED_IDENTITY_STATUS = {
    "unique",
    "authority_overlap_primary",
    "authority_overlap_alias",
}


def _load_base() -> Any:
    path = Path(__file__).resolve().with_name(BASE_NAME)
    if not path.is_file():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location("height_difference_3_validator_base", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load base validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()
ValidationError = BASE.ValidationError


def _number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"invalid numeric {field}={value!r}") from exc
    if not math.isfinite(number):
        raise ValidationError(f"non-finite numeric {field}={value!r}")
    return number


def _validate_registry(
    path: Path,
    *,
    row_start: int,
    row_end: int,
    canonical_count: int,
    tolerance: float = TOLERANCE,
) -> dict[str, Any]:
    expected_count = row_end - row_start + 1
    count = 0
    first_rows: list[int] = []
    last_row: int | None = None
    seen_parcels: set[str] = set()
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception as exc:
                raise ValidationError(f"invalid JSONL line {line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValidationError(f"JSONL line {line_no} is not an object")

            row_no = int(row.get("row_no"))
            expected_row = row_start + count
            if row_no != expected_row:
                raise ValidationError(
                    f"non-contiguous row registry at line {line_no}: {row_no} != {expected_row}"
                )

            parcel_id = str(row.get("parcel_id") or "").strip()
            inspire_id = str(row.get("hmlr_inspire_id") or "").strip()
            if not parcel_id or not inspire_id:
                raise ValidationError(f"row {row_no} lacks parcel_id or hmlr_inspire_id")
            if parcel_id in seen_parcels:
                raise ValidationError(f"duplicate parcel identity at row {row_no}: {parcel_id}")
            seen_parcels.add(parcel_id)

            easting = _number(row.get("bng_easting"), "bng_easting")
            northing = _number(row.get("bng_northing"), "bng_northing")
            lon = _number(row.get("longitude"), "longitude")
            lat = _number(row.get("latitude"), "latitude")
            if not (0.0 <= easting <= 700000.0 and 0.0 <= northing <= 1300000.0):
                raise ValidationError(f"row {row_no} BNG coordinate outside valid extent")
            if not (-8.5 <= lon <= 2.5 and 49.0 <= lat <= 61.5):
                raise ValidationError(f"row {row_no} source coordinate outside Great Britain")

            status = str(row.get("canonical_identity_status") or "").strip()
            if status not in ALLOWED_IDENTITY_STATUS:
                raise ValidationError(f"row {row_no} has unsupported canonical identity status {status!r}")
            try:
                primary_row_no = int(row.get("canonical_primary_row_no"))
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"row {row_no} lacks canonical_primary_row_no") from exc
            if not 1 <= primary_row_no <= canonical_count:
                raise ValidationError(f"row {row_no} canonical primary outside 1..{canonical_count}")

            if status in {"unique", "authority_overlap_primary"} and primary_row_no != row_no:
                raise ValidationError(f"row {row_no} primary/unique status does not point to itself")
            if status == "authority_overlap_alias" and primary_row_no == row_no:
                raise ValidationError(f"row {row_no} alias points to itself")

            groups[inspire_id].append(
                {
                    "row_no": row_no,
                    "status": status,
                    "primary_row_no": primary_row_no,
                    "longitude": lon,
                    "latitude": lat,
                }
            )
            if len(first_rows) < 3:
                first_rows.append(row_no)
            last_row = row_no
            count += 1

    if count != expected_count or first_rows != list(range(row_start, min(row_end, row_start + 2) + 1)) or last_row != row_end:
        raise ValidationError(
            f"shard registry mismatch count={count} first={first_rows} last={last_row}"
        )

    alias_rows = 0
    primary_rows = 0
    external_primary_alias_groups = 0
    for inspire_id, rows in groups.items():
        primary_numbers = {int(row["primary_row_no"]) for row in rows}
        if len(primary_numbers) != 1:
            raise ValidationError(f"HMLR identity {inspire_id} points to multiple canonical primaries")
        primary_row_no = next(iter(primary_numbers))
        lon0 = float(rows[0]["longitude"])
        lat0 = float(rows[0]["latitude"])
        for row in rows[1:]:
            if abs(float(row["longitude"]) - lon0) > tolerance or abs(float(row["latitude"]) - lat0) > tolerance:
                raise ValidationError(f"conflicting coordinates for repeated HMLR identity {inspire_id}")

        statuses = [str(row["status"]) for row in rows]
        if len(rows) > 1 and "unique" in statuses:
            raise ValidationError(f"repeated HMLR identity {inspire_id} contains an invalid unique row")

        in_shard_primary = [row for row in rows if int(row["row_no"]) == primary_row_no]
        if row_start <= primary_row_no <= row_end:
            if len(rows) == 1 and rows[0]["status"] == "unique":
                if len(in_shard_primary) != 1:
                    raise ValidationError(f"HMLR identity {inspire_id} unique row mapping is inconsistent")
            else:
                if len(in_shard_primary) != 1:
                    raise ValidationError(f"HMLR identity {inspire_id} lacks its in-shard canonical primary")
                if in_shard_primary[0]["status"] != "authority_overlap_primary":
                    raise ValidationError(f"HMLR identity {inspire_id} in-shard primary is not marked primary")
                primary_rows += 1
        else:
            if in_shard_primary:
                raise ValidationError(f"HMLR identity {inspire_id} has impossible external primary mapping")
            if any(status == "authority_overlap_primary" for status in statuses):
                raise ValidationError(f"HMLR identity {inspire_id} marks a primary outside the shard")
            if any(status == "authority_overlap_alias" for status in statuses):
                external_primary_alias_groups += 1

        for row in rows:
            if row["status"] == "authority_overlap_alias":
                alias_rows += 1
            elif len(rows) > 1 and row["status"] != "authority_overlap_primary":
                raise ValidationError(f"HMLR identity {inspire_id} duplicate row is not explicitly alias-marked")

    return {
        "row_count": count,
        "first_rows": first_rows,
        "last_row": last_row,
        "unique_parcel_ids": len(seen_parcels),
        "unique_hmlr_ids": len(groups),
        "authority_overlap_alias_rows": alias_rows,
        "authority_overlap_primary_rows_in_shard": primary_rows,
        "external_primary_alias_groups": external_primary_alias_groups,
        "sha256": BASE.sha256_file(path),
        "duplicate_hmlr_identity_policy": "EXPLICIT_SAME_COORDINATE_AUTHORITY_OVERLAP_ALIAS_ONLY",
    }


def validate_jsonl_registry(path: Path) -> dict[str, Any]:
    return _validate_registry(
        path,
        row_start=ROW_START,
        row_end=ROW_END,
        canonical_count=CANONICAL_COUNT,
    )


BASE.validate_jsonl_registry = validate_jsonl_registry


def build_plan(output_dir: Path, security_geojson: Path) -> dict[str, Any]:
    plan = BASE.build_plan(output_dir, security_geojson)
    plan["validator_variant"] = "ALIAS_SAFE_V2"
    plan["duplicate_hmlr_identity_policy"] = (
        "ONLY_EXPLICIT_AUTHORITY_OVERLAP_ALIASES_WITH_ONE_PRIMARY_AND_IDENTICAL_COORDINATES"
    )
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--plan-output", type=Path)
    args = parser.parse_args()
    plan = build_plan(args.output_dir, args.security_geojson)
    output = args.plan_output or args.output_dir / "resume_validation_latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": plan["all_stages_valid"],
        "first_invalid_stage": plan["first_invalid_stage"],
        "validator_variant": plan["validator_variant"],
        "plan": str(output),
    }))
    return 0 if plan["all_stages_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
