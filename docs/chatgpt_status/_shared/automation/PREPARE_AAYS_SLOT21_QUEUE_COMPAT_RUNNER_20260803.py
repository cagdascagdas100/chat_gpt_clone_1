#!/usr/bin/env python3
"""Prepare and execute a transient slot-21-compatible copy of the canonical AAYS runner.

The canonical runner remains single-instance. This shim only patches its generated
remote queue mirror to include `_shared/slots_21/<slot>/queue/<task>` paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
from dataclasses import dataclass

SCAN_SOURCE = "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1"
DAEMON_SOURCE = "RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1"
PATCHED_SCAN = "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_SLOT21_PATCHED_20260803.ps1"
PATCHED_DAEMON = "RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_SLOT21_PATCHED_20260803.ps1"

OLD_QUEUE_REGEX = r"^docs/chatgpt_status/[^/]+/queue/[^/]+$"
NEW_QUEUE_REGEX = (
    r"^(?:docs/chatgpt_status/[^/]+/queue/[^/]+|"
    r"docs/chatgpt_status/_shared/slots_21/[^/]+/queue/[^/]+)$"
)
DAEMON_RUNNER_LINE = (
    '$runner = Join-Path $automationRoot "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1"'
)


@dataclass(frozen=True)
class Prepared:
    mode: str
    script_path: pathlib.Path
    scan_source_sha256: str
    daemon_source_sha256: str | None


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8", newline="")
    tmp.replace(path)


def patch_scan(text: str) -> str:
    if text.count(OLD_QUEUE_REGEX) != 1:
        raise RuntimeError("SCAN_QUEUE_REGEX_MARKER_COUNT_NOT_ONE")
    return text.replace(OLD_QUEUE_REGEX, NEW_QUEUE_REGEX, 1)


def ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def patch_daemon(text: str, patched_scan_path: pathlib.Path) -> str:
    if text.count(DAEMON_RUNNER_LINE) != 1:
        raise RuntimeError("DAEMON_RUNNER_MARKER_COUNT_NOT_ONE")
    replacement = "$runner = " + ps_single_quote(str(patched_scan_path))
    return text.replace(DAEMON_RUNNER_LINE, replacement, 1)


def prepare(repo_root: pathlib.Path, work_root: pathlib.Path, mode: str) -> Prepared:
    automation = repo_root / "docs" / "chatgpt_status" / "_shared" / "automation"
    scan_source_path = automation / SCAN_SOURCE
    daemon_source_path = automation / DAEMON_SOURCE
    if not scan_source_path.is_file():
        raise FileNotFoundError(f"SCAN_RUNNER_MISSING:{scan_source_path}")
    if mode == "daemon" and not daemon_source_path.is_file():
        raise FileNotFoundError(f"DAEMON_RUNNER_MISSING:{daemon_source_path}")

    output_dir = work_root / "_slot21_queue_compat"
    scan_text = read_text(scan_source_path)
    patched_scan_path = output_dir / PATCHED_SCAN
    write_text(patched_scan_path, patch_scan(scan_text))

    if mode == "scan":
        return Prepared(mode, patched_scan_path, sha256_text(scan_text), None)

    daemon_text = read_text(daemon_source_path)
    patched_daemon_path = output_dir / PATCHED_DAEMON
    write_text(patched_daemon_path, patch_daemon(daemon_text, patched_scan_path))
    return Prepared(
        mode,
        patched_daemon_path,
        sha256_text(scan_text),
        sha256_text(daemon_text),
    )


def find_powershell() -> str:
    for name in ("powershell.exe", "powershell", "pwsh.exe", "pwsh"):
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("POWERSHELL_EXECUTABLE_NOT_FOUND")


def self_test() -> None:
    fixture_scan = (
        "prefix\n"
        "  } | Where-Object { $_.path -match '" + OLD_QUEUE_REGEX + "' })\n"
        "suffix\n"
    )
    patched = patch_scan(fixture_scan)
    assert NEW_QUEUE_REGEX in patched
    queue_pattern = re.compile(NEW_QUEUE_REGEX)
    assert queue_pattern.fullmatch("docs/chatgpt_status/aays1/queue/task.json")
    assert queue_pattern.fullmatch(
        "docs/chatgpt_status/_shared/slots_21/ready_to_sell_3/queue/task.v3.task.json"
    )
    assert not queue_pattern.fullmatch(
        "docs/chatgpt_status/_shared/slots_21/ready_to_sell_3/status_latest.json"
    )
    fixture_daemon = "before\n" + DAEMON_RUNNER_LINE + "\nafter\n"
    patched_daemon = patch_daemon(fixture_daemon, pathlib.Path(r"F:\work\patched.ps1"))
    assert "patched.ps1" in patched_daemon
    try:
        patch_scan(fixture_scan.replace(OLD_QUEUE_REGEX, "missing"))
    except RuntimeError as exc:
        assert str(exc) == "SCAN_QUEUE_REGEX_MARKER_COUNT_NOT_ONE"
    else:
        raise AssertionError("missing marker must fail closed")
    print(json.dumps({"self_test": "PASS", "queue_modes": 2}))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--work-root")
    parser.add_argument("--mode", choices=("scan", "daemon"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("powershell_args", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.repo_root or not args.work_root or not args.mode:
        raise SystemExit("--repo-root, --work-root and --mode are required")

    prepared = prepare(pathlib.Path(args.repo_root), pathlib.Path(args.work_root), args.mode)
    passthrough = list(args.powershell_args)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    command = [
        find_powershell(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(prepared.script_path),
        *passthrough,
    ]
    evidence = {
        "mode": prepared.mode,
        "script_path": str(prepared.script_path),
        "scan_source_sha256": prepared.scan_source_sha256,
        "daemon_source_sha256": prepared.daemon_source_sha256,
        "single_runner_preserved": True,
    }
    print(json.dumps(evidence, sort_keys=True), flush=True)
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
