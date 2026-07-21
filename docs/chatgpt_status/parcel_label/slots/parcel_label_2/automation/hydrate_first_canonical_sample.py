from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "parcel_label_2"
TARGET_IDS = ["parcel_30762", "parcel_30763", "parcel_30764"]
REPO = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
DATA_ROOT = REPO / "england_map_web" / "data"
SLOT_ROOT = REPO / "docs" / "chatgpt_status" / "parcel_label" / "slots" / SLOT_ID
OUT_ROOT = SLOT_ROOT / "runner_outputs"
WEB_OUTPUT = DATA_ROOT / "distance_property_types" / "parcel_label_2_canonical_sample_latest.json"
CANDIDATE_PATH = DATA_ROOT / "distance_property_types" / "parcel_label_2_candidates.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def locate_targets() -> tuple[Path | None, dict[str, dict]]:
    found: dict[str, dict] = {}
    candidates = sorted(
        [p for p in DATA_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".geojson"}],
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    for path in candidates:
        if path in {WEB_OUTPUT, CANDIDATE_PATH}:
            continue
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                payload = json.load(handle)
        except Exception:
            continue
        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list):
            continue
        for feature in features:
            props = feature.get("properties") or {}
            parcel_id = props.get("parcel_id") or props.get("security_parcel_id")
            if parcel_id in TARGET_IDS:
                found[parcel_id] = feature
        if len(found) == len(TARGET_IDS):
            return path, found
    return None, found


def compact_properties(props: dict) -> dict:
    keys = [
        "row_no",
        "matrix_record",
        "parcel_id",
        "hmlr_row_id",
        "hmlr_inspire_id",
        "hmlr_area_m2",
        "hmlr_lon",
        "hmlr_lat",
        "hmlr_geometry_accuracy",
        "london_authority",
        "use6_class_color",
        "use6_accuracy",
        "match_method_summary",
    ]
    return {key: props.get(key) for key in keys if key in props}


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    WEB_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    source_path, features = locate_targets()
    rows = []
    polygon_rows = 0
    carrier_rows = 0

    for parcel_id in TARGET_IDS:
        feature = features.get(parcel_id)
        if not feature:
            rows.append(
                {
                    "parcel_id": parcel_id,
                    "candidate_status": "CANONICAL_FEATURE_NOT_FOUND",
                    "accuracy_score_4": 0,
                    "needs_manual_review": True,
                    "next_gate": "restore or expose the canonical 92,283-row carrier",
                }
            )
            continue

        carrier_rows += 1
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type")
        is_polygon = geometry_type in {"Polygon", "MultiPolygon"}
        if is_polygon:
            polygon_rows += 1
        rows.append(
            {
                "parcel_id": parcel_id,
                "candidate_status": (
                    "CANONICAL_POLYGON_CARRIER_FOUND_SOURCE_BINDING_PENDING"
                    if is_polygon
                    else "CANONICAL_POINT_CARRIER_FOUND_EXACT_GEOMETRY_PENDING"
                ),
                "source_file": str(source_path) if source_path else None,
                "geometry_type": geometry_type,
                "geometry": geometry,
                "properties": compact_properties(feature.get("properties") or {}),
                "accuracy_score_4": 3 if is_polygon else 2,
                "needs_manual_review": True,
                "source_candidate_binding": "NOT_PERFORMED_NO_SPATIAL_OR_IDENTITY_PROOF",
            }
        )

    output = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "parcel_partition": {"start": 30762, "end": 61522, "count": 30761},
        "target_ids": TARGET_IDS,
        "source_file": str(source_path) if source_path else None,
        "source_file_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path else None,
        "canonical_carrier_rows_found": carrier_rows,
        "polygon_or_multipolygon_rows_found": polygon_rows,
        "source_research_candidates_available": CANDIDATE_PATH.exists(),
        "rows": rows,
        "actual_verified_slot_rows_written": 0,
        "binding_rule": "Never bind SOURCE_* research candidates to canonical parcel IDs without exact identity or spatial evidence.",
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    text = json.dumps(output, ensure_ascii=False, indent=2)
    result_path = OUT_ROOT / "parcel_label_2_canonical_sample_latest.json"
    result_path.write_text(text, encoding="utf-8")
    WEB_OUTPUT.write_text(text, encoding="utf-8")
    print(f"SLOT_ID={SLOT_ID}")
    print(f"SOURCE_FILE={source_path}")
    print(f"CANONICAL_CARRIER_ROWS_FOUND={carrier_rows}")
    print(f"POLYGON_ROWS_FOUND={polygon_rows}")
    print("ACTUAL_VERIFIED_SLOT_ROWS_WRITTEN=0")
    print("FINAL_READY=false")
    return 0 if carrier_rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
