#!/usr/bin/env python3
"""Run Ofcom or ONSPD validation on the exact stratified manifest row identities."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, required=True)
    p.add_argument("--mode", choices=["ofcom", "onspd"], required=True)
    p.add_argument("--manifest", default="england_map_web/data/aays_21_slots/internet_access_3/stratified_candidate_manifest_latest.json")
    p.add_argument("--rows", default="england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json")
    p.add_argument("--sample-size", type=int, default=384)
    return p.parse_args()


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    options = args()
    repo = options.repo_root.expanduser().resolve()
    automation = Path(__file__).resolve().parent
    manifest = load(repo / options.manifest)
    rows = load(repo / options.rows)
    if not isinstance(manifest, list) or len(manifest) != options.sample_size:
        raise ValueError(f"stratified manifest count mismatch: {len(manifest) if isinstance(manifest, list) else 'not-list'}")
    if not isinstance(rows, list) or len(rows) != 30761:
        raise ValueError("full migrated rows missing or wrong count")
    manifest_ids = [int(item["row_no"]) for item in manifest]
    if len(set(manifest_ids)) != len(manifest_ids):
        raise ValueError("duplicate row identities in stratified manifest")
    row_lookup = {int(row["row_no"]): row for row in rows}
    missing = [row_no for row_no in manifest_ids if row_no not in row_lookup]
    if missing:
        raise ValueError(f"manifest rows missing from full migrated rows: {missing[:20]}")
    selected = [row_lookup[row_no] for row_no in manifest_ids]
    script_name = "002_ofcom_2026_sample_revalidation.py" if options.mode == "ofcom" else "005_onspd_2026_centroid_crosscheck.py"
    module = import_module(automation / script_name, f"stratified_{options.mode}")
    original_sampler = module.deterministic_sample
    original_argv = sys.argv[:]

    def exact_manifest_sample(_rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
        if size != options.sample_size:
            raise ValueError(f"adapter sample-size mismatch: {size} != {options.sample_size}")
        return selected

    module.deterministic_sample = exact_manifest_sample
    try:
        sys.argv = [script_name, "--repo-root", str(repo), "--rows", options.rows, "--sample-size", str(options.sample_size)]
        return int(module.main())
    finally:
        module.deterministic_sample = original_sampler
        sys.argv = original_argv


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
