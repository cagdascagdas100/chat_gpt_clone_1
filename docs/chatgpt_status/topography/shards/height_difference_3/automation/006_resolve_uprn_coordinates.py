#!/usr/bin/env python3
"""Resolve canonical parcel coordinates by exact UPRN join to OS Open UPRN.

No fuzzy, nearest-point, or address-text matching is performed. The script only
fills missing coordinate fields when the canonical row and OS row share the
same exact UPRN.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROW_START = 61523
ROW_END = 92283
EXPECTED_COUNT = 30761


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_no} is not an object")
            rows.append(dict(value))
    return rows


def _normal_uprn(value: Any) -> str:
    text = str(value or "").strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    if not text.isdigit() or len(text) > 12:
        return ""
    return text


def _has_coordinates(row: dict[str, Any]) -> bool:
    for key in ("longitude", "latitude", "bng_easting", "bng_northing"):
        value = str(row.get(key, "")).strip()
        if not value:
            return False
        try:
            float(value)
        except ValueError:
            return False
    return True


def _field_map(fieldnames: list[str] | None) -> dict[str, str]:
    if not fieldnames:
        raise ValueError("OS Open UPRN CSV has no header")
    by_upper = {name.strip().upper(): name for name in fieldnames}
    required = ["UPRN", "X_COORDINATE", "Y_COORDINATE", "LATITUDE", "LONGITUDE"]
    missing = [name for name in required if name not in by_upper]
    if missing:
        raise ValueError(f"OS Open UPRN CSV lacks fields: {missing}")
    return {name: by_upper[name] for name in required}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-export", type=Path, required=True)
    parser.add_argument("--os-open-uprn-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)

    rows = _load_jsonl(args.canonical_export)
    numbers = [int(str(row.get("row_no", "-1"))) for row in rows]
    if len(rows) != EXPECTED_COUNT or set(numbers) != set(range(ROW_START, ROW_END + 1)):
        raise ValueError("canonical export must contain exactly rows 61523..92283")

    target_indexes: dict[str, list[int]] = {}
    already_resolved = 0
    missing_uprn = 0
    for index, row in enumerate(rows):
        if _has_coordinates(row):
            already_resolved += 1
            continue
        uprn = _normal_uprn(row.get("uprn") or row.get("UPRN"))
        if not uprn:
            missing_uprn += 1
            continue
        target_indexes.setdefault(uprn, []).append(index)

    remaining = set(target_indexes)
    matched_uprns = 0
    matched_rows = 0
    scanned_os_rows = 0
    with args.os_open_uprn_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = _field_map(reader.fieldnames)
        for source in reader:
            scanned_os_rows += 1
            uprn = _normal_uprn(source.get(fields["UPRN"]))
            if not uprn or uprn not in remaining:
                continue
            try:
                easting = float(str(source[fields["X_COORDINATE"]]).strip())
                northing = float(str(source[fields["Y_COORDINATE"]]).strip())
                latitude = float(str(source[fields["LATITUDE"]]).strip())
                longitude = float(str(source[fields["LONGITUDE"]]).strip())
            except (KeyError, ValueError) as exc:
                raise ValueError(f"invalid OS Open UPRN coordinate row for {uprn}") from exc
            for index in target_indexes[uprn]:
                rows[index]["uprn"] = uprn
                rows[index]["bng_easting"] = easting
                rows[index]["bng_northing"] = northing
                rows[index]["latitude"] = latitude
                rows[index]["longitude"] = longitude
                rows[index]["coordinate_source"] = "OS_OPEN_UPRN_EXACT_UPRN_JOIN"
                rows[index]["coordinate_source_version"] = "2026-06"
                rows[index]["coordinate_matching_method"] = "exact_uprn"
                matched_rows += 1
            matched_uprns += 1
            remaining.remove(uprn)
            if not remaining:
                break

    unresolved_rows = sum(not _has_coordinates(row) for row in rows)
    _write_jsonl(args.output, rows)
    report = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "canonical_rows": len(rows),
        "already_coordinate_resolved_rows": already_resolved,
        "target_uprn_count": len(target_indexes),
        "matched_uprn_count": matched_uprns,
        "matched_parcel_rows": matched_rows,
        "missing_uprn_rows": missing_uprn,
        "unresolved_coordinate_rows": unresolved_rows,
        "os_open_uprn_rows_scanned": scanned_os_rows,
        "matching_method": "exact_uprn_only",
        "nearest_point_matching_used": False,
        "measurement_values_written": 0,
        "status": "COORDINATE_JOIN_COMPLETE" if unresolved_rows == 0 else "PARTIAL_COORDINATE_JOIN",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write_json(args.report, report)
    print(json.dumps({"ok": True, "matched_rows": matched_rows, "unresolved_rows": unresolved_rows}))
    return 0 if unresolved_rows == 0 else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
