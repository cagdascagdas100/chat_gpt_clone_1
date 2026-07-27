#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_2"
TARGET_ROWS = [30762, 46142, 61522]
EXPECTED_COVERAGE_ID = "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _preserved_rows(payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("preserved EA evidence must contain exactly three rows")
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        row_no = int(row["row_no"])
        result[row_no] = {
            "hmlr_inspire_id": str(row["hmlr_inspire_id"]),
            "height_min_m": float(row["height_min_m"]),
            "height_max_m": float(row["height_max_m"]),
            "height_difference_m": float(row["height_difference_m"]),
            "result_confidence_percent": float(row.get("result_confidence_percent", 0.0)),
        }
    if sorted(result) != TARGET_ROWS:
        raise ValueError(f"preserved EA exact row set mismatch: {sorted(result)}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ea-samples", type=Path, required=True)
    parser.add_argument("--preserved-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-coverage-id", default=EXPECTED_COVERAGE_ID)
    parser.add_argument("--tolerance-m", type=float, default=0.001)
    args = parser.parse_args()

    try:
        if args.tolerance_m < 0 or not math.isfinite(args.tolerance_m):
            raise ValueError("tolerance must be finite and non-negative")
        current = _load(args.ea_samples)
        preserved = _load(args.preserved_evidence)
        if current.get("slot_id") != SLOT_ID or current.get("status") != "THREE_EA_DTM1M_POLYGON_SAMPLES_READY":
            raise ValueError("current EA sample gate is not ready")
        if str(current.get("coverage_id")) != args.expected_coverage_id:
            raise ValueError(f"current EA coverage id mismatch: {current.get('coverage_id')}")
        reference = _preserved_rows(preserved)
        current_rows = current.get("samples")
        if not isinstance(current_rows, list) or len(current_rows) != 3:
            raise ValueError("current EA sample payload must contain exactly three rows")
        joined: list[dict[str, Any]] = []
        seen: set[int] = set()
        for row in current_rows:
            row_no = int(row["row_no"])
            if row_no in seen:
                raise ValueError(f"duplicate current EA row: {row_no}")
            seen.add(row_no)
            expected = reference.get(row_no)
            if expected is None:
                raise ValueError(f"unexpected current EA row: {row_no}")
            hmlr_id = str(row["hmlr_inspire_id"])
            if hmlr_id != expected["hmlr_inspire_id"]:
                raise ValueError(f"HMLR binding mismatch for row {row_no}: {hmlr_id}")
            min_m = float(row["min_m_odn"])
            max_m = float(row["max_m_odn"])
            median_m = float(row["median_m_odn"])
            if not all(math.isfinite(value) for value in (min_m, max_m, median_m)) or max_m < min_m:
                raise ValueError(f"invalid current EA height statistics for row {row_no}")
            difference_m = round(max_m - min_m, 3)
            preserved_difference_m = round(float(expected["height_difference_m"]), 3)
            delta_m = round(difference_m - preserved_difference_m, 3)
            if abs(delta_m) > args.tolerance_m + 1e-12:
                raise ValueError(
                    f"current EA parcel height-difference drift for row {row_no}: "
                    f"current={difference_m:.3f} preserved={preserved_difference_m:.3f} delta={delta_m:.3f}"
                )
            joined.append({
                "row_no": row_no,
                "parcel_id": str(row["parcel_id"]),
                "hmlr_inspire_id": hmlr_id,
                "height_min_m_odn": round(min_m, 3),
                "height_max_m_odn": round(max_m, 3),
                "height_difference_m": difference_m,
                "parcel_elevation_median_m_odn": round(median_m, 3),
                "preserved_height_difference_m": preserved_difference_m,
                "current_minus_preserved_height_difference_m": delta_m,
                "preserved_result_confidence_percent": expected["result_confidence_percent"],
                "geotiff_sha256": row.get("geotiff_sha256"),
            })
        if sorted(seen) != TARGET_ROWS:
            raise ValueError(f"current EA exact row set mismatch: {sorted(seen)}")
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "status": "THREE_CURRENT_EA_HEIGHT_DIFFERENCES_MATCH_PRESERVED_EXACT_RESULTS",
            "coverage_id": args.expected_coverage_id,
            "metric_contract": {
                "height_difference_m": "EA DTM 1m max_m_odn minus min_m_odn over valid pixel centres inside exact HMLR polygon",
                "parcel_elevation_median_m_odn": "EA DTM 1m median elevation ODN; distinct from parcel height difference",
                "terrain50_role": "secondary coarse elevation crosscheck; does not replace primary EA parcel height-difference metric",
            },
            "tolerance_m": args.tolerance_m,
            "row_count": len(joined),
            "rows": joined,
            "ea_samples_path": str(args.ea_samples),
            "ea_samples_sha256": _sha256(args.ea_samples),
            "preserved_evidence_path": str(args.preserved_evidence),
            "preserved_evidence_sha256": _sha256(args.preserved_evidence),
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "status": "BLOCKED_CURRENT_EA_HEIGHT_DIFFERENCE_METRIC_CONSISTENCY",
            "error": f"{type(exc).__name__}: {exc}",
            "coverage_id_required": args.expected_coverage_id,
            "tolerance_m": args.tolerance_m,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "rows": payload.get("row_count", 0)}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
