# -*- coding: utf-8 -*-
"""Continuation-triggered, bounded recovery gate for all 21 AAYS slots."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable


WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
ACTIVE_STATES = {"CLAIMED", "RUNNING", "PUBLISHING", "RESULT_READY_FOR_SERIAL_PUBLISH"}
BLOCKED_STATES = {"BLOCKED", "BLOCKED_NO_DECLARED_OUTPUT", "STALE"}
SAFE_TIMEOUT_MARKERS = (
    "CHILD_REMOTE_CHECKOUT_TIMEOUT",
    "CHILD_REMOTE_FETCH_TIMEOUT",
    "SPARSE_EXPANSION_TIMEOUT",
    "SPARSE_LIST_TIMEOUT",
    "TIMED OUT AFTER",
)
LOCK_MARKERS = ("INDEX.LOCK", "SPARSE-CHECKOUT.LOCK", "SHALLOW.LOCK", "ANOTHER GIT PROCESS")
DATA_BLOCKER_MARKERS = (
    "OUTPUT_NOT_PRESENT",
    "SOURCE_NOT_FOUND",
    "SOURCE_READ_FAILED",
    "CANONICAL_SHARD",
    "NOT_FOUND_IN_REMOTE_REPOSITORY",
    "FEATURE_COUNT_ZERO",
    "EXPORT_NOT_STARTED",
    "NOT_PARCEL_MATCHED",
    "INFERENCE_NOT_EXECUTED",
    "DATABASE_HEALTH_DEGRADED",
    "NO_NATIONAL_ENGLAND_CANONICAL_PARCEL_INVENTORY",
    "NO_DATA",
    "NOT_DOWNLOADED",
    "PAYLOAD_NOT_CAPTURED",
    "SOURCE_LOADER_EVIDENCE_NOT_EXECUTED",
    "CANONICAL_PARCEL_QUERIES_NOT_EXECUTED",
    "ROW_FACTOR_MATRIX_NOT_BUILT",
)
SOURCE_DISCOVERY_POLICY = "LOCAL_FILES_THEN_FREE_PUBLIC_NO_AUTH"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    temporary = path.with_name(f"{path.name}.tmp.{uuid.uuid4().hex}")
    temporary.write_bytes(data)
    last_error: OSError | None = None
    for attempt in range(20):
        try:
            os.replace(temporary, path)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(min(0.05 * (attempt + 1), 0.25))
    temporary.unlink(missing_ok=True)
    raise last_error or PermissionError(path)


class SlotRecoverySupervisor:
    """Plans once per continuation attempt and applies only bounded repairs."""

    def __init__(
        self,
        root: Path,
        repo: Path,
        worktree_for_slot: Callable[[str], Path],
        git_executable: Path | None,
        slot_ids: set[str],
        progress_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.repo = repo.resolve()
        self.worktree_for_slot = worktree_for_slot
        self.git_executable = git_executable
        self.slot_ids = set(slot_ids)
        self.progress_callback = progress_callback
        self.wait_seconds = max(15, int(os.environ.get("AAYS_RECOVERY_WAIT_SECONDS", "120")))
        self.proactive_after_seconds = max(
            60, int(os.environ.get("AAYS_RECOVERY_PROACTIVE_AFTER_SECONDS", "300"))
        )
        self.state_root = self.root / "state" / "recovery"
        self.slot_root = self.state_root / "slots"
        self.problem_solver_request_root = self.state_root / "problem_solver_requests"
        self.summary_path = self.state_root / "summary_latest.json"
        self._summary_lock = None

    def _git(self, worktree: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        if self.git_executable is None:
            raise RuntimeError("RECOVERY_GIT_NOT_AVAILABLE")
        command = [str(self.git_executable), "-C", str(worktree), *args]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
            try:
                stdout, stderr = process.communicate(timeout=min(5.0, remaining))
                return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
            except subprocess.TimeoutExpired:
                if self.progress_callback is not None:
                    self.progress_callback("RECOVERY_GIT_ACTIVE")

    @staticmethod
    def _git_dir(worktree: Path) -> Path:
        marker = worktree / ".git"
        if marker.is_dir():
            return marker
        if marker.is_file():
            first = marker.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
            if first.casefold().startswith("gitdir:"):
                value = Path(first.split(":", 1)[1].strip())
                return value if value.is_absolute() else (worktree / value).resolve()
        raise RuntimeError("RECOVERY_WORKTREE_GIT_DIR_NOT_RESOLVED")

    @staticmethod
    def _trigger_key(task: dict[str, Any]) -> str:
        identity = "|".join(
            str(task.get(name) or "")
            for name in ("slot_id", "task_id", "attempt_id", "idempotency_key")
        )
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]

    def _slot_documents(self, slot_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        directory = self.root / "state" / "slots" / slot_id
        status = read_json(directory / "status_latest.json", {}) or {}
        heartbeat = read_json(directory / "heartbeat_latest.json", {}) or {}
        remote_status = read_json(
            self.repo / "docs" / "chatgpt_status" / "_shared" / "slots_21"
            / slot_id / "status_latest.json",
            {},
        ) or {}
        remote_parts: list[str] = []
        remote_blocker = str(remote_status.get("blocker") or "").strip()
        if remote_blocker:
            remote_parts.append(remote_blocker)
        remote_blockers = remote_status.get("blockers")
        if isinstance(remote_blockers, list):
            remote_parts.extend(str(value).strip() for value in remote_blockers if str(value).strip())
        if remote_parts:
            merged = dict(status)
            local_blocker = self._blocker_text(status)
            merged["blocker"] = " | ".join(dict.fromkeys(
                [value for value in (local_blocker, *remote_parts) if value]
            ))
            status = merged
        return status, heartbeat

    @staticmethod
    def _blocker_text(status: dict[str, Any]) -> str:
        values = [status.get("blocker")]
        result = status.get("result")
        if isinstance(result, dict):
            values.extend((result.get("blocker"), result.get("error")))
            # `state=BLOCKED` is a lifecycle label, not a diagnostic.  Treating
            # it as the blocker made an otherwise reason-free blocked slot look
            # unsafe and prevented the bounded recovery plan from ever opening.
            result_state = str(result.get("state") or "").strip()
            if result_state and result_state.upper() not in BLOCKED_STATES:
                values.append(result_state)
        return " | ".join(str(value) for value in values if value).strip()

    @staticmethod
    def _heartbeat_age(heartbeat: dict[str, Any]) -> float | None:
        stamp = parse_time(heartbeat.get("heartbeat_at") or heartbeat.get("updated_at"))
        if stamp is None:
            return None
        return max(0.0, (datetime.now(timezone.utc) - stamp).total_seconds())

    def _current_coordinator_healthy(self) -> bool:
        heartbeat = read_json(self.root / "state" / "coordinator_heartbeat_latest.json", {}) or {}
        age = self._heartbeat_age(heartbeat)
        if age is None or age > 45:
            return False
        return str(heartbeat.get("state") or "").upper() in {
            "RUNNING", "RECOVERY_GIT_ACTIVE", "STARTING_REMOTE_SYNC", "INITIALIZING_STATE",
        }

    def _health(self, slot_id: str) -> dict[str, Any]:
        status, heartbeat = self._slot_documents(slot_id)
        state = str(status.get("state") or "IDLE").upper()
        heartbeat_age = self._heartbeat_age(heartbeat)
        stale_after = int(heartbeat.get("stale_after_seconds") or 3600)
        stale_active = state in ACTIVE_STATES and (
            heartbeat_age is None or heartbeat_age > stale_after
        )
        return {
            "slot_id": slot_id,
            "state": state,
            "task_id": status.get("task_id"),
            "attempt_id": status.get("attempt_id"),
            "status_updated_at": status.get("updated_at"),
            "blocker": self._blocker_text(status),
            "heartbeat_age_seconds": None if heartbeat_age is None else round(heartbeat_age, 1),
            "stale_after_seconds": stale_after,
            "stale_active": stale_active,
            "needs_recovery": state in BLOCKED_STATES or stale_active,
        }

    def _diagnostics(self, worktree: Path) -> dict[str, Any]:
        diagnostics: dict[str, Any] = {
            "worktree": str(worktree),
            "exists": worktree.is_dir(),
            "head": None,
            "clean": False,
            "status_error": None,
            "locks": [],
        }
        if not worktree.is_dir():
            return diagnostics
        try:
            head = self._git(worktree, "rev-parse", "HEAD")
            if head.returncode == 0:
                diagnostics["head"] = head.stdout.strip() or None
            status = self._git(worktree, "status", "--porcelain", "--untracked-files=no", timeout=60)
            diagnostics["clean"] = status.returncode == 0 and not status.stdout.strip()
            if status.returncode != 0:
                diagnostics["status_error"] = status.stderr.strip()
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            diagnostics["status_error"] = f"{type(exc).__name__}:{exc}"
        try:
            lock_roots = (
                ("slot", self._git_dir(worktree), 30),
                ("publisher", self._git_dir(self.repo), 300),
            )
            seen: set[str] = set()
            for scope, git_dir, minimum_age_seconds in lock_roots:
                for relative in ("index.lock", "info/sparse-checkout.lock", "shallow.lock"):
                    path = git_dir / Path(relative)
                    key = str(path).casefold()
                    if key in seen or not path.is_file():
                        continue
                    seen.add(key)
                    stat = path.stat()
                    diagnostics["locks"].append({
                        "path": str(path),
                        "scope": scope,
                        "size": stat.st_size,
                        "age_seconds": round(max(0.0, time.time() - stat.st_mtime), 1),
                        "minimum_age_seconds": minimum_age_seconds,
                    })
        except (OSError, RuntimeError):
            pass
        return diagnostics

    @staticmethod
    def _plan_steps(blocker: str, diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
        upper = blocker.upper()
        steps: list[dict[str, Any]] = [
            {"order": 1, "action": "VERIFY_NO_LIVE_SLOT_LEASE", "safe": True},
            {"order": 2, "action": "CAPTURE_WORKTREE_HEAD_CLEANLINESS_AND_LOCKS", "safe": True},
        ]
        if any(marker in upper for marker in LOCK_MARKERS) or diagnostics.get("locks"):
            steps.append({"order": 3, "action": "REMOVE_ONLY_EMPTY_AGED_ORPHAN_GIT_LOCKS", "safe": True})
        if any(marker in upper for marker in SAFE_TIMEOUT_MARKERS):
            steps.append({"order": 4, "action": "RETRY_ON_VERIFIED_CLEAN_LOCAL_HEAD_ONCE", "safe": True})
        if any(marker in upper for marker in DATA_BLOCKER_MARKERS):
            steps.append({
                "order": 5,
                "action": "DISCOVER_LOCAL_THEN_FREE_PUBLIC_NO_AUTH_SOURCE_OR_WRITE_EVIDENCE_BACKED_NO_DATA",
                "safe": True,
            })
        steps.append({"order": 6, "action": "RESUME_ORIGINAL_CONTINUATION_TASK", "safe": True})
        return steps

    def _write_summary(self, latest: dict[str, Any]) -> None:
        slot_states: dict[str, Any] = {}
        if self.slot_root.is_dir():
            for slot_dir in sorted(self.slot_root.iterdir()):
                if not slot_dir.is_dir():
                    continue
                current = read_json(slot_dir / "latest.json", {}) or {}
                if current:
                    slot_states[slot_dir.name] = {
                        "state": current.get("state"),
                        "trigger_task_id": current.get("trigger_task_id"),
                        "updated_at": current.get("updated_at"),
                        "blocker": current.get("blocker"),
                    }
        atomic_json(self.summary_path, {
            "schema_version": 1,
            "workstream_id": WORKSTREAM_ID,
            "logical_slot_count": len(self.slot_ids),
            "policy": "CONTINUATION_OR_STALE_TRIGGERED_PLAN_WAIT_SAFE_REPAIR_RESUME",
            "wait_seconds": self.wait_seconds,
            "proactive_after_seconds": self.proactive_after_seconds,
            "latest_decision": latest,
            "slot_states": slot_states,
            "updated_at": utc_now(),
            "final_ready": False,
        })

    def _record(self, slot_id: str, trigger_key: str, payload: dict[str, Any]) -> None:
        directory = self.slot_root / slot_id
        payload["updated_at"] = utc_now()
        atomic_json(directory / f"{trigger_key}.json", payload)
        atomic_json(directory / "latest.json", payload)
        self._write_summary({
            "slot_id": slot_id,
            "state": payload.get("state"),
            "trigger_task_id": payload.get("trigger_task_id"),
            "updated_at": payload.get("updated_at"),
        })

    def _remove_orphan_locks(self, diagnostics: dict[str, Any]) -> tuple[list[str], list[str]]:
        removed: list[str] = []
        retained: list[str] = []
        for item in diagnostics.get("locks") or []:
            path = Path(str(item.get("path") or ""))
            size = int(item.get("size") or 0)
            age = float(item.get("age_seconds") or 0.0)
            minimum_age = float(item.get("minimum_age_seconds") or 30.0)
            if path.is_file() and size == 0 and age >= minimum_age:
                try:
                    path.unlink()
                    removed.append(str(path))
                except OSError:
                    retained.append(str(path))
            else:
                retained.append(str(path))
        return removed, retained

    def _materialize_read_paths(self, worktree: Path, task: dict[str, Any]) -> str | None:
        """Checkout exact declared inputs without expanding broad parent directories."""
        exact_read_paths: list[str] = []
        values = task.get("read_paths")
        if isinstance(values, list):
            exact_read_paths.extend(str(value) for value in values if value)
        if task.get("script_path"):
            exact_read_paths.append(str(task["script_path"]))
        exact_read_paths = sorted({
            value.replace("\\", "/").strip("/")
            for value in exact_read_paths
            if value and ":" not in value and ".." not in PurePosixPath(value).parts
        })
        for offset in range(0, len(exact_read_paths), 50):
            batch = exact_read_paths[offset:offset + 50]
            try:
                materialize = self._git(
                    worktree, "checkout", "--ignore-skip-worktree-bits",
                    "HEAD", "--", *batch, timeout=300,
                )
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                return f"READ_PATH_CHECKOUT_EXCEPTION:{type(exc).__name__}:{exc}"
            if materialize.returncode != 0:
                return f"READ_PATH_CHECKOUT_FAILED:{materialize.stderr.strip()}"
        return None

    def _provision_isolated_worktree(
        self,
        slot_id: str,
        trigger_key: str,
        task: dict[str, Any],
        current_worktree: Path,
    ) -> tuple[Path | None, str | None]:
        """Preserve a dirty worktree and route one retry to a clean local-HEAD worktree."""
        expected_head_result = self._git(self.repo, "rev-parse", "HEAD", timeout=30)
        expected_head = (
            expected_head_result.stdout.strip()
            if expected_head_result.returncode == 0 else None
        )
        # Keep new worktrees under a short F: path. This avoids MAX_PATH failures
        # while preserving every older long-path recovery directory as evidence.
        worktree_base = self.root / "wt"
        target: Path | None = None
        provisioned: Path | None = None
        for version in range(1, 100):
            candidate = worktree_base / slot_id / f"{trigger_key[:12]}-v{version}"
            if not candidate.is_dir():
                target = candidate
                break
            diagnostics = self._diagnostics(candidate)
            if (
                diagnostics.get("clean")
                and diagnostics.get("head")
                and (not expected_head or diagnostics.get("head") == expected_head)
            ):
                target = candidate
                provisioned = candidate
                break
        if target is None:
            return None, "ALL_VERSIONED_ISOLATED_WORKTREES_NOT_CLEAN"
        if provisioned is None:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                add = self._git(
                    self.repo,
                    "worktree", "add", "--no-checkout", "--detach", str(target), "HEAD",
                    timeout=180,
                )
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                return None, f"ISOLATED_WORKTREE_ADD_EXCEPTION:{type(exc).__name__}:{exc}"
            if add.returncode != 0:
                return None, f"ISOLATED_WORKTREE_ADD_FAILED:{add.stderr.strip()}"

            candidate_paths: list[str] = []
            # Derive isolation only from the task's authoritative contract.
            # Legacy required_sparse_paths can contain a whole top-level web
            # tree and would recreate the original portable-disk bottleneck.
            for name in ("read_paths", "exact_write_paths"):
                values = task.get(name)
                if isinstance(values, list):
                    candidate_paths.extend(str(value) for value in values if value)
            if task.get("script_path"):
                candidate_paths.append(str(task["script_path"]))
            sparse_directories: set[str] = set()
            for value in candidate_paths:
                normalized = value.replace("\\", "/").strip("/")
                if not normalized or "/" not in normalized:
                    continue
                repo_path = PurePosixPath(normalized)
                sparse_root = str(repo_path.parent) if repo_path.suffix else normalized
                if sparse_root not in ("", "."):
                    sparse_directories.add(sparse_root)
            # Some legacy contracts declare both a very broad directory and
            # the slot-specific descendant. Materialising the ancestor defeats
            # sparse checkout and can stall a portable disk for minutes. Keep
            # the narrow descendants when both are present.
            sparse_directories = {
                candidate
                for candidate in sparse_directories
                if not any(
                    other != candidate and other.startswith(candidate.rstrip("/") + "/")
                    for other in sparse_directories
                )
            }
            if sparse_directories:
                try:
                    sparse = self._git(
                        target, "sparse-checkout", "set", "--cone", *sorted(sparse_directories),
                        timeout=300,
                    )
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    return None, f"ISOLATED_SPARSE_EXCEPTION:{type(exc).__name__}:{exc}"
                if sparse.returncode != 0:
                    return None, f"ISOLATED_SPARSE_FAILED:{sparse.stderr.strip()}"
                try:
                    reset = self._git(target, "reset", "--mixed", "HEAD", timeout=180)
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    return None, f"ISOLATED_MIXED_RESET_EXCEPTION:{type(exc).__name__}:{exc}"
                if reset.returncode != 0:
                    return None, f"ISOLATED_MIXED_RESET_FAILED:{reset.stderr.strip()}"
                try:
                    reapply = self._git(target, "sparse-checkout", "reapply", timeout=180)
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    return None, f"ISOLATED_TARGETED_CHECKOUT_EXCEPTION:{type(exc).__name__}:{exc}"
                if reapply.returncode != 0:
                    return None, f"ISOLATED_SPARSE_REAPPLY_FAILED:{reapply.stderr.strip()}"
                tracked_sparse_directories: list[str] = []
                for sparse_directory in sorted(sparse_directories):
                    try:
                        probe = self._git(
                            target, "cat-file", "-e", f"HEAD:{sparse_directory}", timeout=30,
                        )
                    except (OSError, RuntimeError, subprocess.TimeoutExpired):
                        continue
                    if probe.returncode == 0:
                        tracked_sparse_directories.append(sparse_directory)
                if tracked_sparse_directories:
                    try:
                        checkout = self._git(
                            target, "checkout", "HEAD", "--", *tracked_sparse_directories, timeout=300,
                        )
                    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                        return None, f"ISOLATED_TARGETED_CHECKOUT_EXCEPTION:{type(exc).__name__}:{exc}"
                    if checkout.returncode != 0:
                        return None, f"ISOLATED_TARGETED_CHECKOUT_FAILED:{checkout.stderr.strip()}"
                try:
                    deleted = self._git(
                        target, "diff", "--name-only", "--diff-filter=D", "-z", timeout=120,
                    )
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    return None, f"ISOLATED_DELETED_SCAN_EXCEPTION:{type(exc).__name__}:{exc}"
                if deleted.returncode != 0:
                    return None, f"ISOLATED_DELETED_SCAN_FAILED:{deleted.stderr.strip()}"
                deleted_paths = [value for value in deleted.stdout.split("\0") if value]
                for offset in range(0, len(deleted_paths), 100):
                    try:
                        restore = self._git(
                            target, "checkout", "HEAD", "--", *deleted_paths[offset:offset + 100],
                            timeout=300,
                        )
                    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                        return None, f"ISOLATED_ANCESTOR_RESTORE_EXCEPTION:{type(exc).__name__}:{exc}"
                    if restore.returncode != 0:
                        return None, f"ISOLATED_ANCESTOR_RESTORE_FAILED:{restore.stderr.strip()}"
            else:
                try:
                    checkout = self._git(target, "checkout", "--detach", "HEAD", timeout=300)
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    return None, f"ISOLATED_CHECKOUT_EXCEPTION:{type(exc).__name__}:{exc}"
                if checkout.returncode != 0:
                    return None, f"ISOLATED_CHECKOUT_FAILED:{checkout.stderr.strip()}"
            provisioned = target

        read_path_error = self._materialize_read_paths(provisioned, task)
        if read_path_error:
            return None, f"ISOLATED_{read_path_error}"

        diagnostics = self._diagnostics(provisioned)
        if not diagnostics.get("clean") or not diagnostics.get("head"):
            return None, "ISOLATED_WORKTREE_VERIFICATION_FAILED"
        try:
            relative = provisioned.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return None, "ISOLATED_WORKTREE_OUTSIDE_PORTABLE_ROOT"
        override_path = self.root / "state" / "worktree_overrides.json"
        overrides = read_json(override_path, {}) or {}
        if not isinstance(overrides, dict):
            overrides = {}
        overrides[slot_id] = relative
        atomic_json(override_path, overrides)
        return provisioned, None

    def gate(self, source: Path, task: dict[str, Any]) -> dict[str, Any]:
        slot_id = str(task.get("slot_id") or "")
        if slot_id not in self.slot_ids:
            return {"decision": "BLOCK", "reason": "RECOVERY_UNKNOWN_SLOT", "task": task}
        health = self._health(slot_id)
        if not health["needs_recovery"]:
            return {"decision": "ALLOW", "reason": "SLOT_HEALTHY_OR_IDLE", "task": task}

        trigger_key = self._trigger_key(task)
        plan_path = self.slot_root / slot_id / f"{trigger_key}.json"
        plan = read_json(plan_path, {}) or {}
        problem_solver_request = read_json(
            self.problem_solver_request_root / f"{slot_id}.json", {}
        ) or {}
        problem_solver_requested_at = parse_time(problem_solver_request.get("requested_at"))
        plan_updated_at = parse_time(plan.get("updated_at"))
        problem_solver_is_new = bool(
            problem_solver_requested_at
            and (plan_updated_at is None or problem_solver_requested_at > plan_updated_at)
        )
        status_updated = parse_time(health.get("status_updated_at"))
        now = datetime.now(timezone.utc)
        try:
            source_updated = datetime.fromtimestamp(source.stat().st_mtime, timezone.utc)
        except OSError:
            source_updated = None
        blocker_text = str(health.get("blocker") or "")
        blocker_upper = blocker_text.upper()
        status_age = (
            max(0.0, (now - status_updated).total_seconds()) if status_updated else None
        )
        continuation_is_new = bool(
            source_updated and (status_updated is None or source_updated > status_updated)
        ) or problem_solver_is_new
        current_host_healthy = self._current_coordinator_healthy()
        stale_host_claim = any(
            marker in blocker_upper
            for marker in (
                "HEARTBEAT_STALE", "CANONICAL F HOST", "CANONICAL F: HOST", "F_HOST",
                "EXTERNAL_CANONICAL_F", "EXISTING_SHARED_RUNNER", "SHARED_RUNNER_GLOBAL",
            )
        )
        local_host_recovered = current_host_healthy and stale_host_claim
        safe_transient = (
            not blocker_text
            or any(marker in blocker_upper for marker in SAFE_TIMEOUT_MARKERS)
            or any(marker in blocker_upper for marker in LOCK_MARKERS)
            or bool(health.get("stale_active"))
            or local_host_recovered
        )
        real_data_blocker = any(marker in blocker_upper for marker in DATA_BLOCKER_MARKERS)
        proactive_eligible = bool(
            status_age is not None
            and status_age >= self.proactive_after_seconds
            and (safe_transient or real_data_blocker)
        )
        if not plan and not continuation_is_new and not proactive_eligible:
            return {
                "decision": "BLOCK",
                "reason": "WAITING_FOR_NEW_CONTINUATION_OR_PROACTIVE_THRESHOLD",
                "task": task,
            }
        if plan and problem_solver_is_new:
            plan.update({
                "policy_version": max(10, int(plan.get("policy_version") or 1)),
                "state": "RECOVERY_WAITING",
                "wait_until": utc_now(),
                "automatic_retry_count": 0,
                "repair_reason": "PROBLEM_SOLVER_SLOT_REOPENED",
                "trigger_mode": "PROBLEM_SOLVER_SLOT",
                "problem_solver_request_id": problem_solver_request.get("request_id"),
                "problem_solver_requested_at": problem_solver_request.get("requested_at"),
                "reopened_at": utc_now(),
            })
            self._record(slot_id, trigger_key, plan)
        if plan.get("state") == "RECOVERY_SUCCEEDED":
            applied_at = parse_time(plan.get("applied_at"))
            if applied_at and status_updated and status_updated > applied_at:
                if plan.get("source_discovery_policy") == SOURCE_DISCOVERY_POLICY:
                    plan.update({
                        "state": "RECOVERY_NO_DATA_CONTINUE",
                        "repair_reason": "EVIDENCE_BACKED_NO_DATA_CONTINUE",
                        "no_data_continued_at": utc_now(),
                    })
                    self._record(slot_id, trigger_key, plan)
                    return {
                        "decision": "NO_DATA_CONTINUE",
                        "reason": "EVIDENCE_BACKED_NO_DATA_CONTINUE",
                        "task": task,
                    }
                if real_data_blocker:
                    plan.update({
                        "policy_version": 7,
                        "state": "RECOVERY_WAITING",
                        "blocker": health.get("blocker") or health.get("state"),
                        "plan_steps": self._plan_steps(str(health.get("blocker") or ""), {}),
                        "wait_until": utc_now(),
                        "automatic_retry_count": 0,
                        "repair_reason": "DATA_BLOCKER_DISCOVERED_AFTER_GENERIC_RETRY",
                        "source_discovery_policy": SOURCE_DISCOVERY_POLICY,
                        "source_discovery_reopened_at": utc_now(),
                    })
                    self._record(slot_id, trigger_key, plan)
                    return {
                        "decision": "WAIT",
                        "reason": "SOURCE_DISCOVERY_PLAN_REOPENED",
                        "task": task,
                    }
                plan.update({
                    "state": "RECOVERY_PARKED",
                    "repair_reason": "AUTOMATIC_RETRY_DID_NOT_CLEAR_BLOCKER",
                    "parked_at": utc_now(),
                })
                self._record(slot_id, trigger_key, plan)
                return {
                    "decision": "BLOCK",
                    "reason": "AUTOMATIC_RETRY_DID_NOT_CLEAR_BLOCKER",
                    "task": task,
                }
            return {
                "decision": "WAIT",
                "reason": "AUTOMATIC_RETRY_ALREADY_RELEASED_WAITING_FOR_RESULT",
                "task": task,
            }
        if plan.get("state") == "RECOVERY_NO_DATA_CONTINUE":
            return {
                "decision": "NO_DATA_CONTINUE",
                "reason": "EVIDENCE_BACKED_NO_DATA_CONTINUE",
                "task": task,
            }
        if plan.get("state") == "RECOVERY_PARKED":
            if (
                (
                    int(plan.get("policy_version") or 1) < 9
                    or continuation_is_new
                    or local_host_recovered
                )
                and (safe_transient or real_data_blocker)
            ):
                plan.update({
                    "policy_version": 9,
                    "state": "RECOVERY_WAITING",
                    "wait_until": utc_now(),
                    "repair_reason": "POLICY_V7_SOURCE_DISCOVERY_OR_GENERIC_RECOVERY_REOPENED",
                    "reopened_at": utc_now(),
                })
                self._record(slot_id, trigger_key, plan)
            else:
                return {"decision": "BLOCK", "reason": "NEW_CONTINUATION_REQUIRED_AFTER_PARK", "task": task}

        worktree = self.worktree_for_slot(slot_id)
        read_path_error = self._materialize_read_paths(worktree, task)
        diagnostics = self._diagnostics(worktree)
        if read_path_error:
            diagnostics["read_path_materialization_error"] = read_path_error
            diagnostics["clean"] = False
        if not plan:
            wait_until = now + timedelta(seconds=self.wait_seconds)
            plan = {
                "schema_version": 1,
                "policy_version": 7,
                "workstream_id": WORKSTREAM_ID,
                "slot_id": slot_id,
                "state": "RECOVERY_WAITING",
                "trigger_task_id": task.get("task_id"),
                "trigger_attempt_id": task.get("attempt_id"),
                "source_queue_path": str(source),
                "trigger_mode": (
                    "PROBLEM_SOLVER_SLOT"
                    if problem_solver_is_new
                    else ("CONTINUATION" if continuation_is_new else "PROACTIVE_STALE_BLOCK")
                ),
                "problem_solver_request_id": problem_solver_request.get("request_id"),
                "source_updated_at": source_updated.isoformat().replace("+00:00", "Z") if source_updated else None,
                "blocked_status_updated_at": health.get("status_updated_at"),
                "blocker": health.get("blocker") or health.get("state"),
                "health_before": health,
                "diagnostics_before": diagnostics,
                "plan_steps": self._plan_steps(str(health.get("blocker") or ""), diagnostics),
                "created_at": utc_now(),
                "wait_until": wait_until.isoformat().replace("+00:00", "Z"),
                "automatic_retry_limit": 1,
                "automatic_retry_count": 0,
                "destructive_actions_allowed": False,
                "fake_data_allowed": False,
                "final_ready": False,
            }
            self._record(slot_id, trigger_key, plan)
            return {"decision": "WAIT", "reason": "RECOVERY_PLAN_CREATED_WAITING", "task": task}

        wait_until = parse_time(plan.get("wait_until")) or now
        if now < wait_until:
            return {"decision": "WAIT", "reason": "RECOVERY_WAIT_THRESHOLD_NOT_REACHED", "task": task}

        blocker = str(plan.get("blocker") or "")
        upper = blocker.upper()
        blocker_is_generic_state = upper in BLOCKED_STATES
        removed, retained = self._remove_orphan_locks(diagnostics)
        diagnostics_after = self._diagnostics(worktree)
        flags: dict[str, Any] = {
            "recovery_triggered": True,
            "recovery_plan_key": trigger_key,
        }
        safe_to_retry = False
        reason = "NO_SAFE_AUTOMATIC_REPAIR_FOR_BLOCKER"
        isolated_worktree: Path | None = None
        isolated_error: str | None = None
        if (
            not diagnostics_after.get("clean")
            and (safe_transient or real_data_blocker)
        ):
            isolated_worktree, isolated_error = self._provision_isolated_worktree(
                slot_id, trigger_key, task, worktree,
            )
            if isolated_worktree is not None:
                diagnostics_after = self._diagnostics(isolated_worktree)
                flags["isolated_recovery_worktree"] = str(isolated_worktree)
        if diagnostics_after.get("clean") and diagnostics_after.get("head"):
            if removed or any(marker in upper for marker in LOCK_MARKERS):
                safe_to_retry = not retained
                reason = "ORPHAN_LOCK_RECOVERY_APPLIED" if safe_to_retry else "LOCK_RETAINED_NOT_SAFE"
            elif any(marker in upper for marker in SAFE_TIMEOUT_MARKERS):
                safe_to_retry = True
                flags["allow_verified_local_head_fallback"] = True
                flags["allow_existing_sparse_paths_after_timeout"] = True
                reason = "VERIFIED_LOCAL_HEAD_RETRY_ENABLED"
            elif local_host_recovered:
                safe_to_retry = True
                reason = "CURRENT_LOCAL_HOST_LIVENESS_RETRY_ENABLED"
            elif not blocker or blocker_is_generic_state:
                safe_to_retry = True
                reason = "BLOCKED_WITHOUT_DIAGNOSTIC_SINGLE_RETRY_ENABLED"
        if any(marker in upper for marker in DATA_BLOCKER_MARKERS):
            safe_to_retry = bool(diagnostics_after.get("clean") and diagnostics_after.get("head"))
            reason = (
                "FREE_PUBLIC_SOURCE_DISCOVERY_RETRY_ENABLED"
                if safe_to_retry
                else "SOURCE_DISCOVERY_REQUIRES_CLEAN_OR_ISOLATED_WORKTREE"
            )
            if safe_to_retry:
                flags.update({
                    "source_discovery_policy": SOURCE_DISCOVERY_POLICY,
                    "allow_free_public_source_discovery": True,
                    "forbid_user_source_request": True,
                    "forbid_email_or_account_sources": True,
                    "allow_evidence_backed_no_data": True,
                    "continue_after_no_data": True,
                })

        plan.update({
            "state": "RECOVERY_SUCCEEDED" if safe_to_retry else "RECOVERY_PARKED",
            "automatic_retry_count": 1 if safe_to_retry else 0,
            "repair_reason": reason,
            "removed_orphan_locks": removed,
            "retained_locks": retained,
            "isolated_recovery_worktree": str(isolated_worktree) if isolated_worktree else None,
            "isolated_recovery_error": isolated_error,
            "diagnostics_after": diagnostics_after,
            "task_recovery_flags": flags if safe_to_retry else {},
            "source_discovery_policy": SOURCE_DISCOVERY_POLICY if real_data_blocker else None,
            "applied_at": utc_now(),
        })
        self._record(slot_id, trigger_key, plan)
        recovered = dict(task)
        recovered.update(flags)
        return {
            "decision": "ALLOW" if safe_to_retry else "BLOCK",
            "reason": reason,
            "task": recovered if safe_to_retry else task,
        }

    def summary(self) -> dict[str, Any]:
        return read_json(self.summary_path, {}) or {
            "policy": "CONTINUATION_OR_STALE_TRIGGERED_PLAN_WAIT_SAFE_REPAIR_RESUME",
            "logical_slot_count": len(self.slot_ids),
            "wait_seconds": self.wait_seconds,
            "proactive_after_seconds": self.proactive_after_seconds,
            "slot_states": {},
        }
