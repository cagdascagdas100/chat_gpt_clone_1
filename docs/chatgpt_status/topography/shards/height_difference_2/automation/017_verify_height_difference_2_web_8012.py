#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import requests

DEFAULT_BASE = "http://127.0.0.1:8012/england_map_web/data/aays_21_slots/height_difference_2/"
TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-020"
TARGET_ROWS = [30762, 46142, 61522]
EXPECTED_PRE_ACCEPTANCE_STATUS = "THREE_OFFICIAL_NUMERIC_ROWS_READY_PENDING_WEB_ACCEPTANCE"


def _get(session: requests.Session, url: str, timeout: int) -> requests.Response:
    response = session.get(url, timeout=timeout, allow_redirects=False)
    response.raise_for_status()
    return response


def _safe_operation_file_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("operation file name is not a non-empty string")
    name = value.strip()
    parsed = urlparse(name)
    path = PurePosixPath(name.replace("\\", "/"))
    if parsed.scheme or parsed.netloc or name.startswith(("/", "\\")):
        raise ValueError(f"operation file escapes slot root: {name}")
    if len(path.parts) != 1 or ".." in path.parts or path.suffix.lower() != ".json":
        raise ValueError(f"operation file is not a safe slot-local JSON basename: {name}")
    return name


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--expected-operation-rows", type=int, default=1036)
    parser.add_argument("--expected-candidates-sha256", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)
    stages = []
    try:
        expected_candidate_sha = args.expected_candidates_sha256.strip().lower()
        if len(expected_candidate_sha) != 64 or any(ch not in "0123456789abcdef" for ch in expected_candidate_sha):
            raise ValueError("expected candidates SHA256 is required and must be 64 lowercase/hex characters")

        session = requests.Session()
        session.headers.update({"User-Agent": "TerraYield-AAYS/height_difference_2-web-acceptance"})
        base = args.base_url if args.base_url.endswith("/") else args.base_url + "/"
        index_response = _get(session, urljoin(base, "index.html"), args.timeout)
        if "height_difference_2" not in index_response.text or "operations_manifest.json" not in index_response.text:
            raise ValueError("index.html lacks slot or operations manifest binding")
        stages.append({"stage": "INDEX_HTTP", "status": "PASS", "url": index_response.url, "status_code": index_response.status_code, "sha256": hashlib.sha256(index_response.content).hexdigest()})

        manifest_response = _get(session, urljoin(base, "operations_manifest.json"), args.timeout)
        manifest = manifest_response.json()
        if manifest.get("slot_id") != "height_difference_2":
            raise ValueError(f"operations manifest slot mismatch: {manifest.get('slot_id')}")
        files = manifest.get("operation_files")
        if not isinstance(files, list) or not files:
            raise ValueError("operations manifest has no files")
        safe_files = [_safe_operation_file_name(name) for name in files]
        if len(set(safe_files)) != len(safe_files):
            raise ValueError("operations manifest contains duplicate file names")
        expected = int(manifest.get("expected_visible_operation_rows", 0))
        if expected < args.expected_operation_rows:
            raise ValueError(f"manifest expected rows {expected} below {args.expected_operation_rows}")
        stages.append({"stage": "OPERATIONS_MANIFEST_HTTP", "status": "PASS", "url": manifest_response.url, "expected_visible_operation_rows": expected, "file_count": len(safe_files), "slot_id": manifest.get("slot_id"), "sha256": hashlib.sha256(manifest_response.content).hexdigest()})

        operations = []
        file_records = []
        for name in safe_files:
            response = _get(session, urljoin(base, name), args.timeout)
            rows = response.json().get("operations", [])
            if not isinstance(rows, list):
                raise ValueError(f"operation file {name} has invalid rows")
            operations.extend(rows)
            file_records.append({"file": name, "rows": len(rows), "sha256": hashlib.sha256(response.content).hexdigest()})
        numbers = [int(row["operation_no"]) for row in operations]
        if len(numbers) != expected or len(set(numbers)) != expected:
            raise ValueError(f"operation row count/uniqueness mismatch: {len(numbers)} vs {expected}")
        if not numbers:
            raise ValueError("operation rows are empty")
        if sorted(numbers) != list(range(min(numbers), max(numbers) + 1)):
            raise ValueError("operation numbers are not contiguous")
        if any(row.get("fake_data") is True for row in operations):
            raise ValueError("operation row advertises fake_data=true")
        stages.append({"stage": "OPERATION_ROWS_HTTP", "status": "PASS", "row_count": len(numbers), "first_operation": min(numbers), "last_operation": max(numbers), "files": file_records})

        candidate_response = _get(session, urljoin(base, "candidates_latest.json"), args.timeout)
        candidate_sha = hashlib.sha256(candidate_response.content).hexdigest()
        if candidate_sha != expected_candidate_sha:
            raise ValueError(f"candidate HTTP SHA256 mismatch: {candidate_sha}")
        candidates = candidate_response.json()
        if candidates.get("slot_id") != "height_difference_2" or candidates.get("task_id") != TASK_ID or candidates.get("attempt_id") != ATTEMPT_ID:
            raise ValueError("candidate payload slot/task/attempt binding mismatch")
        if candidates.get("final_ready") is True or candidates.get("fake_data") is True:
            raise ValueError("candidate payload violates safety flags")
        if candidates.get("status") != EXPECTED_PRE_ACCEPTANCE_STATUS:
            raise ValueError(f"candidate status mismatch before web acceptance: {candidates.get('status')}")
        if int(candidates.get("expected_web_operation_rows", 0)) < args.expected_operation_rows:
            raise ValueError("candidate payload web-row binding below requested floor")
        candidate_rows = candidates.get("candidates")
        if not isinstance(candidate_rows, list):
            raise ValueError("candidate payload candidates is not a list")
        candidate_count = int(candidates.get("candidate_count", len(candidate_rows)))
        if candidate_count != 3 or len(candidate_rows) != 3:
            raise ValueError(f"candidate count mismatch: declared={candidate_count} actual={len(candidate_rows)}")
        row_set = sorted(int(row["row_no"]) for row in candidate_rows)
        if row_set != TARGET_ROWS:
            raise ValueError(f"candidate exact row set mismatch: {row_set}")
        if any(row.get("final_ready") is True or row.get("fake_data") is True for row in candidate_rows):
            raise ValueError("candidate row violates safety flags")
        stages.append({"stage": "CANDIDATES_HTTP", "status": "PASS", "candidate_count": candidate_count, "candidate_rows": row_set, "candidate_status": candidates.get("status"), "expected_web_operation_rows": candidates.get("expected_web_operation_rows"), "sha256": candidate_sha, "expected_sha256": expected_candidate_sha, "task_id": candidates.get("task_id"), "attempt_id": candidates.get("attempt_id")})

        payload = {"schema_version": 3, "slot_id": "height_difference_2", "task_id": TASK_ID, "attempt_id": ATTEMPT_ID, "status": "PORT_8012_WEB_ACCEPTANCE_PASSED", "base_url": base, "visible_operation_rows": len(numbers), "candidate_count": candidate_count, "candidate_rows": row_set, "candidate_status": candidates.get("status"), "candidate_http_sha256": candidate_sha, "exact_target_rows_verified": True, "current_candidate_bytes_verified": True, "operation_file_path_guard_verified": True, "stages": stages, "final_ready": False, "fake_data": False}
        code = 0
    except Exception as exc:
        payload = {"schema_version": 3, "slot_id": "height_difference_2", "task_id": TASK_ID, "attempt_id": ATTEMPT_ID, "status": "BLOCKED_PORT_8012_WEB_ACCEPTANCE", "error": f"{type(exc).__name__}: {exc}", "stages": stages, "exact_target_rows_verified": False, "current_candidate_bytes_verified": False, "operation_file_path_guard_verified": False, "final_ready": False, "fake_data": False}
        code = 2
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"ok": code == 0, "status": payload["status"], "rows": payload.get("visible_operation_rows", 0), "candidate_rows": payload.get("candidate_rows", []), "candidate_sha256": payload.get("candidate_http_sha256")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
