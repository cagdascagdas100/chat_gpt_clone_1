from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"
EXPECTED_BLOB = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_FEATURE_COUNT = 92283
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
ALLOWED_CHAIN_STATES = {"BLOCKED_EPOCH_PROVENANCE", "CHAIN_EXECUTION_PASS_NONFINAL"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class StrictJsonError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def reject_constant(value: str) -> None:
    raise StrictJsonError(f"NONFINITE_JSON_CONSTANT:{value}")


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise StrictJsonError(f"DUPLICATE_JSON_KEY:{key}")
        out[key] = value
    return out


def strict_load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp = Path(tmp.name)
    os.replace(temp, path)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def iso_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def flag_false(doc: dict[str, Any], key: str) -> bool:
    return doc.get(key) is False


def zero_business(doc: dict[str, Any]) -> bool:
    return doc.get("actual_business_data_rows_written") == 0


def require(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)


def validate_finality(doc: dict[str, Any], prefix: str, errors: list[str]) -> None:
    require(flag_false(doc, "fake_data"), f"{prefix}_FAKE_DATA_NOT_FALSE", errors)
    require(flag_false(doc, "final_ready"), f"{prefix}_FINAL_READY_NOT_FALSE", errors)
    require(zero_business(doc), f"{prefix}_BUSINESS_ROWS_NOT_ZERO", errors)
    for key in ("db_write", "migration", "production_deploy"):
        if key in doc:
            require(doc.get(key) is False, f"{prefix}_{key.upper()}_NOT_FALSE", errors)


def validate_rows(rows: Any, errors: list[str], prefix: str) -> None:
    require(isinstance(rows, list) and len(rows) == 3, f"{prefix}_ROW_COUNT_NOT_3", errors)
    if not isinstance(rows, list):
        return
    ids: list[str] = []
    for index, row in enumerate(rows):
        require(isinstance(row, dict), f"{prefix}_ROW_{index}_NOT_OBJECT", errors)
        if not isinstance(row, dict):
            continue
        parcel_id = row.get("parcel_id")
        ids.append(str(parcel_id))
        require(row.get("geometry_type") == "Point", f"{prefix}_{parcel_id}_GEOMETRY_NOT_POINT", errors)
        lon = row.get("longitude")
        lat = row.get("latitude")
        require(finite_number(lon) and -180 <= float(lon) <= 180, f"{prefix}_{parcel_id}_LONGITUDE_INVALID", errors)
        require(finite_number(lat) and -90 <= float(lat) <= 90, f"{prefix}_{parcel_id}_LATITUDE_INVALID", errors)
        require(row.get("finite_coordinates") is True, f"{prefix}_{parcel_id}_FINITE_FLAG_NOT_TRUE", errors)
        require(row.get("source_blob_sha") == EXPECTED_BLOB, f"{prefix}_{parcel_id}_SOURCE_BLOB_MISMATCH", errors)
    require(ids == TARGET_IDS, f"{prefix}_TARGET_ORDER_INVALID:{ids}", errors)
    require(len(set(ids)) == 3, f"{prefix}_TARGET_IDS_NOT_UNIQUE", errors)


def validate_canonical(doc: Any, errors: list[str], prefix: str) -> dict[str, Any]:
    require(isinstance(doc, dict), f"{prefix}_NOT_OBJECT", errors)
    if not isinstance(doc, dict):
        return {}
    require(doc.get("slot_id") == SLOT_ID, f"{prefix}_SLOT_MISMATCH", errors)
    source = doc.get("source")
    require(isinstance(source, dict), f"{prefix}_SOURCE_MISSING", errors)
    if isinstance(source, dict):
        require(source.get("git_blob_sha") == EXPECTED_BLOB, f"{prefix}_BLOB_MISMATCH", errors)
        require(source.get("resolved_path_blob_sha") == EXPECTED_BLOB, f"{prefix}_RESOLVED_BLOB_MISMATCH", errors)
        require(source.get("git_object_type") == "blob", f"{prefix}_OBJECT_TYPE_NOT_BLOB", errors)
        require(source.get("expected_feature_count") == EXPECTED_FEATURE_COUNT, f"{prefix}_EXPECTED_FEATURE_COUNT_INVALID", errors)
        stream_sha = source.get("stream_sha256")
        require(isinstance(stream_sha, str) and HEX64.fullmatch(stream_sha) is not None, f"{prefix}_STREAM_SHA256_INVALID", errors)
        require(isinstance(source.get("source_size_bytes"), int) and source.get("source_size_bytes") > 0, f"{prefix}_SOURCE_SIZE_INVALID", errors)
    require(doc.get("target_ids") == TARGET_IDS, f"{prefix}_TARGET_IDS_INVALID", errors)
    require(doc.get("canonical_point_row_count") == 3, f"{prefix}_ROW_COUNT_FIELD_INVALID", errors)
    rows = doc.get("canonical_point_rows")
    validate_rows(rows, errors, prefix)
    acceptance = doc.get("acceptance")
    require(isinstance(acceptance, dict), f"{prefix}_ACCEPTANCE_MISSING", errors)
    required_acceptance = (
        "exact_path_blob_match", "exact_target_order", "unique_output_target_ids",
        "unique_source_target_occurrences", "all_point_geometry", "all_finite_coordinates",
        "full_stream_hashed", "full_feature_array_parsed", "feature_count_matches_expected", "passed",
    )
    if isinstance(acceptance, dict):
        for key in required_acceptance:
            require(acceptance.get(key) is True, f"{prefix}_ACCEPTANCE_{key.upper()}_NOT_TRUE", errors)
    metrics = doc.get("stream_metrics")
    require(isinstance(metrics, dict), f"{prefix}_STREAM_METRICS_MISSING", errors)
    if isinstance(metrics, dict):
        require(metrics.get("features_array_found") is True, f"{prefix}_FEATURE_ARRAY_NOT_FOUND", errors)
        require(metrics.get("features_array_closed") is True, f"{prefix}_FEATURE_ARRAY_NOT_CLOSED", errors)
        require(metrics.get("features_scanned") == EXPECTED_FEATURE_COUNT, f"{prefix}_FEATURES_SCANNED_INVALID", errors)
        require(metrics.get("expected_feature_count") == EXPECTED_FEATURE_COUNT, f"{prefix}_METRIC_EXPECTED_COUNT_INVALID", errors)
        require(metrics.get("feature_count_matches_expected") is True, f"{prefix}_FEATURE_COUNT_MATCH_FALSE", errors)
        require(metrics.get("full_feature_array_parsed") is True, f"{prefix}_FULL_ARRAY_PARSED_FALSE", errors)
        require(metrics.get("full_stream_hashed") is True, f"{prefix}_FULL_STREAM_HASHED_FALSE", errors)
        require(metrics.get("error") is None, f"{prefix}_STREAM_ERROR_PRESENT", errors)
        occurrences = metrics.get("target_occurrence_counts")
        require(isinstance(occurrences, dict), f"{prefix}_OCCURRENCES_MISSING", errors)
        if isinstance(occurrences, dict):
            require({key: occurrences.get(key) for key in TARGET_IDS} == {key: 1 for key in TARGET_IDS}, f"{prefix}_OCCURRENCES_INVALID", errors)
        require(metrics.get("duplicate_target_ids") == [], f"{prefix}_DUPLICATE_TARGETS_PRESENT", errors)
        require(metrics.get("targets_found") == TARGET_IDS, f"{prefix}_TARGETS_FOUND_INVALID", errors)
    require(doc.get("errors") == [], f"{prefix}_ERRORS_NOT_EMPTY", errors)
    validate_finality(doc, prefix, errors)
    return doc


def canonical_projection(doc: dict[str, Any]) -> dict[str, Any]:
    source = doc.get("source") or {}
    metrics = doc.get("stream_metrics") or {}
    return {
        "slot_id": doc.get("slot_id"),
        "source": {
            "git_blob_sha": source.get("git_blob_sha"),
            "resolved_path_blob_sha": source.get("resolved_path_blob_sha"),
            "stream_sha256": source.get("stream_sha256"),
            "source_size_bytes": source.get("source_size_bytes"),
            "expected_feature_count": source.get("expected_feature_count"),
        },
        "target_ids": doc.get("target_ids"),
        "canonical_point_rows": doc.get("canonical_point_rows"),
        "canonical_point_row_count": doc.get("canonical_point_row_count"),
        "occurrences": metrics.get("target_occurrence_counts"),
        "features_scanned": metrics.get("features_scanned"),
        "acceptance": doc.get("acceptance"),
    }


def validate_probe(doc: Any, errors: list[str]) -> None:
    prefix = "PROBE"
    require(isinstance(doc, dict), f"{prefix}_NOT_OBJECT", errors)
    if not isinstance(doc, dict):
        return
    require(doc.get("slot_id") == SLOT_ID, f"{prefix}_SLOT_MISMATCH", errors)
    source = doc.get("source")
    require(isinstance(source, dict), f"{prefix}_SOURCE_MISSING", errors)
    if isinstance(source, dict):
        require(source.get("expected_blob_sha") == EXPECTED_BLOB, f"{prefix}_EXPECTED_BLOB_MISMATCH", errors)
        require(source.get("resolved_path_blob_sha") == EXPECTED_BLOB, f"{prefix}_RESOLVED_BLOB_MISMATCH", errors)
        require(source.get("object_type") == "blob", f"{prefix}_OBJECT_TYPE_NOT_BLOB", errors)
        require(isinstance(source.get("object_size_bytes"), int) and source.get("object_size_bytes") > 0, f"{prefix}_OBJECT_SIZE_INVALID", errors)
        require(isinstance(source.get("bounded_prefix_sha256"), str) and HEX64.fullmatch(source.get("bounded_prefix_sha256")) is not None, f"{prefix}_PREFIX_SHA256_INVALID", errors)
    decision = doc.get("decision")
    require(isinstance(decision, dict), f"{prefix}_DECISION_MISSING", errors)
    if isinstance(decision, dict):
        require(decision.get("policy") in {"UNKNOWN_FAIL_CLOSED", "ETRS89_EQUIVALENCE_PROVEN", "WGS84_TO_ETRS89_TRANSFORM_PROVEN"}, f"{prefix}_POLICY_INVALID", errors)
        require(isinstance(decision.get("accepted"), bool), f"{prefix}_ACCEPTED_NOT_BOOL", errors)
        require(isinstance(decision.get("blockers"), list), f"{prefix}_BLOCKERS_NOT_LIST", errors)
    require(doc.get("errors") == [], f"{prefix}_ERRORS_NOT_EMPTY", errors)
    validate_finality(doc, prefix, errors)


def validate_watchdog(doc: Any, errors: list[str]) -> None:
    prefix = "WATCHDOG"
    require(isinstance(doc, dict), f"{prefix}_NOT_OBJECT", errors)
    if not isinstance(doc, dict):
        return
    require(doc.get("slot_id") == SLOT_ID, f"{prefix}_SLOT_MISMATCH", errors)
    require(doc.get("state") in ALLOWED_CHAIN_STATES, f"{prefix}_STATE_INVALID", errors)
    started = iso_utc(doc.get("started_at"))
    completed = iso_utc(doc.get("completed_at"))
    require(started is not None and completed is not None and completed >= started, f"{prefix}_TIME_RANGE_INVALID", errors)
    require(finite_number(doc.get("duration_seconds")) and float(doc.get("duration_seconds")) >= 0, f"{prefix}_DURATION_INVALID", errors)
    rows = doc.get("process_rows")
    require(isinstance(rows, list) and len(rows) >= 4, f"{prefix}_PROCESS_ROWS_INVALID", errors)
    timeouts = 0
    kills = 0
    if isinstance(rows, list):
        names: list[str] = []
        for i, row in enumerate(rows):
            require(isinstance(row, dict), f"{prefix}_ROW_{i}_NOT_OBJECT", errors)
            if not isinstance(row, dict):
                continue
            name = row.get("name")
            names.append(str(name))
            require(isinstance(name, str) and name, f"{prefix}_ROW_{i}_NAME_INVALID", errors)
            require(isinstance(row.get("timeout_seconds"), int) and row.get("timeout_seconds") >= 30, f"{prefix}_{name}_TIMEOUT_INVALID", errors)
            require(finite_number(row.get("duration_seconds")) and float(row.get("duration_seconds")) >= 0, f"{prefix}_{name}_DURATION_INVALID", errors)
            timed_out = row.get("timed_out")
            kill_attempted = row.get("kill_attempted")
            kill_succeeded = row.get("kill_succeeded")
            require(isinstance(timed_out, bool), f"{prefix}_{name}_TIMED_OUT_NOT_BOOL", errors)
            require(isinstance(kill_attempted, bool), f"{prefix}_{name}_KILL_ATTEMPTED_NOT_BOOL", errors)
            require(isinstance(kill_succeeded, bool), f"{prefix}_{name}_KILL_SUCCEEDED_NOT_BOOL", errors)
            if timed_out is True:
                timeouts += 1
                require(kill_attempted is True, f"{prefix}_{name}_TIMEOUT_WITHOUT_KILL_ATTEMPT", errors)
                require(kill_succeeded is True, f"{prefix}_{name}_TIMEOUT_WITHOUT_TREE_KILL", errors)
                require(row.get("passed") is False, f"{prefix}_{name}_TIMEOUT_MARKED_PASS", errors)
            if kill_succeeded is True:
                kills += 1
            if row.get("passed") is True:
                require(timed_out is False and row.get("exit_code") == 0, f"{prefix}_{name}_PASS_CONTRACT_INVALID", errors)
        require(len(names) == len(set(names)), f"{prefix}_PROCESS_NAMES_NOT_UNIQUE", errors)
    require(doc.get("timeout_count") == timeouts, f"{prefix}_TIMEOUT_COUNT_MISMATCH", errors)
    require(doc.get("killed_process_tree_count") == kills, f"{prefix}_KILL_COUNT_MISMATCH", errors)
    require(isinstance(doc.get("blockers"), list), f"{prefix}_BLOCKERS_NOT_LIST", errors)
    validate_finality(doc, prefix, errors)


def validate_chain(doc: Any, watchdog: Any, errors: list[str]) -> None:
    prefix = "CHAIN"
    require(isinstance(doc, dict), f"{prefix}_NOT_OBJECT", errors)
    if not isinstance(doc, dict):
        return
    require(doc.get("slot_id") == SLOT_ID, f"{prefix}_SLOT_MISMATCH", errors)
    require(doc.get("expected_blob_sha") == EXPECTED_BLOB, f"{prefix}_EXPECTED_BLOB_MISMATCH", errors)
    require(doc.get("state") in ALLOWED_CHAIN_STATES, f"{prefix}_STATE_INVALID", errors)
    require(doc.get("canonical_point_output_exists") is True, f"{prefix}_CANONICAL_FLAG_FALSE", errors)
    require(doc.get("epoch_provenance_probe_output_exists") is True, f"{prefix}_PROBE_FLAG_FALSE", errors)
    require(doc.get("execution_watchdog_path") == "docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_execution_watchdog_latest.json", f"{prefix}_WATCHDOG_PATH_INVALID", errors)
    if isinstance(watchdog, dict):
        require(doc.get("state") == watchdog.get("state"), f"{prefix}_WATCHDOG_STATE_MISMATCH", errors)
        require(doc.get("steps") == watchdog.get("process_rows"), f"{prefix}_WATCHDOG_ROWS_MISMATCH", errors)
    started = iso_utc(doc.get("started_at"))
    completed = iso_utc(doc.get("completed_at"))
    require(started is not None and completed is not None and completed >= started, f"{prefix}_TIME_RANGE_INVALID", errors)
    require(isinstance(doc.get("blockers"), list), f"{prefix}_BLOCKERS_NOT_LIST", errors)
    validate_finality(doc, prefix, errors)


def validate_paths(repo: Path, paths: dict[str, str]) -> dict[str, Any]:
    errors: list[str] = []
    docs: dict[str, Any] = {}
    for name, rel in paths.items():
        path = repo / rel
        if not path.is_file():
            errors.append(f"{name.upper()}_FILE_MISSING")
            continue
        try:
            docs[name] = strict_load(path)
        except Exception as exc:
            errors.append(f"{name.upper()}_STRICT_JSON_FAILED:{type(exc).__name__}:{exc}")
    canonical = validate_canonical(docs.get("canonical"), errors, "CANONICAL")
    reconciliation = validate_canonical(docs.get("reconciliation"), errors, "RECONCILIATION")
    website = validate_canonical(docs.get("website_canonical"), errors, "WEBSITE_CANONICAL")
    if canonical and reconciliation:
        require(canonical_projection(canonical) == canonical_projection(reconciliation), "CANONICAL_RECONCILIATION_MISMATCH", errors)
        require(reconciliation.get("reconciliation_kind") == "EXACT_BLOB_FULL_ARRAY_ORDERED_THREE_POINT_EXTRACTION", "RECONCILIATION_KIND_INVALID", errors)
        require(reconciliation.get("expected_target_count") == 3 and reconciliation.get("observed_target_count") == 3, "RECONCILIATION_TARGET_COUNTS_INVALID", errors)
    if canonical and website:
        require(canonical_projection(canonical) == canonical_projection(website), "CANONICAL_WEBSITE_MISMATCH", errors)
        require(website.get("rows_visible") == 3, "WEBSITE_ROWS_VISIBLE_INVALID", errors)
    validate_probe(docs.get("probe"), errors)
    validate_watchdog(docs.get("watchdog"), errors)
    validate_chain(docs.get("chain"), docs.get("watchdog"), errors)
    return {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "validated_at": utc_now(),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "validated_paths": paths,
        "canonical_projection": canonical_projection(canonical) if canonical else None,
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    manifest = strict_load(Path(args.manifest))
    if manifest.get("slot_id") != SLOT_ID:
        raise SystemExit("MANIFEST_SLOT_MISMATCH")
    report = validate_paths(repo, manifest["required_checkpoint_paths"])
    atomic_json(Path(args.output), report)
    print(f"HD3_STRICT_CHECKPOINT_VALID={str(report['valid']).lower()}")
    print(f"HD3_STRICT_CHECKPOINT_ERRORS={report['error_count']}")
    print("FINAL_READY=false")
    return 0 if report["valid"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
