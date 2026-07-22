#!/usr/bin/env python3
"""Contract tests for corrected internet_access_3 migration semantics."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
from pathlib import Path

SLOT_ID = "internet_access_3"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/011_corrected_migration_contract_tests_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "england_map_web").exists() and (item / "docs").exists():
            return item
    raise FileNotFoundError("repository root not found")


def module(path: Path):
    spec = importlib.util.spec_from_file_location("corrected_migration", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


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
    repo = root(args.repo_root)
    worker = module(Path(__file__).resolve().parent / "014_migrate_existing_semantics_corrected.py")
    tests: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        tests.append({"name": name, "passed": bool(condition), "detail": detail})

    check("PARSE_UNABLE30_INTEGER", worker.legacy_unable30("Very High; unable30=17%") == 17.0, "integer percent")
    check("PARSE_UNABLE30_DECIMAL", worker.legacy_unable30("Very High; unable30=17.9%") == 17.9, "decimal percent")
    check("REJECT_UNABLE30_OUT_OF_RANGE", worker.legacy_unable30("unable30=101%") is None, "out of range")
    check("ABSENT_UNABLE30_IS_NONE", worker.legacy_unable30("Very High; postcode=RM70YL") is None, "absent value")

    row = {"row_no": 61523, "legacy_internet_level_value": "Very High; unable30=12.5%", "unable_30mbps_pct": 12.5, "decent_broadband_unavailable_pct": None}
    feature = {"type": "Feature", "geometry": None, "properties": dict(row)}
    rows = [dict(row) for _ in range(worker.ROWS_EXPECTED)]
    features = [{"type": "Feature", "geometry": None, "properties": dict(row)} for _ in range(worker.ROWS_EXPECTED)]
    result = worker.enforce_semantics(rows, features)
    check("CORRECT_VALUE_ACCEPTED", result["passed"], str(result))
    check("ALL_ROWS_CHECKED", result["rows_checked"] == worker.ROWS_EXPECTED, str(result["rows_checked"]))
    check("DECENT_FIELD_REMAINS_NULL", all(item.get("decent_broadband_unavailable_pct") is None for item in rows), "separate Ofcom metric")
    check("NO_PROMOTION_OR_SCORE_FIELDS", "automatic" not in Path(worker.__file__).read_text(encoding="utf-8").lower() and "quality_scores_created" not in Path(worker.__file__).read_text(encoding="utf-8").lower(), "guarded migration only")

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
    atomic_json(repo / args.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
