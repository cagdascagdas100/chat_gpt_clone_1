#!/usr/bin/env python3
"""Fail-closed execution lock for the existing internet_access_3 single-runner chain.

The lock permits unrelated branch movement but requires exact Git blobs and a clean
working tree for every critical slot script and pinned canonical data source.
It never claims a slot, mutates a queue, writes a heartbeat, or starts a runner.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
ROW_PARTITION = (61523, 92283, 30761)
ALLOWED_PATHS = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3",
    "docs/chatgpt_status/_shared/slots_18/internet_access_3",
    "england_map_web/data/aays_18_slots/internet_access_3",
)
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class GateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise GateError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def load_manifest(path: Path) -> dict[str, Any]:
    require(path.is_file() and path.stat().st_size > 0, "manifest missing or empty")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GateError(f"manifest invalid JSON: {exc}") from exc
    require(isinstance(value, dict), "manifest object required")
    return value


def normalize_relpath(value: Any, name: str) -> str:
    text = str(value or "").replace("\\", "/").strip("/")
    require(text and not text.startswith("../") and "/../" not in f"/{text}/", f"{name}: unsafe path")
    require(not Path(text).is_absolute(), f"{name}: absolute path forbidden")
    return text


def validate_manifest(value: dict[str, Any]) -> dict[str, Any]:
    require(value.get("slot_id") == SLOT_ID, "wrong slot_id")
    partition = value.get("row_partition") or {}
    actual_partition = (int(partition.get("start", -1)), int(partition.get("end", -1)), int(partition.get("count", -1)))
    require(actual_partition == ROW_PARTITION, "row partition mismatch")
    allowed = tuple(value.get("allowed_paths") or ())
    require(allowed == ALLOWED_PATHS, "allowed_paths mismatch")
    require(value.get("direct_push_forbidden") is True, "direct push guard missing")
    require(value.get("single_shared_runner_only") is True, "single runner guard missing")
    require(value.get("create_new_runner") is False, "new runner must be false")
    require(value.get("queue_submission") is False, "queue submission must be false")
    require(value.get("auto_claim") is False, "auto_claim must be false")
    for key in ("fake_data", "db_write", "migration", "production_deploy", "final_ready"):
        require(value.get(key) is False, f"{key} must be false")

    rows = value.get("locked_blobs")
    require(isinstance(rows, list) and len(rows) >= 3, "locked_blobs must contain at least three rows")
    seen: set[str] = set()
    cleaned: list[dict[str, str]] = []
    for index, row in enumerate(rows, 1):
        require(isinstance(row, dict), f"locked blob {index}: object required")
        path = normalize_relpath(row.get("path"), f"locked blob {index}")
        sha = str(row.get("git_blob_sha") or "").lower()
        role = str(row.get("role") or "").strip()
        require(SHA1_RE.fullmatch(sha) is not None, f"locked blob {index}: invalid Git blob SHA")
        require(role, f"locked blob {index}: role required")
        require(path not in seen, f"locked blob {index}: duplicate path")
        seen.add(path)
        critical_script = path.startswith(ALLOWED_PATHS[0] + "/automation/")
        canonical_source = path in {
            "england_map_web/data/program_layer_matrix/security.geojson",
            "england_map_web/data/program_layer_matrix/internet.geojson",
        }
        require(critical_script or canonical_source, f"locked blob {index}: path outside critical scope")
        cleaned.append({"path": path, "git_blob_sha": sha, "role": role})
    return {"locked_blobs": cleaned}


def audit(repo_root: Path, manifest_path: Path, output_path: Path, git_ref: str = "HEAD") -> dict[str, Any]:
    require(repo_root.is_dir(), "repo root missing")
    manifest = load_manifest(manifest_path)
    clean = validate_manifest(manifest)
    head_sha = git(repo_root, "rev-parse", git_ref)
    require(SHA1_RE.fullmatch(head_sha) is not None, "HEAD SHA invalid")

    receipts: list[dict[str, Any]] = []
    for item in clean["locked_blobs"]:
        path = item["path"]
        expected = item["git_blob_sha"]
        ref_blob = git(repo_root, "rev-parse", f"{git_ref}:{path}")
        require(ref_blob == expected, f"{path}: ref blob drift")
        local_path = repo_root / path
        require(local_path.is_file(), f"{path}: working-tree file missing")
        working_blob = git(repo_root, "hash-object", "--", path)
        require(working_blob == expected, f"{path}: working-tree blob drift")
        porcelain = git(repo_root, "status", "--porcelain", "--", path)
        require(porcelain == "", f"{path}: working-tree path is dirty")
        size = int(git(repo_root, "cat-file", "-s", expected))
        require(size > 0, f"{path}: empty blob")
        receipts.append(
            {
                "path": path,
                "role": item["role"],
                "expected_blob_sha": expected,
                "ref_blob_sha": ref_blob,
                "working_tree_blob_sha": working_blob,
                "bytes": size,
                "state": "PASS",
            }
        )

    payload = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "PASS_EXECUTION_LOCK_REVIEW_ONLY",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "git_ref": git_ref,
        "observed_head_sha": head_sha,
        "head_movement_policy": "UNRELATED_HEAD_MOVEMENT_ALLOWED_ONLY_WHEN_ALL_LOCKED_BLOBS_REMAIN_EXACT",
        "row_partition": {"start": ROW_PARTITION[0], "end": ROW_PARTITION[1], "count": ROW_PARTITION[2]},
        "locked_blob_count": len(receipts),
        "locked_blobs": receipts,
        "gates": [
            {"gate_no": 1, "name": "SLOT_PARTITION_AND_ALLOWED_PATHS", "state": "PASS"},
            {"gate_no": 2, "name": "EXACT_REF_BLOB_SHA", "state": "PASS"},
            {"gate_no": 3, "name": "EXACT_WORKING_TREE_BLOB_SHA", "state": "PASS"},
            {"gate_no": 4, "name": "CLEAN_CRITICAL_WORKING_TREE_PATHS", "state": "PASS"},
            {"gate_no": 5, "name": "UNRELATED_HEAD_MOVEMENT_POLICY", "state": "PASS"},
            {"gate_no": 6, "name": "NO_CLAIM_QUEUE_HEARTBEAT_OR_NEW_RUNNER", "state": "PASS"},
        ],
        "auto_claim": False,
        "queue_submission": False,
        "create_new_runner": False,
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--git-ref", default="HEAD")
    args = parser.parse_args()
    result = audit(args.repo_root, args.manifest, args.output, args.git_ref)
    print(json.dumps({"state": result["state"], "locked_blob_count": result["locked_blob_count"], "head": result["observed_head_sha"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
