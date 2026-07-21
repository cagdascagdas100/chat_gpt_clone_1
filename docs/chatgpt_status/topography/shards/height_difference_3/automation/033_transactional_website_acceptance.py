#!/usr/bin/env python3
"""Transactional wrapper for height_difference_3 website acceptance.

Snapshots the current website JSON, GeoJSON and runtime files before invoking
031. If 031 fails for any reason, every target is restored byte-for-byte (or
removed when it did not previously exist). No queue, lease, owner, heartbeat,
new runner or parallel runner is created.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".rollback.tmp", dir=path.parent)
    os.close(fd)
    temp = Path(name)
    try:
        temp.write_bytes(value)
        if sha256_bytes(temp.read_bytes()) != sha256_bytes(value):
            raise RuntimeError(f"temporary write hash mismatch: {path}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def atomic_json(path: Path, value: Any) -> None:
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def snapshot(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.exists():
        return {"path": str(resolved), "existed": False, "bytes": None, "sha256": None}
    if not resolved.is_file():
        raise ValueError(f"acceptance target is not a file: {resolved}")
    raw = resolved.read_bytes()
    return {"path": str(resolved), "existed": True, "bytes": raw, "sha256": sha256_bytes(raw)}


def restore(item: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(item["path"]))
    if item["existed"]:
        raw = item["bytes"]
        if not isinstance(raw, bytes):
            raise TypeError(f"snapshot bytes missing: {path}")
        atomic_bytes(path, raw)
        actual = sha256_bytes(path.read_bytes())
        if actual != item["sha256"]:
            raise RuntimeError(f"rollback hash mismatch: {path}")
        return {"path": str(path), "action": "restored", "sha256": actual}
    path.unlink(missing_ok=True)
    return {"path": str(path), "action": "removed_new_file", "sha256": None}


def run(command: list[str]) -> dict[str, Any]:
    started = utc_now()
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "started_at": started,
        "finished_at": utc_now(),
        "command": command,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-16000:],
        "stderr_tail": proc.stderr[-16000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acceptance-script", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--web-json", required=True, type=Path)
    parser.add_argument("--web-geojson", required=True, type=Path)
    parser.add_argument("--web-runtime-status", required=True, type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8012")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--acceptance-output", type=Path)
    parser.add_argument("--transaction-output", type=Path)
    args = parser.parse_args()

    if args.timeout < 1:
        raise ValueError("timeout must be positive")
    acceptance_script = args.acceptance_script.resolve()
    if not acceptance_script.is_file():
        raise FileNotFoundError(acceptance_script)

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    acceptance_output = (args.acceptance_output or out / "website_acceptance_latest.json").resolve()
    transaction_output = (args.transaction_output or out / "website_acceptance_transaction_latest.json").resolve()

    targets = [args.web_json.resolve(), args.web_geojson.resolve(), args.web_runtime_status.resolve(), acceptance_output]
    snapshots = [snapshot(path) for path in targets]
    public_snapshot = [{key: value for key, value in item.items() if key != "bytes"} for item in snapshots]
    state: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "updated_at": utc_now(),
        "status": "WEBSITE_ACCEPTANCE_TRANSACTION_RUNNING",
        "snapshots": public_snapshot,
        "acceptance": None,
        "rollback": [],
        "rollback_succeeded": None,
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_json(transaction_output, state)

    command = [
        sys.executable,
        str(acceptance_script),
        "--output-dir", str(out),
        "--web-json", str(args.web_json.resolve()),
        "--web-geojson", str(args.web_geojson.resolve()),
        "--web-runtime-status", str(args.web_runtime_status.resolve()),
        "--base-url", args.base_url,
        "--timeout", str(args.timeout),
        "--acceptance-output", str(acceptance_output),
    ]
    result = run(command)
    state["acceptance"] = result
    state["updated_at"] = utc_now()

    if result["exit_code"] == 0:
        state["status"] = "WEBSITE_ACCEPTANCE_TRANSACTION_COMMITTED"
        state["rollback_succeeded"] = False
        state["committed_targets"] = [
            {"path": str(path), "exists": path.is_file(), "sha256": sha256_bytes(path.read_bytes()) if path.is_file() else None}
            for path in targets
        ]
        atomic_json(transaction_output, state)
        print(json.dumps({"ok": True, "status": state["status"], "transaction": str(transaction_output)}))
        return 0

    rollback_results: list[dict[str, Any]] = []
    rollback_errors: list[str] = []
    for item in reversed(snapshots):
        try:
            rollback_results.append(restore(item))
        except Exception as exc:
            rollback_errors.append(f"{item['path']}: {type(exc).__name__}: {exc}")
    state["rollback"] = rollback_results
    state["rollback_succeeded"] = not rollback_errors
    state["rollback_errors"] = rollback_errors
    state["status"] = "BLOCKED_WEBSITE_ACCEPTANCE_ROLLED_BACK" if not rollback_errors else "CRITICAL_WEBSITE_ACCEPTANCE_ROLLBACK_FAILED"
    state["updated_at"] = utc_now()
    atomic_json(transaction_output, state)
    print(json.dumps({"ok": False, "status": state["status"], "acceptance_exit_code": result["exit_code"], "rollback_succeeded": state["rollback_succeeded"], "transaction": str(transaction_output)}), file=sys.stderr)
    return int(result["exit_code"]) if not rollback_errors else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
