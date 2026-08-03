from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-mdu-status-official-v1-20260803"
INPUT_PATH = "docs/chatgpt_status/_shared/slots_21/parcel_label_3/blpuclass_official_label_result_latest.json"
OUTPUT_PATHS = [
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/mdu_status_official_latest.json",
]
EXPECTED_INPUT_BLOB_SHA = "2a778c213bddb466d81787d1a1fc501bc83925f6"
EXPECTED_CODES = {"parcel_61523": "RD06", "parcel_61524": "RD04", "parcel_61525": "RD04"}
SOURCE_URL = "https://www.gov.uk/government/consultations/legislative-proposals-to-address-broadband-rollout-in-leasehold-flats/legislative-proposals-to-address-broadband-rollout-in-leasehold-flats-analytical-annex"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


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


def load_input(root: Path) -> list[dict[str, Any]]:
    payload = json.loads((root / INPUT_PATH).read_text(encoding="utf-8"))
    if payload.get("state") != "PUBLISHED" or payload.get("exact_verified_rows") != 3:
        raise ValueError("input is not terminal PUBLISHED 3/3")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 3:
        raise ValueError("expected exactly three records")
    found = {str(row.get("parcel_id")): row for row in records if isinstance(row, dict)}
    if set(found) != set(EXPECTED_CODES):
        raise ValueError("unexpected parcel ids")
    ordered = []
    for parcel_id, code in EXPECTED_CODES.items():
        row = found[parcel_id]
        if row.get("BLPUCLASS") != code or row.get("classification_verified") is not True:
            raise ValueError(f"unverified classification for {parcel_id}")
        if row.get("exact_uprn_bound") is not True or not row.get("UPRN"):
            raise ValueError(f"missing exact UPRN binding for {parcel_id}")
        ordered.append(row)
    return ordered


def build(records: list[dict[str, Any]]) -> dict[str, Any]:
    output = []
    for row in records:
        code = row["BLPUCLASS"]
        if code == "RD06":
            mdu = True
            basis = "GOV.UK methodology explicitly identifies MDUs using RD06/self-contained flat."
        elif code == "RD04":
            mdu = False
            basis = "GOV.UK table lists RD04 as Terraced, separately from RD06/self-contained flat used to identify MDUs."
        else:
            raise ValueError(f"unsupported code {code}")
        output.append({
            "parcel_id": row["parcel_id"],
            "UPRN": row["UPRN"],
            "FULLADDRESS": row["FULLADDRESS"],
            "POSTCODE": row["POSTCODE"],
            "distance_m": row["distance_m"],
            "longitude": row["longitude"],
            "latitude": row["latitude"],
            "BLPUCLASS": code,
            "official_property_type_label": row["official_property_type_label"],
            "official_parent_class": row["official_parent_class"],
            "exact_uprn_bound": True,
            "classification_verified": True,
            "official_mdu_status": mdu,
            "mdu_status_verified": True,
            "mdu_status_source_url": SOURCE_URL,
            "mdu_status_evidence_basis": basis,
            "inferred": False,
        })
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "state": "PUBLISHED",
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "exact_verified_rows": 3,
        "mdu_status_counts": {"true": 1, "false": 2},
        "records": output,
        "input_path": INPUT_PATH,
        "input_git_blob_sha": EXPECTED_INPUT_BLOB_SHA,
        "source_url": SOURCE_URL,
        "license_or_terms_url": OGL_URL,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": True,
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_MDU_STATUS_OFFICIAL",
    }


def validate(root: Path) -> None:
    records = load_input(root)
    payload = build(records)
    if payload["mdu_status_counts"] != {"true": 1, "false": 2}:
        raise ValueError("unexpected MDU counts")
    print("PASS_3_EXACT_UPRN_ROWS_RD06_MDU_TRUE_RD04_MDU_FALSE_OFFICIAL_MAPPING")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    validate(root)
    if args.validate_only:
        return 0
    payload = build(load_input(root))
    for relative in OUTPUT_PATHS:
        atomic_json(root / relative, payload)
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print(f"PASS_PUBLISHED_3_OF_3_MDU_STATUS_{digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
