# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
PARTITION_START = 30762
PARTITION_END = 61522
ONSPD_ITEM_ID = "6fff67d204fd4f339591ed667a6e3642"
ONSPD_URL = f"https://www.arcgis.com/sharing/rest/content/items/{ONSPD_ITEM_ID}/data"
ONSPD_SNAPSHOT = "2026-05"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def norm_postcode(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def progress(path: Path, step: int, operation: str, state: str, **extra: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": utc_now(), "step": step, "operation": operation, "state": state, **extra}
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_wave1(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalized_headers(row: dict[str, str]) -> dict[str, str]:
    return {re.sub(r"[^a-z0-9]+", "", str(k).casefold()): v for k, v in row.items() if k is not None}


def first_value(row: dict[str, str], aliases: list[str]) -> str | None:
    normalized = normalized_headers(row)
    for alias in aliases:
        key = re.sub(r"[^a-z0-9]+", "", alias.casefold())
        if key in normalized:
            return normalized[key]
    return None


def find_postcodes(archive: zipfile.ZipFile, targets: set[str]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    csv_members = [name for name in archive.namelist() if name.casefold().endswith(".csv")]
    area_targets: dict[str, set[str]] = {}
    for postcode in targets:
        match = re.match(r"^[A-Z]+", postcode)
        area_targets.setdefault(match.group(0) if match else "", set()).add(postcode)

    def likely_member(name: str, areas: set[str]) -> bool:
        upper = Path(name).name.upper()
        return any(re.search(rf"(?:_|-){re.escape(area)}(?:_|-|\.)", upper) for area in areas)

    areas = {area for area in area_targets if area}
    ordered = sorted(csv_members, key=lambda name: (not likely_member(name, areas), len(name), name))
    for member in ordered:
        try:
            with archive.open(member, "r") as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
                reader = csv.DictReader(text)
                for row in reader:
                    postcode = norm_postcode(first_value(row, ["pcds", "pcd", "pcd2", "postcode"]))
                    if postcode not in targets or postcode in found:
                        continue
                    termination = first_value(row, ["doterm", "termination_date"])
                    introduction = first_value(row, ["dointr", "introduction_date"])
                    latitude = first_value(row, ["lat", "latitude"])
                    longitude = first_value(row, ["long", "longitude"])
                    found[postcode] = {
                        "postcode": postcode,
                        "onspd_member": member,
                        "introduction_date": introduction,
                        "termination_date": termination,
                        "postcode_status": "TERMINATED" if str(termination or "").strip() else "LIVE_OR_UNTERMINATED",
                        "latitude": latitude,
                        "longitude": longitude,
                    }
                    if len(found) == len(targets):
                        return found
        except (UnicodeError, csv.Error, KeyError):
            continue
    return found


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    root = repo_root()
    shard = root / "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards" / SLOT_ID
    progress_path = shard / "progress/002_progress.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("", encoding="utf-8")
    output_path = shard / "data/002_onspd_crosschecked_candidates.jsonl"
    validation_path = shard / "validation/002_onspd_crosscheck.json"
    status_path = shard / "status/002_status.json"
    report_path = shard / "reports/002_onspd_may_2026_crosscheck.md"

    progress(progress_path, 1, "slot_partition_guard", "PASS", partition=[PARTITION_START, PARTITION_END])
    wave1_path = shard / "data/001_existing_shard2_sample_candidates.jsonl"
    candidates = load_wave1(wave1_path)
    if not candidates:
        blocker = "WAITING_FOR_WAVE1_OFCom_CANDIDATE_OUTPUT"
        write_json(validation_path, {"slot_id": SLOT_ID, "state": "BLOCKED", "blocker": blocker, "final_ready": False})
        write_json(status_path, {"slot_id": SLOT_ID, "state": "BLOCKED_WITH_EVIDENCE", "blocker": blocker, "updated_at": utc_now(), "final_ready": False})
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(f"# ONSPD cross-check\n\n- Blocker: {blocker}\n- final_ready: false\n", encoding="utf-8")
        progress(progress_path, 2, "wave1_candidate_readback", "BLOCKED", blocker=blocker)
        return 0

    targets = {norm_postcode(row.get("postcode")) for row in candidates if norm_postcode(row.get("postcode"))}
    progress(progress_path, 2, "wave1_candidate_readback", "PASS", candidates=len(candidates), distinct_postcodes=len(targets))

    portable_root = Path(os.environ.get("AAYS_PORTABLE_ROOT") or tempfile.gettempdir()).resolve()
    cache_dir = portable_root / "state/source_cache/onspd_may_2026"
    cache_dir.mkdir(parents=True, exist_ok=True)
    zip_path = cache_dir / "onspd_may_2026.zip"
    blocker: str | None = None
    try:
        if not zip_path.is_file() or zip_path.stat().st_size < 10_000_000:
            request = urllib.request.Request(ONSPD_URL, headers={"User-Agent": "AAYS-TerraYield/1.0 official-postcode-validation"})
            temporary = zip_path.with_suffix(".download")
            with urllib.request.urlopen(request, timeout=240) as response, temporary.open("wb") as output:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    output.write(block)
            temporary.replace(zip_path)
        progress(progress_path, 3, "official_onspd_download_or_cache", "PASS", bytes=zip_path.stat().st_size, sha256=sha256_file(zip_path))
        with zipfile.ZipFile(zip_path, "r") as archive:
            official = find_postcodes(archive, targets)
        progress(progress_path, 4, "exact_onspd_postcode_lookup", "PASS", requested=len(targets), found=len(official))
    except Exception as exc:
        official = {}
        blocker = f"ONSPD_DOWNLOAD_OR_PARSE_BLOCKED: {type(exc).__name__}: {exc}"
        progress(progress_path, 3, "official_onspd_download_or_parse", "BLOCKED", blocker=blocker)

    output: list[dict[str, Any]] = []
    live = terminated = missing = 0
    for candidate in candidates:
        postcode = norm_postcode(candidate.get("postcode"))
        ons = official.get(postcode)
        if ons is None:
            missing += 1
            status = "ONSPD_NOT_CONFIRMED"
        elif ons["postcode_status"] == "TERMINATED":
            terminated += 1
            status = "ONSPD_TERMINATED_REVIEW_REQUIRED"
        else:
            live += 1
            status = "ONSPD_CONFIRMED"
        output.append({**candidate, "onspd_snapshot_date": ONSPD_SNAPSHOT, "onspd_item_id": ONSPD_ITEM_ID,
                       "onspd": ons, "onspd_crosscheck_status": status,
                       "parcel_measured_speed": False, "final_ready": False})
    write_jsonl(output_path, output)
    validation = {
        "slot_id": SLOT_ID,
        "sample_rows": len(output),
        "onspd_confirmed": live,
        "onspd_terminated_review_required": terminated,
        "onspd_not_confirmed": missing,
        "source_snapshot_date": ONSPD_SNAPSHOT,
        "source_item_id": ONSPD_ITEM_ID,
        "maximum_accuracy": "3/4_POSTCODE_PROXY",
        "parcel_measured_values_written": 0,
        "blocker": blocker,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "validated_at": utc_now(),
    }
    write_json(validation_path, validation)
    write_json(status_path, {"slot_id": SLOT_ID, "state": "BLOCKED_WITH_EVIDENCE" if blocker else "ONSPD_CROSSCHECK_COMPLETE",
                             "verified_candidates": live, "review_required": terminated, "not_confirmed": missing,
                             "blocker": blocker, "updated_at": utc_now(), "final_ready": False})
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# internet_access_2 — ONSPD May 2026 cross-check\n\n"
        f"- Input sample rows: {len(output)}\n- ONSPD confirmed: {live}\n"
        f"- Terminated/review required: {terminated}\n- Not confirmed: {missing}\n"
        f"- Blocker: {blocker or 'none'}\n- Maximum accuracy: 3/4 postcode proxy\n"
        "- Parcel-measured values written: 0\n- final_ready: false\n",
        encoding="utf-8",
    )
    progress(progress_path, 5, "onspd_crosscheck_artifacts_written", "PASS", rows=len(output), confirmed=live,
             terminated=terminated, missing=missing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
