from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "parcel_label_2"
TASK_VERSION = "5.1-powershell-carrier"
ATTEMPT_ID = "parcel-label-2-20260721-010"
TARGET_IDS = ["parcel_30762", "parcel_30763", "parcel_30764"]
CANONICAL_FEATURE_COUNT = 92283
EXPECTED_GIT_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
SOURCE_RELATIVE_PATH = Path("england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson")
REQUIRED_TARGET_KEYS = {"row_no", "hmlr_inspire_id", "hmlr_lon", "hmlr_lat"}
ALLOWED_GEOMETRY_TYPES = {"Point", "Polygon", "MultiPolygon"}
ENGLAND_LONGITUDE_RANGE = (-6.5, 2.1)
ENGLAND_LATITUDE_RANGE = (49.8, 56.2)

REPO = Path(os.environ.get("AAYS_REPO_ROOT", Path(__file__).resolve().parents[6])).resolve()
SOURCE_PATH = REPO / SOURCE_RELATIVE_PATH
OUT_ROOT = REPO / "docs/chatgpt_status/parcel_label/slots/parcel_label_2/runner_outputs"
RESULT_PATH = OUT_ROOT / "parcel_label_2_canonical_sample_latest.json"
RECONCILIATION_PATH = OUT_ROOT / "parcel_label_2_canonical_sample_reconciliation_latest.json"
WEB_OUTPUT = REPO / "england_map_web/data/distance_property_types/parcel_label_2_canonical_sample_latest.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def parcel_index(value: object) -> int | None:
    if not isinstance(value, str) or not value.startswith("parcel_"):
        return None
    suffix = value.removeprefix("parcel_")
    return int(suffix) if suffix.isdigit() else None


def normalized_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def normalized_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def compact_properties(props: dict) -> dict:
    keys = [
        "row_no", "matrix_record", "parcel_id", "security_parcel_id",
        "hmlr_row_id", "hmlr_inspire_id", "hmlr_area_m2", "hmlr_lon",
        "hmlr_lat", "hmlr_geometry_accuracy", "london_authority",
        "use6_class_color", "use6_accuracy", "match_method_summary",
    ]
    return {key: props.get(key) for key in keys if key in props}


def validate_features(features: list[dict]) -> tuple[bool, str, dict[str, dict], dict]:
    seen: set[str] = set()
    found: dict[str, dict] = {}
    inspire_ids: set[str] = set()
    minimum_index: int | None = None
    maximum_index: int | None = None

    for feature in features:
        if not isinstance(feature, dict):
            return False, "FEATURE_NOT_OBJECT", {}, {}
        props = feature.get("properties") or {}
        if not isinstance(props, dict):
            return False, "PROPERTIES_NOT_OBJECT", {}, {}
        parcel_id = props.get("parcel_id") or props.get("security_parcel_id")
        index = parcel_index(parcel_id)
        if index is None:
            return False, "NON_CANONICAL_PARCEL_ID_FORMAT", {}, {"parcel_id": parcel_id}
        if index < 1 or index > CANONICAL_FEATURE_COUNT:
            return False, "PARCEL_ID_OUTSIDE_CANONICAL_RANGE", {}, {"parcel_id": parcel_id}
        if parcel_id in seen:
            return False, "DUPLICATE_CANONICAL_PARCEL_ID", {}, {"parcel_id": parcel_id}
        row_no = normalized_integer(props.get("row_no"))
        if row_no != index:
            return False, "ROW_NO_PARCEL_ID_MISMATCH", {}, {
                "parcel_id": parcel_id, "parcel_index": index, "row_no": props.get("row_no")
            }
        seen.add(parcel_id)
        minimum_index = index if minimum_index is None else min(minimum_index, index)
        maximum_index = index if maximum_index is None else max(maximum_index, index)
        if parcel_id in TARGET_IDS:
            found[parcel_id] = feature

    summary = {
        "unique_parcel_id_count": len(seen),
        "minimum_parcel_index": minimum_index,
        "maximum_parcel_index": maximum_index,
        "row_no_parcel_id_alignment_passed": True,
        "target_ids_found": sorted(found),
    }
    if len(seen) != CANONICAL_FEATURE_COUNT:
        return False, "UNIQUE_PARCEL_ID_COUNT_MISMATCH", {}, summary
    if minimum_index != 1 or maximum_index != CANONICAL_FEATURE_COUNT:
        return False, "CANONICAL_PARCEL_ID_RANGE_MISMATCH", {}, summary
    if set(found) != set(TARGET_IDS):
        return False, "TARGET_CANONICAL_IDS_MISSING", {}, summary

    target_summary: dict[str, dict] = {}
    for parcel_id in TARGET_IDS:
        feature = found[parcel_id]
        props = feature.get("properties") or {}
        missing = sorted(key for key in REQUIRED_TARGET_KEYS if key not in props)
        if missing:
            return False, "TARGET_HMLR_SCHEMA_SIGNATURE_MISMATCH", {}, {
                **summary, "parcel_id": parcel_id, "missing_keys": missing
            }
        inspire_id = props.get("hmlr_inspire_id")
        if not isinstance(inspire_id, str) or not inspire_id.strip():
            return False, "TARGET_HMLR_INSPIRE_ID_INVALID", {}, {**summary, "parcel_id": parcel_id}
        if inspire_id in inspire_ids:
            return False, "TARGET_HMLR_INSPIRE_ID_DUPLICATE", {}, {
                **summary, "parcel_id": parcel_id, "hmlr_inspire_id": inspire_id
            }
        inspire_ids.add(inspire_id)
        longitude = normalized_float(props.get("hmlr_lon"))
        latitude = normalized_float(props.get("hmlr_lat"))
        if longitude is None or latitude is None:
            return False, "TARGET_HMLR_COORDINATE_NOT_NUMERIC", {}, {**summary, "parcel_id": parcel_id}
        if not ENGLAND_LONGITUDE_RANGE[0] <= longitude <= ENGLAND_LONGITUDE_RANGE[1]:
            return False, "TARGET_HMLR_LONGITUDE_OUTSIDE_ENGLAND_RANGE", {}, {**summary, "parcel_id": parcel_id}
        if not ENGLAND_LATITUDE_RANGE[0] <= latitude <= ENGLAND_LATITUDE_RANGE[1]:
            return False, "TARGET_HMLR_LATITUDE_OUTSIDE_ENGLAND_RANGE", {}, {**summary, "parcel_id": parcel_id}
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type") if isinstance(geometry, dict) else None
        coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
        if geometry_type not in ALLOWED_GEOMETRY_TYPES or coordinates in (None, [], {}):
            return False, "TARGET_GEOMETRY_PAYLOAD_INVALID", {}, {
                **summary, "parcel_id": parcel_id, "geometry_type": geometry_type
            }
        target_summary[parcel_id] = {
            "row_no": normalized_integer(props.get("row_no")),
            "hmlr_inspire_id": inspire_id,
            "hmlr_lon": longitude,
            "hmlr_lat": latitude,
            "geometry_type": geometry_type,
        }

    summary.update({
        "target_schema_signature_passed": True,
        "target_hmlr_inspire_ids_unique": True,
        "target_coordinate_plausibility_passed": True,
        "target_geometry_payload_gate_passed": True,
        "target_summary": target_summary,
    })
    return True, "ACCEPTED", found, summary


def main() -> int:
    observed_blob_sha = None
    feature_count = None
    source_error = None
    accepted = False
    acceptance_reason = "SOURCE_NOT_READ"
    found: dict[str, dict] = {}
    identity_summary: dict = {}

    try:
        source_bytes = SOURCE_PATH.read_bytes()
        observed_blob_sha = git_blob_sha(source_bytes)
        if observed_blob_sha != EXPECTED_GIT_BLOB_SHA:
            acceptance_reason = "CANONICAL_GIT_BLOB_SHA_MISMATCH"
        else:
            payload = json.loads(source_bytes.decode("utf-8-sig"))
            features = payload.get("features") if isinstance(payload, dict) else None
            if not isinstance(features, list):
                acceptance_reason = "CANONICAL_FEATURE_ARRAY_MISSING"
            else:
                feature_count = len(features)
                if feature_count != CANONICAL_FEATURE_COUNT:
                    acceptance_reason = "CANONICAL_FEATURE_COUNT_MISMATCH"
                else:
                    accepted, acceptance_reason, found, identity_summary = validate_features(features)
    except Exception as exc:
        source_error = str(exc)
        acceptance_reason = "CANONICAL_SOURCE_READ_FAILED"

    rows = []
    polygon_rows = 0
    for parcel_id in TARGET_IDS:
        feature = found.get(parcel_id)
        if not feature:
            rows.append({
                "parcel_id": parcel_id,
                "candidate_status": "CANONICAL_FEATURE_NOT_ACCEPTED",
                "geometry_type": None,
                "accuracy_score_4": 0,
                "needs_manual_review": True,
                "source_candidate_binding": "NOT_PERFORMED",
            })
            continue
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type")
        if geometry_type in {"Polygon", "MultiPolygon"}:
            polygon_rows += 1
        rows.append({
            "parcel_id": parcel_id,
            "candidate_status": (
                "CANONICAL_POLYGON_CARRIER_FOUND_SOURCE_BINDING_PENDING"
                if geometry_type in {"Polygon", "MultiPolygon"}
                else "CANONICAL_POINT_CARRIER_FOUND_EXACT_GEOMETRY_PENDING"
            ),
            "source_file": str(SOURCE_RELATIVE_PATH).replace("\\", "/"),
            "source_git_blob_sha": observed_blob_sha,
            "geometry_type": geometry_type,
            "geometry": geometry,
            "properties": compact_properties(feature.get("properties") or {}),
            "accuracy_score_4": 0,
            "carrier_validation_passed": True,
            "needs_manual_review": True,
            "source_candidate_binding": "NOT_PERFORMED_NO_EXACT_IDENTITY_OR_SPATIAL_PROOF",
        })

    carrier_rows = len(found)
    output = {
        "schema_version": 5,
        "slot_id": SLOT_ID,
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "generated_at": utc_now(),
        "parcel_partition": {"start": 30762, "end": 61522, "count": 30761},
        "target_ids": TARGET_IDS,
        "canonical_source": str(SOURCE_RELATIVE_PATH).replace("\\", "/"),
        "required_git_blob_sha": EXPECTED_GIT_BLOB_SHA,
        "observed_git_blob_sha": observed_blob_sha,
        "git_blob_gate_passed": observed_blob_sha == EXPECTED_GIT_BLOB_SHA,
        "required_feature_count": CANONICAL_FEATURE_COUNT,
        "observed_feature_count": feature_count,
        "strict_carrier_acceptance_passed": accepted,
        "acceptance_reason": acceptance_reason,
        "source_error": source_error,
        "identity_summary": identity_summary,
        "canonical_carrier_rows_found": carrier_rows,
        "polygon_or_multipolygon_rows_found": polygon_rows,
        "rows": rows,
        "actual_verified_slot_rows_written": 0,
        "binding_rule": "SOURCE_* candidates remain noncanonical until independent exact identity or spatial proof binds them to exact parcel geometry.",
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    reconciliation = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "required_git_blob_sha": EXPECTED_GIT_BLOB_SHA,
        "observed_git_blob_sha": observed_blob_sha,
        "git_blob_gate_passed": output["git_blob_gate_passed"],
        "strict_carrier_acceptance_passed": accepted,
        "acceptance_reason": acceptance_reason,
        "expected_target_rows": len(TARGET_IDS),
        "canonical_carrier_rows_found": carrier_rows,
        "unique_target_rows_found": len(set(found)),
        "polygon_or_multipolygon_rows_found": polygon_rows,
        "actual_verified_slot_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for path in (RESULT_PATH, WEB_OUTPUT):
        write_json(path, output)
    write_json(RECONCILIATION_PATH, reconciliation)

    print(f"SLOT_ID={SLOT_ID}")
    print(f"TASK_VERSION={TASK_VERSION}")
    print(f"ATTEMPT_ID={ATTEMPT_ID}")
    print(f"OBSERVED_GIT_BLOB_SHA={observed_blob_sha}")
    print(f"STRICT_CARRIER_ACCEPTANCE_PASSED={str(accepted).lower()}")
    print(f"CANONICAL_CARRIER_ROWS_FOUND={carrier_rows}")
    print("ACTUAL_VERIFIED_SLOT_ROWS_WRITTEN=0")
    print("FINAL_READY=false")
    return 0 if accepted and carrier_rows == len(TARGET_IDS) else 2


if __name__ == "__main__":
    raise SystemExit(main())
