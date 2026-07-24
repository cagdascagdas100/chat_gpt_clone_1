#!/usr/bin/env python3
"""Run Ofcom or ONSPD validation on exact stratified row identities.

The adapter additionally requires a high exact-postcode match ratio. A child worker
exit code alone is not accepted as sufficient evidence.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
import tempfile
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
    p.add_argument("--minimum-match-ratio", type=float, default=0.95)
    return p.parse_args()


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_json(path: Path, payload: Any) -> None:
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


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    options = args()
    if not 0 < options.minimum_match_ratio <= 1:
        raise ValueError("minimum-match-ratio must be within (0,1]")
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
    child_output = (
        "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/002_ofcom_2026_sample_revalidation_latest.json"
        if options.mode == "ofcom"
        else "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/004_onspd_2026_centroid_crosscheck_latest.json"
    )
    adapter_output = (
        "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/021_stratified_ofcom_adapter_latest.json"
        if options.mode == "ofcom"
        else "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/022_stratified_onspd_adapter_latest.json"
    )
    web_output = (
        "england_map_web/data/aays_21_slots/internet_access_3/stratified_ofcom_adapter_latest.json"
        if options.mode == "ofcom"
        else "england_map_web/data/aays_21_slots/internet_access_3/stratified_onspd_adapter_latest.json"
    )
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
        child_exit = int(module.main())
    finally:
        module.deterministic_sample = original_sampler
        sys.argv = original_argv
    child = load(repo / child_output) if (repo / child_output).exists() else {}
    result = child.get("result") or {}
    selected_count = int(result.get("sample_rows_selected") or 0)
    match_field = "official_postcodes_found" if options.mode == "ofcom" else "onspd_exact_postcodes_found"
    matches = int(result.get(match_field) or 0)
    minimum = math.ceil(options.sample_size * options.minimum_match_ratio)
    blockers: list[str] = []
    if child_exit != 0:
        blockers.append(f"{options.mode.upper()}_CHILD_EXIT_NONZERO:{child_exit}")
    if selected_count != options.sample_size:
        blockers.append(f"{options.mode.upper()}_EXACT_MANIFEST_SAMPLE_COUNT_MISMATCH:{selected_count}!={options.sample_size}")
    if matches < minimum:
        blockers.append(f"{options.mode.upper()}_EXACT_POSTCODE_MATCH_RATIO_BELOW_GATE:{matches}<{minimum}")
    passed = not blockers
    summary = {
        "schema_version": 1,
        "task_id": f"aays1-internet-access-3-stratified-{options.mode}-adapter-20260722",
        "slot_id": SLOT_ID,
        "mode": options.mode,
        "state": "runtime_validation_passed" if passed else "blocked",
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "guard": {
            "exact_manifest_row_identity_required": True,
            "sample_size_required": options.sample_size,
            "minimum_match_ratio": options.minimum_match_ratio,
            "minimum_matches_required": minimum,
        },
        "child_execution": {"script": script_name, "exit_code": child_exit, "runner_output": child_output},
        "result": {
            "sample_rows_selected": selected_count,
            "exact_postcodes_found": matches,
            "parcel_relations_promoted": 0,
            "confidence_uplifts": 0,
        },
        "validation": {"passed": passed, "blockers": blockers},
        "output_semantics": "EXACT_STRATIFIED_POSTCODE_VALIDATION_ADAPTER",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_json(repo / adapter_output, summary)
    atomic_json(repo / web_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
