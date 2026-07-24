from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check(condition: bool, name: str, detail: str, results: list[dict[str, Any]]) -> None:
    results.append({"name": name, "pass": bool(condition), "detail": detail})


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("gas_emissions_2_runtime_guard_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"GUARD_IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def start_server(directory: Path, port: int) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(directory),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def wait_server(port: int) -> None:
    import urllib.request
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1):
                return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("TEST_HTTP_SERVER_TIMEOUT")


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def run(repo: Path) -> dict[str, Any]:
    root = repo / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_2/automation"
    guard_path = root / "gas_emissions_2_runtime_pipeline_guard_v2.py"
    base_path = root / "gas_emissions_2_runtime_pipeline.py"
    carrier_path = root / "gas_emissions_2_runtime_pipeline_v5_1.ps1"
    results: list[dict[str, Any]] = []

    check(guard_path.is_file(), "guard_exists", str(guard_path), results)
    check(base_path.is_file(), "base_pipeline_exists", str(base_path), results)
    check(carrier_path.is_file(), "carrier_exists", str(carrier_path), results)
    guard_text = guard_path.read_text(encoding="utf-8") if guard_path.is_file() else ""
    carrier_text = carrier_path.read_text(encoding="utf-8") if carrier_path.is_file() else ""

    try:
        ast.parse(guard_text)
        syntax_ok = True
        detail = "ast.parse PASS"
    except Exception as exc:
        syntax_ok = False
        detail = f"{type(exc).__name__}:{exc}"
    check(syntax_ok, "guard_python_syntax", detail, results)

    tokens = [
        'SLOT_ID = "gas_emissions_2"',
        'TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"',
        'GUARD_VERSION = "20260721_24"',
        "PORT_OWNERSHIP_PREFLIGHT",
        "BLOCKED_PORT_ALREADY_IN_USE",
        "resolve_browser_executable",
        "AAYS_CHROMIUM_PATH",
        "runtime_asset_paths",
        "verify_served_assets",
        "SERVED_RUNTIME_ASSET_SHA_MISMATCH",
        "served_asset_validation",
        "browser_error_events",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-software-rasterizer",
        "completion_forbidden_without_remote_commit_readback",
        '"browser_acceptance_after": 66',
        '"final_ready": False',
        '"fake_data": False',
        '"db_write": False',
        '"migration": False',
        '"production_deploy": False',
    ]
    for token in tokens:
        check(token in guard_text, "guard_token", token, results)

    carrier_tokens = [
        "gas_emissions_2_runtime_pipeline_guard_v2.py",
        "SINGLE_SHARED_RUNNER_ONLY=true",
        "NEW_RUNNER=false",
        "PARALLEL_RUNNER=false",
        "DIRECT_PUSH=false",
        "FINAL_READY=false",
        "'..\\..\\..\\..\\..\\..'",
    ]
    for token in carrier_tokens:
        check(token in carrier_text, "carrier_token", token, results)

    check("git push" not in guard_text.lower() and "git push" not in carrier_text.lower(), "no_direct_push_command", "git push absent", results)

    functional: dict[str, Any] = {}
    if syntax_ok:
        module = load_module(guard_path)
        check(module.sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "sha256_known_vector", "abc SHA256", results)

        holder = socket.socket()
        holder.bind(("127.0.0.1", 0))
        occupied_port = holder.getsockname()[1]
        occupied = module.port_preflight("127.0.0.1", occupied_port)
        holder.close()
        released = module.port_preflight("127.0.0.1", occupied_port)
        check(occupied.get("pass") is False, "port_rejects_occupied", str(occupied), results)
        check(released.get("pass") is True, "port_accepts_released", str(released), results)
        functional["port_preflight"] = {"occupied": occupied, "released": released}

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                browser = module.resolve_browser_executable(playwright)
            check(browser.get("pass") is True, "browser_executable_resolved", str(browser), results)
            functional["browser_resolution"] = browser
        except Exception as exc:
            check(False, "browser_executable_resolved", f"{type(exc).__name__}:{exc}", results)

        web = repo / "england_map_web/data/aays_21_slots/gas_emissions_2"
        manifest = json.loads((web / "candidate_manifest_latest.json").read_text(encoding="utf-8-sig"))
        required = [
            "runtime_evidence_collector.html",
            "candidate_manifest_latest.json",
            "qa_rules_latest.json",
            "sources_latest.json",
            "status_latest.json",
        ] + [str(item.get("path") or "").lstrip("./") for item in (manifest.get("data_files") or [])]
        required = [name for name in required if name]

        with tempfile.TemporaryDirectory() as tmp:
            stale_root = Path(tmp)
            stale_web = stale_root / "england_map_web/data/aays_21_slots/gas_emissions_2"
            stale_web.mkdir(parents=True)
            for name in required:
                source = web / name
                target = stale_web / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

            port = free_port()
            server = start_server(repo, port)
            try:
                wait_server(port)
                exact = module.verify_served_assets(repo, f"http://127.0.0.1:{port}")
            finally:
                server.terminate()
                server.wait(timeout=5)
            check(exact.get("pass") is True, "served_assets_exact_pass", f"{exact.get('passed')}/{exact.get('asset_count')}", results)
            functional["exact_asset_validation"] = {"passed": exact.get("passed"), "total": exact.get("asset_count")}

            collector = stale_web / "runtime_evidence_collector.html"
            collector.write_text(collector.read_text(encoding="utf-8") + "\n<!-- stale -->\n", encoding="utf-8")
            stale_port = free_port()
            stale_server = start_server(stale_root, stale_port)
            try:
                wait_server(stale_port)
                mismatch = module.verify_served_assets(repo, f"http://127.0.0.1:{stale_port}")
            finally:
                stale_server.terminate()
                stale_server.wait(timeout=5)
            check(mismatch.get("pass") is False, "served_assets_stale_rejected", f"{mismatch.get('passed')}/{mismatch.get('asset_count')}", results)
            mismatch_rows = [item for item in mismatch.get("results") or [] if not item.get("pass")]
            check(any(item.get("path", "").endswith("runtime_evidence_collector.html") for item in mismatch_rows), "collector_sha_mismatch_detected", str(mismatch_rows[:2]), results)
            functional["stale_asset_validation"] = {
                "passed": mismatch.get("passed"),
                "total": mismatch.get("asset_count"),
                "mismatch_count": len(mismatch_rows),
            }

    passed = sum(1 for item in results if item["pass"])
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "validation_scope": "LOCAL_STATIC_AND_FUNCTIONAL_RUNTIME_GUARD_V2_SELFTEST",
        "checks": results,
        "passed": passed,
        "total": len(results),
        "all_checks_pass": passed == len(results),
        "functional": functional,
        "runtime_executed": False,
        "browser_acceptance_changed": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    payload = run(Path(args.repo_root).resolve())
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"slot_id": SLOT_ID, "passed": payload["passed"], "total": payload["total"], "all_checks_pass": payload["all_checks_pass"], "final_ready": False}))
    raise SystemExit(0 if payload["all_checks_pass"] else 1)
