from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
SHARD_REL = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_2")
OUTPUT_REL = SHARD_REL / "runner_outputs"
PUBLISHER_VERSION = "20260721_25"

ARTIFACTS = {
    "guard_receipt": OUTPUT_REL / "gas_emissions_2_runtime_guard_v2_receipt_latest.json",
    "pipeline_receipt": OUTPUT_REL / "gas_emissions_2_runtime_pipeline_receipt_latest.json",
    "local_evidence": OUTPUT_REL / "gas_emissions_2_runtime_evidence_local_latest.json",
    "screenshot": OUTPUT_REL / "gas_emissions_2_runtime_evidence_latest.png",
    "dom": OUTPUT_REL / "gas_emissions_2_runtime_dom_latest.html",
    "console": OUTPUT_REL / "gas_emissions_2_runtime_console_latest.json",
    "http_log": OUTPUT_REL / "gas_emissions_2_http_server_latest.log",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def full_sha(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 40 and all(ch in "0123456789abcdefABCDEF" for ch in text)


def validate_local_runtime(repo: Path) -> dict[str, Any]:
    failures: list[str] = []
    resolved = {name: repo / rel for name, rel in ARTIFACTS.items()}
    for name, path in resolved.items():
        if not path.is_file():
            failures.append(f"MISSING_ARTIFACT:{name}:{path}")

    if failures:
        return {"pass": False, "failures": failures, "artifacts": {}}

    try:
        guard = read_json(resolved["guard_receipt"])
        pipeline = read_json(resolved["pipeline_receipt"])
        evidence = read_json(resolved["local_evidence"])
        console = read_json(resolved["console"])
    except Exception as exc:
        return {"pass": False, "failures": [f"JSON_READ:{type(exc).__name__}:{exc}"], "artifacts": {}}

    expected_state = "LOCAL_RUNTIME_PASS_AWAITING_PUBLISHER_COMMIT_READBACK"
    if guard.get("state") != expected_state:
        failures.append(f"GUARD_STATE:{guard.get('state')}")
    if pipeline.get("state") != expected_state:
        failures.append(f"PIPELINE_STATE:{pipeline.get('state')}")
    if guard.get("runtime_executed") is not True:
        failures.append("GUARD_RUNTIME_NOT_EXECUTED")
    if int(guard.get("exit_code") or 0) != 0:
        failures.append(f"GUARD_EXIT:{guard.get('exit_code')}")
    if int(pipeline.get("exit_code") or 0) != 0:
        failures.append(f"PIPELINE_EXIT:{pipeline.get('exit_code')}")

    checks = evidence.get("checks_summary") or {}
    dataset = evidence.get("dataset_summary") or {}
    metadata = evidence.get("runner_metadata_summary") or {}
    expected = {
        "CHECKS_PASS": (checks.get("passed"), 21), "CHECKS_TOTAL": (checks.get("total"), 21),
        "HTTP_PASS": (checks.get("http_passed"), 6), "HTTP_TOTAL": (checks.get("http_total"), 6),
        "INTERACTION_PASS": (checks.get("interaction_passed"), 5), "INTERACTION_TOTAL": (checks.get("interaction_total"), 5),
        "CANDIDATE_ROWS": (dataset.get("candidate_rows"), 100), "UNIQUE_IDS": (dataset.get("unique_candidate_ids"), 100),
        "UNIQUE_LINES": (dataset.get("unique_preview_lines"), 100), "QA_PASS": (dataset.get("qa_pass"), 100),
        "QA_REVIEW": (dataset.get("qa_review"), 0), "DOM_ROWS": (dataset.get("dom_rows"), 100),
        "CONSOLE_ERRORS": (dataset.get("console_errors"), 0), "PARCEL_BOUND": (dataset.get("parcel_bound_rows"), 0),
        "METADATA_PASS": (metadata.get("passed"), 8), "METADATA_TOTAL": (metadata.get("total"), 9),
    }
    for name, (actual, required) in expected.items():
        if actual != required:
            failures.append(f"{name}:{actual}!={required}")
    if checks.get("overall") != "PASS":
        failures.append("CHECKS_OVERALL_NOT_PASS")
    if metadata.get("missing") != ["remote_commit_and_readback"]:
        failures.append(f"METADATA_MISSING:{metadata.get('missing')}")
    if evidence.get("slot_id") != SLOT_ID:
        failures.append("WRONG_SLOT")
    if evidence.get("proof_complete") is not False:
        failures.append("LOCAL_PROOF_COMPLETE_MUST_BE_FALSE")
    if evidence.get("remote_commit_and_readback") is not False:
        failures.append("LOCAL_REMOTE_READBACK_MUST_BE_FALSE")
    if evidence.get("final_ready") is not False:
        failures.append("LOCAL_FINAL_READY_MUST_BE_FALSE")
    if console.get("page_errors") not in ([], None):
        failures.append("PAGE_ERRORS_NOT_ZERO")
    error_events = [event for event in (console.get("console_events") or []) if str(event.get("type") or "").lower() == "error"]
    if error_events:
        failures.append(f"CONSOLE_ERROR_EVENTS:{len(error_events)}")

    artifacts = {}
    for name, path in resolved.items():
        artifacts[name] = {"path": str(path.relative_to(repo)).replace("\\", "/"), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    served_commit = evidence.get("served_commit_sha") or (evidence.get("runner_metadata") or {}).get("served_commit_sha")
    if not full_sha(served_commit):
        failures.append(f"SERVED_COMMIT_INVALID:{served_commit}")

    return {"pass": not failures, "failures": failures, "served_commit_sha": served_commit, "artifacts": artifacts, "local_runtime_state": expected_state}


def prepare(repo: Path, output: Path) -> dict[str, Any]:
    validation = validate_local_runtime(repo)
    payload = {
        "schema_version": 1, "slot_id": SLOT_ID, "publisher_version": PUBLISHER_VERSION, "generated_at": utc_now(),
        "mode": "PREPARE_PUBLISHER_BUNDLE", "local_runtime_validation": validation,
        "ready_for_publisher_commit": validation["pass"],
        "required_remote_readback": {"branch": TARGET_BRANCH, "commit_sha": "REQUIRED_40_HEX", "remote_readback_complete": True, "artifact_sha256_map": "MUST_MATCH_ALL_7_LOCAL_ARTIFACTS"},
        "direct_push_performed": False, "browser_acceptance_before": 66, "browser_acceptance_after": 66,
        "counted_toward_browser_acceptance": False, "proof_complete": False, "final_ready": False,
        "fake_data": False, "db_write": False, "migration": False, "production_deploy": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def verify(repo: Path, readback_path: Path, output: Path) -> dict[str, Any]:
    validation = validate_local_runtime(repo)
    failures = list(validation.get("failures") or [])
    try:
        readback = read_json(readback_path)
    except Exception as exc:
        readback = {}
        failures.append(f"READBACK_JSON:{type(exc).__name__}:{exc}")

    if readback.get("slot_id") != SLOT_ID:
        failures.append("READBACK_WRONG_SLOT")
    if readback.get("branch") != TARGET_BRANCH:
        failures.append(f"READBACK_WRONG_BRANCH:{readback.get('branch')}")
    if not full_sha(readback.get("commit_sha")):
        failures.append(f"READBACK_COMMIT_INVALID:{readback.get('commit_sha')}")
    if readback.get("remote_readback_complete") is not True:
        failures.append("REMOTE_READBACK_NOT_COMPLETE")
    if readback.get("served_commit_sha") != validation.get("served_commit_sha"):
        failures.append("SERVED_COMMIT_READBACK_MISMATCH")

    observed = readback.get("artifact_sha256_map") or {}
    expected_map = {item["path"]: item["sha256"] for item in (validation.get("artifacts") or {}).values()}
    for path, expected_sha in expected_map.items():
        actual_sha = observed.get(path)
        if actual_sha != expected_sha:
            failures.append(f"ARTIFACT_SHA_MISMATCH:{path}:{actual_sha}!={expected_sha}")
    extra = sorted(set(observed) - set(expected_map))
    if extra:
        failures.append(f"UNEXPECTED_READBACK_ARTIFACTS:{extra}")

    verified = validation.get("pass") is True and not failures
    payload = {
        "schema_version": 1, "slot_id": SLOT_ID, "publisher_version": PUBLISHER_VERSION, "generated_at": utc_now(),
        "mode": "VERIFY_REMOTE_ARTIFACT_READBACK", "local_runtime_validation": validation, "remote_readback": readback,
        "failures": failures, "remote_artifact_readback_verified": verified, "proof_complete_candidate": verified,
        "final_proof_commit_and_readback_pending": verified, "browser_acceptance_candidate": 100 if verified else 66,
        "browser_acceptance_recorded": 66, "counted_toward_browser_acceptance": False, "direct_push_performed": False,
        "proof_complete": False, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--mode", choices=("prepare", "verify"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--remote-readback-json")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    repo = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    if args.mode == "prepare":
        result = prepare(repo, output)
        ok = result["ready_for_publisher_commit"]
    else:
        if not args.remote_readback_json:
            raise SystemExit("REMOTE_READBACK_JSON_REQUIRED")
        result = verify(repo, Path(args.remote_readback_json).resolve(), output)
        ok = result["remote_artifact_readback_verified"]
    print(json.dumps({"slot_id": SLOT_ID, "mode": args.mode, "pass": bool(ok), "browser_acceptance_recorded": 66, "final_ready": False}))
    raise SystemExit(0 if ok else 1)
