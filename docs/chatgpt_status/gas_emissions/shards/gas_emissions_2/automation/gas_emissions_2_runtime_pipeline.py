from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
DEFAULT_PORT = 8012
EXPECTED_CHECKS = 21
EXPECTED_HTTP = 6
EXPECTED_INTERACTIONS = 5
EXPECTED_ROWS = 100
EXPECTED_METADATA_LOCAL = 8
EXPECTED_METADATA_FINAL = 9

SHARED_REL = Path("docs/chatgpt_status/_shared/slots_21/gas_emissions_2")
SHARD_REL = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_2")
WEB_REL = Path("england_map_web/data/aays_21_slots/gas_emissions_2")


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


def run_command(command: list[str], cwd: Path, timeout: int = 60) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "pass": completed.returncode == 0,
        }
    except Exception as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}:{exc}",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "pass": False,
        }


def validate_contract(repo: Path, slot_id: str, target_branch: str) -> dict[str, Any]:
    failures: list[str] = []
    if slot_id != SLOT_ID:
        failures.append(f"WRONG_SLOT:{slot_id}")
    if target_branch != TARGET_BRANCH:
        failures.append(f"WRONG_BRANCH:{target_branch}")

    required = {
        "checkpoint": repo / SHARED_REL / "checkpoint_latest.json",
        "status": repo / SHARED_REL / "status_latest.json",
        "ownership": repo / SHARED_REL / "ownership_latest.json",
        "heartbeat": repo / SHARED_REL / "heartbeat_latest.json",
        "current_task": repo / SHARED_REL / "current_task_latest.json",
        "runner_request": repo / SHARED_REL / "runner_browser_acceptance_request_latest.json",
        "collector": repo / WEB_REL / "runtime_evidence_collector.html",
        "collector_contract": repo / WEB_REL / "runtime_evidence_contract_latest.json",
        "collector_qa": repo / WEB_REL / "runtime_evidence_collector_qa_latest.json",
        "acceptance": repo / WEB_REL / "acceptance.html",
        "candidate_manifest": repo / WEB_REL / "candidate_manifest_latest.json",
        "qa_rules": repo / WEB_REL / "qa_rules_latest.json",
        "sources": repo / WEB_REL / "sources_latest.json",
        "web_status": repo / WEB_REL / "status_latest.json",
    }
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in required.items():
        if not path.is_file():
            failures.append(f"MISSING_REQUIRED_FILE:{name}:{path}")
            continue
        if path.suffix.lower() == ".json":
            try:
                payloads[name] = read_json(path)
            except Exception as exc:
                failures.append(f"INVALID_JSON:{name}:{type(exc).__name__}:{exc}")

    for name, payload in payloads.items():
        if payload.get("slot_id") not in (None, SLOT_ID):
            failures.append(f"WRONG_SLOT_PAYLOAD:{name}")

    current_task = payloads.get("current_task") or {}
    allowed = set(current_task.get("allowed_paths") or [])
    for expected in (
        str(SHARD_REL).replace("\\", "/"),
        str(SHARED_REL).replace("\\", "/"),
        str(WEB_REL).replace("\\", "/"),
    ):
        if expected not in allowed:
            failures.append(f"ALLOWED_PATH_MISSING:{expected}")
    if current_task.get("direct_push_forbidden") is not True:
        failures.append("DIRECT_PUSH_GUARD_MISSING")

    ownership = payloads.get("ownership") or {}
    heartbeat = payloads.get("heartbeat") or {}
    if ownership.get("state") not in ("unclaimed", "claimed"):
        failures.append("OWNERSHIP_STATE_INVALID")
    if heartbeat.get("state") not in ("unclaimed", "claimed"):
        failures.append("HEARTBEAT_STATE_INVALID")

    return {
        "pass": not failures,
        "failures": failures,
        "required_file_count": len(required),
        "slot_id": slot_id,
        "target_branch": target_branch,
    }


def re_full_sha(value: str) -> bool:
    return len(value) == 40 and all(ch in "0123456789abcdefABCDEF" for ch in value)


def git_context(repo: Path, target_branch: str) -> dict[str, Any]:
    head = run_command(["git", "rev-parse", "HEAD"], repo)
    branch = run_command(["git", "branch", "--show-current"], repo)
    clean = run_command(["git", "status", "--porcelain"], repo)
    observed_branch = branch.get("stdout") or ""
    failures: list[str] = []
    if not head["pass"] or not re_full_sha(head.get("stdout") or ""):
        failures.append("GIT_HEAD_UNAVAILABLE")
    if not branch["pass"] or observed_branch != target_branch:
        failures.append(f"WRONG_ACTIVE_BRANCH:{observed_branch}")
    if not clean["pass"]:
        failures.append("GIT_STATUS_UNAVAILABLE")
    return {
        "pass": not failures,
        "failures": failures,
        "head_sha": head.get("stdout") or None,
        "active_branch": observed_branch or None,
        "dirty_paths": [line for line in (clean.get("stdout") or "").splitlines() if line],
    }


def wait_http(url: str, timeout: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                url,
                headers={"Cache-Control": "no-cache", "User-Agent": "AAYS-gas-emissions-2-runtime/1.0"},
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                return {"pass": response.status == 200, "http_status": response.status, "error": None}
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            time.sleep(0.5)
    return {"pass": False, "http_status": None, "error": last_error or "HTTP_TIMEOUT"}


def validate_local_evidence(evidence: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    checks = evidence.get("checks_summary") or {}
    dataset = evidence.get("dataset_summary") or {}
    metadata = evidence.get("runner_metadata_summary") or {}

    expected_pairs = {
        "CHECKS": (checks.get("passed"), EXPECTED_CHECKS),
        "CHECKS_TOTAL": (checks.get("total"), EXPECTED_CHECKS),
        "HTTP": (checks.get("http_passed"), EXPECTED_HTTP),
        "HTTP_TOTAL": (checks.get("http_total"), EXPECTED_HTTP),
        "INTERACTIONS": (checks.get("interaction_passed"), EXPECTED_INTERACTIONS),
        "INTERACTIONS_TOTAL": (checks.get("interaction_total"), EXPECTED_INTERACTIONS),
        "CANDIDATE_ROWS": (dataset.get("candidate_rows"), EXPECTED_ROWS),
        "UNIQUE_CANDIDATES": (dataset.get("unique_candidate_ids"), EXPECTED_ROWS),
        "UNIQUE_LINES": (dataset.get("unique_preview_lines"), EXPECTED_ROWS),
        "QA_PASS": (dataset.get("qa_pass"), EXPECTED_ROWS),
        "QA_REVIEW": (dataset.get("qa_review"), 0),
        "DOM_ROWS": (dataset.get("dom_rows"), EXPECTED_ROWS),
        "CONSOLE_ERRORS": (dataset.get("console_errors"), 0),
        "PARCEL_BOUND_ROWS": (dataset.get("parcel_bound_rows"), 0),
        "LOCAL_METADATA": (metadata.get("passed"), EXPECTED_METADATA_LOCAL),
        "METADATA_TOTAL": (metadata.get("total"), EXPECTED_METADATA_FINAL),
    }
    for name, pair in expected_pairs.items():
        actual, expected = pair
        if actual != expected:
            failures.append(f"{name}:{actual}!={expected}")
    if checks.get("overall") != "PASS":
        failures.append("CHECKS_OVERALL_NOT_PASS")
    if evidence.get("slot_id") != SLOT_ID:
        failures.append("EVIDENCE_WRONG_SLOT")
    if evidence.get("final_ready") is not False:
        failures.append("EVIDENCE_FINAL_READY_NOT_FALSE")
    if evidence.get("proof_complete") is not False:
        failures.append("LOCAL_PHASE_MUST_NOT_CLAIM_PROOF_COMPLETE")
    missing = metadata.get("missing") or []
    if missing != ["remote_commit_and_readback"]:
        failures.append(f"UNEXPECTED_METADATA_MISSING:{missing}")
    return not failures, failures


def browser_capture(url: str, screenshot_path: Path, dom_path: Path, timeout_ms: int) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"pass": False, "error": f"PLAYWRIGHT_IMPORT:{type(exc).__name__}:{exc}"}

    console_events: list[dict[str, str]] = []
    page_errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1600, "height": 1200})
            page.on("console", lambda msg: console_events.append({"type": msg.type, "text": msg.text}))
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            response = page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.wait_for_function("window.__gasEmissions2RuntimeEvidenceReady === true", timeout=timeout_ms)
            evidence = page.evaluate("window.__gasEmissions2RuntimeEvidence")
            html = page.content()
            page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()
        dom_path.write_text(html, encoding="utf-8")
        return {
            "pass": True,
            "http_status": response.status if response else None,
            "evidence": evidence,
            "console_events": console_events,
            "page_errors": page_errors,
            "error": None,
        }
    except Exception as exc:
        return {
            "pass": False,
            "http_status": None,
            "evidence": None,
            "console_events": console_events,
            "page_errors": page_errors,
            "error": f"BROWSER:{type(exc).__name__}:{exc}",
        }


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot_id = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    target_branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    output_root = repo / SHARD_REL / "runner_outputs"
    output_root.mkdir(parents=True, exist_ok=True)

    receipt_path = output_root / "gas_emissions_2_runtime_pipeline_receipt_latest.json"
    evidence_path = output_root / "gas_emissions_2_runtime_evidence_local_latest.json"
    screenshot_path = output_root / "gas_emissions_2_runtime_evidence_latest.png"
    dom_path = output_root / "gas_emissions_2_runtime_dom_latest.html"
    console_path = output_root / "gas_emissions_2_runtime_console_latest.json"
    server_log_path = output_root / "gas_emissions_2_http_server_latest.log"

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "task_version": "20260721_23",
        "steps": [],
        "browser_acceptance_before": 66,
        "browser_acceptance_after": 66,
        "actual_business_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }

    def finish(state: str, blocker: str | None, exit_code: int) -> dict[str, Any]:
        artifacts: dict[str, Any] = {}
        for name, path in {
            "receipt": receipt_path,
            "local_evidence": evidence_path,
            "screenshot": screenshot_path,
            "dom": dom_path,
            "console": console_path,
            "server_log": server_log_path,
        }.items():
            if path.is_file():
                artifacts[name] = {
                    "path": str(path.relative_to(repo)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                }
        receipt.update(
            {
                "state": state,
                "blocker": blocker,
                "exit_code": exit_code,
                "completed_at": utc_now(),
                "artifacts": artifacts,
                "publisher_action_required": state == "LOCAL_RUNTIME_PASS_AWAITING_PUBLISHER_COMMIT_READBACK",
                "completion_forbidden_without_remote_commit_readback": True,
            }
        )
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt

    contract = validate_contract(repo, slot_id, target_branch)
    receipt["steps"].append({"name": "CONTRACT", **contract})
    if not contract["pass"]:
        return finish("BLOCKED_CONTRACT", ";".join(contract["failures"]), 2)

    git = git_context(repo, target_branch)
    receipt["steps"].append({"name": "GIT_CONTEXT", **git})
    if not git["pass"]:
        return finish("BLOCKED_GIT_CONTEXT", ";".join(git["failures"]), 3)

    with server_log_path.open("w", encoding="utf-8") as server_log:
        server = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(args.port), "--bind", "127.0.0.1"],
            cwd=str(repo),
            stdout=server_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
    try:
        base_url = f"http://127.0.0.1:{args.port}"
        collector_base = base_url + "/" + str(WEB_REL / "runtime_evidence_collector.html").replace("\\", "/")
        query = urllib.parse.urlencode(
            {
                "served_commit": git["head_sha"],
                "screenshot_path": str(screenshot_path.relative_to(repo)).replace("\\", "/"),
                "runner_output_path": str(evidence_path.relative_to(repo)).replace("\\", "/"),
                "remote_readback": "0",
            }
        )
        collector_url = collector_base + "?" + query

        health = wait_http(collector_base, args.http_wait_timeout)
        receipt["steps"].append({"name": "HTTP_SERVER", **health, "url": collector_base})
        if not health["pass"]:
            return finish("BLOCKED_HTTP_SERVER", str(health.get("error")), 4)

        capture = browser_capture(collector_url, screenshot_path, dom_path, args.browser_timeout_ms)
        receipt["steps"].append(
            {
                "name": "PLAYWRIGHT_CAPTURE",
                "pass": capture.get("pass"),
                "http_status": capture.get("http_status"),
                "error": capture.get("error"),
                "console_event_count": len(capture.get("console_events") or []),
                "page_error_count": len(capture.get("page_errors") or []),
            }
        )
        console_payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "generated_at": utc_now(),
            "console_events": capture.get("console_events") or [],
            "page_errors": capture.get("page_errors") or [],
            "final_ready": False,
        }
        console_path.write_text(json.dumps(console_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not capture.get("pass") or not isinstance(capture.get("evidence"), dict):
            return finish("BLOCKED_BROWSER_CAPTURE", str(capture.get("error")), 5)

        evidence = dict(capture["evidence"])
        evidence.update(
            {
                "runner_capture_phase": "LOCAL_RUNTIME_BEFORE_PUBLISHER_COMMIT",
                "served_commit_sha": git["head_sha"],
                "screenshot_sha256": sha256_file(screenshot_path),
                "dom_sha256": sha256_file(dom_path),
                "console_sha256": sha256_file(console_path),
                "remote_commit_and_readback": False,
                "proof_complete": False,
                "publisher_finalize_required": True,
                "final_ready": False,
            }
        )
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        local_ok, failures = validate_local_evidence(evidence)
        receipt["steps"].append(
            {
                "name": "LOCAL_EVIDENCE_GATE",
                "pass": local_ok,
                "failures": failures,
                "expected_local_metadata": f"{EXPECTED_METADATA_LOCAL}/{EXPECTED_METADATA_FINAL}",
                "expected_checks": f"{EXPECTED_CHECKS}/{EXPECTED_CHECKS}",
            }
        )
        if not local_ok:
            return finish("BLOCKED_LOCAL_EVIDENCE_GATE", ";".join(failures), 6)

        return finish("LOCAL_RUNTIME_PASS_AWAITING_PUBLISHER_COMMIT_READBACK", None, 0)
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
    parser.add_argument("--slot-id", default=SLOT_ID)
    parser.add_argument("--target-branch", default=TARGET_BRANCH)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    parser.add_argument("--browser-timeout-ms", type=int, default=120000)
    return parser.parse_args()


if __name__ == "__main__":
    result = run_pipeline(parse_args())
    print(
        json.dumps(
            {
                "slot_id": SLOT_ID,
                "state": result.get("state"),
                "blocker": result.get("blocker"),
                "exit_code": result.get("exit_code"),
                "browser_acceptance_after": 66,
                "final_ready": False,
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(int(result.get("exit_code") or 0))
