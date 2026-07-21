#!/usr/bin/env python3
"""Extract review-only internet-access candidates for slot internet_access_2.

The script never writes a database, never creates geometry and never promotes a
postcode proxy to a parcel measurement. It reads the existing canonical matrix,
filters row_no 30762..61522, optionally cross-checks exact postcodes against the
Ofcom Connected Nations Spring 2026 r2 postcode CSV files, and writes review
artifacts only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable

ROW_START = 30762
ROW_END = 61522
SLOT_ID = "internet_access_2"
DATA_LEVEL = "POSTCODE_LEVEL_ONLY"


def normalise_postcode(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def normalise_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def parse_matrix_value(raw: Any) -> dict[str, Any]:
    text = str(raw or "").strip()
    result: dict[str, Any] = {
        "internet_level": None,
        "postcode": None,
        "gigabit_percent": None,
        "ufbb100_percent": None,
        "sfbb_percent": None,
        "unable30_percent": None,
    }
    if not text:
        return result
    parts = [part.strip() for part in text.split(";") if part.strip()]
    if parts:
        result["internet_level"] = parts[0]
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = [x.strip() for x in part.split("=", 1)]
        key = key.lower()
        if key == "postcode":
            result["postcode"] = normalise_postcode(value)
            continue
        numeric = value.rstrip("%").strip()
        try:
            number: float | None = float(numeric)
        except ValueError:
            number = None
        aliases = {
            "gigabit": "gigabit_percent",
            "ufbb100": "ufbb100_percent",
            "sfbb": "sfbb_percent",
            "unable30": "unable30_percent",
        }
        if key in aliases:
            result[aliases[key]] = number
    return result


def pick_value(row: dict[str, str], aliases: Iterable[str]) -> str | None:
    normalised = {normalise_header(k): v for k, v in row.items()}
    for alias in aliases:
        value = normalised.get(normalise_header(alias))
        if value not in (None, ""):
            return value
    return None


def postcode_area(postcode: str) -> str:
    match = re.match(r"^[A-Z]+", postcode)
    return match.group(0) if match else ""


def load_ofcom_rows(ofcom_dir: Path | None, postcodes: set[str]) -> tuple[dict[str, dict[str, str]], list[str]]:
    if ofcom_dir is None or not ofcom_dir.exists() or not postcodes:
        return {}, []
    areas = {postcode_area(pc) for pc in postcodes if postcode_area(pc)}
    selected_files: list[Path] = []
    for area in sorted(areas):
        selected_files.extend(sorted(ofcom_dir.glob(f"202601_fixed_postcode_coverage_r2_{area}.csv")))
    index: dict[str, dict[str, str]] = {}
    for path in selected_files:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                postcode = normalise_postcode(
                    pick_value(row, ["postcode", "postcode_space", "Postcode with spaces removed"])
                )
                if postcode in postcodes:
                    index[postcode] = row
    return index, [str(path) for path in selected_files]


def ofcom_metric(row: dict[str, str] | None, aliases: list[str]) -> float | None:
    if not row:
        return None
    value = pick_value(row, aliases)
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace("%", "").strip())
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--ofcom-dir")
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    matrix_path = repo_root / "england_map_web/data/program_layer_matrix/internet.geojson"
    output_root = repo_root / (
        "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
        "shards/internet_access_2/runner_outputs"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    if not matrix_path.exists():
        raise FileNotFoundError(f"matrix source missing: {matrix_path}")

    with matrix_path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)

    selected: list[dict[str, Any]] = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        try:
            row_no = int(properties.get("row_no"))
        except (TypeError, ValueError):
            continue
        if not ROW_START <= row_no <= ROW_END:
            continue
        parsed = parse_matrix_value(properties.get("internet_level_value"))
        if not parsed["postcode"]:
            continue
        selected.append({
            "row_no": row_no,
            "parcel_id": properties.get("parcel_id"),
            "hmlr_inspire_id": properties.get("hmlr_inspire_id"),
            "geometry_type": (feature.get("geometry") or {}).get("type"),
            "matrix_accuracy": properties.get("internet_level_accuracy"),
            **parsed,
        })
        if len(selected) >= max(1, args.limit):
            break

    postcodes = {row["postcode"] for row in selected if row.get("postcode")}
    ofcom_rows, files_read = load_ofcom_rows(
        Path(args.ofcom_dir).resolve() if args.ofcom_dir else None,
        postcodes,
    )

    results: list[dict[str, Any]] = []
    for row in selected:
        postcode = row["postcode"]
        official = ofcom_rows.get(postcode)
        exact_match = official is not None
        results.append({
            **row,
            "slot_id": SLOT_ID,
            "data_level": DATA_LEVEL,
            "ofcom_exact_postcode_match": exact_match,
            "ofcom_gigabit_percent": ofcom_metric(official, ["Gigabit availability (% premises)", "gigabit"]),
            "ofcom_ufbb100_percent": ofcom_metric(official, ["UFBB (100Mbit/s) availability (% premises)", "ufbb100"]),
            "ofcom_sfbb_percent": ofcom_metric(official, ["SFBB availability (% premises)", "sfbb"]),
            "ofcom_unable30_percent": ofcom_metric(official, ["% of premises unable to receive 30Mbit/s", "unable30"]),
            "source_accuracy_score_4": 4 if exact_match else 2,
            "parcel_match_accuracy_score_4": 2,
            "promotion_state": "REVIEW_ONLY_NOT_PROMOTED",
            "business_row_written": False,
            "fake_data": False,
        })

    json_path = output_root / "001_shard2_postcode_candidates_latest.json"
    csv_path = output_root / "001_shard2_postcode_candidates_latest.csv"
    output = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "row_partition": {"start": ROW_START, "end": ROW_END},
        "data_level": DATA_LEVEL,
        "matrix_source": str(matrix_path),
        "ofcom_files_read": files_read,
        "candidate_count": len(results),
        "ofcom_exact_match_count": sum(1 for row in results if row["ofcom_exact_postcode_match"]),
        "promoted_parcel_rows": 0,
        "actual_business_data_rows_written": 0,
        "truth_boundary": "Postcode values are area-level proxies. Point geometry is not parcel geometry. No row is promoted without reviewed canonical geometry and provenance.",
        "rows": results,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fieldnames = sorted({key for row in results for key in row}) if results else [
        "slot_id", "row_no", "postcode", "data_level", "promotion_state"
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(json.dumps({
        "slot_id": SLOT_ID,
        "candidate_count": len(results),
        "ofcom_exact_match_count": output["ofcom_exact_match_count"],
        "json_output": str(json_path),
        "csv_output": str(csv_path),
        "actual_business_data_rows_written": 0,
        "final_ready": False,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
