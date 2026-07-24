#!/usr/bin/env python3
"""Materialize exact Git blobs and run the internet_access_3 review pipeline.

This entrypoint is fail-closed and review-only. It verifies that the authoritative
repository paths resolve to the expected Git blob SHAs, materializes those blobs
into an isolated temporary repo skeleton, copies only the required slot automation,
and invokes the existing bounded Ofcom r2 orchestrator. It never mutates the source
working tree and never writes business data, scores, a database, or a deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

SLOT_ID = "internet_access_3"
CANONICAL_REPO_PATH = "england_map_web/data/program_layer_matrix/security.geojson"
LEGACY_REPO_PATH = "england_map_web/data/program_layer_matrix/internet.geojson"
EXPECTED_CANONICAL_BLOB_SHA = "8afd1d2bac414cf0f6b9484014e7878a4ceff877"
EXPECTED_LEGACY_BLOB_SHA = "9c24fd366e29c3356b1e5178295b903edf8680ff"
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
)


class GateError(RuntimeError):
    """Raised when a truth or provenance gate fails."""


def run_git(repo_root: Path, *args: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=not binary,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", "replace") if binary else completed.stderr
        raise GateError(f"git {' '.join(args)} failed: {stderr.strip()}")
    return completed.stdout


def resolve_path_blob(repo_root: Path, git_ref: str, repo_path: str) -> str:
    value = str(run_git(repo_root, "rev-parse", f"{git_ref}:{repo_path}")).strip()
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value.lower()):
        raise GateError(f"invalid blob SHA for {git_ref}:{repo_path}: {value!r}")
    return value.lower()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize_blob(repo_root: Path, blob_sha: str, destination: Path) -> dict[str, Any]:
    blob_type = str(run_git(repo_root, "cat-file", "-t", blob_sha)).strip()
    if blob_type != "blob":
        raise GateError(f"Git object {blob_sha} is {blob_type!r}, expected 'blob'")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    if temporary.exists():
        temporary.unlink()

    with temporary.open("wb") as output:
        process = subprocess.Popen(
            ["git", "-C", str(repo_root), "cat-file", "blob", blob_sha],
            stdout=output,
            stderr=subprocess.PIPE,
        )
        _, stderr = process.communicate()
    if process.returncode != 0:
        temporary.unlink(missing_ok=True)
        raise GateError(f"git cat-file blob {blob_sha} failed: {stderr.decode('utf-8', 'replace').strip()}")
    if temporary.stat().st_size <= 0:
        temporary.unlink(missing_ok=True)
        raise GateError(f"materialized blob is empty: {blob_sha}")
    os.replace(temporary, destination)
    return {
        "git_blob_sha": blob_sha,
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
    }


def copy_required_automation(repo_root: Path, exact_repo_root: Path) -> list[dict[str, Any]]:
    source_root = repo_root / AUTOMATION_RELATIVE
    target_root = exact_repo_root / AUTOMATION_RELATIVE
    target_root.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, Any]] = []
    for name in REQUIRED_AUTOMATION:
        source = source_root / name
        if not source.is_file():
            raise GateError(f"required automation missing: {source}")
        target = target_root / name
        shutil.copy2(source, target)
        copied.append({"name": name, "sha256": sha256_file(target), "bytes": target.stat().st_size})
    return copied


def build_child_command(
    exact_repo_root: Path,
    work_root: Path,
    ofcom_zip: Path | None,
    ofcom_url: str | None,
    download_retries: int,
    download_timeout_seconds: int,
) -> list[str]:
    script = exact_repo_root / AUTOMATION_RELATIVE / "008_download_validate_run_slot3.py"
    command = [
        sys.executable,
        str(script),
        "--repo-root",
        str(exact_repo_root),
        "--work-root",
        str(work_root),
        "--download-retries",
        str(download_retries),
        "--download-timeout-seconds",
        str(download_timeout_seconds),
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
    parser.add_argument("--expected-canonical-blob-sha", default=EXPECTED_CANONICAL_BLOB_SHA)
    parser.add_argument("--expected-legacy-blob-sha", default=EXPECTED_LEGACY_BLOB_SHA)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    if not (repo_root / ".git").exists() and not (repo_root / ".git").is_file():
        raise GateError(f"repo root is not a Git checkout: {repo_root}")
    work_root = (args.work_root or (repo_root / "outputs/internet_access_3_verified_run")).resolve()
    exact_repo_root = work_root / "exact_git_blob_repo"
    manifest_path = work_root / "internet_access_3_exact_blob_materialization_latest.json"
    work_root.mkdir(parents=True, exist_ok=True)

    diagnostics: dict[str, Any] = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "git_ref": args.git_ref,
        "repo_root": str(repo_root),
        "exact_repo_root": str(exact_repo_root),
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }

    try:
        canonical_resolved = resolve_path_blob(repo_root, args.git_ref, CANONICAL_REPO_PATH)
        legacy_resolved = resolve_path_blob(repo_root, args.git_ref, LEGACY_REPO_PATH)
        diagnostics["resolved_blobs"] = {
            "canonical": canonical_resolved,
            "legacy_internet": legacy_resolved,
        }
        if canonical_resolved != args.expected_canonical_blob_sha.lower():
            raise GateError(
                f"canonical blob mismatch: expected {args.expected_canonical_blob_sha}, found {canonical_resolved}"
            )
        if legacy_resolved != args.expected_legacy_blob_sha.lower():
            raise GateError(
                f"legacy internet blob mismatch: expected {args.expected_legacy_blob_sha}, found {legacy_resolved}"
            )

        canonical_target = exact_repo_root / CANONICAL_REPO_PATH
        legacy_target = exact_repo_root / LEGACY_REPO_PATH
        diagnostics["materialized"] = {
            "canonical": materialize_blob(repo_root, canonical_resolved, canonical_target),
            "legacy_internet": materialize_blob(repo_root, legacy_resolved, legacy_target),
        }
        diagnostics["automation"] = copy_required_automation(repo_root, exact_repo_root)
        command = build_child_command(
            exact_repo_root,
            work_root,
            args.ofcom_zip,
            args.ofcom_url,
            args.download_retries,
            args.download_timeout_seconds,
        )
        diagnostics["child_command"] = command
        diagnostics["state"] = "EXACT_BLOBS_MATERIALIZED_CHILD_STARTING"
        manifest_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        diagnostics["child_returncode"] = completed.returncode
        diagnostics["child_stdout_tail"] = completed.stdout[-8000:]
        diagnostics["child_stderr_tail"] = completed.stderr[-8000:]
        diagnostics["state"] = (
            "COMPLETE_REVIEW_OUTPUT_READY" if completed.returncode == 0 else "CHILD_BLOCKED_AT_VERIFIED_GATE"
        )
        manifest_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in diagnostics.items() if k not in {"child_stdout_tail", "child_stderr_tail"}}, sort_keys=True))
        return completed.returncode
    except Exception as exc:
        diagnostics["state"] = "BLOCKED_EXACT_BLOB_GATE"
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
        manifest_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(diagnostics["error"], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
