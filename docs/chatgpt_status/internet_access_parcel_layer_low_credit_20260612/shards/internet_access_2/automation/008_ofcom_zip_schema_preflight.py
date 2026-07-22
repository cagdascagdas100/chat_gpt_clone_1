# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io
import json
import os
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
SHARD_REL = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_2"
)
EXPECTED_R2_POSTCODE_FILE_COUNT = 121
EXPECTED_PATTERN = re.compile(r"202601_fixed_postcode_coverage_r2_[A-Z0-9]+\.csv$", re.I)
CORE_ALIASES = {
    "postcode": ["postcode", "postcode_space"],
    "gigabit": ["Gigabit availability (% premises)", "Gigabit availability"],
    "ufbb100": ["UFBB (100Mbit/s) availability (% premises)", "UFBB100 availability (% premises)"],
    "sfbb": ["SFBB availability (% premises)", "SFBB availability"],
    "unable30": ["% of premises unable to receive 30Mbit/s", "unable to receive 30Mbit/s"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    start = Path.cwd().resolve()
    for path in (start, *start.parents):
        if (path / "england_map_web").is_dir() and (path / "docs/chatgpt_status").is_dir():
            return path
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def normalise_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def candidate_paths() -> list[Path]:
    paths: list[Path] = []
    portable = os.environ.get("AAYS_PORTABLE_ROOT")
    if portable:
        paths.append(Path(portable) / "state/source_cache/ofcom_spring_2026/ofcom_fixed_coverage_202601_v2.zip")
    paths.append(Path(tempfile.gettempdir()) / "state/source_cache/ofcom_spring_2026/ofcom_fixed_coverage_202601_v2.zip")
    extra = os.environ.get("AAYS_OFCom_ZIP_PATH")
    if extra:
        paths.insert(0, Path(extra))
    unique: list[Path] = []
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def header_match(fieldnames: list[str], aliases: list[str]) -> str | None:
    lookup = {normalise_header(name): name for name in fieldnames}
    for alias in aliases:
        key = normalise_header(alias)
        if key in lookup:
            return lookup[key]
    return None


def inspect_zip(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "state": "NOT_PRESENT"}
    if path.stat().st_size < 1_000_000 or not zipfile.is_zipfile(path):
        return {"path": str(path), "state": "INVALID_ZIP", "bytes": path.stat().st_size}
    with zipfile.ZipFile(path, "r") as archive:
        members = [name.replace("\\", "/") for name in archive.namelist()]
        r2_members = sorted(name for name in members if EXPECTED_PATTERN.search(name))
        if not r2_members:
            return {
                "path": str(path),
                "state": "NO_R2_POSTCODE_FILES",
                "bytes": path.stat().st_size,
                "member_count": len(members),
                "expected_r2_postcode_file_count": EXPECTED_R2_POSTCODE_FILE_COUNT,
                "r2_postcode_file_count": 0,
            }
        sample_member = r2_members[0]
        with archive.open(sample_member, "r") as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""))
            fieldnames = list(reader.fieldnames or [])
            first_row = next(reader, None)
        matched = {key: header_match(fieldnames, aliases) for key, aliases in CORE_ALIASES.items()}
        missing = [key for key, value in matched.items() if value is None]
        file_count_ok = len(r2_members) == EXPECTED_R2_POSTCODE_FILE_COUNT
        sample_row_ok = first_row is not None
        if not file_count_ok:
            state = "R2_POSTCODE_FILE_COUNT_MISMATCH"
        elif missing:
            state = "CORE_COLUMNS_MISSING"
        elif not sample_row_ok:
            state = "SAMPLE_POSTCODE_FILE_EMPTY"
        else:
            state = "PASS"
        return {
            "path": str(path),
            "state": state,
            "bytes": path.stat().st_size,
            "member_count": len(members),
            "expected_r2_postcode_file_count": EXPECTED_R2_POSTCODE_FILE_COUNT,
            "r2_postcode_file_count": len(r2_members),
            "r2_postcode_file_count_ok": file_count_ok,
            "sample_member": sample_member,
            "fieldnames": fieldnames,
            "matched_core_columns": matched,
            "missing_core_columns": missing,
            "sample_row_present": sample_row_ok,
        }


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    root = repo_root()
    shard = root / SHARD_REL
    inspections = [inspect_zip(path) for path in candidate_paths()]
    accepted = next((item for item in inspections if item.get("state") == "PASS"), None)
    state = "OFCom_R2_ZIP_SCHEMA_ACCEPTED" if accepted else "OFCom_R2_ZIP_NOT_READY"
    blocker = None if accepted else "OFFICIAL_OFCom_R2_ZIP_NOT_PRESENT_OR_SCHEMA_NOT_ACCEPTED"
    validation = {
        "slot_id": SLOT_ID,
        "state": state,
        "expected_r2_postcode_file_count": EXPECTED_R2_POSTCODE_FILE_COUNT,
        "accepted_path": accepted.get("path") if accepted else None,
        "inspections": inspections,
        "official_coverage_verified_candidates": 0,
        "accuracy_written": 0,
        "parcel_measured_values_written": 0,
        "blocker": blocker,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "validated_at": now(),
    }
    write_json(shard / "validation/008_ofcom_zip_schema_preflight.json", validation)
    write_json(shard / "source_snapshots/008_ofcom_zip_schema_readback.json", validation)
    write_json(shard / "status/008_status.json", {
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID"),
        "state": state,
        "completed_operations": 3 if accepted else 2,
        "total_operations": 3,
        "progress_percent": 100.0 if accepted else 66.67,
        **validation,
        "next_step": "RUN_STRICT_EXACT_R2_JOIN" if accepted else "PROVISION_OFFICIAL_OFCom_R2_ZIP_THEN_RETRY",
        "updated_at": now(),
    })
    write_json(shard / "web/008_ofcom_zip_schema_preflight_latest.json", {
        "slot_id": SLOT_ID,
        "generated_at": now(),
        "state": state,
        "accepted": accepted is not None,
        "expected_r2_postcode_file_count": EXPECTED_R2_POSTCODE_FILE_COUNT,
        "r2_postcode_file_count": accepted.get("r2_postcode_file_count") if accepted else 0,
        "matched_core_columns": accepted.get("matched_core_columns") if accepted else {},
        "official_coverage_verified_candidates": 0,
        "final_ready": False,
    })
    report_path = shard / "reports/008_ofcom_zip_schema_preflight.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# internet_access_2 — Ofcom r2 ZIP schema preflight\n\n"
        f"- State: {state}\n"
        f"- Accepted path: {accepted.get('path') if accepted else 'none'}\n"
        f"- Expected r2 postcode files: {EXPECTED_R2_POSTCODE_FILE_COUNT}\n"
        f"- Accepted r2 postcode files: {accepted.get('r2_postcode_file_count') if accepted else 0}\n"
        f"- Blocker: {blocker or 'none'}\n"
        "- Candidate accuracy written: 0\n"
        "- final_ready: false\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
