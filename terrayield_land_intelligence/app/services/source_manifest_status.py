from __future__ import annotations

from pathlib import Path
from typing import Any


def _as_bool(value: Any) -> bool:
    return bool(value)


def summarize_listing_manifest_entries(
    entries: list[dict[str, Any]],
    *,
    manifest_path: Path,
    container_key: str,
    source_name: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    missing_active_files: list[str] = []
    active_entries = 0
    demo_entries = 0
    live_ready_entries = 0

    for entry in entries:
        active = entry.get("active", True) is not False
        is_demo = bool(entry.get("is_demo")) or entry.get("provider_kind") == "demo" or entry.get("truth_tier") == "demo"
        file_drop_path = str(entry.get("file_drop_path") or "").strip()
        missing_file = False
        if active and file_drop_path:
            candidate = manifest_path.parent / file_drop_path
            missing_file = not candidate.exists()
            if missing_file:
                missing_active_files.append(file_drop_path)
        live_ready = active and not is_demo and not missing_file
        active_entries += 1 if active else 0
        demo_entries += 1 if is_demo else 0
        live_ready_entries += 1 if live_ready else 0
        row = dict(entry)
        row["active"] = active
        row["is_demo"] = is_demo
        row["live_ready"] = live_ready
        rows.append(row)

    return {
        "source_name": source_name,
        "manifest_path": str(manifest_path),
        "container_key": container_key,
        "manifest_exists": True,
        "parse_error": None,
        "manifest_entries": len(entries),
        "active_entries": active_entries,
        "demo_entries": demo_entries,
        "live_ready_entries": live_ready_entries,
        "missing_active_files": missing_active_files,
        "has_demo_only_manifest": demo_entries > 0 and live_ready_entries == 0,
        "has_live_ready_manifest": live_ready_entries > 0,
        "manifest_rows": rows,
    }


def summarize_facilities_manifest_entries(
    entries: list[dict[str, Any]],
    *,
    manifest_path: Path,
    container_key: str,
    source_name: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    active_entries = 0
    live_ready_entries = 0
    missing_active_files: list[str] = []

    for entry in entries:
        active = entry.get("active", True) is not False
        mode = str(entry.get("mode") or "").strip().lower()
        download_ready = active and mode == "download" and bool(entry.get("download_url"))
        file_path = str(entry.get("file_path") or entry.get("file_drop_path") or "").strip()
        missing_file = False
        if active and file_path and not download_ready:
            candidate = manifest_path.parent / file_path
            missing_file = not candidate.exists()
            if missing_file:
                missing_active_files.append(file_path)
        live_ready = active and (download_ready or not missing_file)
        active_entries += 1 if active else 0
        live_ready_entries += 1 if live_ready else 0
        row = dict(entry)
        row["active"] = active
        row["download_ready"] = download_ready
        row["live_ready"] = live_ready
        rows.append(row)

    return {
        "source_name": source_name,
        "manifest_path": str(manifest_path),
        "container_key": container_key,
        "manifest_exists": True,
        "parse_error": None,
        "manifest_entries": len(entries),
        "active_entries": active_entries,
        "demo_entries": 0,
        "live_ready_entries": live_ready_entries,
        "missing_active_files": missing_active_files,
        "has_demo_only_manifest": False,
        "has_live_ready_manifest": live_ready_entries > 0,
        "manifest_rows": rows,
    }


def derive_manifest_availability(status: dict[str, Any]) -> str:
    if not status.get("manifest_exists"):
        return "missing_manifest"
    if status.get("parse_error"):
        return "parse_error"
    if status.get("missing_active_files"):
        return "missing_files"
    if status.get("has_live_ready_manifest"):
        return "live_ready"
    if status.get("has_demo_only_manifest"):
        return "demo_only"
    if int(status.get("active_entries") or 0) == 0 and int(status.get("manifest_entries") or 0) > 0:
        return "inactive_only"
    return str(status.get("availability") or "inactive_only")


def inspect_configured_manifest_status(source_name: str, settings: object) -> dict[str, Any]:
    return {}


def inspect_configured_listing_manifest_status(source_name: str, settings: object) -> dict[str, Any]:
    return inspect_configured_manifest_status(source_name, settings)
