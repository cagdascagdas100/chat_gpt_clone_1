#!/usr/bin/env python3
"""Fail-closed exact canonical Point extractor for height_difference_2.

This script writes no elevation, polygon, database, migration, deployment or
business result. It only extracts three canonical Point seeds after validating
the exact Git blob identity, feature count, ordinal alignment and geometry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any
from urllib.request import Request, urlopen

SLOT_ID = "height_difference_2"
SCRIPT_VERSION = "1.0-fail-closed"
SOURCE_BRANCH = "codex/aays-single-runner-v5-20260706"
SOURCE_PATH = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
SOURCE_URL = (
    "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/"
    + SOURCE_BRANCH + "/" + SOURCE_PATH
)
EXPECTED_GIT_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_FEATURE_COUNT = 92283
TARGET_ROWS = (30762, 46142, 61522)
MAX_SOURCE_BYTES = 1_000_000_000
USER_AGENT = "AAYS-height-difference-2-seed-extractor/1.0"


class EvidenceError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def download_to_temp(url: str) -> Path:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json,application/json"})
    fd, name = tempfile.mkstemp(prefix="height_difference_2_", suffix=".geojson")
    os.close(fd)
    path = Path(name)
    total = 0
    try:
        with urlopen(request, timeout=300) as response, path.open("wb") as handle:
            status = getattr(response, "status", 200)
            if status != 200:
                raise EvidenceError(f"HTTP_{status}")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_SOURCE_BYTES:
                    raise EvidenceError(f"SOURCE_TOO_LARGE:{total}")
                handle.write(chunk)
        if total == 0:
            raise EvidenceError("EMPTY_SOURCE")
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def require_transformer() -> Any:
    try:
        from pyproj import Transformer  # type: ignore
    except Exception as exc:
        raise EvidenceError(f"PYPROJ_REQUIRED:{exc}") from exc
    return Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def validate_point(feature: Any, row_no: int, transformer: Any) -> dict[str, Any]:
    expected_id = f"parcel_{row_no}"
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise EvidenceError(f"FEATURE_INVALID:{row_no}")
    properties = feature.get("properties")
    if not isinstance(properties, dict) or properties.get("security_parcel_id") != expected_id:
        raise EvidenceError(f"ORDINAL_ID_MISMATCH:{row_no}")
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        raise EvidenceError(f"POINT_REQUIRED:{expected_id}")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        raise EvidenceError(f"POINT_COORDINATES_INVALID:{expected_id}")
    longitude, latitude = float(coordinates[0]), float(coordinates[1])
    if not (math.isfinite(longitude) and math.isfinite(latitude)):
        raise EvidenceError(f"NON_FINITE_POINT:{expected_id}")
    if not (-9.0 <= longitude <= 3.0 and 49.0 <= latitude <= 61.0):
        raise EvidenceError(f"POINT_OUTSIDE_PLAUSIBLE_GB_RANGE:{expected_id}")
    easting, northing = transformer.transform(longitude, latitude)
    if not (math.isfinite(easting) and math.isfinite(northing)):
        raise EvidenceError(f"NON_FINITE_BNG:{expected_id}")
    if not (0.0 <= easting <= 700000.0 and 0.0 <= northing <= 1300000.0):
        raise EvidenceError(f"BNG_OUTSIDE_PLAUSIBLE_RANGE:{expected_id}")
    return {
        "row_no": row_no,
        "parcel_id": expected_id,
        "longitude": longitude,
        "latitude": latitude,
        "bng_easting_m": round(easting, 3),
        "bng_northing_m": round(northing, 3),
        "source_geometry_type": "Point",
        "hmlr_inspire_id": None,
        "height_min_m": None,
        "height_max_m": None,
        "height_difference_m": None,
        "result_confidence_percent": None,
        "business_row": False,
    }


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "england_map_web/data/aays_21_slots/height_difference_2/"
            "canonical_points_increment_031.runtime.json"
        ),
    )
    parser.add_argument("--source-file", type=Path, default=None)
    args = parser.parse_args()

    downloaded = args.source_file is None
    source_path = download_to_temp(SOURCE_URL) if downloaded else args.source_file
    if source_path is None or not source_path.is_file():
        raise EvidenceError("SOURCE_FILE_MISSING")
    try:
        observed_sha = git_blob_sha1(source_path)
        if observed_sha != EXPECTED_GIT_BLOB_SHA:
            raise EvidenceError(f"GIT_BLOB_SHA_MISMATCH:{observed_sha}")
        with source_path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
        if document.get("type") != "FeatureCollection":
            raise EvidenceError("FEATURE_COLLECTION_REQUIRED")
        features = document.get("features")
        if not isinstance(features, list) or len(features) != EXPECTED_FEATURE_COUNT:
            raise EvidenceError(f"FEATURE_COUNT_MISMATCH:{len(features) if isinstance(features, list) else 'invalid'}")
        transformer = require_transformer()
        rows = [validate_point(features[row_no - 1], row_no, transformer) for row_no in TARGET_ROWS]
        if len({row["parcel_id"] for row in rows}) != len(TARGET_ROWS):
            raise EvidenceError("TARGET_IDS_NOT_UNIQUE")
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "script_version": SCRIPT_VERSION,
            "generated_at": utc_now(),
            "source_branch": SOURCE_BRANCH,
            "source_path": SOURCE_PATH,
            "source_git_blob_sha": observed_sha,
            "source_feature_count": len(features),
            "target_rows": list(TARGET_ROWS),
            "rows": rows,
            "actual_business_rows_written": 0,
            "official_numeric_rows_written": 0,
            "fake_data": False,
            "final_ready": False,
        }
        atomic_json(args.output, payload)
        print(json.dumps({"ok": True, "output": str(args.output), "row_count": len(rows)}, sort_keys=True))
        return 0
    finally:
        if downloaded:
            source_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
