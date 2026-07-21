#!/usr/bin/env python3
"""Materialize exact source blobs and run the direct-ZIP targeted slot-3 pipeline."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

SLOT_ID = "internet_access_3"
BASE_ENTRYPOINT = "010_materialize_exact_blobs_and_run_slot3.py"
TARGET_ENTRYPOINT = "014_run_slot3_targeted_pipeline.py"
AUTOMATION_RELATIVE = Path(
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_3/automation"
)
REQUIRED_AUTOMATION = (
    "002_extract_slot3_ofcom_2026_candidates.py",
    "003_selftest_slot3_extractor.py",
    "005_stream_extract_slot3_inputs.py",
    "006_selftest_stream_extract_slot3_inputs.py",
    "008_download_validate_run_slot3.py",
    "012_extract_slot3_ofcom_needed_postcodes.py",
    "013_selftest_targeted_postcode_join.py",
    "014_run_slot3_targeted_pipeline.py",
    "016_selftest_targeted_pipeline_wiring.py",
    "017_stream_ofcom_zip_needed_postcodes.py",
    "018_selftest_direct_zip_stream_join.py",
)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_targeted_automation(repo_root: Path, exact_repo_root: Path, base: Any) -> list[dict[str, Any]]:
    source_root = repo_root / AUTOMATION_RELATIVE
    target_root = exact_repo_root / AUTOMATION_RELATIVE
    target_root.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, Any]] = []
    for name in REQUIRED_AUTOMATION:
        source = source_root / name
        if not source.is_file():
            raise base.GateError(f"required targeted automation missing: {source}")
        target = target_root / name
        shutil.copy2(source, target)
        copied.append({"name": name, "sha256": base.sha256_file(target), "bytes": target.stat().st_size})
    return copied


def build_child_command(
    exact_repo_root: Path,
    work_root: Path,
    ofcom_zip: Path | None,
    ofcom_url: str | None,
    retries: int,
    timeout: int,
) -> list[str]:
    script = exact_repo_root / AUTOMATION_RELATIVE / TARGET_ENTRYPOINT
    command = [
        sys.executable,
        str(script),
        "--repo-root",
        str(exact_repo_root),
        "--work-root",
        str(work_root),
        "--download-retries",
        str(retries),
        "--download-timeout-seconds",
        str(timeout),
    ]
    if ofcom_zip is not None:
        command.extend(["--ofcom-zip", str(ofcom_zip.resolve())])
    if ofcom_url:
        command.extend(["--ofcom-url", ofcom_url])
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--git-ref", default="HEAD")
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--ofcom-zip", type=Path)
    parser.add_argument("--ofcom-url")
    parser.add_argument("--download-retries", type=int, default=4)
    parser.add_argument("--download-timeout-seconds", type=int, default=600)
    parser.add_argument("--expected-canonical-blob-sha")
    parser.add_argument("--expected-legacy-blob-sha")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    automation_root = repo_root / AUTOMATION_RELATIVE
    base = load_module(automation_root / BASE_ENTRYPOINT, "internet_access_3_exact_blob_base")
    if not (repo_root / ".git").exists() and not (repo_root / ".git").is_file():
        raise base.GateError(f"repo root is not a Git checkout: {repo_root}")

    expected_canonical = (args.expected_canonical_blob_sha or base.EXPECTED_CANONICAL_BLOB_SHA).lower()
    expected_legacy = (args.expected_legacy_blob_sha or base.EXPECTED_LEGACY_BLOB_SHA).lower()
    work_root = (args.work_root or (repo_root / "outputs/internet_access_3_verified_run")).resolve()
    exact_repo_root = work_root / "exact_git_blob_repo"
    manifest_path = work_root / "internet_access_3_exact_targeted_materialization_latest.json"
    work_root.mkdir(parents=True, exist_ok=True)

    diagnostics: dict[str, Any] = {
        "schema_version": 5,
        "slot_id": SLOT_ID,
        "git_ref": args.git_ref,
        "repo_root": str(repo_root),
        "exact_repo_root": str(exact_repo_root),
        "target_pipeline": TARGET_ENTRYPOINT,
        "join_strategy": "DIRECT_ZIP_STREAM_AREA_PARTITIONED_EXACT_UNIQUENESS_RETAIN_ONLY_NEEDED_SLOT3_POSTCODES",
        "ofcom_csv_extracted_to_disk": False,
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }

    try:
        canonical_resolved = base.resolve_path_blob(repo_root, args.git_ref, base.CANONICAL_REPO_PATH)
        legacy_resolved = base.resolve_path_blob(repo_root, args.git_ref, base.LEGACY_REPO_PATH)
        diagnostics["resolved_blobs"] = {"canonical": canonical_resolved, "legacy_internet": legacy_resolved}
        if canonical_resolved != expected_canonical:
            raise base.GateError(f"canonical blob mismatch: expected {expected_canonical}, found {canonical_resolved}")
        if legacy_resolved != expected_legacy:
            raise base.GateError(f"legacy internet blob mismatch: expected {expected_legacy}, found {legacy_resolved}")

        canonical_target = exact_repo_root / base.CANONICAL_REPO_PATH
        legacy_target = exact_repo_root / base.LEGACY_REPO_PATH
        diagnostics["materialized"] = {
            "canonical": base.materialize_blob(repo_root, canonical_resolved, canonical_target),
            "legacy_internet": base.materialize_blob(repo_root, legacy_resolved, legacy_target),
        }
        diagnostics["automation"] = copy_targeted_automation(repo_root, exact_repo_root, base)
        command = build_child_command(
            exact_repo_root,
            work_root,
            args.ofcom_zip,
            args.ofcom_url,
            args.download_retries,
            args.download_timeout_seconds,
        )
        diagnostics["child_command"] = command
        diagnostics["state"] = "EXACT_BLOBS_MATERIALIZED_DIRECT_ZIP_TARGETED_CHILD_STARTING"
        manifest_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        diagnostics["child_returncode"] = completed.returncode
        diagnostics["child_stdout_tail"] = completed.stdout[-8000:]
        diagnostics["child_stderr_tail"] = completed.stderr[-8000:]
        diagnostics["state"] = (
            "COMPLETE_DIRECT_ZIP_TARGETED_REVIEW_OUTPUT_READY"
            if completed.returncode == 0
            else "DIRECT_ZIP_TARGETED_CHILD_BLOCKED_AT_VERIFIED_GATE"
        )
        manifest_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in diagnostics.items() if k not in {"child_stdout_tail", "child_stderr_tail"}}, sort_keys=True))
        return completed.returncode
    except Exception as exc:
        diagnostics["state"] = "BLOCKED_EXACT_DIRECT_ZIP_TARGETED_BLOB_GATE"
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
        manifest_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(diagnostics["error"], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
