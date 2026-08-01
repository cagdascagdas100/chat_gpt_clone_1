from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-next-source-discovery-v1-20260801"
MANIFEST_PATH = "docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/next_source_discovery_manifest_20260801.json"
CHECKPOINT_PATH = "docs/chatgpt_status/_shared/slots_21/parcel_label_3/checkpoint_latest.json"
WRITE_PATH = "docs/chatgpt_status/_shared/slots_21/parcel_label_3/next_source_discovery_result_latest.json"
TARGET_COUNT = 3
EXPECTED_STEP = "SELECT_NEXT_UNPUBLISHED_OFFICIAL_OR_FREE_CANDIDATE_BATCH"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json_sha256(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + ".part")
    part.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(part, path)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"NOT_OBJECT:{path}")
    return payload


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("schema_version") != 1 or manifest.get("slot_id") != SLOT_ID:
        raise ValueError("INVALID_MANIFEST_IDENTITY")
    groups = manifest.get("candidate_groups")
    if not isinstance(groups, list) or len(groups) != TARGET_COUNT:
        raise ValueError("CANDIDATE_GROUP_COUNT_NOT_3")
    roads: set[str] = set()
    validated: list[dict[str, Any]] = []
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("CANDIDATE_GROUP_NOT_OBJECT")
        road = " ".join(str(group.get("road") or "").split())
        source_url = str(group.get("source_url") or "")
        source_hash = str(group.get("source_content_sha256") or "")
        commits = group.get("prior_publication_commits")
        if not road or road.casefold() in roads:
            raise ValueError("DUPLICATE_OR_EMPTY_ROAD")
        if not source_url.startswith("https://"):
            raise ValueError("NON_HTTPS_SOURCE")
        if not SHA256_RE.fullmatch(source_hash):
            raise ValueError("INVALID_SOURCE_SHA256")
        if not isinstance(commits, list) or not all(COMMIT_RE.fullmatch(str(commit or "")) for commit in commits):
            raise ValueError("INVALID_PRIOR_PUBLICATION_COMMITS")
        roads.add(road.casefold())
        validated.append(group)
    return validated


def run(repo: Path) -> dict[str, Any]:
    manifest = load_json(repo / MANIFEST_PATH)
    checkpoint = load_json(repo / CHECKPOINT_PATH)
    groups = validate_manifest(manifest)
    if checkpoint.get("first_unverified_step") != EXPECTED_STEP:
        raise ValueError("CHECKPOINT_STEP_MISMATCH")

    decisions: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    for group in groups:
        commits = list(group.get("prior_publication_commits") or [])
        decision = {
            "road": group["road"],
            "source_url": group["source_url"],
            "source_content_sha256": group["source_content_sha256"],
            "source_record_scope": group["source_record_scope"],
            "prior_publication_commits": commits,
            "decision": "EXCLUDE_ALREADY_PUBLISHED" if commits else "SELECT_UNPUBLISHED",
        }
        decisions.append(decision)
        if not commits:
            selected.append(decision)

    selected = selected[:1]
    state = "PUBLISHED_SELECTION" if selected else "NO_DATA_CONTINUE"
    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": len(decisions),
        "target_count": TARGET_COUNT,
        "previous_percent": 0.0,
        "progress_percent": round(100.0 * len(decisions) / TARGET_COUNT, 4),
        "percent_increase": round(100.0 * len(decisions) / TARGETCOUNT, 4),
        "selected_candidate_groups": selected,
        "decisions": decisions,
        "source_evidence": {
            "manifest_path": MANIFEST_PATH,
            "manifest_content_sha256": canonical_json_sha256(manifest),
            "accessed_at": manifest.get("accessed_at"),
            "candidate_group_count": len(groups),
            "proven_fields": ["road", "source_url", "source_record_scope", "prior_publication_commits"],
        },
        "blocker": None if selected else {
            "code": "CANONICAL_CANDIDATE_MANIFEST_GROUPS_ALREADY_PUBLISHED",
            "state": "NO_DATA_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "FETCH_SELECTED_UNPUBLISHED_CANDIDATE_GROUP"
            if selected
            else "DISCOVER_NEW_OPEN_SOURCE_BEYOND_EXISTING_CANONICAL_CANDIDATE_MANIFEST"
        ),
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    return payload


def validate_only() -> dict[str, Any]:
    for path in (MANIFEST_PATH, CHECKPOINT_PATH, WRITE_PATH):
        parsed = Path(path)
        if parsed.is_absolute() or ".." in parsed.parts:
            raise ValueError("NON_RELATIVE_PATH")
    return {
        "state": "VALIDATED",
        "target_count": TARGET_COUNT,
        "resource_class": "light_read",
        "read_paths": [MANIFEST_PATH, CHECKPOINT_PATH],
        "write_paths": [WRITE_PATH],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        print(json.dumps(validate_only(), ensure_ascii=False))
        return 0
    repo = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
    result = run(repo)
    atomic_json(repo / WRITE_PATH, result)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "selected_count": len(result["selected_candidate_groups"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
