#!/usr/bin/env python3
"""Stream-validate the canonical GeoJSON and transactionally export one shard.

Identity is explicit; feature order, nearest fill and synthetic elevation are forbidden.
The shard JSONL, extraction manifest and first-candidate manifest are published as one
rollback-capable bundle. Existing valid outputs are preserved on every failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
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
        found_type = False
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
                if found_type:
                    raise ValueError("duplicate type member")
                found_type = True
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
        if not found_type or not found_features:
            raise ValueError("FeatureCollection lacks type or features")
        stream.skip_ws()
        if stream.pos < len(stream.buffer) or (not stream.eof and stream._fill()):
            stream.skip_ws()
            if stream.pos < len(stream.buffer):
                raise ValueError("trailing content after FeatureCollection")
    finally:
        stream.close()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_json_fsync(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _publish_bundle(staged: dict[Path, Path], output_dir: Path) -> None:
    """Publish all targets or restore the complete previous bundle."""
    backup_dir = Path(tempfile.mkdtemp(prefix=".canonical_bundle_", suffix=".backup", dir=output_dir))
    moved_old: list[tuple[Path, Path]] = []
    published: list[Path] = []
    try:
        for target, stage in staged.items():
            if not stage.is_file() or stage.stat().st_size <= 0:
                raise ValueError(f"staged output missing or empty: {stage}")
            if target.exists():
                backup = backup_dir / target.name
                target.replace(backup)
                moved_old.append((target, backup))
        try:
            for target, stage in staged.items():
                stage.replace(target)
                published.append(target)
            _fsync_dir(output_dir)
        except Exception:
            for target in reversed(published):
                target.unlink(missing_ok=True)
            for target, backup in reversed(moved_old):
                if backup.exists():
                    backup.replace(target)
            _fsync_dir(output_dir)
            raise
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)


def as_int(value: Any, field: str) -> int:
    try:
        result = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer {field}={value!r}") from exc
    return result


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
    if not isinstance(coords, list) or len(coords) != 2:
        raise ValueError(f"row_no {row_no} must have exactly two Point coordinates")
    glon = as_float(coords[0], "geometry.longitude")
    glat = as_float(coords[1], "geometry.latitude")
    if abs(glon - lon) > tolerance or abs(glat - lat) > tolerance:
        raise ValueError(f"row_no {row_no} geometry and HMLR coordinates disagree")
    easting, northing = transformer.transform(lon, lat)
    if not all(math.isfinite(value) for value in (easting, northing)):
        raise ValueError(f"row_no {row_no} transformation produced non-finite BNG coordinates")
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
        "bng_coordinate_method": "PYPROJ_EPSG4326_TO_EPSG27700_STRICT_NO_BALLPARK_ONLY_BEST",
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
    source = source.resolve()
    if not source.is_file() or source.stat().st_size <= 0:
        raise ValueError("canonical source must be a non-empty regular file")
    if canonical_count < 1 or row_start < 1 or row_end < row_start or row_end > canonical_count:
        raise ValueError("invalid canonical/shard bounds")
    if not math.isfinite(tolerance) or tolerance < 0 or tolerance > 1e-4:
        raise ValueError("coordinate tolerance must be finite and between 0 and 1e-4")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / f"canonical_shard_{row_start}_{row_end}.jsonl"
    manifest_path = output_dir / "stream_extraction_manifest.json"
    candidates_path = output_dir / "first_three_canonical_candidates.json"
    source_stat_before = source.stat()
    source_hash_before = sha256_file(source)

    stage_dir = Path(tempfile.mkdtemp(prefix=".canonical_extract_", suffix=".stage", dir=output_dir))
    stage_shard = stage_dir / final_path.name
    stage_manifest = stage_dir / manifest_path.name
    stage_candidates = stage_dir / candidates_path.name
    transformer = Transformer.from_crs(
        SOURCE_CRS, TARGET_CRS, always_xy=True, allow_ballpark=False, only_best=True
    )
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
        shard.sort(key=lambda row: row["row_no"])
        expected_shard = row_end - row_start + 1
        if len(shard) != expected_shard or [row["row_no"] for row in shard] != list(range(row_start, row_end + 1)):
            raise ValueError("shard registry is not complete, contiguous and explicit")

        source_stat_after = source.stat()
        source_hash_after = sha256_file(source)
        if (
            source_stat_before.st_size != source_stat_after.st_size
            or source_stat_before.st_mtime_ns != source_stat_after.st_mtime_ns
            or source_hash_before != source_hash_after
        ):
            raise ValueError("canonical source changed during extraction")

        first_three = shard[:3]
        with stage_shard.open("w", encoding="utf-8", newline="\n") as out:
            for row in shard:
                out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            out.flush()
            os.fsync(out.fileno())
        shard_sha = sha256_file(stage_shard)

        identity_digest = hashlib.sha256()
        for row_no in range(1, canonical_count + 1):
            parcel_id, inspire_id, lon, lat, authority = identity_by_row[row_no]
            identity_digest.update(f"{row_no}\t{parcel_id}\t{inspire_id}\t{lon:.8f}\t{lat:.8f}\t{authority}\n".encode())
        result = {
            "schema_version": 2,
            "slot_id": "height_difference_3",
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
            "source_sha256": source_hash_after,
            "source_size_bytes": source_stat_after.st_size,
            "export_path": str(final_path),
            "export_sha256": shard_sha,
            "strict_crs_transform": True,
            "source_stability_verified": True,
            "transactional_output_bundle": True,
            "previous_valid_outputs_preserved_on_failure": True,
            "row_order_inference_used": False,
            "nearest_fill_used": False,
            "measurement_values_written": 0,
            "final_ready": False,
            "fake_data": False,
        }
        _write_json_fsync(stage_manifest, result)
        candidate_payload = {
            "schema_version": 2,
            "slot_id": "height_difference_3",
            "canonical_export_path": str(final_path),
            "canonical_export_sha256": shard_sha,
            "candidate_count": len(first_three),
            "candidates": first_three,
            "measurement_values_written": 0,
            "final_ready": False,
            "fake_data": False,
        }
        _write_json_fsync(stage_candidates, candidate_payload)
        _publish_bundle(
            {final_path: stage_shard, manifest_path: stage_manifest, candidates_path: stage_candidates},
            output_dir,
        )
        return result
    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}_", suffix=".json.tmp", dir=path.parent)
    os.close(fd)
    temp = Path(name)
    try:
        _write_json_fsync(temp, value)
        temp.replace(path)
        _fsync_dir(path.parent)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _validate_query_outputs(output_dir: Path, extraction: dict[str, Any]) -> dict[str, Any]:
    starter_path = output_dir / "starter_three_query_manifest.json"
    summary_path = output_dir / "operation_summary.json"
    if not starter_path.is_file() or not summary_path.is_file():
        raise ValueError("query preparer did not produce both required manifests")
    starter = json.loads(starter_path.read_text(encoding="utf-8-sig"))
    summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    if starter.get("slot_id") != "height_difference_3" or starter.get("starter_candidate_count") != 3:
        raise ValueError("starter manifest identity/count mismatch")
    if starter.get("canonical_export_sha256") != extraction.get("export_sha256"):
        raise ValueError("starter manifest is not bound to the current canonical shard hash")
    if summary.get("selected_candidates") != 3:
        raise ValueError("operation summary candidate count mismatch")
    return {
        "starter_manifest_sha256": sha256_file(starter_path),
        "operation_summary_sha256": sha256_file(summary_path),
        "starter_candidate_count": 3,
        "canonical_export_sha256": extraction["export_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--query-preparer", type=Path)
    parser.add_argument("--query-preparer-timeout", type=int, default=180)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    if args.query_preparer_timeout < 1:
        raise ValueError("query-preparer-timeout must be positive")
    if not args.source_geojson.is_file():
        raise FileNotFoundError(args.source_geojson)
    output_dir = args.output_dir.resolve()
    result = stream_extract(args.source_geojson.resolve(), output_dir)
    if args.query_preparer:
        query_script = args.query_preparer.resolve()
        if not query_script.is_file():
            raise FileNotFoundError(query_script)
        cmd = [sys.executable, str(query_script), "--input", result["export_path"], "--output-dir", str(output_dir)]
        if args.no_network:
            cmd.append("--no-network")
        try:
            completed = subprocess.run(
                cmd, text=True, capture_output=True, check=False, timeout=args.query_preparer_timeout
            )
            receipt = {
                "schema_version": 2,
                "command": cmd,
                "returncode": completed.returncode,
                "stdout": completed.stdout[-12000:],
                "stderr": completed.stderr[-12000:],
                "timed_out": False,
                "canonical_export_sha256": result["export_sha256"],
            }
        except subprocess.TimeoutExpired as exc:
            receipt = {
                "schema_version": 2,
                "command": cmd,
                "returncode": None,
                "stdout": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
                "stderr": (exc.stderr or "")[-12000:] if isinstance(exc.stderr, str) else "",
                "timed_out": True,
                "canonical_export_sha256": result["export_sha256"],
            }
            _atomic_json(output_dir / "query_preparer_execution.json", receipt)
            raise RuntimeError("query preparer timed out") from exc
        if completed.returncode == 0:
            receipt["validated_outputs"] = _validate_query_outputs(output_dir, result)
        _atomic_json(output_dir / "query_preparer_execution.json", receipt)
        if completed.returncode != 0:
            raise RuntimeError("query preparer failed; see query_preparer_execution.json")
    print(json.dumps({"ok": True, "shard_rows": result["shard_rows_exported"], "first_three": result["first_three_explicit_rows"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
