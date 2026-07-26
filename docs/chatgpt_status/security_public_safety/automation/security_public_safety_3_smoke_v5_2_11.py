from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("security_public_safety_3_smoke_v5_2_10.py")
TASK_VERSION = "5.2.11-final-artifact-manifest"
ATTEMPT_ID = "security-public-safety-3-20260721-020"
SUPERSEDES_ATTEMPT_ID = "security-public-safety-3-20260721-019"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
FOUR_GATES = ["canonical_gate", "crime_api_gate", "outcomes_api_gate", "iod25_gate"]

OUTPUT_REL = Path("docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_candidates_v5_2_latest.json")
RECON_REL = Path("docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_reconciliation_v5_2_latest.json")
WEBSITE_REL = Path("england_map_web/data/security_public_safety/security_public_safety_3_smoke_rows_latest.json")
MANIFEST_REL = Path("england_map_web/data/security_public_safety/security_public_safety_3_publication_manifest_latest.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_base():
    spec = importlib.util.spec_from_file_location(
        "security_public_safety_3_smoke_v5_2_10_base", BASE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load V5.2.10 verifier: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
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


def valid_sha256(value: object) -> str | None:
    text = str(value or "").lower()
    return text if len(text) == 64 and all(ch in "0123456789abcdef" for ch in text) else None


def finite_number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_fingerprint(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def manifest_fingerprint_valid(payload: dict[str, Any]) -> bool:
    existing = valid_sha256(payload.get("manifest_evidence_fingerprint"))
    if existing is None:
        return False
    unsigned = dict(payload)
    unsigned.pop("manifest_evidence_fingerprint", None)
    return canonical_fingerprint(unsigned) == existing


def artifact_paths(repo_root: Path) -> dict[str, Path]:
    return {
        "output": repo_root / OUTPUT_REL,
        "website": repo_root / WEBSITE_REL,
        "reconciliation": repo_root / RECON_REL,
    }


def safe_read_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            return None, "TOP_LEVEL_NOT_OBJECT"
        return value, None
    except Exception as exc:
        return None, f"{type(exc).__name__}:{exc}"


def quarantine_primary(payload: dict[str, Any], phase: str, errors: list[str]) -> None:
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row["security_score_percent"] = None
        row["publication_quarantine_gate"] = False
        row["prepublication_artifact_digest_gate"] = False
        row["published_score_release_gate"] = False
        row["final_artifact_manifest_gate"] = False
        row["final_artifact_manifest_fingerprint"] = None
        row["needs_manual_review"] = True
        current = str(row.get("candidate_status") or "")
        if not current.startswith("FINAL_MANIFEST_QUARANTINED_"):
            row["candidate_status"] = "FINAL_MANIFEST_QUARANTINED_" + current
    payload.update(
        {
            "task_version": TASK_VERSION,
            "attempt_id": ATTEMPT_ID,
            "supersedes_attempt_id": SUPERSEDES_ATTEMPT_ID,
            "publication_quarantine_passed": False,
            "prepublication_artifact_digest_gate": False,
            "published_score_release_gate": False,
            "final_artifact_manifest_required": True,
            "final_artifact_manifest_passed": False,
            "final_artifact_manifest_fingerprint": None,
            "final_artifact_manifest_phase": phase,
            "final_artifact_manifest_errors": sorted(set(errors)),
            "published_score_row_count": 0,
            "verified_slot_rows": 0,
            "actual_slot_rows_written": 0,
            "runtime_acceptance_passed": False,
            "runtime_execution_success": False,
            "fake_data": False,
            "final_ready": False,
        }
    )


def failed_manifest(repo_root: Path, phase: str, errors: list[str]) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "slot_id": "security_public_safety_3",
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "supersedes_attempt_id": SUPERSEDES_ATTEMPT_ID,
        "generated_at": utc_now(),
        "phase": phase,
        "final_artifact_manifest_required": True,
        "final_artifact_manifest_passed": False,
        "final_artifact_sha256": {},
        "base_publication_evidence_fingerprint": None,
        "published_score_row_count": 0,
        "ordered_target_parcels": TARGET_IDS,
        "errors": sorted(set(errors)),
        "fake_data": False,
        "final_ready": False,
    }
    payload["manifest_evidence_fingerprint"] = canonical_fingerprint(payload)
    atomic_write_json(repo_root / MANIFEST_REL, payload)
    return payload


def pre_run_quarantine(repo_root: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    paths = artifact_paths(repo_root)
    for name in ("output", "website"):
        path = paths[name]
        if not path.is_file():
            continue
        payload, error = safe_read_object(path)
        if error:
            errors.append(f"PRE_RUN_PARSE_FAILED:{name}:{error}")
            if name == "website":
                return False, errors
            continue
        quarantine_primary(payload, "pre-run", ["PRE_RUN_QUARANTINE"])
        try:
            atomic_write_json(path, payload)
        except Exception as exc:
            errors.append(f"PRE_RUN_WRITE_FAILED:{name}:{type(exc).__name__}")
            return False, errors
    try:
        failed_manifest(repo_root, "pre-run", ["RUNTIME_NOT_STARTED"])
    except Exception as exc:
        errors.append(f"PRE_RUN_MANIFEST_WRITE_FAILED:{type(exc).__name__}")
        return False, errors
    return True, errors


def row_final_signature(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "parcel_id": row.get("parcel_id"),
        "accuracy_score_4": row.get("accuracy_score_4"),
        "security_score_percent": row.get("security_score_percent"),
        "publication_quarantine_gate": bool(row.get("publication_quarantine_gate")),
        "prepublication_artifact_digest_gate": bool(
            row.get("prepublication_artifact_digest_gate")
        ),
        "published_score_release_gate": bool(row.get("published_score_release_gate")),
        **{gate: bool(row.get(gate)) for gate in FOUR_GATES},
    }


def validate_final_primary(
    name: str, payload: dict[str, Any]
) -> tuple[list[str], list[dict[str, Any]], int, str | None, str | None, str | None]:
    errors: list[str] = []
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    dict_rows = [row for row in rows if isinstance(row, dict)]
    ids = [row.get("parcel_id") for row in dict_rows]
    if len(rows) != 3 or len(dict_rows) != 3 or ids != TARGET_IDS:
        errors.append(f"{name}:ORDERED_THREE_ROW_IDENTITY_MISMATCH")
    if payload.get("attempt_id") != ATTEMPT_ID or payload.get("task_version") != TASK_VERSION:
        errors.append(f"{name}:CURRENT_LINEAGE_MISMATCH")
    if not payload.get("publication_quarantine_passed"):
        errors.append(f"{name}:PUBLICATION_QUARANTINE_FALSE")
    if not payload.get("prepublication_artifact_digest_gate"):
        errors.append(f"{name}:TOP_PREPUBLICATION_DIGEST_GATE_FALSE")
    if not payload.get("published_score_release_gate"):
        errors.append(f"{name}:TOP_SCORE_RELEASE_GATE_FALSE")
    if not payload.get("runtime_acceptance_passed"):
        errors.append(f"{name}:RUNTIME_ACCEPTANCE_FALSE")
    publication_fp = valid_sha256(payload.get("publication_evidence_fingerprint"))
    base_fp = valid_sha256(payload.get("base_run_evidence_fingerprint"))
    run_generated_at = payload.get("run_generated_at")
    if publication_fp is None:
        errors.append(f"{name}:PUBLICATION_FINGERPRINT_MISSING")
    if base_fp is None:
        errors.append(f"{name}:BASE_RUN_FINGERPRINT_MISSING")
    if not isinstance(run_generated_at, str) or not run_generated_at:
        errors.append(f"{name}:RUN_GENERATED_AT_MISSING")
    pre = payload.get("prepublication_artifact_sha256")
    if not isinstance(pre, dict) or set(pre) != {"output", "website", "reconciliation"}:
        errors.append(f"{name}:PREPUBLICATION_DIGEST_SET_MISMATCH")
    elif not all(valid_sha256(value) for value in pre.values()):
        errors.append(f"{name}:PREPUBLICATION_DIGEST_INVALID")
    released = 0
    signatures: list[dict[str, Any]] = []
    for row in dict_rows:
        parcel_id = row.get("parcel_id")
        four_count = sum(bool(row.get(gate)) for gate in FOUR_GATES)
        release = bool(row.get("published_score_release_gate"))
        score = finite_number(row.get("security_score_percent"))
        if release:
            released += 1
            if not row.get("publication_quarantine_gate"):
                errors.append(f"{name}:ROW_PUBLICATION_GATE_FALSE:{parcel_id}")
            if not row.get("prepublication_artifact_digest_gate"):
                errors.append(f"{name}:ROW_PREPUBLICATION_GATE_FALSE:{parcel_id}")
            if four_count != 4 or row.get("accuracy_score_4") != 4:
                errors.append(f"{name}:ROW_RELEASE_WITHOUT_STRICT_FOUR:{parcel_id}")
            if score is None or not 0.0 <= score <= 100.0:
                errors.append(f"{name}:ROW_RELEASE_SCORE_INVALID:{parcel_id}")
        elif row.get("security_score_percent") is not None:
            errors.append(f"{name}:ROW_HIDDEN_SCORE_NOT_NULL:{parcel_id}")
        signatures.append(row_final_signature(row))
    if released < 1:
        errors.append(f"{name}:ZERO_RELEASED_ROWS")
    if payload.get("published_score_row_count") != released:
        errors.append(f"{name}:PUBLISHED_COUNT_MISMATCH")
    if payload.get("verified_slot_rows") != released:
        errors.append(f"{name}:VERIFIED_COUNT_MISMATCH")
    if payload.get("actual_slot_rows_written") != released:
        errors.append(f"{name}:ACTUAL_WRITTEN_COUNT_MISMATCH")
    return sorted(set(errors)), signatures, released, publication_fp, base_fp, run_generated_at


def enforce_failure_quarantine(
    repo_root: Path, phase: str, errors: list[str]
) -> None:
    paths = artifact_paths(repo_root)
    for name in ("output", "website"):
        path = paths[name]
        if not path.is_file():
            continue
        payload, error = safe_read_object(path)
        if error:
            errors.append(f"FAILURE_PARSE_FAILED:{name}:{error}")
            continue
        quarantine_primary(payload, phase, errors)
        atomic_write_json(path, payload)
    recon_path = paths["reconciliation"]
    if recon_path.is_file():
        payload, error = safe_read_object(recon_path)
        if error:
            errors.append(f"FAILURE_PARSE_FAILED:reconciliation:{error}")
        else:
            payload.update(
                {
                    "task_version": TASK_VERSION,
                    "attempt_id": ATTEMPT_ID,
                    "supersedes_attempt_id": SUPERSEDES_ATTEMPT_ID,
                    "publication_quarantine_passed": False,
                    "published_score_row_count": 0,
                    "actual_slot_rows_written": 0,
                    "final_artifact_manifest_required": True,
                    "final_artifact_manifest_passed": False,
                    "final_artifact_manifest_fingerprint": None,
                    "final_artifact_manifest_errors": sorted(set(errors)),
                    "runtime_acceptance_passed": False,
                    "runtime_execution_success": False,
                    "fake_data": False,
                    "final_ready": False,
                }
            )
            atomic_write_json(recon_path, payload)
    failed_manifest(repo_root, phase, errors)


def finalize(repo_root: Path, prior_return_code: int) -> int:
    errors: list[str] = []
    if prior_return_code != 0:
        errors.append(f"BASE_EXIT_NONZERO:{prior_return_code}")
    paths = artifact_paths(repo_root)
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        if not path.is_file():
            errors.append(f"MISSING_FINAL_ARTIFACT:{name}")
            continue
        payload, error = safe_read_object(path)
        if error:
            errors.append(f"FINAL_PARSE_FAILED:{name}:{error}")
        else:
            payloads[name] = payload

    output_sig: list[dict[str, Any]] | None = None
    website_sig: list[dict[str, Any]] | None = None
    output_release = 0
    website_release = 0
    output_pub_fp = output_base_fp = output_run_at = None
    website_pub_fp = website_base_fp = website_run_at = None
    if "output" in payloads:
        (
            new_errors,
            output_sig,
            output_release,
            output_pub_fp,
            output_base_fp,
            output_run_at,
        ) = validate_final_primary("OUTPUT", payloads["output"])
        errors.extend(new_errors)
    if "website" in payloads:
        (
            new_errors,
            website_sig,
            website_release,
            website_pub_fp,
            website_base_fp,
            website_run_at,
        ) = validate_final_primary("WEBSITE", payloads["website"])
        errors.extend(new_errors)
    if output_sig is not None and website_sig is not None:
        if output_sig != website_sig or output_release != website_release:
            errors.append("OUTPUT_WEBSITE_FINAL_SIGNATURE_MISMATCH")

    publication_fp: str | None = None
    base_fp: str | None = None
    run_generated_at: str | None = None
    if "output" in payloads and "website" in payloads:
        if output_pub_fp is None or output_pub_fp != website_pub_fp:
            errors.append("OUTPUT_WEBSITE_PUBLICATION_FINGERPRINT_MISMATCH")
        else:
            publication_fp = output_pub_fp
        if output_base_fp is None or output_base_fp != website_base_fp:
            errors.append("OUTPUT_WEBSITE_BASE_FINGERPRINT_MISMATCH")
        else:
            base_fp = output_base_fp
        if output_run_at is None or output_run_at != website_run_at:
            errors.append("OUTPUT_WEBSITE_RUN_TIMESTAMP_MISMATCH")
        else:
            run_generated_at = output_run_at

    if "reconciliation" in payloads:
        recon = payloads["reconciliation"]
        if recon.get("attempt_id") != ATTEMPT_ID or recon.get("task_version") != TASK_VERSION:
            errors.append("RECONCILIATION_CURRENT_LINEAGE_MISMATCH")
        if not recon.get("publication_quarantine_passed"):
            errors.append("RECONCILIATION_PUBLICATION_QUARANTINE_FALSE")
        if valid_sha256(recon.get("publication_evidence_fingerprint")) != publication_fp:
            errors.append("RECONCILIATION_PUBLICATION_FINGERPRINT_MISMATCH")
        if valid_sha256(recon.get("base_run_evidence_fingerprint")) != base_fp:
            errors.append("RECONCILIATION_BASE_FINGERPRINT_MISMATCH")
        if recon.get("run_generated_at") != run_generated_at:
            errors.append("RECONCILIATION_RUN_TIMESTAMP_MISMATCH")
        if recon.get("published_score_row_count") != output_release:
            errors.append("RECONCILIATION_PUBLISHED_COUNT_MISMATCH")
        if recon.get("actual_slot_rows_written") != output_release:
            errors.append("RECONCILIATION_ACTUAL_WRITTEN_MISMATCH")

    if errors:
        try:
            enforce_failure_quarantine(repo_root, "final-validation-failed", errors)
        except Exception as exc:
            errors.append(f"FAILURE_QUARANTINE_CRASHED:{type(exc).__name__}")
            try:
                failed_manifest(repo_root, "failure-quarantine-crashed", errors)
            except Exception:
                pass
        return 2

    final_hashes = {name: file_sha256(path) for name, path in paths.items()}
    manifest = {
        "schema_version": 1,
        "slot_id": "security_public_safety_3",
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "supersedes_attempt_id": SUPERSEDES_ATTEMPT_ID,
        "generated_at": utc_now(),
        "phase": "final",
        "final_artifact_manifest_required": True,
        "final_artifact_manifest_passed": True,
        "base_publication_evidence_fingerprint": publication_fp,
        "base_run_evidence_fingerprint": base_fp,
        "run_generated_at": run_generated_at,
        "final_artifact_sha256": final_hashes,
        "ordered_target_parcels": TARGET_IDS,
        "published_score_row_count": output_release,
        "errors": [],
        "fake_data": False,
        "final_ready": False,
    }
    manifest["manifest_evidence_fingerprint"] = canonical_fingerprint(manifest)
    manifest_path = repo_root / MANIFEST_REL
    try:
        atomic_write_json(manifest_path, manifest)
        readback, error = safe_read_object(manifest_path)
        if error or readback != manifest:
            raise RuntimeError(f"manifest readback mismatch: {error}")
        if not manifest_fingerprint_valid(readback):
            raise RuntimeError("manifest fingerprint invalid")
        for name, path in paths.items():
            if file_sha256(path) != final_hashes[name]:
                raise RuntimeError(f"final artifact changed after manifest: {name}")
    except Exception as exc:
        errors.append(f"FINAL_MANIFEST_WRITE_OR_READBACK_FAILED:{type(exc).__name__}")
        enforce_failure_quarantine(repo_root, "manifest-failed", errors)
        return 2

    return 0


def main() -> int:
    repo_root = Path(
        os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main")
    )
    ready, pre_errors = pre_run_quarantine(repo_root)
    if not ready:
        try:
            enforce_failure_quarantine(repo_root, "pre-run-failed", pre_errors)
        except Exception:
            pass
        print("PRE_RUN_PUBLICATION_QUARANTINE_PASSED=false")
        print("FINAL_READY=false")
        return 2

    base = load_base()
    base.TASK_VERSION = TASK_VERSION
    base.ATTEMPT_ID = ATTEMPT_ID
    base.SUPERSEDES_ATTEMPT_ID = SUPERSEDES_ATTEMPT_ID
    try:
        prior_return_code = int(base.main())
    except Exception as exc:
        errors = [f"BASE_EXECUTION_EXCEPTION:{type(exc).__name__}:{exc}"]
        try:
            enforce_failure_quarantine(repo_root, "base-exception", errors)
        except Exception:
            pass
        print(f"BASE_EXECUTION_EXCEPTION={type(exc).__name__}:{exc}")
        print("FINAL_READY=false")
        return 2

    result = finalize(repo_root, prior_return_code)
    print("PRE_RUN_PUBLICATION_QUARANTINE_PASSED=true")
    print(f"FINAL_ARTIFACT_MANIFEST_PASSED={str(result == 0).lower()}")
    print(f"ATTEMPT_ID={ATTEMPT_ID}")
    print("FINAL_READY=false")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
