#!/usr/bin/env python3
"""Normalize legacy internet_access_3 unable30 semantics immediately after migration.

The legacy token `unable30` means the percentage of premises unable to receive
30 Mbit/s. It must not populate the separate Ofcom decent-broadband-unavailable
field. This step is local and idempotent; it creates no values or scores.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
TASK_ID = "aays1-internet-access-3-normalize-legacy-unable30-semantics-20260722"
DEFAULT_ROWS = "england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json"
DEFAULT_GEOJSON = "england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.geojson"
DEFAULT_VALIDATION = "england_map_web/data/aays_21_slots/internet_access_3/migration_validation_latest.json"
DEFAULT_RUNNER_OUTPUT = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_3/runner_outputs/005_legacy_semantic_normalization_latest.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--rows", default=DEFAULT_ROWS)
    parser.add_argument("--geojson", default=DEFAULT_GEOJSON)
    parser.add_argument("--migration-validation", default=DEFAULT_VALIDATION)
    parser.add_argument("--runner-output", default=DEFAULT_RUNNER_OUTPUT)
    return parser.parse_args()


def find_repo_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
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


def normalize_row(row: dict[str, Any]) -> tuple[bool, bool]:
    changed = False
    conflict = False
    has_legacy = bool(row.get("legacy_internet_level_value"))
    if "unable_30mbps_pct" not in row:
        row["unable_30mbps_pct"] = row.get("decent_broadband_unavailable_pct")
        row["decent_broadband_unavailable_pct"] = None
        changed = True
    elif has_legacy and row.get("decent_broadband_unavailable_pct") is not None:
        conflict = True

    blockers = list(row.get("blockers") or [])
    marker = "LEGACY_UNABLE30_SEMANTIC_CORRECTED_TO_UNABLE_30MBPS"
    if has_legacy and marker not in blockers:
        blockers.append(marker)
        row["blockers"] = blockers
        changed = True
    return changed, conflict


def main() -> int:
    args = parse_args()
    root = find_repo_root(args.repo_root)
    rows_path = root / args.rows
    geojson_path = root / args.geojson
    validation_path = root / args.migration_validation
    runner_output_path = root / args.runner_output

    rows = load_json(rows_path)
    geojson = load_json(geojson_path)
    migration_validation = load_json(validation_path)
    features = geojson.get("features") or []

    if not isinstance(rows, list) or len(rows) != 30761:
        raise ValueError("internet_rows_latest.json must contain 30761 rows")
    if geojson.get("type") != "FeatureCollection" or len(features) != 30761:
        raise ValueError("internet_rows_latest.geojson must contain 30761 features")

    row_by_number = {int(row["row_no"]): row for row in rows}
    changed_rows = 0
    conflict_rows: list[int] = []
    for row in rows:
        changed, conflict = normalize_row(row)
        changed_rows += int(changed)
        if conflict:
            conflict_rows.append(int(row["row_no"]))

    geometry_missing_rows: list[int] = []
    for feature in features:
        props = feature.get("properties") or {}
        row_no = int(props["row_no"])
        canonical = row_by_number.get(row_no)
        if canonical is None:
            geometry_missing_rows.append(row_no)
            continue
        feature["properties"] = canonical

    blockers: list[str] = []
    if conflict_rows:
        blockers.append(f"DECENT_BROADBAND_FIELD_CONFLICT:{len(conflict_rows)}")
    if geometry_missing_rows:
        blockers.append(f"GEOJSON_ROW_NOT_IN_JSON:{len(geometry_missing_rows)}")

    migration_validation.setdefault("semantic_normalization", {})
    migration_validation["semantic_normalization"].update({
        "legacy_token": "unable30",
        "correct_target": "unable_30mbps_pct",
        "forbidden_target": "decent_broadband_unavailable_pct",
        "changed_rows": changed_rows,
        "conflict_rows": conflict_rows[:100],
        "passed": not blockers,
    })
    if blockers:
        existing = list((migration_validation.get("validation") or {}).get("blockers") or [])
        migration_validation.setdefault("validation", {})["blockers"] = sorted(set(existing + blockers))
        migration_validation["validation"]["passed"] = False
        migration_validation["state"] = "blocked"

    summary = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if not blockers else "blocked",
        "result": {
            "rows_checked": len(rows),
            "rows_changed": changed_rows,
            "semantic_conflict_rows": len(conflict_rows),
            "geojson_missing_rows": len(geometry_missing_rows),
            "new_values_created": 0,
            "quality_scores_created": 0,
            "actual_business_data_rows_written": 0,
        },
        "validation": {
            "passed": not blockers,
            "blockers": blockers,
            "conflict_row_examples": conflict_rows[:100],
            "geometry_missing_row_examples": geometry_missing_rows[:100],
        },
        "output_semantics": "LEGACY_UNABLE30_NORMALIZED_WITHOUT_VALUE_CREATION",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }

    atomic_write_json(rows_path, rows)
    atomic_write_json(geojson_path, geojson)
    atomic_write_json(validation_path, migration_validation)
    atomic_write_json(runner_output_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
