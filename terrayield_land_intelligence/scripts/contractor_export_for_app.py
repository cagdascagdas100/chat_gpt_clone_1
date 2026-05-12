#!/usr/bin/env python3
"""Export contractor intelligence for app consumption with DO_NOT_CONTACT controls."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from pandas.errors import EmptyDataError

from contractor_env import load_contractor_env

DEFAULT_STORAGE_ROOT = r"E:\AAYS_DATA\contractor"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=object)
    except EmptyDataError:
        return pd.DataFrame()


def clean_value(v: Any) -> Any:
    if pd.isna(v):
        return None
    return v


def safe_bool(v: Any) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes"}


def sanitize_for_app(row: Dict[str, Any]) -> Dict[str, Any]:
    legal_score = int(float(row.get("legal_contact_score") or 0))
    do_not_contact = safe_bool(row.get("do_not_contact")) or legal_score < 50
    out = {k: clean_value(v) for k, v in row.items()}
    out["do_not_contact"] = do_not_contact
    out["contact_status"] = "DO_NOT_CONTACT" if do_not_contact else (out.get("contact_status") or "READY")
    # Defense-in-depth: do not expose actionable contact-like fields for blocked records.
    if do_not_contact:
        for key in ["registered_office_address", "postal_code", "company_source_url"]:
            out[key] = None
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Export app-ready contractor intelligence snapshots.")
    parser.add_argument("--storage-root", default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--export-root", default=None)
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    args = parser.parse_args()
    env_info = load_contractor_env(Path(args.project_root))
    storage_root = Path(args.storage_root)
    curated = storage_root / "curated"
    export_root = Path(args.export_root) if args.export_root else storage_root / "exports"
    export_root.mkdir(parents=True, exist_ok=True)

    contractors_file = curated / "contractor_score_snapshot.csv"
    projects_file = curated / "contractor_project_snapshot.csv"
    matches_file = curated / "contractor_parcel_match.csv"
    if not contractors_file.exists():
        raise FileNotFoundError(f"Missing curated contractors: {contractors_file}")
    contractors = read_csv_or_empty(contractors_file).to_dict(orient="records")
    safe_contractors = [sanitize_for_app(row) for row in contractors]

    pd.DataFrame(safe_contractors).to_csv(export_root / "contractors_for_app.csv", index=False, encoding="utf-8")
    with (export_root / "contractors_for_app.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for row in safe_contractors:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    if projects_file.exists():
        projects = read_csv_or_empty(projects_file)
        projects.to_csv(export_root / "contractor_projects_for_app.csv", index=False, encoding="utf-8")
    else:
        projects = pd.DataFrame()
    if matches_file.exists():
        matches = read_csv_or_empty(matches_file)
        matches.to_csv(export_root / "contractor_parcel_matches_for_app.csv", index=False, encoding="utf-8")
    else:
        matches = pd.DataFrame()

    blocked = sum(1 for r in safe_contractors if r.get("do_not_contact"))
    manifest = {
        "generated_at": utc_now(),
        "contractor_count": len(safe_contractors),
        "do_not_contact_count": blocked,
        "project_count": len(projects),
        "parcel_match_count": len(matches),
        "exports": [
            str(export_root / "contractors_for_app.csv"),
            str(export_root / "contractors_for_app.jsonl"),
            str(export_root / "contractor_projects_for_app.csv") if projects_file.exists() else None,
            str(export_root / "contractor_parcel_matches_for_app.csv") if matches_file.exists() else None,
        ],
        "contact_rule": "DO_NOT_CONTACT when legal_contact_score < 50 or do_not_contact=true; contact-like fields suppressed in app export.",
        "db_env_report": env_info["report"],
    }
    write_json(export_root / "export_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
