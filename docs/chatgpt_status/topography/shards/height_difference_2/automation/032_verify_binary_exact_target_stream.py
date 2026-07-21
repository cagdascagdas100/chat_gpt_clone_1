#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any

TARGET_ROWS = (30762, 46142, 61522)
CHUNK_SIZES = (4096, 8192, 65536)
EXTRACTOR_REL = "docs/chatgpt_status/topography/shards/height_difference_2/automation/007_extract_three_canonical_candidates.py"


def load_extractor(root: Path):
    path = root / EXTRACTOR_REL
    spec = importlib.util.spec_from_file_location("height_difference_2_binary_extractor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Extractor import failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def feature(row: int, *, parcel: str | None = None, inspire: str | None = None, valid: bool = True, filler: str = "") -> dict[str, Any]:
    lon = -0.2 - row / 10_000_000
    lat = 51.2 + row / 100_000_000
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "row_no": row,
            "parcel_id": parcel or f"parcel_{row}",
            "hmlr_row_id": str(row + 9),
            "hmlr_inspire_id": inspire or f"INSPIRE_{row}",
            "hmlr_area_m2": 100 + row % 7,
            "hmlr_lon": lon,
            "hmlr_lat": lat,
            "hmlr_geometry_accuracy": "4/4" if valid else "2/4",
            "london_authority": "Fixture authority",
            "filler": filler,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    extractor = load_extractor(root)

    filler = 'x{"k":"\\\\\\\""}' * 700
    cases = {
        "positive": [feature(1, filler=filler), feature(30762, filler=filler), feature(40000, filler=filler), feature(46142, filler=filler), feature(61522, filler=filler), feature(70000, filler=filler)],
        "missing": [feature(30762), feature(61522)],
        "invalid": [feature(30762), feature(46142, valid=False), feature(61522)],
        "duplicate_row": [feature(30762), feature(46142), feature(46142, parcel="parcel_duplicate", inspire="INSPIRE_DUPLICATE"), feature(61522)],
        "duplicate_id": [feature(30762, inspire="SAME"), feature(46142, inspire="SAME"), feature(61522, inspire="OTHER")],
        "nearest_only": [feature(30761), feature(46141), feature(61521)],
    }

    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="height_difference_2_binary_stream_") as temp_dir:
        temp = Path(temp_dir)
        for case_name, features in cases.items():
            source = temp / f"{case_name}.geojson"
            raw = json.dumps(
                {
                    "type": "FeatureCollection",
                    "metadata": {"note": "fixture braces { } [ ] and escaped strings"},
                    "features": features,
                    "tail": "hash must include trailing bytes",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            source.write_bytes(raw)
            expected_success = case_name == "positive"
            for chunk_bytes in CHUNK_SIZES:
                payload = extractor.extract(source, chunk_bytes)
                actual_success = payload.get("status") == "THREE_EXACT_CANONICAL_CANDIDATE_SEEDS_EXTRACTED"
                metrics = payload.get("stream_metrics") or {}
                passed = all(
                    [
                        actual_success == expected_success,
                        payload.get("source_sha256") == hashlib.sha256(raw).hexdigest(),
                        metrics.get("parser") == "binary-feature-object-stream-v2",
                        metrics.get("chunk_bytes") == chunk_bytes,
                        metrics.get("full_json_load_avoided") is True,
                        metrics.get("sha256_same_pass") is True,
                        metrics.get("scanned_through_features_array_end") is True,
                        payload.get("nearest_row_fallback_used") is False,
                        payload.get("legacy_point_topography_values_promoted") is False,
                        payload.get("official_polygon_measurements_written") == 0,
                    ]
                )
                checks.append(
                    {
                        "name": f"{case_name}_chunk_{chunk_bytes}",
                        "passed": passed,
                        "status": payload.get("status"),
                        "candidate_seed_count": payload.get("candidate_seed_count"),
                        "source_sha256_matches": payload.get("source_sha256") == hashlib.sha256(raw).hexdigest(),
                        "stream_metrics": metrics,
                    }
                )

    passed_count = sum(1 for check in checks if check["passed"])
    result = {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "attempt_id": "height-difference-2-20260721-020",
        "status": "PASS" if passed_count == len(checks) else "FAIL",
        "passed": passed_count,
        "total": len(checks),
        "target_rows": list(TARGET_ROWS),
        "chunk_sizes": list(CHUNK_SIZES),
        "checks": checks,
        "product_rows_promoted": 0,
        "fixture_only": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": passed_count == len(checks), "passed": passed_count, "total": len(checks)}))
    return 0 if passed_count == len(checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())
