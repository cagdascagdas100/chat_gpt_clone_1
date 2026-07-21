from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
REQUIRED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_IDS = [f"parcel_{number}" for number in range(30762, 31062)]
SAMPLE_IDS = EXPECTED_IDS[:3]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_sibling(filename: str, module_name: str) -> Any:
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_sample(payload: dict[str, Any]) -> tuple[bool, str]:
    rows = payload.get("rows") or []
    guard = payload.get("canonical_guard") or {}
    exact_guard = guard.get("pass") is True and guard.get("observed_blob_sha") == REQUIRED_BLOB_SHA
    ids = [str(row.get("parcel_id") or "") for row in rows]
    api = all(row.get("official_api_http_status") == 200 and bool(row.get("official_api_sha256")) for row in rows)
    semantics = all(row.get("output_semantics") == "AREA_LEVEL_PROXY" and row.get("parcel_measurement") is False for row in rows)
    max_three = all(int(row.get("accuracy_score_4") or 0) <= 3 for row in rows)
    passed = ids == SAMPLE_IDS and exact_guard and api and semantics and max_three
    return passed, f"ids={ids == SAMPLE_IDS};blob={exact_guard};api={api};semantics={semantics};max3={max_three}"


def valid_hydration(payload: dict[str, Any]) -> tuple[bool, str]:
    rows = payload.get("rows") or []
    guard = payload.get("canonical_guard") or {}
    ids = [str(row.get("parcel_id") or "") for row in rows]
    exact_guard = guard.get("pass") is True and guard.get("observed_blob_sha") == REQUIRED_BLOB_SHA
    parity = bool((payload.get("artifacts") or {}).get("parity_pass"))
    semantics = payload.get("output_semantics") == "AREA_LEVEL_PROXY" and all(row.get("parcel_measurement") is False for row in rows)
    api_evidence = all(
        int(row.get("accuracy_score_4") or 0) < 3
        or (row.get("official_api_http_status") == 200 and bool(row.get("official_api_sha256")))
        for row in rows
    )
    passed = len(rows) == 300 and ids == EXPECTED_IDS and int(payload.get("canonical_rows") or 0) == 300 and exact_guard and parity and semantics and api_evidence
    return passed, f"rows={len(rows)};ids={ids == EXPECTED_IDS};canonical={payload.get('canonical_rows')};blob={exact_guard};parity={parity};semantics={semantics};api={api_evidence}"


def valid_acceptance(payload: dict[str, Any], html_path: Path, json_path: Path) -> tuple[bool, str]:
    if not html_path.is_file() or not json_path.is_file():
        return False, "CURRENT_WEB_ARTIFACT_MISSING"
    browser = payload.get("browser") or {}
    html = payload.get("html") or {}
    js = payload.get("json") or {}
    hashes = html.get("sha256") == sha256_file(html_path) and js.get("sha256") == sha256_file(json_path)
    browser_ok = (
        browser.get("available") is True
        and browser.get("row_count") == 300
        and browser.get("body_visible_row_count") == "300"
        and not browser.get("console_errors")
        and not browser.get("page_errors")
        and not browser.get("error")
    )
    passed = payload.get("all_checks_pass") is True and hashes and browser_ok
    return passed, f"all={payload.get('all_checks_pass')};hashes={hashes};browser={browser_ok}"


def run_command(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(command, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "pass": completed.returncode == 0,
    }


def wait_http(url: str, timeout: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                return {"pass": response.status == 200, "http_status": response.status, "error": None}
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            time.sleep(0.5)
    return {"pass": False, "http_status": None, "error": last_error or "HTTP_TIMEOUT"}


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    shard = repo / "docs/chatgpt_status/aays1/shards" / SLOT_ID
    out = shard / "runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots" / SLOT_ID
    out.mkdir(parents=True, exist_ok=True)
    web.mkdir(parents=True, exist_ok=True)
    receipt_path = out / "security_public_safety_2_pipeline_receipt_latest.json"
    receipt: dict[str, Any] = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "pipeline_version": "2.0-resume-safe",
        "generated_at": utc_now(),
        "steps": [],
        "reused_stages": [],
        "executed_stages": [],
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }

    def finish(state: str, blocker: str | None, code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": code, "completed_at": utc_now()})
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt

    if slot != SLOT_ID or branch != TARGET_BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)
    v1 = load_sibling("security_public_safety_2_runner_pipeline.py", "slot2_pipeline_v1")
    contract = v1.validate_contract(repo, slot, branch)
    receipt["steps"].append({"name": "CONTRACT", **contract})
    if not contract.get("pass"):
        return finish("BLOCKED_CONTRACT", ";".join(contract.get("failures") or []), 2)

    guarded = load_sibling("security_public_safety_2_batch_hydrate_v3_guarded.py", "slot2_guarded_batch")
    source, guard = guarded.materialize_exact_source(repo)
    exact = source is not None and guard.get("pass") is True and guard.get("observed_blob_sha") == REQUIRED_BLOB_SHA
    receipt["steps"].append({"name": "EXACT_BLOB", "pass": exact, "guard": guard})
    if not exact:
        guarded.write_fail_closed(repo, guard)
        return finish("BLOCKED_EXACT_BLOB", "EXACT_CANONICAL_GIT_BLOB_NOT_VERIFIED", 3)

    sample_path = out / "security_public_safety_2_sample_candidates_latest.json"
    sample_ok = False
    sample_detail = "MISSING"
    if sample_path.is_file():
        try:
            sample_ok, sample_detail = valid_sample(read_json(sample_path))
        except Exception as exc:
            sample_detail = f"INVALID:{type(exc).__name__}:{exc}"
    if sample_ok:
        receipt["reused_stages"].append("THREE_SAMPLE")
        receipt["steps"].append({"name": "THREE_SAMPLE_RESUME", "pass": True, "detail": sample_detail})
    else:
        script = shard / "automation/security_public_safety_2_sample_hydrate_v2_guarded.py"
        result = run_command([sys.executable, str(script)], repo, args.sample_timeout)
        receipt["executed_stages"].append("THREE_SAMPLE")
        receipt["steps"].append({"name": "THREE_SAMPLE_COMMAND", **result})
        if not result["pass"] or not sample_path.is_file():
            return finish("BLOCKED_SAMPLE_COMMAND", "THREE_SAMPLE_COMMAND_FAILED_OR_OUTPUT_MISSING", 4)
        sample_ok, sample_detail = valid_sample(read_json(sample_path))
        receipt["steps"].append({"name": "THREE_SAMPLE_GATE", "pass": sample_ok, "detail": sample_detail})
        if not sample_ok:
            return finish("BLOCKED_SAMPLE_GATE", sample_detail, 5)

    hydrated_path = out / "security_public_safety_2_hydrated_300_latest.json"
    hydrated_ok = False
    hydrated_detail = "MISSING"
    if hydrated_path.is_file():
        try:
            hydrated_ok, hydrated_detail = valid_hydration(read_json(hydrated_path))
        except Exception as exc:
            hydrated_detail = f"INVALID:{type(exc).__name__}:{exc}"
    if hydrated_ok:
        receipt["reused_stages"].append("HYDRATE_300")
        receipt["steps"].append({"name": "HYDRATE_300_RESUME", "pass": True, "detail": hydrated_detail})
    else:
        script = shard / "automation/security_public_safety_2_batch_hydrate_v3_guarded.py"
        result = run_command([sys.executable, str(script)], repo, args.batch_timeout)
        receipt["executed_stages"].append("HYDRATE_300")
        receipt["steps"].append({"name": "HYDRATE_300_COMMAND", **result})
        if not result["pass"] or not hydrated_path.is_file():
            return finish("BLOCKED_HYDRATE_COMMAND", "HYDRATE_COMMAND_FAILED_OR_OUTPUT_MISSING", 6)
        hydrated_ok, hydrated_detail = valid_hydration(read_json(hydrated_path))
        receipt["steps"].append({"name": "HYDRATE_300_GATE", "pass": hydrated_ok, "detail": hydrated_detail})
        if not hydrated_ok:
            return finish("BLOCKED_HYDRATE_GATE", hydrated_detail, 7)

    html_path = web / "progress.html"
    web_json_path = web / "hydrated_300_latest.json"
    acceptance_path = out / "security_public_safety_2_acceptance_latest.json"
    acceptance_ok = False
    acceptance_detail = "MISSING"
    if acceptance_path.is_file():
        try:
            acceptance_ok, acceptance_detail = valid_acceptance(read_json(acceptance_path), html_path, web_json_path)
        except Exception as exc:
            acceptance_detail = f"INVALID:{type(exc).__name__}:{exc}"
    if acceptance_ok:
        receipt["reused_stages"].append("HTTP_SHA_DOM_CONSOLE_BROWSER")
        receipt["steps"].append({"name": "ACCEPTANCE_RESUME", "pass": True, "detail": acceptance_detail})
        return finish("PIPELINE_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK", None, 0)

    server_log = out / "security_public_safety_2_http_server_latest.log"
    with server_log.open("w", encoding="utf-8") as log:
        server = subprocess.Popen([sys.executable, "-m", "http.server", str(args.port), "--bind", "127.0.0.1"], cwd=str(repo), stdout=log, stderr=subprocess.STDOUT, text=True)
    try:
        base_url = f"http://127.0.0.1:{args.port}"
        html_url = base_url + "/england_map_web/data/aays_18_slots/security_public_safety_2/progress.html"
        json_url = base_url + "/england_map_web/data/aays_18_slots/security_public_safety_2/hydrated_300_latest.json"
        health = wait_http(html_url, args.http_wait_timeout)
        receipt["steps"].append({"name": "HTTP_SERVER", **health, "url": html_url})
        if not health["pass"]:
            return finish("BLOCKED_HTTP_SERVER", str(health.get("error")), 8)
        script = shard / "automation/security_public_safety_2_acceptance_v3.py"
        command = [sys.executable, str(script), "--html-url", html_url, "--json-url", json_url, "--browser", "--browser-url", html_url, "--output", str(acceptance_path)]
        result = run_command(command, repo, args.acceptance_timeout)
        receipt["executed_stages"].append("HTTP_SHA_DOM_CONSOLE_BROWSER")
        receipt["steps"].append({"name": "ACCEPTANCE_COMMAND", **result})
        if not result["pass"] or not acceptance_path.is_file():
            return finish("BLOCKED_ACCEPTANCE_COMMAND", "ACCEPTANCE_COMMAND_FAILED_OR_OUTPUT_MISSING", 9)
        acceptance_ok, acceptance_detail = valid_acceptance(read_json(acceptance_path), html_path, web_json_path)
        receipt["steps"].append({"name": "ACCEPTANCE_GATE", "pass": acceptance_ok, "detail": acceptance_detail})
        if not acceptance_ok:
            return finish("BLOCKED_ACCEPTANCE_GATE", acceptance_detail, 10)
        return finish("PIPELINE_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK", None, 0)
    finally:
        try:
            server.terminate()
            server.wait(timeout=10)
        except Exception:
            try:
                server.kill()
            except Exception:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--sample-timeout", type=int, default=900)
    parser.add_argument("--batch-timeout", type=int, default=3600)
    parser.add_argument("--acceptance-timeout", type=int, default=300)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({
        "slot_id": SLOT_ID,
        "pipeline_version": "2.0-resume-safe",
        "state": result.get("state"),
        "blocker": result.get("blocker"),
        "reused_stages": result.get("reused_stages"),
        "executed_stages": result.get("executed_stages"),
        "exit_code": result.get("exit_code"),
        "final_ready": False,
    }))
    raise SystemExit(int(result.get("exit_code") or 0))
