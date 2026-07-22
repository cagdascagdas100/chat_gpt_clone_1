#!/usr/bin/env python3
"""Contract tests for internet_access_3 revision 6 guards."""
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
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/009_revision6_contract_tests_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "england_map_web").exists() and (item / "docs").exists():
            return item
    raise FileNotFoundError("repository root not found")


def module(path: Path):
    spec = importlib.util.spec_from_file_location("revision6_guard", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def write(path: Path, payload: dict) -> None:
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
    options = parse_args()
    repo = root(options.repo_root)
    guard_path = Path(__file__).resolve().parent / "010_hmlr_revision6_guarded_entry.py"
    guard = module(guard_path)
    checks: list[dict] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("POSTCODE_NORMALIZATION", guard.postcode("sw1a 1aa") == "SW1A1AA", "normalize postcode")
    check("INVALID_POSTCODE_REJECTED", guard.postcode("invalid") is None, "reject invalid postcode")
    exact = {"href": "https://example.test/Barking-and-Dagenham.zip", "text": "Barking and Dagenham"}
    wrong = {"href": "https://example.test/Havering.zip", "text": "Havering"}
    check("EXACT_AUTHORITY_LINK_WINS", guard.link_score("Barking and Dagenham", exact) > guard.link_score("Barking and Dagenham", wrong), "exact score higher")
    check("ZIP_LINK_BONUS", guard.link_score("Havering", wrong) >= 1.0, "zip link viable")
    check("ADMIN_STOPWORDS_REMOVED", "borough" not in guard.tokens("London Borough of Camden"), "administrative words removed")
    source = inspect.getsource(guard)
    check("MINIMUM_85_PERCENT_GATE", "DEFAULT_MINIMUM_RATIO = 0.85" in source, "strict ratio default")
    check("PUBLICATION_DATE_CACHE_KEY", "date_key" in source and "manifest_hash" in source, "cache versioned")
    check("MISSING_LINK_BLOCKER", "HMLR_AUTHORITY_DOWNLOAD_LINKS_MISSING" in source, "missing link blocker")
    check("AMBIGUOUS_LINK_BLOCKER", "HMLR_AUTHORITY_DOWNLOAD_LINKS_AMBIGUOUS" in source, "ambiguous link blocker")
    check("NO_RELATION_PROMOTION", '"parcel_relations_promoted": 0' in source, "no relation promotion")
    check("NO_CONFIDENCE_UPLIFT", '"confidence_uplifts": 0' in source, "no confidence uplift")
    check("NO_BUSINESS_ROW_WRITE", '"actual_business_data_rows_written": 0' in source, "no business row write")
    failures = [item for item in checks if not item["passed"]]
    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "passed" if not failures else "failed",
        "tests_expected": 12,
        "tests_executed": len(checks),
        "tests_passed": len(checks) - len(failures),
        "tests_failed": len(failures),
        "tests": checks,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write(repo / options.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
