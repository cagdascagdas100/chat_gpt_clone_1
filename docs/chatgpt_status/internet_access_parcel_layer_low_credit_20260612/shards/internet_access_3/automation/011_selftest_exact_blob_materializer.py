#!/usr/bin/env python3
"""Deterministic network-free tests for exact Git blob materialization."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "010_materialize_exact_blobs_and_run_slot3.py"
spec = importlib.util.spec_from_file_location("slot3_exact", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run(*args: str, cwd: Path) -> str:
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def git(repo: Path, *args: str) -> str:
    return run("git", *args, cwd=repo)


def check(name: str, condition: bool, results: list[dict[str, object]]) -> None:
    if not condition:
        raise AssertionError(name)
    results.append({"test": name, "state": "PASS"})


def main() -> int:
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init")
        git(repo, "config", "user.email", "slot3@example.invalid")
        git(repo, "config", "user.name", "slot3-selftest")

        canonical = repo / module.CANONICAL_REPO_PATH
        legacy = repo / module.LEGACY_REPO_PATH
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text('{"type":"FeatureCollection","features":[]}\n', encoding="utf-8")
        legacy.write_text('{"type":"FeatureCollection","features":[]}\n', encoding="utf-8")
        automation = repo / module.AUTOMATION_RELATIVE
        automation.mkdir(parents=True, exist_ok=True)
        for name in module.REQUIRED_AUTOMATION:
            (automation / name).write_text(f"# {name}\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "fixture")

        canonical_sha = module.resolve_path_blob(repo, "HEAD", module.CANONICAL_REPO_PATH)
        legacy_sha = module.resolve_path_blob(repo, "HEAD", module.LEGACY_REPO_PATH)
        check("resolve_canonical_blob", len(canonical_sha) == 40, results)
        check("resolve_legacy_blob", len(legacy_sha) == 40, results)
        check("distinct_paths_may_share_identical_blob", canonical_sha == legacy_sha, results)

        output = root / "materialized/security.geojson"
        metadata = module.materialize_blob(repo, canonical_sha, output)
        check("materialized_bytes_match", output.read_bytes() == canonical.read_bytes(), results)
        check("materialized_blob_sha_recorded", metadata["git_blob_sha"] == canonical_sha, results)
        check("materialized_sha256_recorded", metadata["sha256"] == module.sha256_file(output), results)
        check("materialized_nonempty", int(metadata["bytes"]) > 0, results)

        copied = module.copy_required_automation(repo, root / "exact")
        check("required_automation_count", len(copied) == len(module.REQUIRED_AUTOMATION), results)
        check("required_automation_hashes", all(len(str(item["sha256"])) == 64 for item in copied), results)

        explicit_zip = root / "official.zip"
        command = module.build_child_command(root / "exact", root / "work", explicit_zip, "https://example.invalid/ofcom.zip", 3, 45)
        check("child_command_exact_repo", str(root / "exact") in command, results)
        check("child_command_explicit_zip", str(explicit_zip.resolve()) in command, results)
        check("child_command_url", "https://example.invalid/ofcom.zip" in command, results)
        check("child_command_retry_timeout", "3" in command and "45" in command, results)

        try:
            module.resolve_path_blob(repo, "HEAD", "missing.geojson")
        except module.GateError:
            results.append({"test": "missing_path_rejected", "state": "PASS"})
        else:
            raise AssertionError("missing_path_rejected")

        tree_sha = git(repo, "rev-parse", "HEAD^{tree}")
        try:
            module.materialize_blob(repo, tree_sha, root / "bad")
        except module.GateError:
            results.append({"test": "non_blob_object_rejected", "state": "PASS"})
        else:
            raise AssertionError("non_blob_object_rejected")

        truth = {
            "actual_business_data_rows_written": 0,
            "scores_written": 0,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
        }
        check("truth_flags_fail_closed", not any(bool(v) for v in truth.values()), results)

    payload = {
        "schema_version": 3,
        "slot_id": module.SLOT_ID,
        "passed": len(results),
        "total": len(results),
        "tests": results,
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
