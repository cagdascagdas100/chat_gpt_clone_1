#!/usr/bin/env python3
"""Contract tests for official NSUL/ONSUD ArcGIS release discovery."""
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
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/016_ons_uprn_arcgis_release_discovery_tests_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "docs").exists() and (item / "england_map_web").exists():
            return item
    raise FileNotFoundError("repository root not found")


def module(path: Path):
    spec = importlib.util.spec_from_file_location("release_discovery", path)
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


def main() -> int:
    args = parse_args()
    repo = root(args.repo_root)
    worker = module(Path(__file__).resolve().parent / "020_ons_uprn_arcgis_release_discovery.py")
    product = {
        "product_id": "nsul",
        "canonical_name": "National Statistics UPRN Lookup",
        "required_title_tokens": ["national statistics uprn lookup", "may 2026"],
        "excluded_title_tokens": ["user guide", "metadata", "overview", "web map", "dashboard"],
        "minimum_data_item_size_bytes": 1_000_000,
    }
    tests: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        tests.append({"name": name, "passed": bool(condition), "detail": detail})

    data = {"id": "data", "title": "National Statistics UPRN Lookup (May 2026) (Epoch 126)", "owner": "ONS_Geography", "type": "CSV Collection", "size": 500_000_000, "tags": ["ONS Geography Open Data", "NSUL"]}
    guide = {"id": "guide", "title": "National Statistics UPRN Lookup (May 2026) (Epoch 126) User Guide", "owner": "ONS_Geography", "type": "Document Link", "size": 416_000, "tags": ["User Guide"]}
    old = {"id": "old", "title": "National Statistics UPRN Lookup (December 2025) (Epoch 123)", "owner": "ONS_Geography", "type": "CSV Collection", "size": 470_000_000, "tags": ["NSUL"]}
    metadata = {"id": "metadata", "title": "National Statistics UPRN Lookup (May 2026) Metadata", "owner": "ONS_Geography", "type": "Document Link", "size": 2_000_000, "tags": ["Metadata"]}
    data_score, data_reasons = worker.item_score(data, product)
    guide_score, _ = worker.item_score(guide, product)
    old_score, _ = worker.item_score(old, product)
    metadata_score, _ = worker.item_score(metadata, product)
    check("DATA_PACKAGE_ELIGIBLE", data_score >= 100, str((data_score, data_reasons)))
    check("USER_GUIDE_EXCLUDED", guide_score <= -1000, str(guide_score))
    check("OLDER_RELEASE_EXCLUDED", old_score <= -1000, str(old_score))
    check("METADATA_EXCLUDED", metadata_score <= -1000, str(metadata_score))
    check("ONS_AUTHORITY_SIGNAL", "ONS_AUTHORITY_SIGNAL" in data_reasons, repr(data_reasons))
    check("MINIMUM_DATA_SIZE_SIGNAL", "MINIMUM_DATA_SIZE_MET" in data_reasons, repr(data_reasons))
    check("NORMALIZATION_STABLE", worker.normalized("ONS UPRN—Directory (May 2026)") == "ons uprn directory may 2026", worker.normalized("ONS UPRN—Directory (May 2026)"))
    source = inspect.getsource(worker)
    check("AMBIGUITY_BLOCKER_PRESENT", "ambiguous_top_score" in source and "TOP_SCORE_AMBIGUOUS" in source, "ambiguity must block")
    check("NO_PROMOTION_POLICY", '"parcel_relations_promoted": 0' in source and '"confidence_uplifts": 0' in source, "no promotion or confidence uplift")
    check("SAFETY_FLAGS_PRESENT", all(token in source for token in ['"fake_data": False', '"db_write": False', '"migration": False', '"production_deploy": False']), "safety flags")
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
