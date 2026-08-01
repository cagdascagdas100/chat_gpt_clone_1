#!/usr/bin/env python3
"""Inventory canonical ready_to_sell_3 parcel/geometry evidence; fail closed."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "ready_to_sell_3"
CONTINUATION_KEY = "6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a"
ALLOWED_OUTPUT = Path(
    "docs/chatgpt_status/aays1/shards/ready_to_sell_3/validation/"
    "automation_168_parcel_geometry_inventory_latest.json"
)

def projection(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": item.get("candidate_id"),
            "title": item.get("title"),
            "parcel_match": item.get("parcel_match"),
            "geometry_match": item.get("geometry_match"),
        }
        for item in candidates
    ]

def projection_sha256(candidates: list[dict[str, Any]]) -> str:
    raw = json.dumps(
        projection(candidates),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def analyze(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("slot_id") != SLOT_ID:
        raise ValueError("manifest slot mismatch")
    if manifest.get("continuation_key") != CONTINUATION_KEY:
        raise ValueError("manifest continuation mismatch")

    evidence: list[dict[str, Any]] = []
    inspected: list[dict[str, Any]] = []
    parcel_positive = 0
    geometry_positive = 0

    for source in manifest.get("sources", []):
        rel = Path(source["relative_path"])
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(f"missing exact read path: {rel}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("slot_id") != SLOT_ID:
            raise ValueError(f"slot mismatch: {rel}")
        if data.get("continuation_key") != CONTINUATION_KEY:
            raise ValueError(f"continuation mismatch: {rel}")

        candidates = data.get("candidates")
        if not isinstance(candidates, list):
            raise ValueError(f"candidates missing: {rel}")
        actual_projection_sha256 = projection_sha256(candidates)
        expected_projection_sha256 = source["projection_sha256"]
        if actual_projection_sha256 != expected_projection_sha256:
            raise ValueError(f"projection SHA-256 mismatch: {rel}")

        for item in candidates:
            parcel = item.get("parcel_match")
            geometry = item.get("geometry_match")
            if parcel not in (None, False, "", [], {}):
                parcel_positive += 1
            if geometry not in (None, False, "", [], {}):
                geometry_positive += 1
            inspected.append(
                {
                    "candidate_id": item.get("candidate_id"),
                    "title": item.get("title"),
                    "parcel_match": parcel,
                    "geometry_match": geometry,
                    "source_wave": data.get("wave"),
                }
            )

        evidence.append(
            {
                "relative_path": str(rel),
                "repository_url": source["repository_url"],
                "accessed_at": source["accessed_at"],
                "projection_sha256": actual_projection_sha256,
                "hash_scope": source["hash_scope"],
                "relevant_record_ids": source["relevant_record_ids"],
                "proven_fields": source["proven_fields"],
                "publisher_source_urls": source["publisher_source_urls"],
                "license_or_terms_status": source["license_or_terms_status"],
                "candidate_count": len(candidates),
            }
        )

    candidate_count = len(inspected)
    if candidate_count == 0:
        raise ValueError("no canonical candidates inspected")
    no_data = parcel_positive == 0 and geometry_positive == 0
    return {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "continuation_key": CONTINUATION_KEY,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state": "NO_DATA_CONTINUE" if no_data else "READY_FOR_ACCEPTANCE",
        "panel_status": "BLOCKED" if no_data else "BİLGİ TOPLANIYOR",
        "completed_count": candidate_count,
        "target_count": candidate_count,
        "progress_percent": candidate_count / candidate_count * 100,
        "source_count": len(evidence),
        "candidate_count": candidate_count,
        "parcel_matches": parcel_positive,
        "geometry_matches": geometry_positive,
        "no_data_reason": (
            "All inspected canonical candidate records contain explicit null/empty "
            "parcel_match and geometry_match values; no parcel or geometry value was inferred."
            if no_data
            else None
        ),
        "evidence": evidence,
        "inspected_records": inspected,
        "fake_data": False,
    }

def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)

def self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        rel = Path("wave.json")
        rows = [
            {
                "candidate_id": "a",
                "title": "Alpha",
                "parcel_match": None,
                "geometry_match": None,
            },
            {
                "candidate_id": "b",
                "title": "Beta",
                "parcel_match": None,
                "geometry_match": None,
            },
        ]
        (root / rel).write_text(
            json.dumps(
                {
                    "slot_id": SLOT_ID,
                    "continuation_key": CONTINUATION_KEY,
                    "wave": 1,
                    "candidates": rows,
                }
            ),
            encoding="utf-8",
        )
        manifest = {
            "slot_id": SLOT_ID,
            "continuation_key": CONTINUATION_KEY,
            "sources": [
                {
                    "relative_path": str(rel),
                    "repository_url": "fixture://wave",
                    "accessed_at": "2026-08-01T14:43:00Z",
                    "projection_sha256": projection_sha256(rows),
                    "hash_scope": "normalized_candidate_binding_projection",
                    "relevant_record_ids": ["a", "b"],
                    "proven_fields": ["parcel_match", "geometry_match"],
                    "publisher_source_urls": [],
                    "license_or_terms_status": "fixture",
                }
            ],
        }
        result = analyze(root, manifest)
        assert result["state"] == "NO_DATA_CONTINUE"
        assert result["completed_count"] == 2
        assert result["target_count"] == 2
        assert result["progress_percent"] == 100
        assert result["parcel_matches"] == 0
        assert result["geometry_matches"] == 0
    print("SELF_TEST_PASS")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--manifest")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.manifest or not args.output:
        parser.error("--manifest and --output are required unless --self-test is used")

    root = Path(args.repo_root).resolve()
    output_rel = Path(args.output)
    if output_rel != ALLOWED_OUTPUT:
        raise SystemExit("output path outside exact_write_paths")
    manifest_path = root / args.manifest
    if not manifest_path.is_file():
        raise SystemExit(f"missing manifest: {args.manifest}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = analyze(root, manifest)
    atomic_write(root / output_rel, result)
    return 0

if __name__ == "__main__":
    sys.exit(main())
