#!/usr/bin/env python3
"""Candidate-aware fail-closed PROJ/OSTN15 gate for four hardened rows.

Coordinates are read from the hash-bound candidate manifest rather than embedded in
code. PROJ network state is restored after the check and evidence is written
atomically. No elevation or height-difference value is created.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

import pyproj
from pyproj import CRS, Geod, Transformer, network
from pyproj.transformer import TransformerGroup

SOURCE = CRS.from_epsg(27700)
TARGET = CRS.from_epsg(4326)
GRID_NAME = "uk_os_OSTN15_NTv2_OSGBtoETRS.tif"
EXPECTED_ROWS = [61536, 61537, 61538, 61539]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}_", suffix=".json.tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _finite(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} is non-finite: {value!r}")
    return number


def _candidates(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = _load(path)
    values = payload.get("candidates")
    if not isinstance(values, list):
        raise ValueError("candidate manifest lacks candidates list")
    rows = [int(item.get("row_no")) for item in values]
    if rows != EXPECTED_ROWS or len(set(rows)) != len(rows):
        raise ValueError(f"candidate row set/order mismatch: {rows}")
    seen_parcels: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in values:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        inspire_id = str(
            item.get("hmlr_inspire_id")
            or item.get("national_cadastral_reference")
            or item.get("parcel_registry_id")
            or ""
        ).strip()
        if not parcel_id or parcel_id in seen_parcels or not inspire_id:
            raise ValueError(f"candidate identity mismatch at row {row_no}")
        easting = _finite(item.get("bng_easting"), f"row {row_no} easting")
        northing = _finite(item.get("bng_northing"), f"row {row_no} northing")
        longitude = _finite(item.get("longitude"), f"row {row_no} longitude")
        latitude = _finite(item.get("latitude"), f"row {row_no} latitude")
        if not (0 <= easting <= 700000 and 0 <= northing <= 1300000):
            raise ValueError(f"row {row_no} lies outside accepted BNG extent")
        if not (-8.5 <= longitude <= 2.5 and 49.0 <= latitude <= 61.5):
            raise ValueError(f"row {row_no} lies outside accepted GB display extent")
        seen_parcels.add(parcel_id)
        result.append(
            {
                "row_no": row_no,
                "parcel_id": parcel_id,
                "hmlr_inspire_id": inspire_id,
                "easting": easting,
                "northing": northing,
                "source_longitude": longitude,
                "source_latitude": latitude,
            }
        )
    return result, _sha256(path)


def run_gate(
    candidate_manifest: Path,
    output: Path,
    *,
    enable_network: bool,
    maximum_display_delta_m: float,
) -> dict[str, Any]:
    if not math.isfinite(maximum_display_delta_m) or maximum_display_delta_m <= 0 or maximum_display_delta_m > 100:
        raise ValueError("maximum-display-delta-m must be within (0, 100]")
    candidate_manifest = candidate_manifest.resolve()
    if not candidate_manifest.is_file() or candidate_manifest.stat().st_size <= 0:
        raise FileNotFoundError(candidate_manifest)
    candidates, manifest_sha_before = _candidates(candidate_manifest)

    network_before = bool(network.is_network_enabled())
    transformers: list[dict[str, Any]] = []
    probe_points: list[dict[str, Any]] = []
    transform_error: str | None = None
    best_available = False
    best: dict[str, Any] | None = None
    unavailable_operation_count = 0
    try:
        if enable_network and not network_before:
            network.set_network_enabled(True)
        network_during = bool(network.is_network_enabled())
        group = TransformerGroup(SOURCE, TARGET, always_xy=True, allow_ballpark=False)
        unavailable_operation_count = len(group.unavailable_operations)
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
        transformer = Transformer.from_crs(
            SOURCE,
            TARGET,
            always_xy=True,
            allow_ballpark=False,
            only_best=True,
        )
        geod = Geod(ellps="WGS84")
        for item in candidates:
            lon, lat = transformer.transform(item["easting"], item["northing"])
            finite = math.isfinite(lon) and math.isfinite(lat)
            _, _, display_delta_m = geod.inv(
                item["source_longitude"],
                item["source_latitude"],
                lon,
                lat,
            )
            display_delta_m = abs(float(display_delta_m))
            probe_points.append(
                {
                    **item,
                    "transformed_longitude": lon,
                    "transformed_latitude": lat,
                    "finite": finite,
                    "display_delta_m": round(display_delta_m, 3),
                    "display_delta_within_sanity_limit": display_delta_m <= maximum_display_delta_m,
                }
            )
    except Exception as exc:
        network_during = bool(network.is_network_enabled())
        transform_error = f"{type(exc).__name__}: {exc}"
    finally:
        if bool(network.is_network_enabled()) != network_before:
            network.set_network_enabled(network_before)
    network_after = bool(network.is_network_enabled())

    manifest_sha_after = _sha256(candidate_manifest)
    best_uses_grid = bool(best and best.get("uses_ostn15_grid"))
    best_no_ballpark = bool(best and not best.get("contains_ballpark"))
    try:
        best_accuracy = float(best.get("accuracy_m")) if best else math.inf
    except (TypeError, ValueError):
        best_accuracy = math.inf
    best_accuracy_ok = 0 <= best_accuracy <= 1.0
    all_finite = len(probe_points) == len(EXPECTED_ROWS) and all(item["finite"] for item in probe_points)
    all_deltas_ok = len(probe_points) == len(EXPECTED_ROWS) and all(
        item["display_delta_within_sanity_limit"] for item in probe_points
    )
    input_hash_stable = manifest_sha_after == manifest_sha_before
    network_restored = network_after == network_before
    passed = (
        best_available
        and best_uses_grid
        and best_no_ballpark
        and best_accuracy_ok
        and all_finite
        and all_deltas_ok
        and input_hash_stable
        and network_restored
        and transform_error is None
    )
    payload = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "batch_id": 116,
        "status": "READY_CANDIDATE_AWARE_PROJ_OSTN15_ONLY_BEST" if passed else "BLOCKED_PROJ_OSTN15_GATE",
        "candidate_manifest": str(candidate_manifest),
        "candidate_manifest_sha256": manifest_sha_before,
        "candidate_manifest_hash_stable": input_hash_stable,
        "expected_rows": EXPECTED_ROWS,
        "candidate_rows": [item["row_no"] for item in candidates],
        "pyproj_version": pyproj.__version__,
        "proj_version": pyproj.proj_version_str,
        "source_crs": "EPSG:27700",
        "target_crs": "EPSG:4326",
        "network_before": network_before,
        "network_explicitly_requested": bool(enable_network),
        "network_during": network_during,
        "network_after": network_after,
        "network_state_restored": network_restored,
        "allow_ballpark": False,
        "only_best": True,
        "required_grid": GRID_NAME,
        "best_available": best_available,
        "best_transformer": best,
        "transformers": transformers,
        "unavailable_operation_count": unavailable_operation_count,
        "probe_points": probe_points,
        "all_identity_fields_present": True,
        "all_finite": all_finite,
        "maximum_display_delta_m": maximum_display_delta_m,
        "max_observed_display_delta_m": max(
            (float(item["display_delta_m"]) for item in probe_points),
            default=None,
        ),
        "all_display_deltas_within_sanity_limit": all_deltas_ok,
        "transform_error": transform_error,
        "passed": passed,
        "measurement_values_written": 0,
        "candidate_promotion_allowed": False,
        "evidence_atomic_materialization": True,
        "final_ready": False,
        "fake_data": False,
    }
    _atomic_json(output.resolve(), payload)
    return payload


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enable-network", action="store_true")
    parser.add_argument("--maximum-display-delta-m", type=float, default=20.0)
    args = parser.parse_args(argv)
    payload = run_gate(
        args.candidate_manifest,
        args.output,
        enable_network=args.enable_network,
        maximum_display_delta_m=args.maximum_display_delta_m,
    )
    print(
        json.dumps(
            {
                "ok": payload["passed"],
                "status": payload["status"],
                "rows": payload["candidate_rows"],
                "candidate_manifest_sha256": payload["candidate_manifest_sha256"],
                "output": str(args.output.resolve()),
            }
        )
    )
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
