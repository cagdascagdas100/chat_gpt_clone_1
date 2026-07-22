from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"
SELECTABLE = {"pickup_requested", "queued", "ready", "pending", "pending_repo_queue", "queued_for_single_shared_runner"}

class StrictJsonError(ValueError):
    pass

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def reject_constant(value: str) -> None:
    raise StrictJsonError(f"NONFINITE_JSON_CONSTANT:{value}")

def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise StrictJsonError(f"DUPLICATE_JSON_KEY:{key}")
        out[key] = value
    return out

def strict_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant)

def load_or_none(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return strict_load(path)
    except Exception:
        return None

def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp = Path(tmp.name)
    os.replace(temp, path)

def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)

def require(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)

def git_blob_sha(path: Path) -> str | None:
    if not path.is_file():
        return None
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

def projection(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task.get("task_id"),
        "attempt_id": task.get("attempt_id"),
        "slot_id": task.get("slot_id"),
        "priority": task.get("priority"),
        "page_key": task.get("page_key"),
        "target_branch": task.get("target_branch"),
        "source_branch": task.get("source_branch"),
        "script_path": task.get("script_path"),
        "automation_script": task.get("automation_script"),
        "sample_parcels": task.get("sample_parcels"),
        "parcel_partition": task.get("parcel_partition"),
        "canonical_source": task.get("canonical_source"),
        "single_shared_runner_required": task.get("single_shared_runner_required"),
        "new_runner_allowed": task.get("new_runner_allowed"),
        "fake_data": task.get("fake_data"),
        "final_ready": task.get("final_ready"),
    }

def run_base_validator(repo: Path, manifest: Path, validator: Path, output: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(validator), "--repo-root", str(repo), "--manifest", str(manifest), "--output", str(output)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
        check=False,
    )
    report = load_or_none(output)
    if not isinstance(report, dict):
        return {
            "valid": False,
            "error_count": 1,
            "errors": [f"BASE_VALIDATOR_REPORT_MISSING_EXIT_{completed.returncode}", completed.stderr[-2000:]],
        }
    return report

def in_window(value: datetime | None, start: datetime | None, end: datetime | None, skew: timedelta) -> bool:
    return bool(value and start and end and start - skew <= value <= end + skew)

def validate_generation(repo: Path, manifest: dict[str, Any], docs: dict[str, Any], base_report: dict[str, Any]) -> dict[str, Any]:
    errors = list(base_report.get("errors", []))
    skew = timedelta(seconds=int(manifest.get("max_clock_skew_seconds", 5)))
    task_path = repo / manifest["canonical_queue_path"]
    template_path = repo / manifest["priority2_template_path"]
    queue = docs.get("queue")
    template = docs.get("template")
    started = docs.get("runner_started")
    preflight = docs.get("preflight")
    outer = docs.get("outer_watchdog")
    canonical = docs.get("canonical")
    reconciliation = docs.get("reconciliation")
    website = docs.get("website_canonical")
    probe = docs.get("probe")
    watchdog = docs.get("watchdog")
    chain = docs.get("chain")

    require(isinstance(queue, dict), "CURRENT_QUEUE_NOT_STRICT_OBJECT", errors)
    require(isinstance(template, dict), "PRIORITY2_TEMPLATE_NOT_STRICT_OBJECT", errors)
    if isinstance(queue, dict) and isinstance(template, dict):
        require(projection(queue) == projection(template), "CURRENT_QUEUE_TEMPLATE_PROJECTION_MISMATCH", errors)
        require(queue.get("task_id") == manifest["canonical_task_id"], "CURRENT_QUEUE_TASK_ID_MISMATCH", errors)
        require(queue.get("attempt_id") == manifest["expected_attempt_id"], "CURRENT_QUEUE_ATTEMPT_ID_MISMATCH", errors)
        require(queue.get("script_path") == manifest["expected_script_path"], "CURRENT_QUEUE_SCRIPT_PATH_MISMATCH", errors)
        require(str(queue.get("status", "")).lower() in SELECTABLE | {"running", "done"}, "CURRENT_QUEUE_STATUS_INVALID", errors)
    require(git_blob_sha(template_path) == manifest["expected_priority2_template_blob_sha"], "PRIORITY2_TEMPLATE_BLOB_MISMATCH", errors)

    require(isinstance(started, dict), "RUNNER_STARTED_NOT_STRICT_OBJECT", errors)
    runner_started_at = parse_time(started.get("started_at")) if isinstance(started, dict) else None
    if isinstance(started, dict):
        require(started.get("task_id") == manifest["canonical_task_id"], "RUNNER_STARTED_TASK_ID_MISMATCH", errors)
        require(started.get("page_key") == manifest["page_key"], "RUNNER_STARTED_PAGE_KEY_MISMATCH", errors)
        require(started.get("queue_started") is True, "RUNNER_STARTED_QUEUE_FLAG_FALSE", errors)
    require(runner_started_at is not None, "RUNNER_STARTED_TIME_INVALID", errors)

    require(isinstance(preflight, dict), "PREFLIGHT_NOT_STRICT_OBJECT", errors)
    preflight_start = parse_time(preflight.get("started_at")) if isinstance(preflight, dict) else None
    preflight_end = parse_time(preflight.get("completed_at")) if isinstance(preflight, dict) else None
    if isinstance(preflight, dict):
        require(preflight.get("slot_id") == SLOT_ID, "PREFLIGHT_SLOT_MISMATCH", errors)
        require(preflight.get("task_id") == manifest["canonical_task_id"], "PREFLIGHT_TASK_ID_MISMATCH", errors)
        require(preflight.get("accepted") is True, "PREFLIGHT_NOT_ACCEPTED", errors)
        require(preflight.get("network_access_attempted") is False, "PREFLIGHT_NETWORK_FLAG_NOT_FALSE", errors)
    require(preflight_start is not None and preflight_end is not None and preflight_end >= preflight_start, "PREFLIGHT_TIME_RANGE_INVALID", errors)

    require(isinstance(outer, dict), "OUTER_WATCHDOG_NOT_STRICT_OBJECT", errors)
    outer_start = parse_time(outer.get("started_at")) if isinstance(outer, dict) else None
    outer_end = parse_time(outer.get("completed_at")) if isinstance(outer, dict) else None
    if isinstance(outer, dict):
        require(outer.get("slot_id") == SLOT_ID, "OUTER_WATCHDOG_SLOT_MISMATCH", errors)
        require(outer.get("task_id") == manifest["expected_outer_task_id"], "OUTER_WATCHDOG_TASK_ID_MISMATCH", errors)
        require(outer.get("state") == "OUTER_WATCHDOG_PASS_NONFINAL", "OUTER_WATCHDOG_NOT_PASS", errors)
        require(outer.get("timeout_count") == 0, "OUTER_WATCHDOG_TIMEOUT_PRESENT", errors)
        require(outer.get("preflight_output_exists") is True, "OUTER_PREFLIGHT_FLAG_FALSE", errors)
        require(outer.get("child_watchdog_output_exists") is True, "OUTER_CHILD_WATCHDOG_FLAG_FALSE", errors)
        require(outer.get("child_chain_output_exists") is True, "OUTER_CHILD_CHAIN_FLAG_FALSE", errors)
    require(outer_start is not None and outer_end is not None and outer_end >= outer_start, "OUTER_WATCHDOG_TIME_RANGE_INVALID", errors)

    if runner_started_at and outer_start:
        require(outer_start >= runner_started_at - skew, "OUTER_WATCHDOG_PREDATES_RUNNER_START", errors)
    if outer_start and outer_end and preflight_start and preflight_end:
        require(in_window(preflight_start, outer_start, outer_end, skew), "PREFLIGHT_START_OUTSIDE_OUTER_WINDOW", errors)
        require(in_window(preflight_end, outer_start, outer_end, skew), "PREFLIGHT_END_OUTSIDE_OUTER_WINDOW", errors)

    generation_times: dict[str, datetime | None] = {
        "canonical": parse_time(canonical.get("generated_at")) if isinstance(canonical, dict) else None,
        "reconciliation": parse_time(reconciliation.get("generated_at")) if isinstance(reconciliation, dict) else None,
        "website_canonical": parse_time(website.get("generated_at")) if isinstance(website, dict) else None,
        "probe": parse_time(probe.get("generated_at")) if isinstance(probe, dict) else None,
        "watchdog_started": parse_time(watchdog.get("started_at")) if isinstance(watchdog, dict) else None,
        "watchdog_completed": parse_time(watchdog.get("completed_at")) if isinstance(watchdog, dict) else None,
        "chain_started": parse_time(chain.get("started_at")) if isinstance(chain, dict) else None,
        "chain_completed": parse_time(chain.get("completed_at")) if isinstance(chain, dict) else None,
    }
    for name, value in generation_times.items():
        require(value is not None, f"{name.upper()}_GENERATION_TIME_INVALID", errors)
        if outer_start and outer_end:
            require(in_window(value, outer_start, outer_end, skew), f"{name.upper()}_OUTSIDE_CURRENT_OUTER_WINDOW", errors)

    if isinstance(canonical, dict):
        require(canonical.get("attempt_id") == manifest["expected_attempt_id"], "CANONICAL_ATTEMPT_ID_MISMATCH", errors)
    if isinstance(reconciliation, dict):
        require(reconciliation.get("attempt_id") == manifest["expected_attempt_id"], "RECONCILIATION_ATTEMPT_ID_MISMATCH", errors)
    if isinstance(website, dict):
        require(website.get("attempt_id") == manifest["expected_attempt_id"], "WEBSITE_CANONICAL_ATTEMPT_ID_MISMATCH", errors)

    ctime = generation_times["canonical"]
    require(ctime == generation_times["reconciliation"] == generation_times["website_canonical"], "CANONICAL_GENERATED_AT_COPIES_MISMATCH", errors)
    if generation_times["watchdog_started"] and generation_times["watchdog_completed"]:
        require(generation_times["watchdog_completed"] >= generation_times["watchdog_started"], "WATCHDOG_GENERATION_RANGE_INVALID", errors)
    if generation_times["chain_started"] and generation_times["chain_completed"]:
        require(generation_times["chain_completed"] >= generation_times["chain_started"], "CHAIN_GENERATION_RANGE_INVALID", errors)

    return {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "validated_at": utc_now(),
        "valid": not errors,
        "base_checkpoint_valid": base_report.get("valid") is True,
        "generation_bound_valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "current_queue_path": manifest["canonical_queue_path"],
        "priority2_template_path": manifest["priority2_template_path"],
        "current_queue_blob_sha": git_blob_sha(task_path),
        "priority2_template_blob_sha": git_blob_sha(template_path),
        "runner_started_at": started.get("started_at") if isinstance(started, dict) else None,
        "outer_started_at": outer.get("started_at") if isinstance(outer, dict) else None,
        "outer_completed_at": outer.get("completed_at") if isinstance(outer, dict) else None,
        "generation_times": {k: (v.isoformat().replace("+00:00", "Z") if v else None) for k, v in generation_times.items()},
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
        "output_semantics": "STRICT_EXACT_BLOB_CHECKPOINT_PLUS_CURRENT_RUN_GENERATION_BINDING_NONFINAL",
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--base-validator", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    base_validator = Path(args.base_validator).resolve()
    manifest = strict_load(manifest_path)
    if manifest.get("slot_id") != SLOT_ID:
        raise SystemExit("MANIFEST_SLOT_MISMATCH")

    base_output = Path(args.output).resolve().with_suffix(".base.json")
    base_report = run_base_validator(repo, manifest_path, base_validator, base_output)
    try:
        base_output.unlink(missing_ok=True)
    except Exception:
        pass

    paths = dict(manifest["required_checkpoint_paths"])
    docs = {name: load_or_none(repo / rel) for name, rel in paths.items()}
    docs["queue"] = load_or_none(repo / manifest["canonical_queue_path"])
    docs["template"] = load_or_none(repo / manifest["priority2_template_path"])
    docs["runner_started"] = load_or_none(repo / manifest["runner_started_path"])
    docs["preflight"] = load_or_none(repo / manifest["preflight_output_path"])
    docs["outer_watchdog"] = load_or_none(repo / manifest["outer_watchdog_output_path"])

    report = validate_generation(repo, manifest, docs, base_report)
    atomic_json(Path(args.output), report)
    print(f"HD3_GENERATION_CHECKPOINT_VALID={str(report['valid']).lower()}")
    print(f"HD3_GENERATION_CHECKPOINT_ERRORS={report['error_count']}")
    print("FINAL_READY=false")
    return 0 if report["valid"] else 4

if __name__ == "__main__":
    raise SystemExit(main())
