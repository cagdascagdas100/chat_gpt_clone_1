#!/usr/bin/env python3
"""Contract tests for stratified internet_access_3 candidate selection."""
from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import os
import tempfile
from pathlib import Path

SLOT_ID = "internet_access_3"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/018_stratified_candidate_sampler_tests_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "docs").exists() and (item / "england_map_web").exists():
            return item
    raise FileNotFoundError("repository root not found")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("stratified_sampler", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def row(row_no: int, authority: str, pc: str, band: str, unable: float) -> dict:
    return {
        "row_no": row_no,
        "canonical_program_parcel_id": f"parcel_{row_no}",
        "hmlr_inspire_id": str(10000000 + row_no),
        "postcode": pc,
        "london_authority": authority,
        "internet_quality_band": band,
        "unable_30mbps_pct": unable,
        "internet_status": "verified_existing_postcode_proxy",
    }


def main() -> int:
    args = parse_args()
    repo = root(args.repo_root)
    worker = load_module(Path(__file__).resolve().parent / "022_stratified_candidate_sampler.py")
    tests: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        tests.append({"name": name, "passed": bool(condition), "detail": detail})

    check("POSTCODE_NORMALIZATION", worker.postcode("sw1a 1aa") == "SW1A1AA", str(worker.postcode("sw1a 1aa")))
    check("POSTCODE_AREA", worker.postcode_area("EC1A 1BB") == "EC", str(worker.postcode_area("EC1A 1BB")))
    check("INVALID_POSTCODE_REJECTED", worker.postcode("invalid") is None, str(worker.postcode("invalid")))
    buckets = [worker.unable_bucket(value) for value in [0, 1, 25, 75, 100, None]]
    check("UNABLE_BUCKETS", buckets == ["0", "0_to_10", "10_to_50", "50_to_100", "100", "missing"], repr(buckets))
    sample_rows = [
        row(1, "A", "SW1A1AA", "Very High", 0),
        row(2, "A", "SW1A2AA", "Very High", 0),
        row(3, "B", "EC1A1BB", "Low", 25),
        row(4, "C", "E11AA", "Very Low", 100),
        row(5, "D", "N11AA", "Medium", 75),
    ]
    selected = worker.round_robin(sample_rows, 4)
    check("ROUND_ROBIN_SIZE", len(selected) == 4, str(len(selected)))
    check("ROUND_ROBIN_UNIQUE", len({item["row_no"] for item in selected}) == len(selected), repr([item["row_no"] for item in selected]))
    check("ROUND_ROBIN_DETERMINISTIC", [item["row_no"] for item in selected] == [item["row_no"] for item in worker.round_robin(sample_rows, 4)], repr([item["row_no"] for item in selected]))
    dist = worker.distribution(sample_rows)
    check("DISTRIBUTION_COUNTS", dist["authority_count"] == 4 and dist["postcode_area_count"] == 4 and dist["quality_band_count"] == 4, repr(dist))
    source = inspect.getsource(worker)
    check("NO_REVALIDATION_CLAIM", '"official_source_rows_revalidated": 0' in source and '"status": "PREPARED_NOT_REVALIDATED"' in source, "prepared-only semantics")
    check("NO_PROMOTION_OR_UPLIFT", '"parcel_relations_promoted": 0' in source and '"confidence_uplifts": 0' in source, "no promotion")
    check("SAFETY_FLAGS", all(token in source for token in ['"fake_data": False', '"db_write": False', '"migration": False', '"production_deploy": False']), "safety flags")
    failures = [item for item in tests if not item["passed"]]
    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "passed" if not failures else "failed",
        "tests_expected": 10,
        "tests_executed": len(tests),
        "tests_passed": len(tests) - len(failures),
        "tests_failed": len(failures),
        "tests": tests,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_json(repo / args.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
