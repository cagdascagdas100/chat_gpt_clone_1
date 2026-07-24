#!/usr/bin/env python3
"""Contract tests for the HMLR postcode-centroid polygon evidence worker."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
from pathlib import Path

SLOT_ID = "internet_access_3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/007_hmlr_geometry_contract_tests_latest.json")
    return parser.parse_args()


def find_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("hmlr_audit", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    args = parse_args()
    root = find_root(args.repo_root)
    worker_path = Path(__file__).resolve().parent / "008_hmlr_inspire_postcode_centroid_polygon_audit.py"
    worker_source = worker_path.read_text(encoding="utf-8")
    worker = load_module(worker_path)
    ring = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    tests = []

    def check(name: str, condition: bool, detail: str) -> None:
        tests.append({"name": name, "passed": bool(condition), "detail": detail})

    parsed = worker.parse_ring("0 0 10 0 10 10 0 10 0 0")
    check("PARSE_GML_POSLIST", parsed == ring, repr(parsed))
    check("POINT_INSIDE_RING", worker.point_in_ring(5.0, 5.0, ring), "5,5 must be inside")
    check("POINT_OUTSIDE_RING", not worker.point_in_ring(15.0, 5.0, ring), "15,5 must be outside")
    check("INSIDE_DISTANCE_ZERO", worker.distance_to_ring(5.0, 5.0, ring) == 0.0, "inside distance must be zero")
    check("OUTSIDE_DISTANCE_EXACT", round(worker.distance_to_ring(15.0, 5.0, ring), 6) == 5.0, "outside distance must be five")
    check("POSTCODE_NORMALIZATION", worker.postcode("sw1a 1aa") == "SW1A1AA", "postcode normalization")
    check("INVALID_POSTCODE_REJECTED", worker.postcode("not-a-postcode") is None, "invalid postcode must be rejected")
    check(
        "NO_PROMOTION_POLICY_PRESENT",
        '"parcel_relation_promoted": False' in worker_source and '"confidence_raised": False' in worker_source,
        "worker must retain explicit no-promotion and no-confidence-uplift flags",
    )

    failures = [item for item in tests if not item["passed"]]
    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "passed" if not failures else "failed",
        "tests_expected": 8,
        "tests_executed": len(tests),
        "tests_passed": len(tests) - len(failures),
        "tests_failed": len(failures),
        "tests": tests,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False
    }
    atomic_json(root / args.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
