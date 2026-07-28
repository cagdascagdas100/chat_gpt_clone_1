# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
TASK_ID = "internet-access-2-ofcom-dynamic-zip-join-existing-11013-v2-20260722T041000Z"
BRANCH = "codex/aays-single-runner-v5-20260706"
QUEUE_REL = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/queue/internet_access_2_ofcom_dynamic_zip_join_existing_11013_006.v3.task.json")
CURRENT_REL = Path("docs/chatgpt_status/_shared/slots_21/internet_access_2/current_task_latest.json")
HEARTBEAT_REL = Path("docs/chatgpt_status/_shared/slots_21/internet_access_2/heartbeat_latest.json")
CLAIM_REL = Path("docs/chatgpt_status/_shared/control/single_runner_active_claim.json")
RECOVERY_REL = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/recovery/011_006_strict_zip_requeue_latest.json")
EXPECTED_FILES = 121
EXPECTED_ROWS = 1_741_096
R2 = re.compile(r"(?:^|/)202601_fixed_postcode_coverage_r2_([A-Z0-9]+)\.csv$", re.I)
R1 = re.compile(r"(?:^|/)202601_fixed_postcode_coverage_r1_([A-Z0-9]+)\.csv$", re.I)
ALIASES = {
    "postcode": ["postcode", "postcode_space"],
    "postcode_area": ["postcode area", "postcode_area"],
    "sfbb": ["SFBB availability (% premises)", "SFBB availability"],
    "ufbb100": ["UFBB (100Mbit/s) availability (% premises)", "UFBB100 availability (% premises)"],
    "ufbb300": ["UFBB availability (% premises)", "UFBB (300Mbit/s) availability (% premises)"],
    "gigabit": ["Gigabit availability (% premises)", "Gigabit availability"],
    "unable30": ["% of premises unable to receive 30Mbit/s", "unable to receive 30Mbit/s"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalise(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def match_header(fields: list[str], aliases: list[str]) -> str | None:
    lookup = {normalise(value): value for value in fields}
    return next((lookup[normalise(alias)] for alias in aliases if normalise(alias) in lookup), None)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"JSON_READ_FAILED:{path}:{type(exc).__name__}:{exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{uuid.uuid4().hex}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def lease_active(value: dict[str, Any]) -> bool:
    state = str(value.get("state") or value.get("status") or "").upper()
    if state in {"DONE", "PUBLISHED", "BLOCKED", "STOPPED", "STOPPED_CLEAN", "FAILED", "CANCELLED"}:
        return False
    lease = parse_time(value.get("lease_expires_at"))
    return bool(lease and lease > datetime.now(timezone.utc))


def inspect_archive(path: Path, expected_files: int, expected_rows: int) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"ARCHIVE_NOT_FOUND:{path}")
    if not zipfile.is_zipfile(path):
        raise RuntimeError("ARCHIVE_NOT_ZIP")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP_CRC_FAILURE:{bad}")
        names = [name.replace("\\", "/") for name in archive.namelist()]
        r2_members = sorted(name for name in names if R2.search(name))
        stale_r1 = sorted(name for name in names if R1.search(name))
        areas: list[str] = []
        total_rows = 0
        missing_columns: list[dict[str, Any]] = []
        empty_files: list[str] = []
        for member in r2_members:
            match = R2.search(member)
            area = match.group(1).upper() if match else ""
            areas.append(area)
            with archive.open(member) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="strict", newline=""))
                fields = list(reader.fieldnames or [])
                matched = {key: match_header(fields, aliases) for key, aliases in ALIASES.items()}
                missing = [key for key, value in matched.items() if not value]
                rows = sum(1 for _ in reader)
            total_rows += rows
            if rows == 0:
                empty_files.append(member)
            if missing:
                missing_columns.append({"file": member, "missing": missing})
        checks = {
            "zip_crc_ok": True,
            "r2_file_count_ok": len(r2_members) == expected_files,
            "unique_postcode_areas_ok": len(set(areas)) == expected_files,
            "total_rows_ok": total_rows == expected_rows,
            "stale_r1_absent": not stale_r1,
            "all_files_nonempty": not empty_files,
            "core_columns_complete": not missing_columns,
        }
        checks["all"] = all(checks.values())
        return {
            "archive_sha256": sha256_file(path),
            "archive_bytes": path.stat().st_size,
            "observed_r2_files": len(r2_members),
            "observed_unique_areas": len(set(areas)),
            "observed_rows": total_rows,
            "observed_stale_r1_files": len(stale_r1),
            "empty_files": empty_files,
            "missing_columns": missing_columns,
            "checks": checks,
        }


def git_process(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    completed = git_process(repo, *args)
    if completed.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{completed.stderr.strip() or completed.stdout.strip()}")
    return completed


def git_error(completed: subprocess.CompletedProcess[str]) -> str:
    return completed.stderr.strip() or completed.stdout.strip() or f"exit={completed.returncode}"


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    completed = git_process(repo, "merge-base", "--is-ancestor", ancestor, descendant)
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    raise RuntimeError(f"ANCESTRY_CHECK_FAILED:{ancestor}:{descendant}:{git_error(completed)}")


def remote_head(repo: Path) -> str:
    values = git(repo, "ls-remote", "origin", f"refs/heads/{BRANCH}").stdout.split()
    if not values:
        raise RuntimeError("REMOTE_HEAD_NOT_FOUND")
    return values[0]


def assert_clean_repo(repo: Path, stage: str) -> None:
    status = git(repo, "status", "--porcelain", "--untracked-files=no").stdout.strip()
    if status:
        raise RuntimeError(f"REPO_NOT_CLEAN_{stage}:{status.replace(chr(10), ' | ')}")


def assert_commit_scope(repo: Path, commit: str, allowed: set[str]) -> None:
    paths = set(git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines())
    if paths != allowed:
        raise RuntimeError(f"REQUEUE_COMMIT_SCOPE_MISMATCH:{sorted(paths)}")


def publish_with_bounded_recovery(repo: Path, commit: str, allowed: set[str]) -> dict[str, Any]:
    assert_commit_scope(repo, commit, allowed)
    first_push = git_process(repo, "push", "origin", f"HEAD:{BRANCH}")
    git(repo, "fetch", "origin", BRANCH)

    if is_ancestor(repo, commit, f"origin/{BRANCH}"):
        return {
            "published_commit": commit,
            "remote_head": remote_head(repo),
            "publish_recovery_used": first_push.returncode != 0,
            "rebase_used": False,
            "bounded_push_retry_count": 0,
            "first_push_error": None if first_push.returncode == 0 else git_error(first_push),
        }

    first_error = git_error(first_push)
    if first_push.returncode == 0:
        first_error = "PUSH_RETURNED_SUCCESS_BUT_COMMIT_NOT_CONTAINED_IN_REMOTE"

    assert_clean_repo(repo, "BEFORE_BOUNDED_REQUEUE_REBASE")
    rebase = git_process(repo, "rebase", f"origin/{BRANCH}")
    if rebase.returncode != 0:
        rebase_error = git_error(rebase)
        git_process(repo, "rebase", "--abort")
        raise RuntimeError(f"BOUNDED_REQUEUE_REBASE_FAILED:{rebase_error}")

    rebased_commit = git(repo, "rev-parse", "HEAD").stdout.strip()
    assert_clean_repo(repo, "AFTER_BOUNDED_REQUEUE_REBASE")
    assert_commit_scope(repo, rebased_commit, allowed)

    retry = git_process(repo, "push", "origin", f"HEAD:{BRANCH}")
    if retry.returncode != 0:
        raise RuntimeError(f"BOUNDED_REQUEUE_PUSH_RETRY_FAILED:{git_error(retry)}")

    git(repo, "fetch", "origin", BRANCH)
    if not is_ancestor(repo, rebased_commit, f"origin/{BRANCH}"):
        raise RuntimeError(
            f"REQUEUE_COMMIT_NOT_CONTAINED_IN_REMOTE_AFTER_RECOVERY:"
            f"commit={rebased_commit} remote={remote_head(repo)}"
        )

    return {
        "published_commit": rebased_commit,
        "remote_head": remote_head(repo),
        "publish_recovery_used": True,
        "rebase_used": True,
        "bounded_push_retry_count": 1,
        "first_push_error": first_error,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Requeue the existing 006 task only after strict official Ofcom ZIP validation")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--expected-files", type=int, default=EXPECTED_FILES, help=argparse.SUPPRESS)
    parser.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS, help=argparse.SUPPRESS)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    archive = Path(args.archive).expanduser().resolve()
    queue_path = repo / QUEUE_REL
    current_path = repo / CURRENT_REL
    heartbeat_path = repo / HEARTBEAT_REL
    claim_path = repo / CLAIM_REL
    recovery_path = repo / RECOVERY_REL

    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")

    queue = read_json(queue_path)
    current = read_json(current_path)
    heartbeat = read_json(heartbeat_path)
    claim = read_json(claim_path)
    if queue.get("task_id") != TASK_ID or current.get("task_id") != TASK_ID:
        raise RuntimeError("TASK_ID_MISMATCH")
    if queue.get("status") not in {"result_ready_for_remote_acceptance", "blocked"}:
        raise RuntimeError(f"QUEUE_NOT_TERMINAL_FOR_RECOVERY:{queue.get('status')}")
    if str(current.get("state")) != "PUBLISHED":
        raise RuntimeError(f"CURRENT_TASK_NOT_RECONCILED_PUBLISHED:{current.get('state')}")
    if lease_active(heartbeat):
        raise RuntimeError("SLOT_HEARTBEAT_LEASE_ACTIVE")
    if lease_active(claim):
        raise RuntimeError("GLOBAL_CLAIM_LEASE_ACTIVE")

    inspection = inspect_archive(archive, args.expected_files, args.expected_rows)
    if not inspection["checks"]["all"]:
        raise RuntimeError("STRICT_ARCHIVE_PREFLIGHT_FAILED:" + json.dumps(inspection["checks"], sort_keys=True))

    if args.publish:
        assert_clean_repo(repo, "BEFORE_REQUEUE")

    prior = {
        "status": queue.get("status"),
        "runner_state": queue.get("runner_state"),
        "runner_child_commit": queue.get("runner_child_commit"),
        "runner_published_at": queue.get("runner_published_at"),
        "attempt_id": queue.get("attempt_id"),
    }
    retry_attempt = uuid.uuid4().hex
    queue.update({
        "status": "queued",
        "attempt_id": retry_attempt,
        "recovery_triggered": True,
        "recovery_retry_count": int(queue.get("recovery_retry_count") or 0) + 1,
        "recovery_reason": "OFFICIAL_OFCom_R2_ZIP_STRICT_PREFLIGHT_PASS",
        "requeued_at": now(),
        "runner_state": "REQUEUED_AFTER_STRICT_OFFICIAL_ZIP_PREFLIGHT",
        "strict_archive_preflight": inspection,
        "prior_publish": prior,
        "final_ready": False,
    })
    recovery = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "state": "EXISTING_006_REQUEUED_AFTER_STRICT_OFFICIAL_ZIP_PREFLIGHT",
        "requeued_at": queue["requeued_at"],
        "new_attempt_id": retry_attempt,
        "archive_preflight": inspection,
        "publish_guard": {
            "mode": "BOUNDED_REBASE_AND_SINGLE_PUSH_RETRY",
            "commit_scope_exact": True,
            "max_push_retries": 1,
            "force_push_used": False,
            "reset_used": False,
        },
        "duplicate_task_created": False,
        "second_runner_started": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    write_json(queue_path, queue)
    write_json(recovery_path, recovery)

    commit = None
    publish_result: dict[str, Any] | None = None
    if args.publish:
        queue_rel = str(QUEUE_REL).replace("\\", "/")
        recovery_rel = str(RECOVERY_REL).replace("\\", "/")
        allowed = {queue_rel, recovery_rel}
        git(repo, "add", "-A", "--", queue_rel, recovery_rel)
        staged = set(git(repo, "diff", "--cached", "--name-only").stdout.splitlines())
        if staged != allowed:
            raise RuntimeError(f"UNEXPECTED_STAGED_PATHS:{sorted(staged)}")
        git(repo, "commit", "-m", "internet_access_2: requeue existing 006 after strict Ofcom ZIP preflight")
        commit = git(repo, "rev-parse", "HEAD").stdout.strip()
        publish_result = publish_with_bounded_recovery(repo, commit, allowed)
        commit = str(publish_result["published_commit"])

    print(json.dumps({
        "state": recovery["state"],
        "task_id": TASK_ID,
        "new_attempt_id": retry_attempt,
        "archive_sha256": inspection["archive_sha256"],
        "observed_r2_files": inspection["observed_r2_files"],
        "observed_unique_areas": inspection["observed_unique_areas"],
        "observed_rows": inspection["observed_rows"],
        "published_commit": commit,
        "remote_head": None if publish_result is None else publish_result["remote_head"],
        "publish_recovery_used": False if publish_result is None else publish_result["publish_recovery_used"],
        "rebase_used": False if publish_result is None else publish_result["rebase_used"],
        "bounded_push_retry_count": 0 if publish_result is None else publish_result["bounded_push_retry_count"],
        "first_push_error": None if publish_result is None else publish_result["first_push_error"],
        "force_push_used": False,
        "reset_used": False,
        "duplicate_task_created": False,
        "second_runner_started": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
