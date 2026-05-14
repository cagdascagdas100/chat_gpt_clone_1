
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

EXPORT_ROOT = Path(os.environ.get("AAYS_CONTRACTOR_EXPORT_ROOT", r"E:\AAYS_DATA\contractor\exports"))

FILES = {
    "companies": "contractors_for_app.csv",
    "companies_jsonl": "contractors_for_app.jsonl",
    "projects": "contractor_projects_for_app.csv",
    "parcel_matches": "contractor_parcel_matches_for_app.csv",
    "manifest": "export_manifest.json",
}

CONTACT_SUPPRESSION_NOTE = (
    "DO_NOT_CONTACT gate is enforced upstream in contractor_export_for_app.py; "
    "this API only serves app-ready export files and does not rehydrate suppressed contact fields."
)


def _path(key: str) -> Path:
    if key not in FILES:
        raise KeyError(key)
    return EXPORT_ROOT / FILES[key]


def export_status() -> dict[str, Any]:
    files: dict[str, Any] = {}
    for key, filename in FILES.items():
        path = EXPORT_ROOT / filename
        files[key] = {
            "filename": filename,
            "path": str(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "modified_at": path.stat().st_mtime if path.exists() else None,
        }
    return {"export_root": str(EXPORT_ROOT), "files": files, "contact_rule": CONTACT_SUPPRESSION_NOTE}


def read_csv_rows(key: str, *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    limit = max(1, min(int(limit), 1000))
    offset = max(0, int(offset))
    path = _path(key)
    if not path.exists():
        return {"key": key, "exists": False, "rows": [], "count": 0, "limit": limit, "offset": offset}
    rows: list[dict[str, Any]] = []
    total = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if total >= offset and len(rows) < limit:
                rows.append(dict(row))
            total += 1
    return {"key": key, "exists": True, "count": total, "limit": limit, "offset": offset, "rows": rows}


def read_manifest() -> dict[str, Any]:
    path = _path("manifest")
    if not path.exists():
        return {"exists": False, "manifest": None}
    with path.open("r", encoding="utf-8-sig") as f:
        return {"exists": True, "manifest": json.load(f)}
