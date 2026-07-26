#!/usr/bin/env python3
"""Prepare an exact serial-publisher manifest for the accepted strict-12 outputs.

This stage never pushes, measures, or changes height_difference values. It reads
Batch 131 local acceptance, re-hashes the exact accepted files, and emits the
expected SHA-256 and Git blob SHA-1 values that a later origin readback must
match byte-for-byte.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

EXPECTED_ROWS = list(range(61540, 61552))
BRANCH = "codex/aays-single-runner-v5-20260706"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"

STRICT_BASE = Path("docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/027_batch130_prepare12_strict_chain")
ACCEPT_BASE = Path("docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/029_batch131_strict12_acceptance")
FILES = {
    "proj": STRICT_BASE / "00_proj_ostn15_gate.json",
    "measurements": STRICT_BASE / "measurement/official_measurements.json",
    "verified_json": STRICT_BASE / "measurement/verified_examples.json",
    "verified_geojson": STRICT_BASE / "measurement/verified_examples.geojson",
    "strict_acceptance": STRICT_BASE / "batch130_strict12_acceptance.json",
    "local_acceptance": ACCEPT_BASE / "batch131_strict12_local_acceptance.json",
    "acceptance_execution": ACCEPT_BASE / "batch131_strict12_acceptance_execution.json",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(argv)

    repo = args.repo_root.resolve()
    local_acceptance_path = repo / FILES["local_acceptance"]
    if not local_acceptance_path.is_file():
        raise FileNotFoundError(local_acceptance_path)
    acceptance = _load(local_acceptance_path)
    if acceptance.get("local_acceptance_passed") is not True:
        raise ValueError("Batch131 local acceptance has not passed")
    if acceptance.get("remote_github_readback_required") is not True:
        raise ValueError("remote GitHub readback gate is unexpectedly disabled")
    if [int(v) for v in (acceptance.get("expected_rows") or [])] != EXPECTED_ROWS:
        raise ValueError("Batch131 local acceptance row set is not exactly 61540..61551")

    prior_hashes = acceptance.get("file_sha256") or {}
    records: list[dict[str, Any]] = []
    for name, relative in FILES.items():
        path = repo / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        data = path.read_bytes()
        sha256 = _sha256(data)
        if name in {"proj", "measurements", "verified_json", "verified_geojson", "strict_acceptance"}:
            expected = str(prior_hashes.get(name) or "")
            if not expected or sha256 != expected:
                raise ValueError(f"local acceptance SHA256 mismatch for {name}")
        records.append(
            {
                "name": name,
                "relative_path": relative.as_posix(),
                "size_bytes": len(data),
                "sha256": sha256,
                "git_blob_sha1": _git_blob_sha1(data),
            }
        )

    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "canonical_branch": BRANCH,
        "expected_rows": EXPECTED_ROWS,
        "expected_verified_count": 12,
        "source_local_acceptance": FILES["local_acceptance"].as_posix(),
        "ready_for_serial_publisher": True,
        "child_direct_push_forbidden": True,
        "new_task_forbidden": True,
        "same_task_id_required": True,
        "files": records,
        "remote_readback_contract": {
            "origin_fetch_required": True,
            "remote_commit_required": True,
            "local_sha256_must_match": True,
            "local_git_blob_sha1_must_match": True,
            "remote_git_blob_sha1_must_match": True,
            "all_files_required": True,
        },
        "numeric_values_changed": 0,
        "numeric_final_acceptance": "PENDING_REMOTE_GITHUB_READBACK",
        "final_ready": False,
        "fake_data": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "files": len(records), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
