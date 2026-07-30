#!/usr/bin/env python3
"""Fail-closed candidate-aware PROJ/OSTN15 display-coordinate gate.

The candidate manifest is hash-bound and must be the transactional output of the
official query-preparation stage. PROJ network state is restored after the gate.
The evidence file is atomically materialized and never promotes a measurement.
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f"candidate manifest is missing or empty: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("candidate manifest must be a JSON object")
    return value


def _write_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}_", suffix=".json.tmp", dir=path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _finite(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid coordinate {label}: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"non-finite coordinate {label}: {value!r}")
    return number


def _valid_sha256(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def _grid_names(transformer: Any) -> list[str]:
    names: list[str] = []
    for operation in getattr(transformer, "operations", ()) or ():
        for grid in getattr(operation, "grids", ()) or ():
            for attr in ("short_name", "full_name", "package_name", "url"):
                value = str(getattr(grid, attr, "") or "").strip()
                if value and value not in names:
                    names.append(value)
    return names


def _transformer_record(item: Any) -> dict[str, Any]:
    definition = str(getattr(item, "definition", "") or "")
    description = str(getattr(item, "description", "") or "")
    grids = _grid_names(item)
    accuracy = getattr(item, "accuracy", None)
    try:
        accuracy_value = float(accuracy)
    except (TypeError, ValueError):
        accuracy_value = None
    combined = "\n".join([definition, description, *grids]).casefold()
    return {
        "description": description,
        "accuracy_m": accuracy_value,
        "definition": definition,
        "grid_names": grids,
        "uses_ostn15_grid": GRID_NAME.casefold() in combined,
        "contains_ballpark": "ballpark" in combined,
    }


def _validate_manifest(manifest: dict[str, Any], expected_rows: list[int]) -> list[dict[str, Any]]:
    if manifest.get("slot_id") != "height_difference_3":
        raise ValueError("candidate manifest slot identity mismatch")
    if int(manifest.get("schema_version") or 0) < 2:
        raise ValueError("candidate manifest schema is too old")
    if manifest.get("canonical_registry_contiguous") is not True:
        raise ValueError("candidate manifest lacks contiguous registry proof")
    if manifest.get("transactional_output_bundle") is not True:
        raise ValueError("candidate manifest lacks transactional output proof")
    if manifest.get("network_queries_enabled") is not True:
        raise ValueError("strict candidate manifest must contain official network discovery")
    if manifest.get("official_ea_host_only") is not True:
        raise ValueError("candidate manifest lacks official EA host-only proof")
    if not _valid_sha256(manifest.get("canonical_export_sha256")):
        raise ValueError("candidate manifest lacks canonical export SHA-256")
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(expected_rows):
        raise ValueError(f"expected {len(expected_rows)} candidates")
    rows: list[int] = []
    parcel_ids: set[str] = set()
    inspire_ids: set[str] = set()
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            raise ValueError(f"candidate {index} is not an object")
        row_no = int(item.get("row_no"))
        parcel_id = str(item.get("parcel_id") or "").strip()
        inspire_id = str(item.get("hmlr_inspire_id") or "").strip()
        if not parcel_id or parcel_id in parcel_ids:
            raise ValueError(f"candidate row {row_no} has empty or duplicate parcel_id")
        if not inspire_id or inspire_id in inspire_ids:
            raise ValueError(f"candidate row {row_no} has empty or duplicate HMLR INSPIRE id")
        parcel_ids.add(parcel_id)
        inspire_ids.add(inspire_id)
        easting = _finite(item.get("bng_easting"), f"row {row_no} easting")
        northing = _finite(item.get("bng_northing"), f"row {row_no} northing")
        lon = _finite(item.get("longitude"), f"row {row_no} longitude")
        lat = _finite(item.get("latitude"), f"row {row_no} latitude")
        if not (0 <= easting <= 700000 and 0 <= northing <= 1300000):
            raise ValueError(f"candidate row {row_no} BNG coordinate is outside accepted extent")
        if not (-8.5 <= lon <= 2.5 and 49.0 <= lat <= 61.5):
            raise ValueError(f"candidate row {row_no} longitude/latitude is outside Great Britain")
        if item.get("measured_value_promoted") is not False:
            raise ValueError(f"candidate row {row_no} unexpectedly allows numeric promotion")
        rows.append(row_no)
    if rows != expected_rows:
        raise ValueError(f"candidate row set/order mismatch: expected={expected_rows} actual={rows}")
    return candidates


def run_gate(
    candidate_manifest: Path,
    output: Path,
    *,
    enable_network: bool,
    expected_row_start: int,
    expected_row_end: int,
    maximum_display_delta_m: float,
    expected_candidate_manifest_sha256: str = "",
) -> dict[str, Any]:
    candidate_manifest = candidate_manifest.resolve()
    output = output.resolve()
    if output == candidate_manifest:
        raise ValueError("output path must differ from candidate manifest")
    if expected_row_start < 1 or expected_row_end < expected_row_start:
        raise ValueError("invalid expected row range")
    if not math.isfinite(maximum_display_delta_m) or maximum_display_delta_m <= 0 or maximum_display_delta_m > 100:
        raise ValueError("maximum display delta must be within (0, 100]")
    manifest_sha_before = _sha256(candidate_manifest)
    expected_sha = expected_candidate_manifest_sha256.strip().lower()
    if expected_sha and manifest_sha_before != expected_sha:
        raise ValueError("candidate manifest SHA-256 mismatch")
    manifest = _load(candidate_manifest)
    expected_rows = list(range(expected_row_start, expected_row_end + 1))
    candidates = _validate_manifest(manifest, expected_rows)
    network_before = bool(network.is_network_enabled())
    network_during = network_before
    probe_points: list[dict[str, Any]] = []
    transformers: list[dict[str, Any]] = []
    transform_error: str | None = None
    best_available = False
    unavailable_operation_count = 0
    try:
        if enable_network != network_before:
            network.set_network_enabled(enable_network)
        network_during = bool(network.is_network_enabled())
        group = TransformerGroup(SOURCE, TARGET, always_xy=True, allow_ballpark=False)
        transformers = [_transformer_record(item) for item in group.transformers]
        best_available = bool(group.best_available)
        unavailable_operation_count = len(group.unavailable_operations)
        transformer = Transformer.from_crs(
            SOURCE, TARGET, always_xy=True, allow_ballpark=False, only_best=True
        )
        geod = Geod(ellps="WGS84")
        for item in candidates:
            row_no = int(item["row_no"])
            easting = _finite(item["bng_easting"], f"row {row_no} easting")
            northing = _finite(item["bng_northing"], f"row {row_no} northing")
            source_lon = _finite(item["longitude"], f"row {row_no} longitude")
            source_lat = _finite(item["latitude"], f"row {row_no} latitude")
            lon, lat = transformer.transform(easting, northing)
            finite = math.isfinite(lon) and math.isfinite(lat)
            in_bounds = finite and -8.5 <= lon <= 2.5 and 49.0 <= lat <= 61.5
            _, _, delta = geod.inv(source_lon, source_lat, lon, lat)
            delta = abs(float(delta))
            probe_points.append({
                "row_no": row_no,
                "parcel_id": item["parcel_id"],
                "hmlr_inspire_id": item["hmlr_inspire_id"],
                "easting": easting,
                "northing": northing,
                "source_longitude": source_lon,
                "source_latitude": source_lat,
                "transformed_longitude": lon,
                "transformed_latitude": lat,
                "finite": finite,
                "within_gb_bounds": in_bounds,
                "display_delta_m": round(delta, 3),
                "display_delta_within_sanity_limit": delta <= maximum_display_delta_m,
            })
    except Exception as exc:
        transform_error = f"{type(exc).__name__}: {exc}"
    finally:
        if bool(network.is_network_enabled()) != network_before:
            network.set_network_enabled(network_before)
    network_restored = bool(network.is_network_enabled()) == network_before
    manifest_sha_after = _sha256(candidate_manifest)
    input_stable = manifest_sha_before == manifest_sha_after
    best = transformers[0] if transformers else None
    best_accuracy = None if best is None else best.get("accuracy_m")
    best_accuracy_ok = isinstance(best_accuracy, (int, float)) and 0 <= float(best_accuracy) <= 1.0
    all_finite = len(probe_points) == len(expected_rows) and all(item["finite"] for item in probe_points)
    all_bounds = len(probe_points) == len(expected_rows) and all(item["within_gb_bounds"] for item in probe_points)
    all_deltas = len(probe_points) == len(expected_rows) and all(item["display_delta_within_sanity_limit"] for item in probe_points)
    passed = bool(
        input_stable
        and best_available
        and best
        and best.get("uses_ostn15_grid") is True
        and best.get("contains_ballpark") is False
        and best_accuracy_ok
        and all_finite
        and all_bounds
        and all_deltas
        and transform_error is None
        and network_restored
    )
    payload = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "purpose": "CANDIDATE_AWARE_PROJ_OSTN15_DISPLAY_TRANSFORM_GATE_NO_NUMERIC_MEASUREMENT",
        "candidate_manifest": str(candidate_manifest),
        "candidate_manifest_sha256": manifest_sha_after,
        "canonical_export_sha256": manifest.get("canonical_export_sha256"),
        "input_stability_verified": input_stable,
        "expected_rows": expected_rows,
        "candidate_rows": [int(item["row_no"]) for item in candidates],
        "source_crs": "EPSG:27700",
        "target_crs": "EPSG:4326",
        "pyproj_version": pyproj.__version__,
        "proj_version": pyproj.proj_version_str,
        "network_before": network_before,
        "network_explicitly_requested": enable_network,
        "network_during": network_during,
        "network_restored": network_restored,
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
        "all_transformed_points_within_gb_bounds": all_bounds,
        "maximum_display_delta_m": maximum_display_delta_m,
        "max_observed_display_delta_m": max((float(item["display_delta_m"]) for item in probe_points), default=None),
        "all_display_deltas_within_sanity_limit": all_deltas,
        "transform_error": transform_error,
        "passed": passed,
        "atomic_evidence_materialization": True,
        "measurement_values_written": 0,
        "candidate_promotion_allowed": False,
        "final_ready": False,
        "fake_data": False,
    }
    _write_atomic(output, payload)
    return payload


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--enable-network", action="store_true")
    ap.add_argument("--expected-row-start", type=int, default=61540)
    ap.add_argument("--expected-row-end", type=int, default=61551)
    ap.add_argument("--maximum-display-delta-m", type=float, default=20.0)
    ap.add_argument("--expected-candidate-manifest-sha256", default="")
    args = ap.parse_args(argv)
    payload = run_gate(
        args.candidate_manifest, args.output,
        enable_network=args.enable_network,
        expected_row_start=args.expected_row_start,
        expected_row_end=args.expected_row_end,
        maximum_display_delta_m=args.maximum_display_delta_m,
        expected_candidate_manifest_sha256=args.expected_candidate_manifest_sha256,
    )
    print(json.dumps({"ok": payload["passed"], "rows": payload["candidate_rows"], "output": str(args.output)}))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
