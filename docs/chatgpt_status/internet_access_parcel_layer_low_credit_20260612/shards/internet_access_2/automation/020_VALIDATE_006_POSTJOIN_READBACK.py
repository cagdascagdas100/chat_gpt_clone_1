# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
TASK_ID = "internet-access-2-ofcom-dynamic-zip-join-existing-11013-v2-20260722T041000Z"
EXPECTED_OUTPUT_ROWS = 11_013
EXPECTED_R2_FILES = 121
EXPECTED_ARCHIVE_ROWS = 1_741_096
EXPECTED_WEB_CHUNKS = 23
SHARD_REL = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2")
QUEUE_REL = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/queue/internet_access_2_ofcom_dynamic_zip_join_existing_11013_006.v3.task.json")
DATA_REL = SHARD_REL / "data/006_existing_11013_official_coverage_candidates.jsonl"
VALIDATION_REL = SHARD_REL / "validation/006_existing_11013_coverage_validation.json"
SOURCE_REL = SHARD_REL / "source_snapshots/006_ofcom_binary_readback.json"
MANIFEST_REL = SHARD_REL / "web/006_existing_11013_rows_manifest.json"
STATUS_REL = SHARD_REL / "status/006_status.json"
PROGRESS_REL = SHARD_REL / "progress/006_progress.jsonl"
R2 = re.compile(r"(?:^|/)202601_fixed_postcode_coverage_r2_([A-Z0-9]+)\.csv$", re.I)
ALIASES = {
    "postcode": ["postcode", "postcode_space"],
    "gigabit_available_pct": ["Gigabit availability (% premises)", "Gigabit availability"],
    "ultrafast_100mbps_available_pct": ["UFBB (100Mbit/s) availability (% premises)", "UFBB100 availability (% premises)"],
    "superfast_30mbps_available_pct": ["SFBB availability (% premises)", "SFBB availability"],
    "unable_30mbps_pct": ["% of premises unable to receive 30Mbit/s", "unable to receive 30Mbit/s"],
}
CORE_KEYS = tuple(key for key in ALIASES if key != "postcode")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalise_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def norm_postcode(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def postcode_area(value: Any) -> str:
    match = re.match(r"^[A-Z]+", norm_postcode(value))
    return match.group(0) if match else ""


def pick(row: dict[str, Any], aliases: Iterable[str]) -> Any:
    lookup = {normalise_key(key): value for key, value in row.items()}
    for alias in aliases:
        key = normalise_key(alias)
        if key in lookup:
            return lookup[key]
    return None


def parse_percent(value: Any) -> float | None:
    text = str(value or "").strip().replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def metrics(row: dict[str, Any] | None) -> dict[str, float | None]:
    if not row:
        return {key: None for key in CORE_KEYS}
    return {key: parse_percent(pick(row, ALIASES[key])) for key in CORE_KEYS}


def valid_percent(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 100.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise RuntimeError(f"JSONL_OBJECT_REQUIRED:{path}")
                rows.append(value)
    return rows


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp.{uuid.uuid4().hex}")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def deterministic_unique(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        postcode = norm_postcode(row.get("postcode"))
        if postcode and postcode not in unique:
            unique[postcode] = row
    ranked = sorted(unique.values(), key=lambda row: hashlib.sha256(norm_postcode(row.get("postcode")).encode("ascii")).hexdigest())
    return ranked[:count]


def archive_rows(archive: zipfile.ZipFile, targets: set[str]) -> dict[str, dict[str, Any]]:
    by_area: dict[str, set[str]] = {}
    for postcode in targets:
        by_area.setdefault(postcode_area(postcode), set()).add(postcode)
    names = [name.replace("\\", "/") for name in archive.namelist()]
    members: dict[str, str] = {}
    for name in names:
        match = R2.search(name)
        if match:
            members[match.group(1).upper()] = name
    found: dict[str, dict[str, Any]] = {}
    for area, postcodes in sorted(by_area.items()):
        member = members.get(area)
        if not member:
            continue
        with archive.open(member) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="strict", newline=""))
            for row in reader:
                postcode = norm_postcode(pick(row, ALIASES["postcode"]))
                if postcode in postcodes:
                    found[postcode] = row
                    if postcodes.issubset(found.keys()):
                        break
    return found


def compare_metrics(expected: dict[str, Any], observed: dict[str, float | None]) -> list[str]:
    failures: list[str] = []
    for key in CORE_KEYS:
        left = expected.get(key)
        right = observed.get(key)
        if not valid_percent(left) or not valid_percent(right) or abs(float(left) - float(right)) > 1e-9:
            failures.append(key)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the completed 006 join against the exact Ofcom r2 ZIP")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--sample-size", type=int, default=64)
    args = parser.parse_args()

    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    if args.sample_size < 8 or args.sample_size > 256:
        raise RuntimeError("SAMPLE_SIZE_OUT_OF_RANGE")

    repo = Path(args.repo).expanduser().resolve()
    archive_path = Path(args.archive).expanduser().resolve()
    queue = read_json(repo / QUEUE_REL)
    validation = read_json(repo / VALIDATION_REL)
    source = read_json(repo / SOURCE_REL)
    manifest = read_json(repo / MANIFEST_REL)
    status = read_json(repo / STATUS_REL)
    output = read_jsonl(repo / DATA_REL)

    if queue.get("task_id") != TASK_ID:
        raise RuntimeError("TASK_ID_MISMATCH")
    if validation.get("source_scan_complete") is not True:
        raise RuntimeError("SOURCE_SCAN_COMPLETE_NOT_TRUE_AT_POSTJOIN")
    if int(validation.get("existing_shard2_rows") or 0) != EXPECTED_OUTPUT_ROWS:
        raise RuntimeError("VALIDATION_OUTPUT_ROW_COUNT_MISMATCH")
    if list(validation.get("missing_postcode_areas") or []):
        raise RuntimeError("VALIDATION_MISSING_POSTCODE_AREAS_NOT_EMPTY")
    if int(source.get("exact_rows_returned") or 0) <= 0:
        raise RuntimeError("SOURCE_EXACT_ROWS_NOT_POSITIVE_AT_POSTJOIN")
    if list(source.get("missing_postcode_areas") or []):
        raise RuntimeError("SOURCE_MISSING_POSTCODE_AREAS_NOT_EMPTY")
    status_state = str(status.get("state") or "").upper()
    if not status_state or any(token in status_state for token in ("FAILED", "ERROR", "BLOCKED", "PARTIAL")):
        raise RuntimeError(f"BUSINESS_STATUS_NOT_EXACT_AT_POSTJOIN:{status_state}")
    preflight = queue.get("strict_archive_preflight") or {}
    checks = preflight.get("checks") or {}
    if checks.get("all") is not True:
        raise RuntimeError("STRICT_ARCHIVE_PREFLIGHT_NOT_PASSED")
    if int(preflight.get("observed_r2_files") or 0) != EXPECTED_R2_FILES:
        raise RuntimeError("STRICT_PREFLIGHT_R2_FILE_COUNT_MISMATCH")
    if int(preflight.get("observed_rows") or 0) != EXPECTED_ARCHIVE_ROWS:
        raise RuntimeError("STRICT_PREFLIGHT_ARCHIVE_ROW_COUNT_MISMATCH")
    if not archive_path.is_file() or not zipfile.is_zipfile(archive_path):
        raise RuntimeError("ARCHIVE_NOT_AVAILABLE_AS_ZIP")

    archive_sha = sha256_file(archive_path)
    if str(preflight.get("archive_sha256") or "").lower() != archive_sha:
        raise RuntimeError("ARCHIVE_SHA256_DOES_NOT_MATCH_PREFLIGHT")
    if len(output) != EXPECTED_OUTPUT_ROWS:
        raise RuntimeError(f"OUTPUT_ROW_COUNT_MISMATCH:{len(output)}")

    verified = [row for row in output if row.get("official_coverage_verified") is True]
    pending = [row for row in output if row.get("onspd_status") == "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING" and row.get("official_coverage_verified") is not True]
    review = [row for row in output if row.get("onspd_status") != "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING"]
    if len(verified) + len(pending) + len(review) != EXPECTED_OUTPUT_ROWS:
        raise RuntimeError("OUTPUT_ACCOUNTING_FAILED")
    if int(validation.get("official_coverage_verified_candidates") or 0) != len(verified):
        raise RuntimeError("VALIDATION_VERIFIED_COUNT_MISMATCH")
    if int(validation.get("postcode_identity_confirmed_coverage_pending") or 0) != len(pending):
        raise RuntimeError("VALIDATION_PENDING_COUNT_MISMATCH")
    if int(validation.get("identity_missing_or_review") or 0) != len(review):
        raise RuntimeError("VALIDATION_REVIEW_COUNT_MISMATCH")
    if int(manifest.get("total_rows") or 0) != EXPECTED_OUTPUT_ROWS:
        raise RuntimeError("WEB_MANIFEST_TOTAL_MISMATCH")
    chunks = list(manifest.get("chunks") or [])
    if len(chunks) != EXPECTED_WEB_CHUNKS:
        raise RuntimeError(f"WEB_MANIFEST_CHUNK_COUNT_MISMATCH:{len(chunks)}")
    manifest_counts = manifest.get("counts") or {}
    if int(manifest_counts.get("verified_3_of_4") or 0) != len(verified):
        raise RuntimeError("WEB_MANIFEST_VERIFIED_COUNT_MISMATCH")
    if int(manifest_counts.get("identity_2_of_4_coverage_pending") or 0) != len(pending):
        raise RuntimeError("WEB_MANIFEST_PENDING_COUNT_MISMATCH")
    if int(manifest_counts.get("identity_missing_or_review") or 0) != len(review):
        raise RuntimeError("WEB_MANIFEST_REVIEW_COUNT_MISMATCH")

    cursor = 1
    chunk_rows_checked = 0
    for expected_chunk, chunk in enumerate(chunks, start=1):
        observed_chunk = int(chunk.get("chunk") or 0)
        row_start = int(chunk.get("row_start") or 0)
        row_end = int(chunk.get("row_end") or 0)
        count = int(chunk.get("count") or 0)
        if observed_chunk != expected_chunk:
            raise RuntimeError(f"WEB_MANIFEST_CHUNK_NUMBER_MISMATCH:{observed_chunk}:{expected_chunk}")
        if row_start != cursor or count <= 0 or row_end != row_start + count - 1:
            raise RuntimeError(f"WEB_MANIFEST_CHUNK_RANGE_MISMATCH:{expected_chunk}")
        relative = str(chunk.get("path") or "")
        if not relative:
            raise RuntimeError(f"WEB_MANIFEST_CHUNK_PATH_MISSING:{expected_chunk}")
        chunk_path = repo / Path(relative)
        chunk_doc = read_json(chunk_path)
        chunk_rows = chunk_doc.get("rows")
        if not isinstance(chunk_rows, list):
            raise RuntimeError(f"WEB_CHUNK_ROWS_LIST_REQUIRED:{expected_chunk}")
        if (
            chunk_doc.get("slot_id") != SLOT_ID
            or int(chunk_doc.get("chunk") or 0) != expected_chunk
            or int(chunk_doc.get("row_start") or 0) != row_start
            or int(chunk_doc.get("row_end") or 0) != row_end
            or len(chunk_rows) != count
        ):
            raise RuntimeError(f"WEB_CHUNK_METADATA_MISMATCH:{expected_chunk}")
        if chunk_rows != output[row_start - 1:row_end]:
            raise RuntimeError(f"WEB_CHUNK_OUTPUT_READBACK_MISMATCH:{expected_chunk}")
        cursor = row_end + 1
        chunk_rows_checked += count
    if cursor != EXPECTED_OUTPUT_ROWS + 1 or chunk_rows_checked != EXPECTED_OUTPUT_ROWS:
        raise RuntimeError("WEB_CHUNK_CONTIGUOUS_ACCOUNTING_FAILED")

    half = max(4, args.sample_size // 2)
    verified_sample = deterministic_unique(verified, half)
    pending_sample = deterministic_unique(pending, half)
    targets = {norm_postcode(row.get("postcode")) for row in [*verified_sample, *pending_sample]}

    with zipfile.ZipFile(archive_path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP_CRC_FAILURE:{bad}")
        r2_members = [name for name in archive.namelist() if R2.search(name.replace("\\", "/"))]
        if len(r2_members) != EXPECTED_R2_FILES:
            raise RuntimeError("RUNTIME_R2_FILE_COUNT_MISMATCH")
        direct = archive_rows(archive, targets)

    verified_failures: list[dict[str, Any]] = []
    for row in verified_sample:
        postcode = norm_postcode(row.get("postcode"))
        direct_row = direct.get(postcode)
        observed = metrics(direct_row)
        failed_keys = compare_metrics(row.get("official_metrics") or {}, observed)
        if not direct_row or failed_keys or row.get("internet_accuracy") != "3/4" or float(row.get("match_confidence") or 0.0) != 0.75:
            verified_failures.append({"postcode": postcode, "failed_keys": failed_keys, "direct_row_found": bool(direct_row)})

    false_pending: list[dict[str, Any]] = []
    for row in pending_sample:
        postcode = norm_postcode(row.get("postcode"))
        observed = metrics(direct.get(postcode))
        if all(valid_percent(observed.get(key)) for key in CORE_KEYS):
            false_pending.append({"postcode": postcode, "reason": "DIRECT_ARCHIVE_CORE_METRICS_COMPLETE"})

    review_failures = [
        {"postcode": norm_postcode(row.get("postcode")), "accuracy": row.get("internet_accuracy")}
        for row in review
        if row.get("official_coverage_verified") is True or row.get("internet_accuracy") == "3/4"
    ]
    failures = {
        "verified_sample_failures": verified_failures,
        "false_pending_sample": false_pending,
        "identity_review_failures": review_failures,
    }
    if any(failures.values()):
        raise RuntimeError("POSTJOIN_READBACK_FAILED:" + json.dumps(failures, sort_keys=True))

    access = source.get("access") or {}
    if access.get("state") not in {"CACHE_HIT", "DOWNLOADED"}:
        raise RuntimeError("SOURCE_ACCESS_STATE_NOT_EXACT")

    result = {
        "state": "PASS_EXACT_ARCHIVE_POSTJOIN_READBACK",
        "validated_at": now(),
        "archive_sha256": archive_sha,
        "archive_bytes": archive_path.stat().st_size,
        "strict_preflight_r2_files": EXPECTED_R2_FILES,
        "strict_preflight_rows": EXPECTED_ARCHIVE_ROWS,
        "output_rows": EXPECTED_OUTPUT_ROWS,
        "verified_rows": len(verified),
        "coverage_pending_rows": len(pending),
        "identity_review_rows": len(review),
        "verified_sample_postcodes": [norm_postcode(row.get("postcode")) for row in verified_sample],
        "pending_sample_postcodes": [norm_postcode(row.get("postcode")) for row in pending_sample],
        "sample_size_requested": args.sample_size,
        "sample_rows_checked": len(verified_sample) + len(pending_sample),
        "web_chunks_checked": len(chunks),
        "web_chunk_rows_checked": chunk_rows_checked,
        "source_exact_rows_returned": int(source.get("exact_rows_returned") or 0),
        "source_scan_complete": True,
        "zip_crc_ok": True,
        "candidate_promotion_performed": False,
        "final_ready": False,
    }
    validation["postjoin_readback"] = result
    validation["postjoin_readback_guard"] = "PASS"
    validation["final_ready"] = False
    write_json_atomic(repo / VALIDATION_REL, validation)

    status["postjoin_readback_guard"] = "PASS"
    status["postjoin_readback"] = result
    status["final_ready"] = False
    status["updated_at"] = now()
    write_json_atomic(repo / STATUS_REL, status)

    with (repo / PROGRESS_REL).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({
            "at": now(),
            "step": 5,
            "operation": "exact_archive_postjoin_readback_guard",
            "state": "PASS",
            "archive_sha256": archive_sha,
            "sample_rows_checked": result["sample_rows_checked"],
            "verified_rows": len(verified),
            "coverage_pending_rows": len(pending),
            "identity_review_rows": len(review),
            "final_ready": False,
        }, ensure_ascii=False, sort_keys=True) + "\n")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
