#!/usr/bin/env python3
"""Run deterministic contract tests for internet_access_3 workers."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
TASK_ID = "aays1-internet-access-3-worker-contract-tests-20260722"
DEFAULT_RUNNER_OUTPUT = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_3/runner_outputs/000_worker_contract_tests_latest.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--runner-output", default=DEFAULT_RUNNER_OUTPUT)
    return parser.parse_args()


def find_repo_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found; pass --repo-root")


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    args = parse_args()
    root = find_repo_root(args.repo_root)
    automation = Path(__file__).resolve().parent
    migration = load_module(automation / "001_migrate_existing_and_close_no_data.py", "ia3_migration")
    revalidation = load_module(automation / "002_ofcom_2026_sample_revalidation.py", "ia3_revalidation")
    ons = load_module(automation / "005_onspd_2026_centroid_crosscheck.py", "ia3_onspd")
    semantic = load_module(automation / "006_normalize_legacy_unable30_semantics.py", "ia3_semantic")

    tests: list[dict[str, Any]] = []

    parsed, errors = migration.parse_legacy_value(
        "Very High; postcode=RM82LL; gigabit=100.0%; ufbb100=100.0%; sfbb=100.0%; unable30=0.0%"
    )
    tests.append({
        "name": "legacy_value_parses_required_fields",
        "passed": not errors and parsed["postcode"] == "RM82LL",
        "detail": {"errors": errors, "postcode": parsed.get("postcode")},
    })

    row = {
        "row_no": 61523,
        "legacy_internet_level_value": "x",
        "decent_broadband_unavailable_pct": 17.5,
        "blockers": [],
    }
    changed, conflict = semantic.normalize_row(row)
    tests.append({
        "name": "unable30_moves_to_30mbps_field",
        "passed": (
            changed and not conflict
            and row.get("unable_30mbps_pct") == 17.5
            and row.get("decent_broadband_unavailable_pct") is None
        ),
        "detail": row,
    })

    tests.append({
        "name": "postcode_normalization",
        "passed": (
            revalidation.normalize_postcode("rm8 2ll") == "RM82LL"
            and revalidation.normalize_postcode("not-a-postcode") is None
            and ons.normalize_postcode("SW1A 1AA") == "SW1A1AA"
        ),
        "detail": {},
    })

    distance = ons.haversine_metres(-0.1276, 51.5072, -0.1276, 51.5072)
    tests.append({
        "name": "haversine_identity",
        "passed": abs(distance) < 0.0001,
        "detail": {"distance_m": distance},
    })

    tests.append({
        "name": "distance_bucket_boundaries",
        "passed": (
            ons.distance_bucket(100) == "WITHIN_100M_POSTCODE_CENTROID"
            and ons.distance_bucket(250) == "WITHIN_250M_POSTCODE_CENTROID"
            and ons.distance_bucket(1001) == "OVER_1KM_FROM_POSTCODE_CENTROID_REVIEW_REQUIRED"
        ),
        "detail": {},
    })

    tests.append({
        "name": "onspd_required_fields_include_coordinates",
        "passed": {"pcd7", "lat", "long", "gridind"}.issubset(ons.REQUIRED_SERVICE_FIELDS),
        "detail": {"required_fields": sorted(ons.REQUIRED_SERVICE_FIELDS)},
    })

    failed = [test for test in tests if not test["passed"]]
    summary = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "state": "tests_passed" if not failed else "tests_failed",
        "result": {
            "tests_total": len(tests),
            "tests_passed": len(tests) - len(failed),
            "tests_failed": len(failed),
            "tests": tests,
        },
        "validation": {
            "passed": not failed,
            "failed_test_names": [test["name"] for test in failed],
        },
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_write_json(root / args.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
