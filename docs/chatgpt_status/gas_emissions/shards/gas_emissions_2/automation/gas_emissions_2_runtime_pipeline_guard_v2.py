from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
DEFAULT_PORT = 8012
SHARD_REL = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_2")
WEB_REL = Path("england_map_web/data/aays_21_slots/gas_emissions_2")
BASE_PIPELINE = Path(__file__).with_name("gas_emissions_2_runtime_pipeline.py")
GUARD_VERSION = "20260721_24"
_CURRENT_REPO: Path | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_base_pipeline() -> Any:
    spec = importlib.util.spec_from_file_location("gas_emissions_2_runtime_pipeline_base", BASE_PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"BASE_PIPELINE_IMPORT_FAILED:{BASE_PIPELINE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def port_preflight(host: str, port: int) -> dict[str, Any]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        sock.bind((host, port))
        return {
            "pass": True,
            "host": host,
            "port": port,
            "requested_port": port,
            "fallback_port": False,
            "error": None,
        }
    except OSError as exc:
        bind_error = f"{type(exc).__name__}:{exc}"
    finally:
        sock.close()
    fallback = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        fallback.bind((host, 0))
        fallback_port = int(fallback.getsockname()[1])
        return {
            "pass": True,
            "host": host,
            "port": fallback_port,
            "requested_port": port,
            "fallback_port": True,
            "error": None,
            "preferred_port_bind_error": bind_error,
        }
    except OSError as exc:
        return {
            "pass": False,
            "host": host,
            "port": port,
            "requested_port": port,
            "fallback_port": False,
            "error": f"{bind_error};FALLBACK:{type(exc).__name__}:{exc}",
        }
    finally:
        fallback.close()


def resolve_browser_executable(playwright: Any) -> dict[str, Any]:
    candidates: list[tuple[str, str | None]] = [
        ("AAYS_CHROMIUM_PATH", os.environ.get("AAYS_CHROMIUM_PATH")),
        ("PLAYWRIGHT_CHROMIUM", getattr(playwright.chromium, "executable_path", None)),
    ]
    for command in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "msedge", "chrome"):
        candidates.append((f"PATH:{command}", shutil.which(command)))
    for root in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
        if root:
            for suffix in (
                "Google/Chrome/Application/chrome.exe",
                "Microsoft/Edge/Application/msedge.exe",
                "Chromium/Application/chrome.exe",
            ):
                candidates.append((f"WINDOWS:{suffix}", str(Path(root) / suffix)))

    checked: list[dict[str, Any]] = []
    for source, raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        exists = path.is_file()
        checked.append({"source": source, "path": str(path), "exists": exists})
        if exists:
            return {"pass": True, "source": source, "path": str(path), "checked": checked}
    return {"pass": False, "source": None, "path": None, "checked": checked}


def fetch_bytes(url: str, timeout: int = 15) -> dict[str, Any]:
    try:
        request = urllib.request.Request(
            url,
            headers={"Cache-Control": "no-cache", "User-Agent": "AAYS-gas-emissions-2-guard/2.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return {
                "pass": response.status == 200,
                "http_status": response.status,
                "sha256": sha256_bytes(body),
                "body_size": len(body),
                "error": None,
            }
    except Exception as exc:
        return {
            "pass": False,
            "http_status": None,
            "sha256": None,
            "body_size": 0,
            "error": f"{type(exc).__name__}:{exc}",
        }


def runtime_asset_paths(repo: Path) -> list[Path]:
    manifest = read_json(repo / WEB_REL / "candidate_manifest_latest.json")
    assets = [
        WEB_REL / "runtime_evidence_collector.html",
        WEB_REL / "candidate_manifest_latest.json",
        WEB_REL / "qa_rules_latest.json",
        WEB_REL / "sources_latest.json",
        WEB_REL / "status_latest.json",
    ]
    for item in manifest.get("data_files") or []:
        raw = str(item.get("path") or "").lstrip("./")
        if raw:
            assets.append(WEB_REL / raw)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in assets:
        key = str(path).replace("\\", "/")
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def verify_served_assets(repo: Path, origin: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for relative in runtime_asset_paths(repo):
        local = repo / relative
        local_exists = local.is_file()
        url = origin.rstrip("/") + "/" + str(relative).replace("\\", "/")
        remote = fetch_bytes(url)
        local_sha = sha256_file(local) if local_exists else None
        passed = local_exists and remote.get("pass") is True and remote.get("sha256") == local_sha
        results.append(
            {
                "path": str(relative).replace("\\", "/"),
                "url": url,
                "local_exists": local_exists,
                "local_sha256": local_sha,
                "served_sha256": remote.get("sha256"),
                "http_status": remote.get("http_status"),
                "body_size": remote.get("body_size"),
                "pass": passed,
                "error": remote.get("error"),
            }
        )
    return {
        "pass": bool(results) and all(item["pass"] for item in results),
        "asset_count": len(results),
        "passed": sum(1 for item in results if item["pass"]),
        "results": results,
    }


def guarded_browser_capture(url: str, screenshot_path: Path, dom_path: Path, timeout_ms: int) -> dict[str, Any]:
    repo = _CURRENT_REPO
    if repo is None:
        return {"pass": False, "error": "GUARD_REPO_CONTEXT_MISSING"}

    parsed = urllib.parse.urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    served = verify_served_assets(repo, origin)
    if not served["pass"]:
        return {
            "pass": False,
            "error": "SERVED_RUNTIME_ASSET_SHA_MISMATCH",
            "served_asset_validation": served,
            "console_events": [],
            "browser_error_events": [],
            "page_errors": [],
        }

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"pass": False, "error": f"PLAYWRIGHT_IMPORT:{type(exc).__name__}:{exc}", "served_asset_validation": served}

    console_events: list[dict[str, str]] = []
    page_errors: list[str] = []
    browser_resolution: dict[str, Any] | None = None
    try:
        with sync_playwright() as playwright:
            browser_resolution = resolve_browser_executable(playwright)
            if not browser_resolution["pass"]:
                return {
                    "pass": False,
                    "error": "BROWSER_EXECUTABLE_NOT_FOUND",
                    "browser_resolution": browser_resolution,
                    "served_asset_validation": served,
                    "console_events": console_events,
                    "browser_error_events": [],
                    "page_errors": page_errors,
                }
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=browser_resolution["path"],
                args=[
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-software-rasterizer",
                ],
            )
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
        browser_errors = [event for event in console_events if event.get("type") == "error"]
        if isinstance(evidence, dict):
            evidence["served_asset_validation"] = {
                "passed": served["passed"],
                "total": served["asset_count"],
                "all_pass": served["pass"],
                "results": served["results"],
            }
        passed = (
            response is not None
            and response.status == 200
            and not browser_errors
            and not page_errors
            and isinstance(evidence, dict)
        )
        return {
            "pass": passed,
            "http_status": response.status if response else None,
            "evidence": evidence,
            "console_events": console_events,
            "browser_error_events": browser_errors,
            "page_errors": page_errors,
            "browser_resolution": browser_resolution,
            "served_asset_validation": served,
            "error": None if passed else "BROWSER_CONSOLE_PAGE_OR_EVIDENCE_ERROR",
        }
    except Exception as exc:
        return {
            "pass": False,
            "http_status": None,
            "evidence": None,
            "console_events": console_events,
            "browser_error_events": [event for event in console_events if event.get("type") == "error"],
            "page_errors": page_errors,
            "browser_resolution": browser_resolution,
            "served_asset_validation": served,
            "error": f"BROWSER:{type(exc).__name__}:{exc}",
        }


def write_guard_receipt(repo: Path, payload: dict[str, Any]) -> Path:
    output = repo / SHARD_REL / "runner_outputs/gas_emissions_2_runtime_guard_v2_receipt_latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def run(args: argparse.Namespace) -> dict[str, Any]:
    global _CURRENT_REPO
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    _CURRENT_REPO = repo
    slot_id = args.slot_id or SLOT_ID
    target_branch = args.target_branch or TARGET_BRANCH

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "guard_version": GUARD_VERSION,
        "generated_at": utc_now(),
        "steps": [],
        "runtime_executed": False,
        "browser_acceptance_before": 66,
        "browser_acceptance_after": 66,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }

    failures: list[str] = []
    if slot_id != SLOT_ID:
        failures.append(f"WRONG_SLOT:{slot_id}")
    if target_branch != TARGET_BRANCH:
        failures.append(f"WRONG_BRANCH:{target_branch}")
    if not BASE_PIPELINE.is_file():
        failures.append(f"BASE_PIPELINE_MISSING:{BASE_PIPELINE}")
    receipt["steps"].append({"name": "GUARD_CONTRACT", "pass": not failures, "failures": failures})
    if failures:
        receipt.update({"state": "BLOCKED_GUARD_CONTRACT", "blocker": ";".join(failures), "exit_code": 20})
        write_guard_receipt(repo, receipt)
        return receipt

    port = port_preflight("127.0.0.1", args.port)
    receipt["steps"].append({"name": "PORT_OWNERSHIP_PREFLIGHT", **port})
    if not port["pass"]:
        receipt.update({"state": "BLOCKED_PORT_ALREADY_IN_USE", "blocker": port.get("error"), "exit_code": 21})
        write_guard_receipt(repo, receipt)
        return receipt
    args.port = int(port["port"])

    base = load_base_pipeline()
    base.browser_capture = guarded_browser_capture
    base_result = base.run_pipeline(args)
    receipt["steps"].append(
        {
            "name": "BASE_PIPELINE",
            "pass": int(base_result.get("exit_code") or 0) == 0,
            "state": base_result.get("state"),
            "blocker": base_result.get("blocker"),
            "exit_code": base_result.get("exit_code"),
        }
    )
    receipt.update(
        {
            "state": base_result.get("state"),
            "blocker": base_result.get("blocker"),
            "exit_code": int(base_result.get("exit_code") or 0),
            "runtime_executed": True,
            "base_pipeline_receipt": str(
                SHARD_REL / "runner_outputs/gas_emissions_2_runtime_pipeline_receipt_latest.json"
            ).replace("\\", "/"),
            "completion_forbidden_without_remote_commit_readback": True,
            "completed_at": utc_now(),
        }
    )
    write_guard_receipt(repo, receipt)
    return receipt


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
    result = run(parse_args())
    print(
        json.dumps(
            {
                "slot_id": SLOT_ID,
                "guard_version": GUARD_VERSION,
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
