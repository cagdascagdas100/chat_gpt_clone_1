from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("security_public_safety_3_smoke_v5_2_9.py")
TASK_VERSION = "5.2.10-publication-quarantine-digest"
ATTEMPT_ID = "security-public-safety-3-20260721-019"
SUPERSEDES_ATTEMPT_ID = "security-public-safety-3-20260721-018"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
FOUR_GATES = ["canonical_gate", "crime_api_gate", "outcomes_api_gate", "iod25_gate"]
BASE_META_GATES = [
    "artifact_quorum_passed",
    "attempt_lineage_gate",
    "row_lineage_immutable_gate",
    "reconciliation_consistency_gate",
    "gate_count_consistency_gate",
    "top_level_counter_consistency_gate",
    "official_evidence_fingerprint_gate",
]
RECON_REQUIRED_TRUE = [
    "runtime_execution_complete",
    "runtime_acceptance_passed",
    "canonical_source_acceptance_passed",
    "target_identity_acceptance_passed",
    "official_latest_month_acceptance_passed",
    "ordered_identity_match",
    "requires_at_least_one_accuracy_4_for_success",
    "requires_list_payload_for_api_gates",
    "requires_force_lookup_for_api_gates",
    "requires_territorial_coverage_for_api_gates",
    "requires_nonempty_iod25_crime_fields",
    "all_unverified_published_scores_null",
    "all_row_memory_gates_passed",
]


def load_base():
    spec = importlib.util.spec_from_file_location(
        "security_public_safety_3_smoke_v5_2_9_base", BASE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load V5.2.9 verifier: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def finite_number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def valid_sha256(value: object) -> str | None:
    text = str(value or "").lower()
    return text if len(text) == 64 and all(ch in "0123456789abcdef" for ch in text) else None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def row_counts(payload: dict[str, Any]) -> dict[str, int]:
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    dict_rows = [row for row in rows if isinstance(row, dict)]
    return {
        "actual_rows": len(dict_rows),
        "unique_rows": len({row.get("parcel_id") for row in dict_rows}),
        "passed_gate_cells": sum(sum(bool(row.get(name)) for name in FOUR_GATES) for row in dict_rows),
        "accuracy_score_4_count": sum(row.get("accuracy_score_4") == 4 for row in dict_rows),
        "force_lookup_acceptance_pass_count": sum(bool(row.get("force_lookup_gate")) for row in dict_rows),
    }


def validate_primary(name: str, payload: dict[str, Any]) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    dict_rows = [row for row in rows if isinstance(row, dict)]
    ids = [row.get("parcel_id") for row in dict_rows]
    if len(rows) != 3 or len(dict_rows) != 3 or ids != TARGET_IDS or len(set(ids)) != 3:
        errors.append(f"{name}:ORDERED_THREE_ROW_IDENTITY_MISMATCH")
    if payload.get("attempt_id") != ATTEMPT_ID or payload.get("task_version") != TASK_VERSION:
        errors.append(f"{name}:CURRENT_LINEAGE_MISMATCH")
    if not payload.get("runtime_execution_complete") or not payload.get("runtime_acceptance_passed"):
        errors.append(f"{name}:BASE_RUNTIME_NOT_ACCEPTED")
    for gate in BASE_META_GATES:
        if not payload.get(gate):
            errors.append(f"{name}:BASE_META_GATE_FALSE:{gate}")
    evidence_fp = valid_sha256(payload.get("run_evidence_fingerprint"))
    if evidence_fp is None:
        errors.append(f"{name}:BASE_EVIDENCE_FINGERPRINT_MISSING")
    for row in dict_rows:
        parcel_id = row.get("parcel_id")
        if row.get("attempt_id") != ATTEMPT_ID or row.get("task_version") != TASK_VERSION:
            errors.append(f"{name}:ROW_LINEAGE_MISMATCH:{parcel_id}")
        four_count = sum(bool(row.get(gate)) for gate in FOUR_GATES)
        if row.get("accuracy_score_4") != four_count:
            errors.append(f"{name}:ROW_GATE_COUNT_MISMATCH:{parcel_id}")
        score = finite_number(row.get("security_score_percent"))
        if four_count == 4:
            if score is None or not 0.0 <= score <= 100.0:
                errors.append(f"{name}:RELEASABLE_SCORE_INVALID:{parcel_id}")
        elif row.get("security_score_percent") is not None:
            errors.append(f"{name}:UNVERIFIED_SCORE_NOT_NULL:{parcel_id}")
    counts = row_counts(payload)
    expected_top = {
        "sample_count": counts["actual_rows"],
        "passed_acceptance_gate_cells": counts["passed_gate_cells"],
        "accuracy_score_4_count": counts["accuracy_score_4_count"],
        "verified_slot_rows": counts["accuracy_score_4_count"],
        "actual_slot_rows_written": counts["accuracy_score_4_count"],
    }
    for key, expected in expected_top.items():
        if payload.get(key) != expected:
            errors.append(f"{name}:TOP_COUNT_MISMATCH:{key}")
    if counts["accuracy_score_4_count"] < 1:
        errors.append(f"{name}:ZERO_RELEASABLE_ROWS")
    return sorted(set(errors)), counts


def reconciliation_signature(payload: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "expected_rows", "actual_rows", "unique_rows", "ordered_identity_match",
        "expected_gate_cells", "passed_gate_cells", "accuracy_score_4_count",
        "force_lookup_acceptance_pass_count", "memory_row_gate_pass_count",
        "memory_row_gate_expected_count", *RECON_REQUIRED_TRUE,
    ]
    return {key: payload.get(key) for key in keys}


def validate_reconciliation(payload: dict[str, Any], expected_counts: dict[str, int], evidence_fp: str) -> list[str]:
    errors: list[str] = []
    if payload.get("attempt_id") != ATTEMPT_ID or payload.get("task_version") != TASK_VERSION:
        errors.append("RECONCILIATION_CURRENT_LINEAGE_MISMATCH")
    for key in RECON_REQUIRED_TRUE:
        if not payload.get(key):
            errors.append(f"RECONCILIATION_FLAG_FALSE:{key}")
    expected = {
        "expected_rows": 3,
        "actual_rows": expected_counts["actual_rows"],
        "unique_rows": expected_counts["unique_rows"],
        "expected_gate_cells": 12,
        "passed_gate_cells": expected_counts["passed_gate_cells"],
        "accuracy_score_4_count": expected_counts["accuracy_score_4_count"],
        "force_lookup_acceptance_pass_count": expected_counts["force_lookup_acceptance_pass_count"],
        "memory_row_gate_pass_count": 3,
        "memory_row_gate_expected_count": 3,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            errors.append(f"RECONCILIATION_COUNT_MISMATCH:{key}")
    if valid_sha256(payload.get("run_evidence_fingerprint")) != evidence_fp:
        errors.append("RECONCILIATION_EVIDENCE_FINGERPRINT_MISMATCH")
    return sorted(set(errors))


def sanitize_primary(payload: dict[str, Any], publication_passed: bool) -> int:
    published = 0
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        releasable = bool(publication_passed and row.get("accuracy_score_4") == 4 and finite_number(row.get("security_score_percent")) is not None)
        row["publication_quarantine_gate"] = publication_passed
        row["published_score_release_gate"] = releasable
        row["prepublication_artifact_digest_gate"] = publication_passed
        if releasable:
            published += 1
        else:
            row["security_score_percent"] = None
            row["needs_manual_review"] = True
            current = str(row.get("candidate_status") or "")
            if not current.startswith("PUBLICATION_QUARANTINED_"):
                row["candidate_status"] = "PUBLICATION_QUARANTINED_" + current
    payload["published_score_row_count"] = published
    payload["verified_slot_rows"] = published
    payload["actual_slot_rows_written"] = published
    return published


def enrich(repo_root: Path, prior_return_code: int) -> int:
    paths = {
        "output": repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_candidates_v5_2_latest.json",
        "website": repo_root / "england_map_web/data/security_public_safety/security_public_safety_3_smoke_rows_latest.json",
        "reconciliation": repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_reconciliation_v5_2_latest.json",
    }
    exists = {name: path.is_file() for name, path in paths.items()}
    errors: list[str] = []
    if prior_return_code != 0:
        errors.append(f"BASE_EXIT_NONZERO:{prior_return_code}")
    for name, present in exists.items():
        if not present:
            errors.append(f"MISSING_ARTIFACT:{name}")
    payloads: dict[str, dict[str, Any]] = {}
    artifact_digests: dict[str, str] = {}
    for name, path in paths.items():
        if not exists[name]:
            continue
        try:
            artifact_digests[name] = file_sha256(path)
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("top-level JSON is not an object")
            payloads[name] = value
        except Exception as exc:
            errors.append(f"ARTIFACT_PARSE_FAILED:{name}:{type(exc).__name__}")
    evidence_fp: str | None = None
    expected_counts: dict[str, int] | None = None
    run_generated_at: str | None = None
    if "output" in payloads and "website" in payloads:
        output_errors, output_counts = validate_primary("OUTPUT", payloads["output"])
        website_errors, website_counts = validate_primary("WEBSITE", payloads["website"])
        errors.extend(output_errors)
        errors.extend(website_errors)
        output_fp = valid_sha256(payloads["output"].get("run_evidence_fingerprint"))
        website_fp = valid_sha256(payloads["website"].get("run_evidence_fingerprint"))
        if output_fp is None or output_fp != website_fp:
            errors.append("OUTPUT_WEBSITE_BASE_FINGERPRINT_MISMATCH")
        else:
            evidence_fp = output_fp
        if output_counts != website_counts:
            errors.append("OUTPUT_WEBSITE_COUNT_MISMATCH")
        else:
            expected_counts = output_counts
        output_generated = payloads["output"].get("generated_at")
        website_generated = payloads["website"].get("generated_at")
        if not isinstance(output_generated, str) or not output_generated or output_generated != website_generated:
            errors.append("OUTPUT_WEBSITE_RUN_TIMESTAMP_MISMATCH")
        else:
            run_generated_at = output_generated
    recon_signature: dict[str, Any] | None = None
    if evidence_fp and expected_counts and "reconciliation" in payloads:
        errors.extend(validate_reconciliation(payloads["reconciliation"], expected_counts, evidence_fp))
        recon_signature = reconciliation_signature(payloads["reconciliation"])
    publication_fingerprint: str | None = None
    if evidence_fp and recon_signature and run_generated_at and len(artifact_digests) == 3:
        publication_fingerprint = canonical_fingerprint({
            "base_evidence_fingerprint": evidence_fp,
            "run_generated_at": run_generated_at,
            "prepublication_artifact_sha256": artifact_digests,
            "reconciliation_signature": recon_signature,
        })
    publication_passed = bool(not errors and publication_fingerprint and all(exists.values()))
    common = {
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "supersedes_attempt_id": SUPERSEDES_ATTEMPT_ID,
        "publication_quarantine_required": True,
        "publication_quarantine_passed": publication_passed,
        "published_score_release_gate": publication_passed,
        "prepublication_artifact_digest_gate": publication_passed,
        "prepublication_artifact_sha256": artifact_digests,
        "base_run_evidence_fingerprint": evidence_fp,
        "publication_evidence_fingerprint": publication_fingerprint,
        "run_generated_at": run_generated_at,
        "publication_quarantine_errors": sorted(set(errors)),
        "runtime_acceptance_passed": publication_passed,
        "runtime_execution_success": publication_passed,
        "strict_gate_version": "exact-blob-stream-mmap-immutable-official-evidence-reconciliation-publication-quarantine-v9",
        "fake_data": False,
        "final_ready": False,
    }
    for name, payload in payloads.items():
        payload.update(common)
        if name in ("output", "website"):
            sanitize_primary(payload, publication_passed)
        else:
            payload["published_score_row_count"] = expected_counts["accuracy_score_4_count"] if publication_passed and expected_counts else 0
            payload["actual_slot_rows_written"] = payload["published_score_row_count"]
        atomic_write_json(paths[name], payload)
    print(f"PUBLICATION_QUARANTINE_PASSED={str(publication_passed).lower()}")
    print(f"PREPUBLICATION_ARTIFACT_DIGESTS={len(artifact_digests)}/3")
    print(f"PUBLICATION_EVIDENCE_FINGERPRINT={publication_fingerprint or ''}")
    return 0 if publication_passed else 2


def main() -> int:
    base = load_base()
    base.TASK_VERSION = TASK_VERSION
    base.ATTEMPT_ID = ATTEMPT_ID
    base.SUPERSEDES_ATTEMPT_ID = SUPERSEDES_ATTEMPT_ID
    prior_return_code = int(base.main())
    repo_root = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
    result = enrich(repo_root, prior_return_code)
    print(f"ATTEMPT_ID={ATTEMPT_ID}")
    print("FINAL_READY=false")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
