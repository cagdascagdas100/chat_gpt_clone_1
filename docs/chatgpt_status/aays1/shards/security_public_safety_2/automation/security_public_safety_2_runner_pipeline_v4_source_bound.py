from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
REQUIRED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_IDS = [f"parcel_{number}" for number in range(30762, 31062)]
SAMPLE_IDS = EXPECTED_IDS[:3]
SOURCE_RECEIPT = "security_public_safety_2_pipeline_receipt_latest.json"
OUTPUT_RECEIPT = "security_public_safety_2_source_bound_resume_receipt_latest.json"
ATTESTATION_RECEIPT = "security_public_safety_2_live_source_attestation_latest.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_repo_root(explicit: str | None) -> Path:
    candidates: list[Path] = []
    for value in (explicit, os.environ.get("AAYS_REPO_ROOT")):
        if value:
            candidates.append(Path(value).expanduser())
    for probe in (Path.cwd(), Path(__file__).resolve().parent):
        try:
            completed = subprocess.run(
                ["git", "-C", str(probe), "rev-parse", "--show-toplevel"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if completed.returncode == 0 and completed.stdout.strip():
                candidates.append(Path(completed.stdout.strip()))
        except Exception:
            pass
    candidates.extend(Path(__file__).resolve().parents)
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate.absolute()
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        if (
            resolved.is_dir()
            and (resolved / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation").is_dir()
            and (resolved / "england_map_web/data/aays_18_slots/security_public_safety_2").is_dir()
        ):
            return resolved
    raise RuntimeError("AAYS_REPO_ROOT_NOT_RESOLVED")


def choose_port(preferred: int) -> int:
    for candidate in (preferred, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", candidate))
                return int(sock.getsockname()[1])
            except OSError:
                continue
    raise RuntimeError("NO_LOCAL_HTTP_PORT_AVAILABLE")


def run_command(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:], "elapsed_seconds": round(time.monotonic() - started, 3), "pass": completed.returncode == 0, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {"command": command, "returncode": None, "stdout_tail": stdout[-4000:], "stderr_tail": stderr[-4000:], "elapsed_seconds": round(time.monotonic() - started, 3), "pass": False, "timed_out": True, "error": "TIMEOUT"}
    except Exception as exc:
        return {"command": command, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}:{exc}", "elapsed_seconds": round(time.monotonic() - started, 3), "pass": False, "timed_out": False, "error": "EXECUTION_EXCEPTION"}


def attestation_bindings(attestation: dict[str, Any]) -> dict[str, Any]:
    provenance = attestation.get("provenance_manifest") or {}
    bootstrap = attestation.get("bootstrap_manifest") or {}
    police = ((((provenance.get("sources") or {}).get("police_latest") or {}).get("parsed") or {}))
    month = police.get("latest_month") or str(police.get("latest_date") or "")[:7] or None
    resolved = attestation.get("resolved_env") or bootstrap.get("resolved_env") or {}
    iod_path = Path(str(resolved.get("AAYS_IOD25_V2_CSV") or ""))
    mps_path = Path(str(resolved.get("AAYS_MPS_LSOA_CSV") or ""))
    checks = {
        "attestation_pass": attestation.get("pass") is True,
        "attestation_state": attestation.get("state") == "LIVE_SOURCE_ATTESTATION_PASSED",
        "police_month": bool(month),
        "iod_path_absolute": iod_path.is_absolute(),
        "mps_path_absolute": mps_path.is_absolute(),
        "iod_file_exists": iod_path.is_file(),
        "mps_file_exists": mps_path.is_file(),
    }
    iod_sha = sha256_file(iod_path) if iod_path.is_file() else None
    mps_sha = sha256_file(mps_path) if mps_path.is_file() else None
    checks["iod_sha"] = bool(iod_sha)
    checks["mps_sha"] = bool(mps_sha)
    return {"pass": all(checks.values()), "checks": checks, "police_month": month, "iod_path": str(iod_path) if iod_path else None, "mps_path": str(mps_path) if mps_path else None, "iod_sha256": iod_sha, "mps_sha256": mps_sha, "blocker": None if all(checks.values()) else "LIVE_ATTESTATION_BINDING_INCOMPLETE"}


def sample_binding(payload: dict[str, Any], bindings: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows") or []
    ids = [str(row.get("parcel_id") or "") for row in rows]
    guard = payload.get("canonical_guard") or {}
    latest = payload.get("official_api_latest") or {}
    checks = {
        "slot_exact": payload.get("slot_id") == SLOT_ID,
        "sample_ids_exact": ids == SAMPLE_IDS,
        "blob_exact": guard.get("pass") is True and guard.get("observed_blob_sha") == REQUIRED_BLOB_SHA,
        "police_month_current": latest.get("month") == bindings.get("police_month"),
        "area_proxy": all(row.get("output_semantics") == "AREA_LEVEL_PROXY" for row in rows),
        "not_parcel_measurement": all(row.get("parcel_measurement") is False for row in rows),
        "api_sha_for_score_3": all(int(row.get("accuracy_score_4") or 0) < 3 or (row.get("official_api_http_status") == 200 and bool(row.get("official_api_sha256"))) for row in rows),
        "fake_false": payload.get("fake_data") is False,
        "final_false": payload.get("final_ready") is False,
    }
    return {"pass": all(checks.values()), "checks": checks, "blocker": None if all(checks.values()) else "SAMPLE_NOT_SOURCE_BOUND"}


def _csv_rows(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle))
    except Exception:
        return None


def hydration_binding(repo: Path, payload: dict[str, Any], bindings: dict[str, Any]) -> dict[str, Any]:
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    json_path = out / "security_public_safety_2_hydrated_300_latest.json"
    csv_path = out / "security_public_safety_2_hydrated_300_latest.csv"
    geojson_path = out / "security_public_safety_2_hydrated_300_latest.geojson"
    html_path = web / "progress.html"
    web_json_path = web / "hydrated_300_latest.json"
    rows = payload.get("rows") or []
    ids = [str(row.get("parcel_id") or "") for row in rows]
    guard = payload.get("canonical_guard") or {}
    latest = payload.get("official_api_latest") or {}
    artifacts = payload.get("artifacts") or {}
    iod = payload.get("iod25") or {}
    mps = payload.get("mps_lsoa") or {}
    try:
        geo_rows = len((read_json(geojson_path).get("features") or [])) if geojson_path.is_file() else None
    except Exception:
        geo_rows = None
    csv_rows = _csv_rows(csv_path) if csv_path.is_file() else None
    checks = {
        "slot_exact": payload.get("slot_id") == SLOT_ID,
        "rows_300": len(rows) == 300,
        "ids_exact": ids == EXPECTED_IDS,
        "canonical_rows_300": int(payload.get("canonical_rows") or -1) == 300,
        "blob_exact": guard.get("pass") is True and guard.get("observed_blob_sha") == REQUIRED_BLOB_SHA,
        "police_month_current": latest.get("month") == bindings.get("police_month"),
        "iod_sha_current": iod.get("sha256") == bindings.get("iod_sha256"),
        "mps_sha_current": mps.get("sha256") == bindings.get("mps_sha256"),
        "iod_loaded": iod.get("status") == "LOADED",
        "mps_loaded": mps.get("status") == "LOADED",
        "csv_exists": csv_path.is_file(),
        "geojson_exists": geojson_path.is_file(),
        "html_exists": html_path.is_file(),
        "web_json_exists": web_json_path.is_file(),
        "csv_rows_300": csv_rows == 300,
        "geojson_rows_300": geo_rows == 300,
        "csv_sha_current": csv_path.is_file() and artifacts.get("csv_sha256") == sha256_file(csv_path),
        "geojson_sha_current": geojson_path.is_file() and artifacts.get("geojson_sha256") == sha256_file(geojson_path),
        "html_sha_current": html_path.is_file() and artifacts.get("html_sha256") == sha256_file(html_path),
        "runner_web_json_equal": json_path.is_file() and web_json_path.is_file() and json_path.read_bytes() == web_json_path.read_bytes(),
        "parity_true": artifacts.get("parity_pass") is True,
        "area_proxy": payload.get("output_semantics") == "AREA_LEVEL_PROXY" and all(row.get("output_semantics") == "AREA_LEVEL_PROXY" for row in rows),
        "not_parcel_measurement": all(row.get("parcel_measurement") is False for row in rows),
        "score4_full_evidence": all(int(row.get("accuracy_score_4") or 0) != 4 or (row.get("official_api_http_status") == 200 and bool(row.get("official_api_sha256")) and row.get("iod25_v2_join_pass") is True and row.get("mps_lsoa_join_pass") is True) for row in rows),
        "fake_false": payload.get("fake_data") is False,
        "final_false": payload.get("final_ready") is False,
    }
    return {"pass": all(checks.values()), "checks": checks, "passed": sum(checks.values()), "total": len(checks), "observed": {"csv_rows": csv_rows, "geojson_rows": geo_rows}, "blocker": None if all(checks.values()) else "HYDRATION_NOT_SOURCE_BOUND_OR_ARTIFACT_INTEGRITY_FAILED"}


def invalidate(paths: list[Path]) -> list[dict[str, Any]]:
    removed: list[dict[str, Any]] = []
    for path in paths:
        if path.is_file():
            removed.append({"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
            path.unlink()
    return removed


def validate_pipeline_receipt(payload: dict[str, Any], started_at: datetime) -> dict[str, Any]:
    steps = payload.get("steps") or []
    acceptance = next((step for step in steps if step.get("name") in {"ACCEPTANCE_GATE", "ACCEPTANCE_RESUME"}), None)
    generated = parse_time(payload.get("generated_at"))
    completed = parse_time(payload.get("completed_at"))
    checks = {
        "slot_exact": payload.get("slot_id") == SLOT_ID,
        "state_exact": payload.get("state") == "PIPELINE_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK",
        "exit_code_present": "exit_code" in payload,
        "exit_zero": payload.get("exit_code") == 0,
        "fresh_generated": bool(generated and generated >= started_at),
        "fresh_completed": bool(completed and completed >= started_at),
        "acceptance_step_present": acceptance is not None,
        "acceptance_step_pass": bool(acceptance and acceptance.get("pass") is True),
        "business_rows_present": "actual_business_rows_written" in payload,
        "business_rows_zero": payload.get("actual_business_rows_written") == 0,
        "fake_data_false": payload.get("fake_data") is False,
        "final_ready_false": payload.get("final_ready") is False,
    }
    return {"pass": all(checks.values()), "checks": checks, "passed": sum(checks.values()), "total": len(checks), "blocker": None if all(checks.values()) else "PIPELINE_RECEIPT_NOT_FRESH_OR_ACCEPTED"}


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo_root(args.repo_root)
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    out.mkdir(parents=True, exist_ok=True)
    web.mkdir(parents=True, exist_ok=True)
    output_path = out / OUTPUT_RECEIPT
    source_path = out / SOURCE_RECEIPT
    attestation_path = out / ATTESTATION_RECEIPT
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "wrapper_version": "4.0-source-bound-artifact-integrity", "generated_at": utc_now(), "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}

    def finish(state: str, blocker: str | None, code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": code, "completed_at": utc_now(), "pass": code == 0})
        output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt

    if slot != SLOT_ID or branch != TARGET_BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)
    if not attestation_path.is_file():
        return finish("BLOCKED_ATTESTATION_BINDING", "LIVE_ATTESTATION_RECEIPT_MISSING", 3)
    try:
        attestation = read_json(attestation_path)
    except Exception as exc:
        return finish("BLOCKED_ATTESTATION_BINDING", f"READ:{type(exc).__name__}:{exc}", 4)
    bindings = attestation_bindings(attestation)
    receipt["bindings"] = bindings
    if not bindings["pass"]:
        return finish("BLOCKED_ATTESTATION_BINDING", bindings.get("blocker"), 5)

    sample_path = out / "security_public_safety_2_sample_candidates_latest.json"
    web_sample = web / "sample_candidates_latest.json"
    hydration_json = out / "security_public_safety_2_hydrated_300_latest.json"
    hydration_csv = out / "security_public_safety_2_hydrated_300_latest.csv"
    hydration_geojson = out / "security_public_safety_2_hydrated_300_latest.geojson"
    web_hydration = web / "hydrated_300_latest.json"
    acceptance_path = out / "security_public_safety_2_acceptance_latest.json"

    sample_check: dict[str, Any] = {"pass": False, "blocker": "MISSING"}
    if sample_path.is_file():
        try:
            sample_check = sample_binding(read_json(sample_path), bindings)
        except Exception as exc:
            sample_check = {"pass": False, "blocker": f"READ:{type(exc).__name__}:{exc}"}
    receipt["sample_preflight"] = sample_check

    hydration_check: dict[str, Any] = {"pass": False, "blocker": "MISSING"}
    if hydration_json.is_file():
        try:
            hydration_check = hydration_binding(repo, read_json(hydration_json), bindings)
        except Exception as exc:
            hydration_check = {"pass": False, "blocker": f"READ:{type(exc).__name__}:{exc}"}
    receipt["hydration_preflight"] = hydration_check

    removed: list[dict[str, Any]] = []
    if not sample_check.get("pass"):
        removed.extend(invalidate([sample_path, web_sample]))
        hydration_check = {"pass": False, "blocker": "DOWNSTREAM_OF_INVALID_SAMPLE"}
    if not hydration_check.get("pass"):
        removed.extend(invalidate([hydration_json, hydration_csv, hydration_geojson, web_hydration, acceptance_path, source_path]))
    receipt["invalidated_artifacts"] = removed

    started_at = datetime.now(timezone.utc)
    if source_path.is_file():
        receipt["stale_pipeline_receipt_removed"] = invalidate([source_path])
    port = choose_port(args.port)
    receipt["requested_port"] = args.port
    receipt["selected_port"] = port
    env = os.environ.copy()
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": TARGET_BRANCH, "AAYS_IOD25_V2_CSV": str(bindings["iod_path"]), "AAYS_MPS_LSOA_CSV": str(bindings["mps_path"])})
    pipeline = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/security_public_safety_2_runner_pipeline_v2_resume.py"
    command = [sys.executable, str(pipeline), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--port", str(port), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout), "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout)]
    result = run_command(command, repo, env, args.pipeline_timeout)
    receipt["pipeline_command"] = result
    if not result["pass"]:
        return finish("BLOCKED_SOURCE_BOUND_PIPELINE_EXECUTION", "TIMEOUT" if result.get("timed_out") else "NONZERO_OR_EXCEPTION", 6)
    if not source_path.is_file():
        return finish("BLOCKED_SOURCE_BOUND_PIPELINE_RECEIPT", "FRESH_PIPELINE_RECEIPT_MISSING", 7)
    try:
        source_receipt = read_json(source_path)
    except Exception as exc:
        return finish("BLOCKED_SOURCE_BOUND_PIPELINE_RECEIPT", f"READ:{type(exc).__name__}:{exc}", 8)
    validation = validate_pipeline_receipt(source_receipt, started_at)
    receipt["pipeline_receipt"] = source_receipt
    receipt["receipt_validation"] = validation
    if not validation["pass"]:
        return finish("BLOCKED_SOURCE_BOUND_PIPELINE_GATE", validation.get("blocker"), 9)
    try:
        post_hydration = hydration_binding(repo, read_json(hydration_json), bindings)
    except Exception as exc:
        post_hydration = {"pass": False, "blocker": f"READ:{type(exc).__name__}:{exc}"}
    receipt["hydration_postflight"] = post_hydration
    if not post_hydration.get("pass"):
        return finish("BLOCKED_SOURCE_BOUND_POSTFLIGHT", post_hydration.get("blocker"), 10)
    return finish("SOURCE_BOUND_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_READBACK", None, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--pipeline-timeout", type=int, default=5700)
    parser.add_argument("--sample-timeout", type=int, default=900)
    parser.add_argument("--batch-timeout", type=int, default=3600)
    parser.add_argument("--acceptance-timeout", type=int, default=300)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "wrapper_version": "4.0-source-bound-artifact-integrity", "state": result.get("state"), "pass": result.get("pass"), "exit_code": result.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
