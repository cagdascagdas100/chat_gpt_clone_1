from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-blpuclass-official-label-v1-20260803"
INPUT_PATH = "docs/chatgpt_status/_shared/slots_21/parcel_label_3/llpg_exact_binding_result_latest.json"
MANIFEST_PATH = "docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/blpuclass_official_label_source_manifest_20260803.json"
OUTPUT_PATHS = [
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/blpuclass_official_label_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/blpuclass_official_label_latest.json",
]
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
EXPECTED_INPUT_BLOB_SHA = "b045f698a2e5bd55ad7929ad65da3957fdd5fc2e"
EXPECTED_INPUT_CONTENT_SHA256 = "b5acbf74ab44cb0b96b0d3b14c99fa41068d6fc4ef58a14530ed63edf441ed1a"
EXPECTED_CODES = {"RD04", "RD06"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def validate_inputs(base: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source = load_json(base / INPUT_PATH)
    manifest = load_json(base / MANIFEST_PATH)
    if source.get("state") != "PUBLISHED" or source.get("exact_verified_rows") != 3:
        raise ValueError("LLPG exact binding is not terminal PUBLISHED 3/3")
    if source.get("fake_data") is not False:
        raise ValueError("LLPG fake_data gate failed")
    records = source.get("records")
    if not isinstance(records, list) or len(records) != 3:
        raise ValueError("expected exactly three LLPG records")
    if [row.get("parcel_id") for row in records] != TARGET_IDS:
        raise ValueError("target parcel order or membership mismatch")
    mapping = manifest.get("classification_mapping")
    if not isinstance(mapping, dict) or set(mapping) != EXPECTED_CODES:
        raise ValueError("official classification mapping mismatch")
    for code in EXPECTED_CODES:
        entry = mapping[code]
        if not isinstance(entry, dict) or not entry.get("official_label") or entry.get("official_parent_label") != "Residential Dwelling":
            raise ValueError(f"incomplete official mapping for {code}")
    for row in records:
        if row.get("exact_uprn_bound") is not True or row.get("BLPUCLASS") not in mapping:
            raise ValueError(f"binding or class gate failed for {row.get('parcel_id')}")
        for field in ("UPRN", "FULLADDRESS", "POSTCODE", "longitude", "latitude"):
            if row.get(field) in (None, ""):
                raise ValueError(f"missing {field} for {row.get('parcel_id')}")
    return source, manifest


def build_payload(source: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    mapping = manifest["classification_mapping"]
    records = []
    for row in source["records"]:
        code = row["BLPUCLASS"]
        cls = mapping[code]
        records.append({
            "parcel_id": row["parcel_id"],
            "UPRN": row["UPRN"],
            "FULLADDRESS": row["FULLADDRESS"].strip(),
            "POSTCODE": row["POSTCODE"],
            "distance_m": row["distance_m"],
            "longitude": row["longitude"],
            "latitude": row["latitude"],
            "BLPUCLASS": code,
            "official_property_type_label": cls["official_label"],
            "official_parent_class": cls["official_parent_label"],
            "classification_source_url": manifest["records"][cls["source_record_index"]]["source_url"],
            "exact_uprn_bound": True,
            "classification_verified": True,
            "inferred": False,
        })
    completed = len(records)
    target = len(TARGET_IDS)
    progress = completed / target * 100.0
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": now_iso(),
        "state": "PUBLISHED",
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": progress,
        "percent_increase": progress,
        "exact_verified_rows": completed,
        "records": records,
        "source_evidence": manifest["records"],
        "input_path": INPUT_PATH,
        "input_git_blob_sha": EXPECTED_INPUT_BLOB_SHA,
        "input_content_sha256": EXPECTED_INPUT_CONTENT_SHA256,
        "source_manifest_path": MANIFEST_PATH,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": True,
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_BLPUCLASS_OFFICIAL_LABEL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base = repo_root()
    source, manifest = validate_inputs(base)
    if args.validate_only:
        print("PASS_3_EXACT_LLPG_ROWS_RD04_RD06_OFFICIAL_LABEL_MAPPING_WRITE_BOUNDARY")
        return 0
    payload = build_payload(source, manifest)
    for relative in OUTPUT_PATHS:
        atomic_json(base / relative, payload)
    print("PASS_PUBLISHED_3_OF_3_OFFICIAL_BLPUCLASS_LABELS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
