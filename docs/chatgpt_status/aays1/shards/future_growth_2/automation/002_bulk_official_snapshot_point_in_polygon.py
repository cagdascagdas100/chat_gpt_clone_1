#!/usr/bin/env python3
"""Download official Planning Data snapshots and test canonical AAYS points.

This runner fails closed:
- only allow-listed official hosts are accepted;
- downloads are atomic and SHA-256 recorded;
- missing geospatial dependencies produce TOOLCHAIN_MISSING;
- listed-building point data is never treated as an affected-area polygon;
- no future-growth score or confidence is emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTINUATION_KEY = "5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462"
ALLOWED_HOSTS = {
    "files.planning.data.gov.uk",
    "www.planning.data.gov.uk",
    "services.arcgis.com",
    "gis.lambeth.gov.uk",
}
USER_AGENT = "AAYS-future-growth-2-bulk-official/1.0"

ROWS = [
    {"row_no": 30762, "parcel_id": "parcel_30762", "lpa": "Enfield", "lon": -0.0407406, "lat": 51.6769078},
    {"row_no": 46142, "parcel_id": "parcel_46142", "lpa": "Havering", "lon": 0.1928191, "lat": 51.5931140},
    {"row_no": 61522, "parcel_id": "parcel_61522", "lpa": "Lambeth", "lon": -0.1392630, "lat": 51.4153374},
]

DATASETS = [
    {"slug": "brownfield-land", "quality": "AUTHORITATIVE_WITH_COVERAGE_WARNING", "geometry": "POLYGON"},
    {"slug": "green-belt", "quality": "MHCLG_MIXED_SNAPSHOT", "geometry": "POLYGON"},
    {"slug": "flood-risk-zone", "quality": "AUTHORITATIVE_STALE_INDICATOR", "geometry": "POLYGON"},
    {"slug": "conservation-area", "quality": "MIXED_INCOMPLETE_DUPLICATES", "geometry": "POLYGON"},
    {"slug": "local-plan-boundary", "quality": "MHCLG_CREATED_SCOPE_ONLY", "geometry": "POLYGON"},
    {"slug": "article-4-direction-area", "quality": "MIXED_INCOMPLETE", "geometry": "POLYGON"},
    {"slug": "tree-preservation-zone", "quality": "MIXED_SMALL_PROVIDER_GROUP", "geometry": "POLYGON"},
    {"slug": "listed-building", "quality": "POINT_ONLY_MIXED", "geometry": "POINT_ONLY"},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_official(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"URL_NOT_ALLOWLISTED: {url}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download_atomic(url: str, target: Path, timeout: int, retries: int) -> dict[str, Any]:
    ensure_official(url)
    target.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, retries + 2):
        part = target.with_suffix(target.suffix + f".part.{os.getpid()}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as response, part.open("wb") as out:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    out.write(block)
                out.flush()
                os.fsync(out.fileno())
            os.replace(part, target)
            return {
                "status": "DOWNLOADED",
                "attempts": attempt,
                "bytes": target.stat().st_size,
                "sha256": sha256_file(target),
                "path": str(target),
                "url": url,
            }
        except Exception as exc:
            last_error = exc
            try:
                part.unlink(missing_ok=True)
            except Exception:
                pass
            if attempt <= retries:
                time.sleep(min(8, attempt * 2))
    return {
        "status": "DOWNLOAD_FAILED",
        "attempts": retries + 1,
        "bytes": 0,
        "sha256": None,
        "path": str(target),
        "url": url,
        "error": f"{type(last_error).__name__}: {last_error}",
    }


def detect_backend() -> str | None:
    if importlib.util.find_spec("pyogrio") and importlib.util.find_spec("shapely"):
        return "pyogrio"
    if importlib.util.find_spec("geopandas") and importlib.util.find_spec("shapely"):
        return "geopandas"
    return None


def read_bbox(path: Path, lon: float, lat: float, backend: str):
    bbox = (lon, lat, lon, lat)
    if backend == "pyogrio":
        import pyogrio
        return pyogrio.read_dataframe(path, bbox=bbox)
    import geopandas as gpd
    return gpd.read_file(path, bbox=bbox)


def intersect_snapshot(path: Path, row: dict[str, Any], dataset: dict[str, str], backend: str | None) -> dict[str, Any]:
    base = {
        "row_no": row["row_no"],
        "parcel_id": row["parcel_id"],
        "lpa": row["lpa"],
        "dataset": dataset["slug"],
        "quality_class": dataset["quality"],
        "source_snapshot": str(path),
        "future_growth_score": None,
        "confidence_pct": 0,
        "data_status": "NO_DATA",
        "parcel_bound": False,
    }
    if dataset["geometry"] == "POINT_ONLY":
        return {**base, "status": "POINT_ONLY_NOT_BINDING", "match_count": 0,
                "note": "Listed-building data is a point within a building and cannot establish affected extent."}
    if not path.exists():
        return {**base, "status": "SNAPSHOT_MISSING", "match_count": 0}
    if backend is None:
        return {**base, "status": "TOOLCHAIN_MISSING", "match_count": 0,
                "note": "Install pyogrio+shapely or geopandas+shapely on the existing canonical runner."}
    try:
        from shapely.geometry import Point
        frame = read_bbox(path, row["lon"], row["lat"], backend)
        if frame.empty:
            return {**base, "status": "NO_INTERSECTION_IN_THIS_DATASET", "match_count": 0,
                    "note": "Dataset-specific zero only; not proof that no planning constraints exist."}
        point = Point(row["lon"], row["lat"])
        matched = frame[frame.geometry.intersects(point)]
        records = []
        for _, item in matched.head(50).iterrows():
            record = {}
            for key, value in item.items():
                if key == "geometry":
                    continue
                if value is None or isinstance(value, (str, int, float, bool)):
                    record[str(key)] = value
                else:
                    record[str(key)] = str(value)
            records.append(record)
        return {
            **base,
            "status": "OFFICIAL_POINT_INTERSECTION_FOUND" if len(matched) else "NO_INTERSECTION_IN_THIS_DATASET",
            "match_count": int(len(matched)),
            "records": records,
            "point_intersection_proven": bool(len(matched)),
            "note": "Primary local-authority cross-check remains required before scoring." if len(matched) else
                    "Dataset-specific zero only; not proof that no planning constraints exist.",
        }
    except Exception as exc:
        return {**base, "status": "SPATIAL_READ_FAILED", "match_count": 0,
                "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--download-only", action="store_true")
    args = parser.parse_args()

    backend = detect_backend()
    downloads = []
    intersections = []
    for dataset in DATASETS:
        url = f"https://files.planning.data.gov.uk/dataset/{dataset['slug']}.geojson"
        target = args.cache_dir / f"{dataset['slug']}.geojson"
        result = download_atomic(url, target, args.timeout, args.retries)
        result["dataset"] = dataset["slug"]
        result["quality_class"] = dataset["quality"]
        downloads.append(result)
        if not args.download_only:
            for row in ROWS:
                intersections.append(intersect_snapshot(target, row, dataset, backend))

    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "continuation_key": CONTINUATION_KEY,
        "generated_at": utc_now(),
        "backend": backend or "TOOLCHAIN_MISSING",
        "downloads": downloads,
        "intersections": intersections,
        "score_policy": "No score emitted; official point intersections require primary-source cross-check.",
        "exact_parcel_bound_rows": 0,
        "scored_business_rows": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_name = tmp.name
    os.replace(temp_name, args.output)
    print(json.dumps({
        "output": str(args.output),
        "downloaded": sum(x["status"] == "DOWNLOADED" for x in downloads),
        "download_failed": sum(x["status"] != "DOWNLOADED" for x in downloads),
        "point_intersections": sum(x.get("match_count", 0) for x in intersections),
        "backend": payload["backend"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
