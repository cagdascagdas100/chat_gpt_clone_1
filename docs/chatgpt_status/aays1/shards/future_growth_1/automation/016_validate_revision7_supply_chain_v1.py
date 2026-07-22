#!/usr/bin/env python3
"""Fail-closed supply-chain validator for future_growth_1 revision-7 inputs.

The validator performs no network calls and writes no business data. It verifies
Git blob SHA-1 values, path scope, required text markers, and JSON pointer values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SLOT_ID = "future_growth_1"
CONTRACT_REVISION = 7
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_CANONICAL = "england_map_web/data/program_layer_matrix/security.geojson"
ALLOWED_QUEUE = "docs/chatgpt_status/aays1/queue/aays1_future_growth_1_official_geometry_pipeline_v7_20260722.task.json"
ALLOWED_PREFIXES = (
    "docs/chatgpt_status/aays1/shards/future_growth_1/",
    "docs/chatgpt_status/aays1/automation/future_growth_1_",
)

def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()

def get_dotted(value: Any, dotted: str) -> Any:
    current = value
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted)
        current = current[part]
    return current

def allowed_path(path: str) -> bool:
    return path in {ALLOWED_CANONICAL, ALLOWED_QUEUE} or path.startswith(ALLOWED_PREFIXES)

def validate(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    add("manifest_slot", manifest.get("slot_id") == SLOT_ID, str(manifest.get("slot_id")))
    add("manifest_revision", manifest.get("contract_revision") == CONTRACT_REVISION, str(manifest.get("contract_revision")))
    files = manifest.get("files")
    add("files_list", isinstance(files, list) and len(files) >= 12, f"count={len(files) if isinstance(files, list) else 'invalid'}")
    if not isinstance(files, list):
        files = []

    paths = [item.get("path") for item in files if isinstance(item, dict)]
    add("unique_paths", len(paths) == len(set(paths)), f"paths={len(paths)} unique={len(set(paths))}")
    rows: list[dict[str, Any]] = []

    for index, item in enumerate(files, 1):
        row: dict[str, Any] = {"index": index}
        if not isinstance(item, dict):
            row.update(path=None, passed=False, errors=["entry_not_object"])
            rows.append(row)
            continue
        path = item.get("path")
        expected = item.get("git_blob_sha")
        errors: list[str] = []
        if not isinstance(path, str) or not allowed_path(path):
            errors.append("path_outside_slot_scope")
        if not isinstance(expected, str) or not SHA1_RE.fullmatch(expected):
            errors.append("invalid_expected_blob_sha")
        file_path = root / path if isinstance(path, str) else root / "__invalid__"
        data = b""
        if not file_path.is_file():
            errors.append("file_missing")
        else:
            data = file_path.read_bytes()
            actual = git_blob_sha(data)
            row["actual_git_blob_sha"] = actual
            if actual != expected:
                errors.append("git_blob_sha_mismatch")
            text = data.decode("utf-8", errors="replace")
            for marker in item.get("required_text", []):
                if marker not in text:
                    errors.append(f"missing_text:{marker}")
            assertions = item.get("json_assertions", {})
            if assertions:
                try:
                    parsed = json.loads(text)
                    for dotted, wanted in assertions.items():
                        try:
                            got = get_dotted(parsed, dotted)
                        except KeyError:
                            errors.append(f"missing_json_key:{dotted}")
                        else:
                            if got != wanted:
                                errors.append(f"json_mismatch:{dotted}")
                except json.JSONDecodeError:
                    errors.append("invalid_json")
        row.update(path=path, expected_git_blob_sha=expected, passed=not errors, errors=errors)
        rows.append(row)

    add("all_file_rows_pass", bool(rows) and all(row["passed"] for row in rows), f"passed={sum(r['passed'] for r in rows)}/{len(rows)}")
    result = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "contract_revision": CONTRACT_REVISION,
        "result": "PASS" if all(c["passed"] for c in checks) else "FAIL",
        "checks": checks,
        "files": rows,
        "files_passed": sum(row["passed"] for row in rows),
        "files_total": len(rows),
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    result = validate(Path(args.root).resolve(), manifest)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["result"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
