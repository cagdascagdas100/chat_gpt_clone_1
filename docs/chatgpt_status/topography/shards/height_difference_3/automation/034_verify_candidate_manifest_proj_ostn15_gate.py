#!/usr/bin/env python3
"""Fail-closed candidate-aware PROJ OSTN15 gate for height_difference_3.

Reads the source-backed candidate manifest produced by the existing query preparer
and validates the exact candidate BNG coordinates with PROJ's best available
EPSG:27700 -> EPSG:4326 transformation. This stage never measures elevation or
promotes a business value.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import pyproj
from pyproj import CRS, Geod, Transformer, network
from pyproj.transformer import TransformerGroup

SOURCE = CRS.from_epsg(27700)
TARGET = CRS.from_epsg(4326)
GRID_NAME = "uk_os_OSTN15_NTv2_OSGBtoETRS.tif"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("candidate manifest must be a JSON object")
    return value


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _finite(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite coordinate: {value!r}")
    return number


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--enable-network", action="store_true")
    ap.add_argument("--expected-row-start", type=int, default=61540)
    ap.add_argument("--expected-row-end", type=int, default=61551)
    ap.add_argument("--maximum-display-delta-m", type=float, default=20.0)
    args = ap.parse_args(argv)

    manifest = _load(args.candidate_manifest.resolve())
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidate manifest lacks candidates list")

    expected_rows = list(range(args.expected_row_start, args.expected_row_end + 1))
    if len(candidates) != len(expected_rows):
        raise ValueError(f"expected {len(expected_rows)} candidates, received {len(candidates)}")

    rows = [int(item["row_no"]) for item in candidates]
    row_set_pass = rows == expected_rows and len(set(rows)) == len(rows)
    if not row_set_pass:
        raise ValueError(f"candidate row set/order mismatch: expected={expected_rows} actual={rows}")

    network_before = bool(network.is_network_enabled())
    if args.enable_network and not network_before:
        network.set_network_enabled(True)
    network_after = bool(network.is_network_enabled())

    group = TransformerGroup(SOURCE, TARGET, always_xy=True, allow_ballpark=False)
    transformers: list[dict[str, Any]] = []
    for item in group.transformers:
        definition = str(item.definition or "")
        description = str(item.description or "")
        transformers.append(
            {
                "description": description,
                "accuracy_m": item.accuracy,
                "definition": definition,
                "uses_ostn15_grid": GRID_NAME in definition,
                "contains_ballpark": "ballpark" in description.casefold() or "ballpark" in definition.casefold(),
            }
        )

    best = transformers[0] if transformers else None
    best_available = bool(group.best_available)
    best_uses_grid = bool(best and best["uses_ostn15_grid"])
    best_no_ballpark = bool(best and not best["contains_ballpark"])
    best_accuracy_ok = bool(best and float(best["accuracy_m"]) >= 0.0 and float(best["accuracy_m"]) <= 1.0)

    probe_points: list[dict[str, Any]] = []
    transform_error: str | None = None
    geod = Geod(ellps="WGS84")
    try:
        transformer = Transformer.from_crs(
            SOURCE,
            TARGET,
            always_xy=True,
            allow_ballpark=False,
            only_best=True,
        )
        for item in candidates:
            row_no = int(item["row_no"])
            easting = _finite(item["bng_easting"])
            northing = _finite(item["bng_northing"])
            source_lon = _finite(item["longitude"])
            source_lat = _finite(item["latitude"])
            lon, lat = transformer.transform(easting, northing)
            finite = math.isfinite(lon) and math.isfinite(lat)
            _, _, display_delta_m = geod.inv(source_lon, source_lat, lon, lat)
            display_delta_m = abs(float(display_delta_m))
            probe_points.append(
                {
                    "row_no": row_no,
                    "parcel_id": item.get("parcel_id"),
                    "hmlr_inspire_id": item.get("hmlr_inspire_id"),
                    "easting": easting,
                    "northing": northing,
                    "source_longitude": source_lon,
                    "source_latitude": source_lat,
                    "transformed_longitude": lon,
                    "transformed_latitude": lat,
                    "finite": finite,
                    "display_delta_m": round(display_delta_m, 3),
                    "display_delta_within_sanity_limit": display_delta_m <= args.maximum_display_delta_m,
                }
            )
    except Exception as exc:
        transform_error = f"{type(exc).__name__}: {exc}"

    all_finite = len(probe_points) == len(expected_rows) and all(item["finite"] for item in probe_points)
    all_display_deltas_ok = len(probe_points) == len(expected_rows) and all(
        item["display_delta_within_sanity_limit"] for item in probe_points
    )
    all_identity_fields_present = all(
        str(item.get("parcel_id") or "").strip() and str(item.get("hmlr_inspire_id") or "").strip()
        for item in probe_points
    )
    max_display_delta_m = max((float(item["display_delta_m"]) for item in probe_points), default=None)

    passed = (
        row_set_pass
        and all_identity_fields_present
        and best_available
        and best_uses_grid
        and best_no_ballpark
        and best_accuracy_ok
        and all_finite
        and all_display_deltas_ok
        and transform_error is None
    )

    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "purpose": "CANDIDATE_AWARE_PROJ_OSTN15_DISPLAY_TRANSFORM_GATE_NO_NUMERIC_MEASUREMENT",
        "candidate_manifest": str(args.candidate_manifest.resolve()),
        "expected_rows": expected_rows,
        "candidate_rows": rows,
        "row_set_pass": row_set_pass,
        "source_crs": "EPSG:27700",
        "target_crs": "EPSG:4326",
        "pyproj_version": pyproj.__version__,
        "proj_version": pyproj.proj_version_str,
        "network_before": network_before,
        "network_explicitly_requested": bool(args.enable_network),
        "network_after": network_after,
        "allow_ballpark": False,
        "only_best": True,
        "required_grid": GRID_NAME,
        "best_available": best_available,
        "best_transformer": best,
        "transformers": transformers,
        "unavailable_operation_count": len(group.unavailable_operations),
        "probe_points": probe_points,
        "all_identity_fields_present": all_identity_fields_present,
        "all_finite": all_finite,
        "maximum_display_delta_m": args.maximum_display_delta_m,
        "max_observed_display_delta_m": max_display_delta_m,
        "all_display_deltas_within_sanity_limit": all_display_deltas_ok,
        "transform_error": transform_error,
        "passed": passed,
        "measurement_values_written": 0,
        "candidate_promotion_allowed": False,
        "final_ready": False,
        "fake_data": False,
    }
    _write(args.output, payload)
    print(json.dumps({"ok": passed, "rows": rows, "output": str(args.output)}))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
