# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
EXPECTED_ROWS = 11013
WEB_CHUNK_SIZE = 500
MATERIAL_DELTA_PP = 10.0
BASE_SCRIPT = "006_ofcom_dynamic_zip_join_existing_11013.py"
SHARD_REL = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_2"
)
CORE_KEYS = (
    "gigabit_available_pct",
    "ultrafast_100mbps_available_pct",
    "superfast_30mbps_available_pct",
    "unable_30mbps_pct",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs/chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def valid_percent(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 100.0


def load_base_module(path: Path):
    spec = importlib.util.spec_from_file_location("internet_access_2_ofcom_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("BASE_SCRIPT_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")

    root = repo_root()
    shard = root / SHARD_REL
    base_path = shard / "automation" / BASE_SCRIPT
    module = load_base_module(base_path)
    result = int(module.main())
    if result != 0:
        return result

    data_path = shard / "data/006_existing_11013_official_coverage_candidates.jsonl"
    validation_path = shard / "validation/006_existing_11013_coverage_validation.json"
    manifest_path = shard / "web/006_existing_11013_rows_manifest.json"
    source_path = shard / "source_snapshots/006_ofcom_binary_readback.json"
    status_path = shard / "status/006_status.json"
    progress_path = shard / "progress/006_progress.jsonl"

    rows = read_jsonl(data_path)
    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(f"STRICT_GUARD_EXPECTED_{EXPECTED_ROWS}_ROWS_GOT_{len(rows)}")

    source = read_json(source_path)
    access = source.get("access") or {}
    zip_access_ok = access.get("state") in {"CACHE_HIT", "DOWNLOADED"}
    missing_areas = list(source.get("missing_postcode_areas") or [])

    verified = 0
    coverage_pending = 0
    identity_review = 0
    invalid_metric_rows = 0
    material_delta_rows = 0
    hardened: list[dict[str, Any]] = []

    for line_no, row in enumerate(rows, start=1):
        metrics = row.get("official_metrics") or {}
        live_identity = row.get("onspd_status") == "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING"
        metric_range_ok = all(valid_percent(metrics.get(key)) for key in CORE_KEYS)
        strict_verified = bool(row.get("official_coverage_verified") and live_identity and metric_range_ok)

        legacy = row.get("legacy_metrics") or {}
        deltas: dict[str, float] = {}
        for key in CORE_KEYS:
            official_value = metrics.get(key)
            legacy_value = legacy.get(key)
            if valid_percent(official_value) and valid_percent(legacy_value):
                deltas[key] = round(float(official_value) - float(legacy_value), 3)
        material_delta = any(abs(value) >= MATERIAL_DELTA_PP for value in deltas.values())
        if material_delta:
            material_delta_rows += 1

        if row.get("official_metrics") and not metric_range_ok:
            invalid_metric_rows += 1

        if strict_verified:
            verified += 1
            candidate_status = "VERIFIED_POSTCODE_PROXY_CANDIDATE_REVIEW_PENDING" if material_delta else "VERIFIED_POSTCODE_PROXY_CANDIDATE"
            accuracy = "3/4"
            confidence = 0.75
            source_level = "POSTCODE_PROXY"
        elif live_identity:
            coverage_pending += 1
            candidate_status = "POSTCODE_IDENTITY_CONFIRMED_COVERAGE_PENDING"
            accuracy = "2/4"
            confidence = 0.0
            source_level = "POSTCODE_IDENTITY_ONLY"
        else:
            identity_review += 1
            candidate_status = row.get("candidate_status") or "NO_DATA_NOT_INFERRED"
            accuracy = row.get("internet_accuracy") or "0/4"
            confidence = 0.0
            source_level = "POSTCODE_IDENTITY_ONLY"

        hardened.append({
            **row,
            "line": line_no,
            "official_coverage_verified": strict_verified,
            "official_metric_range_guard": metric_range_ok,
            "legacy_official_delta_pp": deltas,
            "material_delta_threshold_pp": MATERIAL_DELTA_PP,
            "material_delta_review_required": material_delta,
            "candidate_status": candidate_status,
            "internet_accuracy": accuracy,
            "match_confidence": confidence,
            "source_level": source_level,
            "parcel_measured_speed": False,
            "fake_data": False,
            "final_ready": False,
        })

    if verified + coverage_pending + identity_review != EXPECTED_ROWS:
        raise RuntimeError("STRICT_GUARD_ROW_ACCOUNTING_FAILED")

    write_jsonl(data_path, hardened)

    web_root = shard / "web/006_chunks"
    chunks: list[dict[str, Any]] = []
    for chunk_no, start in enumerate(range(0, len(hardened), WEB_CHUNK_SIZE), start=1):
        chunk_rows = hardened[start:start + WEB_CHUNK_SIZE]
        chunk_path = web_root / f"part_{chunk_no:03d}.json"
        write_json(chunk_path, {
            "slot_id": SLOT_ID,
            "chunk": chunk_no,
            "row_start": start + 1,
            "row_end": start + len(chunk_rows),
            "rows": chunk_rows,
            "final_ready": False,
        })
        chunks.append({
            "chunk": chunk_no,
            "path": str(chunk_path.relative_to(root)).replace("\\", "/"),
            "row_start": start + 1,
            "row_end": start + len(chunk_rows),
            "count": len(chunk_rows),
        })

    source_scan_complete = bool(zip_access_ok and not missing_areas)
    blocker = None if source_scan_complete else (
        access.get("blocker") or "OFCom_2026_EXACT_SOURCE_SCAN_PARTIAL_OR_BLOCKED"
    )

    validation = read_json(validation_path)
    validation.update({
        "official_coverage_verified_candidates": verified,
        "postcode_identity_confirmed_coverage_pending": coverage_pending,
        "identity_missing_or_review": identity_review,
        "invalid_official_metric_rows": invalid_metric_rows,
        "material_delta_review_rows": material_delta_rows,
        "strict_accuracy_guard": "PASS",
        "source_scan_complete": source_scan_complete,
        "missing_postcode_areas": missing_areas,
        "blocker": blocker,
        "maximum_accuracy": "3/4_POSTCODE_PROXY",
        "parcel_measured_values_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "validated_at": utc_now(),
    })
    write_json(validation_path, validation)

    write_json(manifest_path, {
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "total_rows": len(hardened),
        "chunk_size": WEB_CHUNK_SIZE,
        "chunks": chunks,
        "counts": {
            "verified_3_of_4": verified,
            "identity_2_of_4_coverage_pending": coverage_pending,
            "identity_missing_or_review": identity_review,
            "invalid_official_metric_rows": invalid_metric_rows,
            "material_delta_review_rows": material_delta_rows,
        },
        "strict_accuracy_guard": "PASS",
        "final_ready": False,
    })

    status = read_json(status_path)
    status.update({
        "state": "OFFICIAL_COVERAGE_SOURCE_SCANNED_REVIEW_PENDING" if source_scan_complete else "OFFICIAL_COVERAGE_SOURCE_BLOCKED_OR_PARTIAL",
        "completed_operations": 5,
        "total_operations": 6,
        "progress_percent": 83.33,
        "official_coverage_verified_candidates": verified,
        "postcode_identity_confirmed_coverage_pending": coverage_pending,
        "identity_missing_or_review": identity_review,
        "invalid_official_metric_rows": invalid_metric_rows,
        "material_delta_review_rows": material_delta_rows,
        "strict_accuracy_guard": "PASS",
        "blocker": blocker,
        "next_step": "REVIEW_MATERIAL_DELTAS_AND_NO_DATA_ROWS_THEN_PUBLISH_CANONICAL_SHARD2_CANDIDATES" if source_scan_complete else "PROVISION_OFFICIAL_OFCom_ZIP_OR_SUBSCRIPTION_KEY_THEN_RETRY_EXACT_COVERAGE_JOIN",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "updated_at": utc_now(),
    })
    write_json(status_path, status)

    with progress_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({
            "at": utc_now(),
            "step": 5,
            "operation": "strict_accuracy_and_completion_guard",
            "state": "PASS",
            "rows": EXPECTED_ROWS,
            "verified": verified,
            "coverage_pending": coverage_pending,
            "identity_review": identity_review,
            "invalid_metric_rows": invalid_metric_rows,
            "material_delta_rows": material_delta_rows,
            "source_scan_complete": source_scan_complete,
            "progress_percent": 83.33,
            "final_ready": False,
        }, ensure_ascii=False, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
