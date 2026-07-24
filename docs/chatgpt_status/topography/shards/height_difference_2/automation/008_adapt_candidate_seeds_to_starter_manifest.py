#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable
from pyproj import Transformer

ROW_START = 30762
ROW_END = 61522
EXPECTED = 3


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non-finite coordinate")
    return result


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def adapt(source: Path) -> dict[str, Any]:
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    seeds = payload.get("candidate_seeds") if isinstance(payload, dict) else None
    if not isinstance(seeds, list) or len(seeds) != EXPECTED:
        raise ValueError("exactly three candidate_seeds required")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    candidates: list[dict[str, Any]] = []
    rows: set[int] = set()
    inspire_ids: set[str] = set()
    for index, seed_value in enumerate(seeds, start=1):
        if not isinstance(seed_value, dict):
            raise ValueError(f"seed {index} is not an object")
        seed = dict(seed_value)
        row_no = int(seed["row_no"])
        parcel_id = str(seed.get("parcel_id") or "").strip()
        inspire_id = str(seed.get("hmlr_inspire_id") or "").strip()
        authority = str(seed.get("london_authority") or "").strip()
        lon = _finite(seed["hmlr_lon"])
        lat = _finite(seed["hmlr_lat"])
        if not ROW_START <= row_no <= ROW_END:
            raise ValueError(f"seed {index} outside slot")
        if not parcel_id or not inspire_id or not authority:
            raise ValueError(f"seed {index} missing identity or authority")
        if seed.get("hmlr_geometry_accuracy") != "4/4":
            raise ValueError(f"seed {index} geometry accuracy below 4/4")
        if seed.get("legacy_point_topography_values_discarded") is not True:
            raise ValueError(f"seed {index} legacy value gate not confirmed")
        if row_no in rows or inspire_id in inspire_ids:
            raise ValueError("duplicate row or INSPIRE id")
        easting, northing = transformer.transform(lon, lat)
        if not (0 <= easting <= 700000 and 0 <= northing <= 1300000):
            raise ValueError(f"seed {index} BNG outside Great Britain")
        rows.add(row_no)
        inspire_ids.add(inspire_id)
        candidates.append(
            {
                "row_no": row_no,
                "parcel_id": parcel_id,
                "hmlr_row_id": seed.get("hmlr_row_id"),
                "hmlr_inspire_id": inspire_id,
                "local_authority_name": authority,
                "longitude": lon,
                "latitude": lat,
                "bng_easting": round(easting, 3),
                "bng_northing": round(northing, 3),
                "hmlr_area_m2": _finite(seed["hmlr_area_m2"]),
                "identity_location_accuracy": "4/4",
                "candidate_seed_only": True,
                "parcel_polygon_present": False,
                "measurement_eligible": False,
                "legacy_point_topography_values_promoted": False,
            }
        )
    candidates.sort(key=lambda row: row["row_no"])
    return {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "status": "READY_FOR_HMLR_EXACT_ID_MATCH",
        "source_path": str(source),
        "source_sha256": _sha256(source),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "processing_crs": "EPSG:27700",
        "coordinate_transform": "EPSG:4326_TO_EPSG:27700_ALWAYS_XY",
        "row_order_inference_used": False,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        payload = adapt(args.seed_manifest)
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_SEED_ADAPTER",
            "error": f"{type(exc).__name__}: {exc}",
            "candidate_count": 0,
            "measurement_values_written": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "candidates": payload.get("candidate_count", 0)}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
