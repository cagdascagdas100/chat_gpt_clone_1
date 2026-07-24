#!/usr/bin/env python3
"""Run the existing conservative migration with the correct Ofcom unable30 semantic.

The legacy token ``unable30`` means percentage of premises unable to receive
30 Mbit/s. It is not the separate Ofcom decent-broadband-unavailable metric.
This wrapper patches the parser before migration, normalises NO_DATA rows, and
blocks on any semantic conflict. It creates no postcode, score or speed value.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
ROWS_EXPECTED = 30761


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--legacy-worker", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/automation/001_migrate_existing_and_close_no_data.py")
    p.add_argument("--output-root", default="england_map_web/data/aays_21_slots/internet_access_3")
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/001_migration_and_no_data_latest.json")
    return p.parse_args()


def find_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("internet_access_3_legacy_migration", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def legacy_unable30(raw: Any) -> float | None:
    if not isinstance(raw, str):
        return None
    match = re.search(r"(?:^|;)\s*unable30\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*%?", raw, flags=re.I)
    if not match:
        return None
    value = float(match.group(1))
    return value if 0.0 <= value <= 100.0 else None


def enforce_semantics(rows: list[dict[str, Any]], features: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) != ROWS_EXPECTED or len(features) != ROWS_EXPECTED:
        raise ValueError(f"wrong migrated row count rows={len(rows)} features={len(features)}")
    conflicts: list[dict[str, Any]] = []
    corrected = 0
    no_data_normalised = 0
    for row, feature in zip(rows, features):
        props = feature.get("properties") or {}
        raw = row.get("legacy_internet_level_value")
        expected = legacy_unable30(raw)
        for target in (row, props):
            if "unable_30mbps_pct" not in target:
                target["unable_30mbps_pct"] = expected
                if expected is None:
                    no_data_normalised += 1
            if target.get("decent_broadband_unavailable_pct") is not None:
                conflicts.append({"row_no": row.get("row_no"), "code": "DECENT_BROADBAND_FIELD_MUST_REMAIN_NULL_FOR_LEGACY_UNABLE30"})
                target["decent_broadband_unavailable_pct"] = None
        actual = row.get("unable_30mbps_pct")
        if expected is not None:
            if actual is None or abs(float(actual) - expected) > 1e-9:
                conflicts.append({"row_no": row.get("row_no"), "code": "UNABLE30_VALUE_MISMATCH", "expected": expected, "actual": actual})
            else:
                corrected += 1
        props.update(row)
        feature["properties"] = props
    return {
        "rows_checked": len(rows),
        "legacy_unable30_values_verified": corrected,
        "no_data_or_absent_values_normalised": no_data_normalised,
        "semantic_conflicts": conflicts,
        "passed": not conflicts,
    }


def main() -> int:
    args = parse_args()
    root = find_root(args.repo_root)
    worker_path = root / args.legacy_worker
    output_root = root / args.output_root
    runner_output = root / args.runner_output
    worker = load_module(worker_path)
    worker.LEGACY_PERCENT_KEYS["unable30"] = "unable_30mbps_pct"
    worker.CALCULATION_VERSION = "legacy-postcode-proxy-migration-v2-unable30-corrected-score-deferred"

    old_argv = sys.argv[:]
    try:
        sys.argv = [str(worker_path), "--repo-root", str(root)]
        exit_code = int(worker.main())
    finally:
        sys.argv = old_argv
    if exit_code != 0:
        return exit_code

    rows_path = output_root / "internet_rows_latest.json"
    geojson_path = output_root / "internet_rows_latest.geojson"
    validation_path = output_root / "migration_validation_latest.json"
    rows = load_json(rows_path)
    geojson = load_json(geojson_path)
    features = geojson.get("features") if isinstance(geojson, dict) else None
    if not isinstance(rows, list) or not isinstance(features, list):
        raise ValueError("migration outputs are not valid row and GeoJSON collections")
    semantic = enforce_semantics(rows, features)
    summary = load_json(validation_path)
    summary["schema_version"] = max(2, int(summary.get("schema_version", 1)))
    summary["semantic_validation"] = semantic
    summary["calculation_version"] = worker.CALCULATION_VERSION
    summary["output_semantics"] = "POSTCODE_LEVEL_PROXY_OR_NO_DATA_UNABLE30_CORRECTED"
    blockers = list((summary.get("validation") or {}).get("blockers") or [])
    if not semantic["passed"]:
        blockers.append(f"LEGACY_UNABLE30_SEMANTIC_CONFLICTS:{len(semantic['semantic_conflicts'])}")
    summary.setdefault("validation", {})["blockers"] = sorted(set(blockers))
    summary["validation"]["passed"] = not blockers
    summary["state"] = "runtime_validation_passed" if not blockers else "blocked"
    summary["final_ready"] = False
    summary["fake_data"] = False
    summary["db_write"] = False
    summary["migration"] = False
    summary["production_deploy"] = False

    atomic_json(rows_path, rows)
    atomic_json(geojson_path, geojson)
    atomic_json(validation_path, summary)
    atomic_json(runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
