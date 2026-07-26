#!/usr/bin/env python3
"""Fail-closed PROJ OSTN15 gate for height_difference_3 Batch 116.

The parcel/elevation calculations remain in EPSG:27700. This preflight proves
that any BNG->WGS84 display transformation used by the publication chain can
use PROJ's best known British National Grid operation without ballpark fallback.
Network grid access is enabled only when explicitly requested.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import pyproj
from pyproj import CRS, Transformer, network
from pyproj.transformer import TransformerGroup

SOURCE = CRS.from_epsg(27700)
TARGET = CRS.from_epsg(4326)
GRID_NAME = "uk_os_OSTN15_NTv2_OSGBtoETRS.tif"
POINTS = [
    (61536, 529209.089, 169949.549),
    (61537, 529197.094, 170094.802),
    (61538, 529264.730, 170045.496),
    (61539, 529293.920, 170098.724),
]


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--enable-network", action="store_true")
    args = ap.parse_args(argv)

    network_before = bool(network.is_network_enabled())
    if args.enable_network and not network_before:
        network.set_network_enabled(True)
    network_after = bool(network.is_network_enabled())

    group = TransformerGroup(SOURCE, TARGET, always_xy=True, allow_ballpark=False)
    transformers = []
    for item in group.transformers:
        definition = str(item.definition or "")
        transformers.append({
            "description": item.description,
            "accuracy_m": item.accuracy,
            "definition": definition,
            "uses_ostn15_grid": GRID_NAME in definition,
            "contains_ballpark": "ballpark" in (item.description or "").casefold() or "ballpark" in definition.casefold(),
        })

    best = transformers[0] if transformers else None
    best_available = bool(group.best_available)
    best_uses_grid = bool(best and best["uses_ostn15_grid"])
    best_no_ballpark = bool(best and not best["contains_ballpark"])
    best_accuracy_ok = bool(best and float(best["accuracy_m"]) >= 0.0 and float(best["accuracy_m"]) <= 1.0)

    outputs = []
    transform_error = None
    try:
        transformer = Transformer.from_crs(
            SOURCE,
            TARGET,
            always_xy=True,
            allow_ballpark=False,
            only_best=True,
        )
        for row, easting, northing in POINTS:
            lon, lat = transformer.transform(easting, northing)
            outputs.append({
                "row_no": row,
                "easting": easting,
                "northing": northing,
                "longitude": lon,
                "latitude": lat,
                "finite": math.isfinite(lon) and math.isfinite(lat),
            })
    except Exception as exc:
        transform_error = f"{type(exc).__name__}: {exc}"

    all_finite = len(outputs) == len(POINTS) and all(item["finite"] for item in outputs)
    passed = (
        best_available
        and best_uses_grid
        and best_no_ballpark
        and best_accuracy_ok
        and all_finite
        and transform_error is None
    )
    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "batch_id": 116,
        "status": "READY_PROJ_OSTN15_ONLY_BEST" if passed else "BLOCKED_PROJ_OSTN15_GATE",
        "pyproj_version": pyproj.__version__,
        "proj_version": pyproj.proj_version_str,
        "source_crs": "EPSG:27700",
        "target_crs": "EPSG:4326",
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
        "probe_points": outputs,
        "transform_error": transform_error,
        "passed": passed,
        "measurement_values_written": 0,
        "candidate_promotion_allowed": False,
        "final_ready": False,
        "fake_data": False,
    }
    _write(args.output, payload)
    print(json.dumps({"ok": passed, "status": payload["status"], "output": str(args.output)}))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
