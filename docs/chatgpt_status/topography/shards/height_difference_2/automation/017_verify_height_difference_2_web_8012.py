#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import requests

DEFAULT_BASE = "http://127.0.0.1:8012/"
SLOT_RELATIVE_BASE = "england_map_web/data/aays_21_slots/height_difference_2/"
TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-020"
TARGET_ROWS = [30762, 46142, 61522]
EXPECTED_PRE_ACCEPTANCE_STATUS = "THREE_OFFICIAL_NUMERIC_ROWS_READY_PENDING_WEB_ACCEPTANCE"


def _get(session: requests.Session, url: str, timeout: int) -> requests.Response:
    response = session.get(url, timeout=timeout, allow_redirects=False)
    response.raise_for_status()
    return response


def _safe_slot_json_name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} file name is not a non-empty string")
    name = value.strip()
    parsed = urlparse(name)
    path = PurePosixPath(name.replace("\\", "/"))
    if parsed.scheme or parsed.netloc or name.startswith(("/", "\\")):
        raise ValueError(f"{label} file escapes slot root: {name}")
    if len(path.parts) != 1 or ".." in path.parts or path.suffix.lower() != ".json":
        raise ValueError(f"{label} file is not a safe slot-local JSON basename: {name}")
    return name


def _candidate_bases(base_url: str) -> list[str]:
    base = base_url if base_url.endswith("/") else base_url + "/"
    parsed = urlparse(base)
    origin = f"{parsed.scheme}://{parsed.netloc}/" if parsed.scheme and parsed.netloc else DEFAULT_BASE
    candidates = [base, origin, urljoin(origin, SLOT_RELATIVE_BASE)]
    ordered: list[str] = []
    for candidate in candidates:
        normalized = candidate if candidate.endswith("/") else candidate + "/"
        if normalized not in ordered:
            ordered.append(normalized)
    return ordered


def _load_candidate_payload(path: Path, expected_sha256: str, expected_rows: int) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"current candidate payload missing: {path}")
    raw = path.read_bytes()
    candidate_sha = hashlib.sha256(raw).hexdigest()
    if candidate_sha != expected_sha256:
        raise ValueError(f"current candidate local SHA256 mismatch: {candidate_sha}")
    candidates = json.loads(raw.decode("utf-8-sig"))
    if candidates.get("slot_id") != "height_difference_2" or candidates.get("task_id") != TASK_ID or candidates.get("attempt_id") != ATTEMPT_ID:
        raise ValueError("current candidate payload slot/task/attempt binding mismatch")
    if candidates.get("final_ready") is True or candidates.get("fake_data") is True:
        raise ValueError("current candidate payload violates safety flags")
    if candidates.get("status") != EXPECTED_PRE_ACCEPTANCE_STATUS:
        raise ValueError(f"current candidate status mismatch before web acceptance: {candidates.get('status')}")
    if int(candidates.get("expected_web_operation_rows", 0)) < expected_rows:
        raise ValueError("current candidate payload web-row binding below requested floor")
    candidate_rows = candidates.get("candidates")
    if not isinstance(candidate_rows, list):
        raise ValueError("current candidate payload candidates is not a list")
    candidate_count = int(candidates.get("candidate_count", len(candidate_rows)))
    if candidate_count != 3 or len(candidate_rows) != 3:
        raise ValueError(f"current candidate count mismatch: declared={candidate_count} actual={len(candidate_rows)}")
    row_set = sorted(int(row["row_no"]) for row in candidate_rows)
    if row_set != TARGET_ROWS:
        raise ValueError(f"current candidate exact row set mismatch: {row_set}")
    if any(row.get("final_ready") is True or row.get("fake_data") is True for row in candidate_rows):
        raise ValueError("current candidate row violates safety flags")
    return {
        "candidate_count": candidate_count,
        "candidate_rows": row_set,
        "candidate_status": candidates.get("status"),
        "candidate_local_sha256": candidate_sha,
    }


def _example_row_numbers(example: dict[str, Any]) -> set[int]:
    rows: set[int] = set()
    for key in ("row_no", "target_row_no"):
        value = example.get(key)
        if value is not None:
            try:
                rows.add(int(value))
            except (TypeError, ValueError):
                pass
    values = example.get("target_rows")
    if isinstance(values, list):
        for value in values:
            try:
                rows.add(int(value))
            except (TypeError, ValueError):
                pass
    return rows


def _probe_site(session: requests.Session, base: str, expected_operation_rows: int, timeout: int) -> dict[str, Any]:
    stages: list[dict[str, Any]] = []
    index_response = _get(session, urljoin(base, "index.html"), timeout)
    if "height_difference_2" not in index_response.text or "operations_manifest.json" not in index_response.text:
        raise ValueError("index.html lacks slot or operations manifest binding")
    stages.append({"stage": "INDEX_HTTP", "status": "PASS", "url": index_response.url, "status_code": index_response.status_code, "sha256": hashlib.sha256(index_response.content).hexdigest()})

    manifest_response = _get(session, urljoin(base, "operations_manifest.json"), timeout)
    manifest = manifest_response.json()
    if manifest.get("slot_id") != "height_difference_2":
        raise ValueError(f"operations manifest slot mismatch: {manifest.get('slot_id')}")
    files = manifest.get("operation_files")
    if not isinstance(files, list) or not files:
        raise ValueError("operations manifest has no files")
    safe_files = [_safe_slot_json_name(name, "operation") for name in files]
    if len(set(safe_files)) != len(safe_files):
        raise ValueError("operations manifest contains duplicate operation file names")
    expected = int(manifest.get("expected_visible_operation_rows", 0))
    if expected < expected_operation_rows:
        raise ValueError(f"manifest expected rows {expected} below {expected_operation_rows}")
    stages.append({"stage": "OPERATIONS_MANIFEST_HTTP", "status": "PASS", "url": manifest_response.url, "expected_visible_operation_rows": expected, "file_count": len(safe_files), "slot_id": manifest.get("slot_id"), "sha256": hashlib.sha256(manifest_response.content).hexdigest()})

    operations: list[dict[str, Any]] = []
    file_records: list[dict[str, Any]] = []
    for name in safe_files:
        response = _get(session, urljoin(base, name), timeout)
        rows = response.json().get("operations", [])
        if not isinstance(rows, list):
            raise ValueError(f"operation file {name} has invalid rows")
        operations.extend(rows)
        file_records.append({"file": name, "rows": len(rows), "sha256": hashlib.sha256(response.content).hexdigest()})
    numbers = [int(row["operation_no"]) for row in operations]
    if not numbers:
        raise ValueError("operation rows are empty")
    if len(numbers) != expected or len(set(numbers)) != expected:
        raise ValueError(f"operation row count/uniqueness mismatch: {len(numbers)} vs {expected}")
    if sorted(numbers) != list(range(min(numbers), max(numbers) + 1)):
        raise ValueError("operation numbers are not contiguous")
    if any(row.get("fake_data") is True for row in operations):
        raise ValueError("operation row advertises fake_data=true")
    stages.append({"stage": "OPERATION_ROWS_HTTP", "status": "PASS", "row_count": len(numbers), "first_operation": min(numbers), "last_operation": max(numbers), "files": file_records})

    example_files = manifest.get("example_files")
    if not isinstance(example_files, list) or not example_files:
        raise ValueError("operations manifest has no example files")
    safe_example_files = [_safe_slot_json_name(name, "example") for name in example_files]
    if len(set(safe_example_files)) != len(safe_example_files):
        raise ValueError("operations manifest contains duplicate example file names")
    visible_rows: set[int] = set()
    measured_rows: set[int] = set()
    example_records: list[dict[str, Any]] = []
    for name in safe_example_files:
        response = _get(session, urljoin(base, name), timeout)
        examples = response.json().get("examples", [])
        if not isinstance(examples, list):
            raise ValueError(f"example file {name} has invalid rows")
        for example in examples:
            if not isinstance(example, dict):
                continue
            rows = _example_row_numbers(example)
            visible_rows.update(rows)
            if example.get("height_difference_m") is not None and example.get("hmlr_inspire_id"):
                measured_rows.update(rows)
        example_records.append({"file": name, "rows": len(examples), "sha256": hashlib.sha256(response.content).hexdigest()})
    target_visible = sorted(set(TARGET_ROWS).intersection(visible_rows))
    measured_target_visible = sorted(set(TARGET_ROWS).intersection(measured_rows))
    if target_visible != TARGET_ROWS:
        raise ValueError(f"site exact target rows not all visible: {target_visible}")
    if measured_target_visible != TARGET_ROWS:
        raise ValueError(f"site measured exact target rows not all visible: {measured_target_visible}")
    stages.append({"stage": "EXACT_TARGET_EXAMPLES_HTTP", "status": "PASS", "candidate_rows": target_visible, "measured_candidate_rows": measured_target_visible, "file_count": len(safe_example_files), "files": example_records})

    return {
        "base_url": base,
        "visible_operation_rows": len(numbers),
        "site_candidate_rows": target_visible,
        "site_measured_candidate_rows": measured_target_visible,
        "stages": stages,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--expected-operation-rows", type=int, default=1036)
    parser.add_argument("--candidate-payload", type=Path, required=True)
    parser.add_argument("--expected-candidates-sha256", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)
    stages: list[dict[str, Any]] = []
    probe_errors: list[dict[str, str]] = []
    try:
        expected_candidate_sha = args.expected_candidates_sha256.strip().lower()
        if len(expected_candidate_sha) != 64 or any(ch not in "0123456789abcdef" for ch in expected_candidate_sha):
            raise ValueError("expected candidates SHA256 is required and must be 64 lowercase/hex characters")
        current_candidate = _load_candidate_payload(args.candidate_payload.resolve(), expected_candidate_sha, args.expected_operation_rows)
        stages.append({"stage": "CURRENT_WORKTREE_CANDIDATE_PAYLOAD", "status": "PASS", **current_candidate})

        session = requests.Session()
        session.headers.update({"User-Agent": "TerraYield-AAYS/height_difference_2-web-acceptance"})
        site: dict[str, Any] | None = None
        for base in _candidate_bases(args.base_url):
            try:
                site = _probe_site(session, base, args.expected_operation_rows, args.timeout)
                break
            except Exception as exc:
                probe_errors.append({"base_url": base, "error": f"{type(exc).__name__}: {exc}"})
        if site is None:
            raise ValueError(f"no port8012 base passed: {probe_errors}")
        stages.extend(site["stages"])

        payload = {
            "schema_version": 4,
            "slot_id": "height_difference_2",
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "PORT_8012_WEB_ACCEPTANCE_PASSED",
            "base_url": site["base_url"],
            "base_probe_errors": probe_errors,
            "visible_operation_rows": site["visible_operation_rows"],
            "candidate_count": current_candidate["candidate_count"],
            "candidate_rows": current_candidate["candidate_rows"],
            "candidate_status": current_candidate["candidate_status"],
            "candidate_payload_transport": "LOCAL_CURRENT_WORKTREE_PRE_ACCEPTANCE",
            "candidate_local_sha256": current_candidate["candidate_local_sha256"],
            "site_candidate_rows": site["site_candidate_rows"],
            "site_measured_candidate_rows": site["site_measured_candidate_rows"],
            "exact_target_rows_verified": True,
            "current_candidate_bytes_verified": True,
            "operation_file_path_guard_verified": True,
            "example_file_path_guard_verified": True,
            "stages": stages,
            "final_ready": False,
            "fake_data": False,
        }
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 4,
            "slot_id": "height_difference_2",
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "BLOCKED_PORT_8012_WEB_ACCEPTANCE",
            "error": f"{type(exc).__name__}: {exc}",
            "base_probe_errors": probe_errors,
            "stages": stages,
            "exact_target_rows_verified": False,
            "current_candidate_bytes_verified": False,
            "operation_file_path_guard_verified": False,
            "example_file_path_guard_verified": False,
            "final_ready": False,
            "fake_data": False,
        }
        code = 2
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"ok": code == 0, "status": payload["status"], "rows": payload.get("visible_operation_rows", 0), "candidate_rows": payload.get("candidate_rows", []), "candidate_sha256": payload.get("candidate_local_sha256"), "base_url": payload.get("base_url")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
