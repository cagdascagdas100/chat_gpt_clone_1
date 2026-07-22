from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
BASE_ROOTS = {
    "ready_to_sell": "docs/chatgpt_status/aays1",
    "gas_emissions": "docs/chatgpt_status/gas_emissions",
    "height_difference": "docs/chatgpt_status/topography",
    "security_public_safety": "docs/chatgpt_status/aays1",
    "parcel_label": "docs/chatgpt_status/aays1",
    "internet_access": "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612",
    "future_growth": "docs/chatgpt_status/aays1",
}
ACTIVE_STATES = {"CLAIMED", "RUNNING", "PUBLISHING", "RESULT_READY_FOR_SERIAL_PUBLISH"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"AUTHORITATIVE_JSON_READ_FAILED:{path}:{exc}") from exc


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{uuid.uuid4().hex}")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def base_from_slot(slot_id: str) -> tuple[str, int]:
    base, separator, shard_text = slot_id.rpartition("_")
    if not separator or base not in BASE_ROOTS or shard_text not in {"1", "2", "3"}:
        raise RuntimeError(f"UNKNOWN_21_SLOT_ID:{slot_id}")
    return base, int(shard_text)


def blocker_values(*documents: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for document in documents:
        single = document.get("blocker")
        if single:
            values.append(str(single))
        multiple = document.get("blockers")
        if isinstance(multiple, list):
            values.extend(str(value) for value in multiple if value)
    return list(dict.fromkeys(values))


def main() -> int:
    repo = Path.cwd().resolve()
    slot_id = os.environ.get("AAYS_SLOT_ID", "").strip()
    task_id = os.environ.get("AAYS_TASK_ID", "").strip()
    if not slot_id or not task_id:
        raise RuntimeError("COORDINATOR_SLOT_AND_TASK_ENV_REQUIRED")

    base_slot_id, shard_index = base_from_slot(slot_id)
    slot_root = repo / "docs" / "chatgpt_status" / "_shared" / "slots_21" / slot_id
    names = (
        "ownership_latest.json",
        "checkpoint_latest.json",
        "heartbeat_latest.json",
        "current_task_latest.json",
        "status_latest.json",
    )
    paths = {name: slot_root / name for name in names}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError("AUTHORITATIVE_SLOT_FILES_MISSING:" + ",".join(missing))

    documents = {name: read_json(path) for name, path in paths.items()}
    for name, document in documents.items():
        if document.get("slot_id") != slot_id:
            raise RuntimeError(f"AUTHORITATIVE_SLOT_ID_MISMATCH:{name}")
        if document.get("workstream_id") != WORKSTREAM_ID:
            raise RuntimeError(f"AUTHORITATIVE_WORKSTREAM_MISMATCH:{name}")

    ownership = documents["ownership_latest.json"]
    checkpoint = documents["checkpoint_latest.json"]
    heartbeat = documents["heartbeat_latest.json"]
    current_task = documents["current_task_latest.json"]
    status = documents["status_latest.json"]
    current_state = str(current_task.get("state") or "").upper()
    heartbeat_state = str(heartbeat.get("state") or "").upper()
    heartbeat_stale = heartbeat.get("stale") is True or not heartbeat.get("heartbeat_at")
    if current_state in ACTIVE_STATES or (heartbeat_state in ACTIVE_STATES and not heartbeat_stale):
        raise RuntimeError("LIVE_AUTHORITATIVE_LEASE_ALREADY_EXISTS")

    expected_base = str(status.get("base_slot_id") or checkpoint.get("base_slot_id") or "")
    expected_shard = int(status.get("shard_index") or checkpoint.get("shard_index") or 0)
    if expected_base != base_slot_id or expected_shard != shard_index:
        raise RuntimeError("AUTHORITATIVE_SHARD_IDENTITY_MISMATCH")

    partition = status.get("parcel_partition") or checkpoint.get("parcel_partition") or {}
    first_unverified = str(
        checkpoint.get("first_unverified_step")
        or status.get("first_unverified_step")
        or "AUTHORITATIVE_FIRST_UNVERIFIED_STEP_MISSING"
    )
    blockers = blocker_values(status, checkpoint)
    business_evidence: dict[str, Any] = {}
    if base_slot_id == "parcel_label":
        parcel_checkpoint_path = repo / "docs" / "chatgpt_status" / "aays1" / "checkpoints" / "parcel_label_canonical_checkpoint.json"
        parcel_checkpoint = read_json(parcel_checkpoint_path)
        business_evidence = {
            "checkpoint_path": str(parcel_checkpoint_path.relative_to(repo)).replace("\\", "/"),
            "tracked_rows": int(parcel_checkpoint.get("tracked_rows") or 0),
            "verified_rows": int(parcel_checkpoint.get("verified_rows") or 0),
            "published_rows": int(parcel_checkpoint.get("published_rows") or 0),
            "browser_verified_rows": int(parcel_checkpoint.get("browser_verified_rows") or 0),
            "exact_geometry_rows": int(parcel_checkpoint.get("exact_geometry_rows") or 0),
            "canonical_target_rows": 92283,
            "checkpoint_status": parcel_checkpoint.get("checkpoint_status"),
        }
        blockers.extend(blocker_values(parcel_checkpoint))
        if business_evidence["tracked_rows"] < business_evidence["canonical_target_rows"]:
            blockers.append("PARCEL_LABEL_92283_RECONCILIATION_MANIFEST_NOT_ESTABLISHED")
    elif base_slot_id == "internet_access":
        business_evidence = {
            "internet_verified_rows": int(checkpoint.get("internet_verified_rows") or 0),
            "internet_no_data_or_pending_rows": int(checkpoint.get("internet_no_data_or_pending_rows") or 0),
            "measurement_level": "postcode",
            "output_semantics": "AREA_LEVEL_PROXY_OR_NO_DATA",
        }
    blockers = list(dict.fromkeys(blockers))
    blocker = blockers[0] if blockers else None
    portable_root = Path(os.environ.get("AAYS_PORTABLE_ROOT", "")).resolve()
    portable_git = portable_root / "runtime" / "git" / "cmd" / "git.exe"
    git_executable = str(portable_git) if portable_git.is_file() else (shutil.which("git") or "git")
    remote_head = subprocess.run(
        [git_executable, "rev-parse", "HEAD"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if remote_head.returncode != 0 or not remote_head.stdout.strip():
        raise RuntimeError("WORKTREE_HEAD_READ_FAILED:" + remote_head.stderr.strip())

    business_root = BASE_ROOTS[base_slot_id]
    local_output_root = os.environ.get("AAYS_KICKOFF_OUTPUT_ROOT", "").strip()
    if local_output_root:
        output = Path(local_output_root).resolve() / slot_id / "continuation_kickoff_20260720.json"
    else:
        output = repo / Path(business_root) / "shards" / slot_id / "continuation_kickoff_20260720.json"
    if base_slot_id == "future_growth" and blockers:
        kickoff_state = "BLOCKED_AT_VERIFIED_SOURCE_REQUIREMENT"
    elif blockers:
        kickoff_state = "STARTED_FROM_AUTHORITATIVE_CHECKPOINT_WITH_BLOCKERS"
    else:
        kickoff_state = "STARTED_FROM_AUTHORITATIVE_CHECKPOINT"
    payload = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": slot_id,
        "base_slot_id": base_slot_id,
        "shard_index": shard_index,
        "parcel_partition": partition,
        "task_id": task_id,
        "state": kickoff_state,
        "authoritative_checkpoint_sequence": int(checkpoint.get("sequence") or checkpoint.get("checkpoint_sequence") or 0),
        "first_unverified_step": first_unverified,
        "blocker": blocker,
        "blockers": blockers,
        "business_evidence": business_evidence,
        "owner_page_session_id_before": ownership.get("owner_page_session_id"),
        "remote_current_task_state_before": current_task.get("state"),
        "remote_heartbeat_state_before": heartbeat.get("state"),
        "remote_head_readback": remote_head.stdout.strip(),
        "authoritative_file_sha256": {name: sha256_file(path) for name, path in paths.items()},
        "actual_business_data_rows_written": 0,
        "output_semantics": "NO_DATA",
        "source_discovery_required": True,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "local_only": bool(local_output_root),
        "remote_publish": False if local_output_root else None,
        "final_ready": False,
        "started_at": utc_now(),
    }
    dry_run = os.environ.get("AAYS_KICKOFF_DRY_RUN", "").strip().casefold() == "true"
    payload["dry_run"] = dry_run
    if not dry_run:
        atomic_json(output, payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - runner log must preserve the real blocker
        print(f"AAYS_21_SLOT_CONTINUATION_KICKOFF_BLOCKED:{type(exc).__name__}:{exc}", file=sys.stderr)
        raise
