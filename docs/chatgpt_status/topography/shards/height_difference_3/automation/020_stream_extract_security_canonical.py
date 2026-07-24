#!/usr/bin/env python3
"""Stream-validate the 92,283-feature canonical security GeoJSON and export height_difference_3.

Production invariants:
- canonical registry is explicit row_no 1..92283 (feature order is never identity)
- parcel_id is unique; exact-coordinate HMLR authority-overlap aliases are explicitly linked
- source HMLR lon/lat agrees with GeoJSON Point geometry
- only rows 61523..92283 are exported
- no elevation value is produced
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

from pyproj import Transformer

CANONICAL_COUNT = 92283
ROW_START = 61523
ROW_END = 92283
SHARD_COUNT = 30761
SOURCE_CRS = "EPSG:4326"
TARGET_CRS = "EPSG:27700"


class StreamingJSON:
    def __init__(self, path: Path, chunk_chars: int = 1024 * 1024) -> None:
        self.handle = path.open("r", encoding="utf-8-sig")
        self.chunk_chars = chunk_chars
        self.buffer = ""
        self.pos = 0
        self.eof = False
        self.decoder = json.JSONDecoder()

    def close(self) -> None:
        self.handle.close()

    def _compact(self) -> None:
        if self.pos > self.chunk_chars:
            self.buffer = self.buffer[self.pos :]
            self.pos = 0

    def _fill(self) -> bool:
        if self.eof:
            return False
        chunk = self.handle.read(self.chunk_chars)
        if not chunk:
            self.eof = True
            return False
        self.buffer += chunk
        return True

    def skip_ws(self) -> None:
        while True:
            while self.pos < len(self.buffer) and self.buffer[self.pos].isspace():
                self.pos += 1
            if self.pos < len(self.buffer) or not self._fill():
                self._compact()
                return

    def peek(self) -> str:
        self.skip_ws()
        while self.pos >= len(self.buffer):
            if not self._fill():
                raise ValueError("unexpected end of JSON")
        return self.buffer[self.pos]

    def expect(self, char: str) -> None:
        actual = self.peek()
        if actual != char:
            raise ValueError(f"expected {char!r}, found {actual!r}")
        self.pos += 1
        self._compact()

    def decode(self) -> Any:
        self.skip_ws()
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buffer, self.pos)
                self.pos = end
                self._compact()
                return value
            except json.JSONDecodeError as exc:
                if not self._fill():
                    raise ValueError(f"invalid or truncated JSON near character {exc.pos}: {exc.msg}") from exc


def iter_features(path: Path) -> Iterator[dict[str, Any]]:
    stream = StreamingJSON(path)
    try:
        stream.expect("{")
        found_features = False
        first_key = True
        while True:
            token = stream.peek()
            if token == "}":
                stream.expect("}")
                break
            if not first_key:
                stream.expect(",")
            key = stream.decode()
            if not isinstance(key, str):
                raise ValueError("FeatureCollection object key is not a string")
            stream.expect(":")
            if key == "type":
                if stream.decode() != "FeatureCollection":
                    raise ValueError("source must be a GeoJSON FeatureCollection")
            elif key == "features":
                if found_features:
                    raise ValueError("duplicate features member")
                found_features = True
                stream.expect("[")
                first_feature = True
                while True:
                    token = stream.peek()
                    if token == "]":
                        stream.expect("]")
                        break
                    if not first_feature:
                        stream.expect(",")
                    feature = stream.decode()
                    if not isinstance(feature, dict):
                        raise ValueError("feature is not an object")
                    yield feature
                    first_feature = False
            else:
                stream.decode()
            first_key = False
        stream.skip_ws()
        if stream.pos < len(stream.buffer) or (not stream.eof and stream._fill()):
            stream.skip_ws()
            if stream.pos < len(stream.buffer):
                raise ValueError("trailing content after FeatureCollection")
        if not found_features:
            raise ValueError("FeatureCollection lacks features")
    finally:
        stream.close()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_int(value: Any, field: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer {field}={value!r}") from exc


def as_float(value: Any, field: str) -> float:
    try:
        result = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid number {field}={value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"non-finite number {field}={value!r}")
    return result


def normalize(feature: dict[str, Any], transformer: Transformer, tolerance: float) -> dict[str, Any]:
    props = dict(feature.get("properties") or {})
    row_no = as_int(props.get("row_no"), "row_no")
    parcel_id = str(props.get("parcel_id") or "").strip()
    inspire_id = str(props.get("hmlr_inspire_id") or "").strip()
    authority = str(props.get("london_authority") or "").strip()
    if not parcel_id or not inspire_id or not authority:
        raise ValueError(f"row_no {row_no} lacks parcel_id, hmlr_inspire_id or london_authority")
    lon = as_float(props.get("hmlr_lon"), "hmlr_lon")
    lat = as_float(props.get("hmlr_lat"), "hmlr_lat")
    if not (-8.5 <= lon <= 2.5 and 49.0 <= lat <= 61.5):
        raise ValueError(f"row_no {row_no} coordinate is outside Great Britain bounds")
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        raise ValueError(f"row_no {row_no} must have Point geometry")
    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        raise ValueError(f"row_no {row_no} has invalid Point coordinates")
    glon = as_float(coords[0], "geometry.longitude")
    glat = as_float(coords[1], "geometry.latitude")
    if abs(glon - lon) > tolerance or abs(glat - lat) > tolerance:
        raise ValueError(f"row_no {row_no} geometry and HMLR coordinates disagree")
    easting, northing = transformer.transform(lon, lat)
    if not (0 <= easting <= 700000 and 0 <= northing <= 1300000):
        raise ValueError(f"row_no {row_no} transformed BNG coordinate is invalid")
    return {
        "row_no": row_no,
        "parcel_id": parcel_id,
        "parcel_registry_id": None,
        "hmlr_inspire_id": inspire_id,
        "national_cadastral_reference": None,
        "hmlr_row_id": str(props.get("hmlr_row_id") or "").strip() or None,
        "hmlr_area_m2": props.get("hmlr_area_m2"),
        "longitude": lon,
        "latitude": lat,
        "bng_easting": round(float(easting), 3),
        "bng_northing": round(float(northing), 3),
        "local_authority_name": authority,
        "geometry_geojson_epsg4326": geometry,
        "source_coordinate_fields": ["hmlr_lon", "hmlr_lat", "geometry.coordinates"],
        "bng_coordinate_method": "PYPROJ_EPSG4326_TO_EPSG27700_FROM_SOURCE_HMLR_POINT",
        "identity_method": "EXPLICIT_ROW_NO_PARCEL_ID_AND_HMLR_INSPIRE_ID",
        "data_status": "canonical_source_backed_point_pending_current_hmlr_boundary",
        "existing_verified_height_value": None,
    }


def stream_extract(
    source: Path,
    output_dir: Path,
    *,
    canonical_count: int = CANONICAL_COUNT,
    row_start: int = ROW_START,
    row_end: int = ROW_END,
    tolerance: float = 1e-7,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / f"canonical_shard_{row_start}_{row_end}.jsonl"
    fd, temp_name = tempfile.mkstemp(prefix="canonical_shard_", suffix=".tmp", dir=output_dir)
    os.close(fd)
    temp_path = Path(temp_name)

    transformer = Transformer.from_crs(SOURCE_CRS, TARGET_CRS, always_xy=True)
    row_numbers: set[int] = set()
    parcel_ids: set[str] = set()
    inspire_ids: set[str] = set()
    primary_by_inspire: dict[str, tuple[int, float, float]] = {}
    identity_by_row: dict[int, tuple[str, str, float, float, str]] = {}
    shard: list[dict[str, Any]] = []
    shard_by_row: dict[int, dict[str, Any]] = {}
    duplicate_alias_rows = 0
    feature_count = 0

    try:
        for feature_count, feature in enumerate(iter_features(source), start=1):
            row = normalize(feature, transformer, tolerance)
            row_no = row["row_no"]
            if row_no in row_numbers:
                raise ValueError(f"duplicate row_no {row_no}")
            if row["parcel_id"] in parcel_ids:
                raise ValueError(f"duplicate parcel_id {row['parcel_id']}")
            inspire_id = row["hmlr_inspire_id"]
            if inspire_id in inspire_ids:
                primary_row_no, primary_lon, primary_lat = primary_by_inspire[inspire_id]
                # The source contains authority-boundary overlap aliases: the
                # same official INSPIRE id and point can occur under two London
                # authorities. Keep all compatibility rows but bind the alias
                # to one measurement identity; conflicting coordinates block.
                if abs(row["longitude"] - primary_lon) > tolerance or abs(row["latitude"] - primary_lat) > tolerance:
                    raise ValueError(f"conflicting duplicate hmlr_inspire_id {inspire_id}")
                duplicate_alias_rows += 1
                row["canonical_identity_status"] = "authority_overlap_alias"
                row["canonical_primary_row_no"] = primary_row_no
                if primary_row_no in shard_by_row:
                    shard_by_row[primary_row_no]["canonical_identity_status"] = "authority_overlap_primary"
            row_numbers.add(row_no)
            parcel_ids.add(row["parcel_id"])
            if inspire_id not in inspire_ids:
                inspire_ids.add(inspire_id)
                primary_by_inspire[inspire_id] = (row_no, row["longitude"], row["latitude"])
                row["canonical_identity_status"] = "unique"
                row["canonical_primary_row_no"] = row_no
            identity_by_row[row_no] = (
                row["parcel_id"], row["hmlr_inspire_id"], row["longitude"], row["latitude"], row["local_authority_name"]
            )
            if row_start <= row_no <= row_end:
                shard.append(row)
                shard_by_row[row_no] = row

        if feature_count != canonical_count:
            raise ValueError(f"expected {canonical_count} canonical features, received {feature_count}")
        expected = set(range(1, canonical_count + 1))
        if row_numbers != expected:
            missing = sorted(expected - row_numbers)[:20]
            extra = sorted(row_numbers - expected)[:20]
            raise ValueError(f"canonical registry is not exactly 1..{canonical_count}; missing={missing}, extra={extra}")
        expected_shard = row_end - row_start + 1
        shard.sort(key=lambda row: row["row_no"])
        if len(shard) != expected_shard:
            raise ValueError(f"expected {expected_shard} shard rows, received {len(shard)}")
        if [row["row_no"] for row in shard] != list(range(row_start, row_end + 1)):
            raise ValueError("shard registry is not contiguous and explicit")
        first_three = shard[:3]
        with temp_path.open("w", encoding="utf-8") as out:
            for row in shard:
                out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

        identity_digest = hashlib.sha256()
        for row_no in range(1, canonical_count + 1):
            parcel_id, inspire_id, lon, lat, authority = identity_by_row[row_no]
            identity_digest.update(f"{row_no}\t{parcel_id}\t{inspire_id}\t{lon:.8f}\t{lat:.8f}\t{authority}\n".encode())
        temp_path.replace(final_path)
        result = {
            "canonical_features_validated": feature_count,
            "canonical_unique_row_numbers": len(row_numbers),
            "canonical_unique_parcel_ids": len(parcel_ids),
            "canonical_unique_hmlr_inspire_ids": len(inspire_ids),
            "canonical_authority_overlap_alias_rows": duplicate_alias_rows,
            "canonical_measurement_identity_count": len(inspire_ids),
            "shard_rows_exported": len(shard),
            "row_start": row_start,
            "row_end": row_end,
            "first_three_explicit_rows": [row["row_no"] for row in first_three],
            "first_three_candidates": first_three,
            "canonical_identity_sha256": identity_digest.hexdigest(),
            "source_sha256": sha256_file(source),
            "source_size_bytes": source.stat().st_size,
            "export_path": str(final_path),
            "row_order_inference_used": False,
            "nearest_fill_used": False,
            "measurement_values_written": 0,
        }
        (output_dir / "stream_extraction_manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        (output_dir / "first_three_canonical_candidates.json").write_text(
            json.dumps({"slot_id":"height_difference_3","candidates":first_three,"measurement_values_written":0,"final_ready":False}, indent=2) + "\n",
            encoding="utf-8",
        )
        return result
    except Exception:
        temp_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--query-preparer", type=Path)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    if not args.source_geojson.is_file():
        raise FileNotFoundError(args.source_geojson)
    result = stream_extract(args.source_geojson.resolve(), args.output_dir.resolve())
    if args.query_preparer:
        cmd = [sys.executable, str(args.query_preparer.resolve()), "--input", result["export_path"], "--output-dir", str(args.output_dir.resolve())]
        if args.no_network:
            cmd.append("--no-network")
        completed = subprocess.run(cmd, text=True, capture_output=True)
        (args.output_dir / "query_preparer_execution.json").write_text(json.dumps({"command":cmd,"returncode":completed.returncode,"stdout":completed.stdout,"stderr":completed.stderr}, indent=2)+"\n", encoding="utf-8")
        if completed.returncode != 0:
            raise RuntimeError("query preparer failed; see query_preparer_execution.json")
    print(json.dumps({"ok":True,"shard_rows":result["shard_rows_exported"],"first_three":result["first_three_explicit_rows"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
