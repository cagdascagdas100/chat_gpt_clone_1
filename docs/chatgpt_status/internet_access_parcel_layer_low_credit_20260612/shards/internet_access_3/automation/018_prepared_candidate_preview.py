#!/usr/bin/env python3
"""Publish a deterministic prepared-candidate preview for the web page.

The preview contains existing proxy evidence only. Rows are labelled PREPARED,
not revalidated, and no confidence or score is raised.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
ROWS_EXPECTED = 30761
PREVIEW_SIZE = 16


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--rows", default="england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json")
    p.add_argument("--output-root", default="england_map_web/data/aays_21_slots/internet_access_3")
    p.add_argument("--preview-size", type=int, default=PREVIEW_SIZE)
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/013_prepared_candidate_preview_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "england_map_web").exists() and (item / "docs").exists():
            return item
    raise FileNotFoundError("repository root not found")


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def select(rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    eligible = [row for row in rows if row.get("internet_status") == "verified_existing_postcode_proxy" and row.get("postcode")]
    eligible.sort(key=lambda row: int(row["row_no"]))
    if not eligible:
        return []
    take = min(max(1, size), len(eligible))
    indexes = [0] if take == 1 else [round(i * (len(eligible) - 1) / (take - 1)) for i in range(take)]
    return [eligible[index] for index in indexes]


def main() -> int:
    parsed = args()
    repo = root(parsed.repo_root)
    output_root = repo / parsed.output_root
    rows = load(repo / parsed.rows)
    if not isinstance(rows, list) or len(rows) != ROWS_EXPECTED:
        raise ValueError("migrated shard rows missing or wrong count")
    selected = select(rows, parsed.preview_size)
    preview = []
    for row in selected:
        preview.append({
            "row_no": int(row["row_no"]),
            "parcel_id": row.get("canonical_program_parcel_id"),
            "hmlr_inspire_id": row.get("hmlr_inspire_id"),
            "london_authority": row.get("london_authority"),
            "postcode": row.get("postcode"),
            "gigabit_available_pct": row.get("gigabit_available_pct"),
            "ultrafast_or_100mbps_available_pct": row.get("ultrafast_or_100mbps_available_pct"),
            "superfast_30mbps_available_pct": row.get("superfast_30mbps_available_pct"),
            "unable_30mbps_pct": row.get("unable_30mbps_pct"),
            "status": "PREPARED_NOT_REVALIDATED",
            "source_level": "EXISTING_POSTCODE_PROXY",
            "confidence_raised": False,
            "parcel_relation_promoted": False
        })
    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "prepared" if preview else "blocked",
        "preview_rows_requested": parsed.preview_size,
        "preview_rows_prepared": len(preview),
        "candidate_rows_revalidated": 0,
        "source_accuracy_score": 50,
        "parcel_match_accuracy_score": 50,
        "output_semantics": "PREPARED_EXISTING_PROXY_PREVIEW_ONLY",
        "rows": preview,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False
    }
    atomic_json(output_root / "prepared_candidate_preview_latest.json", summary)
    atomic_json(repo / parsed.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if preview else 2


if __name__ == "__main__":
    raise SystemExit(main())
