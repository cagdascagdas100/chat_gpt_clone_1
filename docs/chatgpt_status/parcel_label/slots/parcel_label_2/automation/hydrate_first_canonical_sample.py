from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "parcel_label_2"
TARGET_IDS = ["parcel_30762", "parcel_30763", "parcel_30764"]
CANONICAL_FEATURE_COUNT = 92283
REQUIRED_TARGET_SCHEMA_KEYS = {"row_no", "hmlr_inspire_id", "hmlr_lon", "hmlr_lat"}
ALLOWED_GEOMETRY_TYPES = {"Point", "Polygon", "MultiPolygon"}
ENGLAND_LONGITUDE_RANGE = (-6.5, 2.1)
ENGLAND_LATITUDE_RANGE = (49.8, 56.2)
REPO = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
DATA_ROOT = REPO / "england_map_web" / "data"
SLOT_ROOT = REPO / "docs" / "chatgpt_status" / "parcel_label" / "slots" / SLOT_ID
OUT_ROOT = SLOT_ROOT / "runner_outputs"
WEB_OUTPUT = DATA_ROOT / "distance_property_types" / "parcel_label_2_canonical_sample_latest.json"
CANDIDATE_PATH = DATA_ROOT / "distance_property_types" / "parcel_label_2_candidates.json"
PRIORITY_CARRIERS = [
    DATA_ROOT / "program_layer_matrix" / "security.geojson",
    DATA_ROOT / "security.geojson",
    DATA_ROOT / "parcel_security_scores_rechecked_0_120m_spatial.geojson",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_carrier_paths() -> list[Path]:
    priority = [path for path in PRIORITY_CARRIERS if path.is_file()]
    priority_set = set(priority)
    excluded = {WEB_OUTPUT, CANDIDATE_PATH}
    fallback = sorted(
        [
            path
            for path in DATA_ROOT.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".json", ".geojson"}
            and path not in excluded
            and path not in priority_set
        ],
        key=lambda path: path.stat().st_size,
        reverse=True,
    )
    return priority + fallback


def candidate_inventory_fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        stat = path.stat()
        try:
            relative = path.relative_to(DATA_ROOT).as_posix()
        except ValueError:
            relative = f"runtime-cache/{path.name}"
        digest.update(f"{relative}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode("utf-8"))
    return digest.hexdigest()


def unchanged_negative_inventory(fingerprint: str) -> bool:
    result_path = OUT_ROOT / "parcel_label_2_canonical_sample_latest.json"
    try:
        previous = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return False
    return (
        isinstance(previous, dict)
        and previous.get("source_file") is None
        and previous.get("candidate_inventory_fingerprint") == fingerprint
    )


def parcel_index(parcel_id: object) -> int | None:
    if not isinstance(parcel_id, str) or not parcel_id.startswith("parcel_"):
        return None
    suffix = parcel_id.removeprefix("parcel_")
    if not suffix.isdigit():
        return None
    return int(suffix)


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


def validate_identity_carrier(features: list[dict]) -> tuple[bool, str, dict[str, dict], dict]:
    seen_ids: set[str] = set()
    found: dict[str, dict] = {}
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
        if parcel_id in seen_ids:
            return False, "DUPLICATE_CANONICAL_PARCEL_ID", {}, {"parcel_id": parcel_id}

        row_no = normalized_integer(props.get("row_no"))
        if row_no != index:
            return False, "ROW_NO_PARCEL_ID_MISMATCH", {}, {
                "parcel_id": parcel_id,
                "parcel_index": index,
                "row_no": props.get("row_no"),
            }

        seen_ids.add(parcel_id)
        minimum_index = index if minimum_index is None else min(minimum_index, index)
        maximum_index = index if maximum_index is None else max(maximum_index, index)
        if parcel_id in TARGET_IDS:
            found[parcel_id] = feature

    identity_summary = {
        "unique_parcel_id_count": len(seen_ids),
        "minimum_parcel_index": minimum_index,
        "maximum_parcel_index": maximum_index,
        "row_no_parcel_id_alignment_passed": True,
        "target_ids_found": sorted(found),
    }
    if len(seen_ids) != CANONICAL_FEATURE_COUNT:
        return False, "UNIQUE_PARCEL_ID_COUNT_MISMATCH", {}, identity_summary
    if minimum_index != 1 or maximum_index != CANONICAL_FEATURE_COUNT:
        return False, "CANONICAL_PARCEL_ID_RANGE_MISMATCH", {}, identity_summary
    if set(found) != set(TARGET_IDS):
        return False, "TARGET_CANONICAL_IDS_MISSING", {}, identity_summary

    schema_missing: dict[str, list[str]] = {}
    target_coordinate_summary: dict[str, dict] = {}
    target_inspire_ids: set[str] = set()
    for parcel_id, feature in found.items():
        props = feature.get("properties") or {}
        missing = sorted(key for key in REQUIRED_TARGET_SCHEMA_KEYS if key not in props)
        if missing:
            schema_missing[parcel_id] = missing
            continue

        inspire_id = props.get("hmlr_inspire_id")
        if not isinstance(inspire_id, str) or not inspire_id.strip():
            return False, "TARGET_HMLR_INSPIRE_ID_INVALID", {}, {
                **identity_summary,
                "parcel_id": parcel_id,
                "hmlr_inspire_id": inspire_id,
            }
        if inspire_id in target_inspire_ids:
            return False, "TARGET_HMLR_INSPIRE_ID_DUPLICATE", {}, {
                **identity_summary,
                "parcel_id": parcel_id,
                "hmlr_inspire_id": inspire_id,
            }
        target_inspire_ids.add(inspire_id)

        longitude = normalized_float(props.get("hmlr_lon"))
        latitude = normalized_float(props.get("hmlr_lat"))
        if longitude is None or latitude is None:
            return False, "TARGET_HMLR_COORDINATE_NOT_NUMERIC", {}, {
                **identity_summary,
                "parcel_id": parcel_id,
                "hmlr_lon": props.get("hmlr_lon"),
                "hmlr_lat": props.get("hmlr_lat"),
            }
        if not (ENGLAND_LONGITUDE_RANGE[0] <= longitude <= ENGLAND_LONGITUDE_RANGE[1]):
            return False, "TARGET_HMLR_LONGITUDE_OUTSIDE_ENGLAND_RANGE", {}, {
                **identity_summary,
                "parcel_id": parcel_id,
                "hmlr_lon": longitude,
            }
        if not (ENGLAND_LATITUDE_RANGE[0] <= latitude <= ENGLAND_LATITUDE_RANGE[1]):
            return False, "TARGET_HMLR_LATITUDE_OUTSIDE_ENGLAND_RANGE", {}, {
                **identity_summary,
                "parcel_id": parcel_id,
                "hmlr_lat": latitude,
            }

        geometry = feature.get("geometry")
        geometry_type = geometry.get("type") if isinstance(geometry, dict) else None
        if geometry_type not in ALLOWED_GEOMETRY_TYPES:
            return False, "TARGET_GEOMETRY_TYPE_INVALID", {}, {
                **identity_summary,
                "parcel_id": parcel_id,
                "geometry_type": geometry_type,
            }

        target_coordinate_summary[parcel_id] = {
            "hmlr_lon": longitude,
            "hmlr_lat": latitude,
            "geometry_type": geometry_type,
        }

    if schema_missing:
        identity_summary["target_schema_missing"] = schema_missing
        return False, "TARGET_HMLR_SCHEMA_SIGNATURE_MISMATCH", {}, identity_summary

    identity_summary["target_schema_signature_passed"] = True
    identity_summary["target_hmlr_inspire_ids_unique"] = True
    identity_summary["target_coordinate_plausibility_passed"] = True
    identity_summary["target_geometry_type_gate_passed"] = True
    identity_summary["target_coordinate_summary"] = target_coordinate_summary
    return True, "ACCEPTED", found, identity_summary


def locate_targets() -> tuple[
    Path | None,
    dict[str, dict],
    int,
    int | None,
    list[dict],
    dict,
    str,
    int,
    bool,
]:
    candidate_paths = candidate_carrier_paths()
    inventory_fingerprint = candidate_inventory_fingerprint(candidate_paths)
    if unchanged_negative_inventory(inventory_fingerprint):
        return (
            None,
            {},
            0,
            None,
            [],
            {},
            inventory_fingerprint,
            len(candidate_paths),
            True,
        )

    scanned_files = 0
    rejected_carriers: list[dict] = []
    for path in candidate_paths:
        scanned_files += 1
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                payload = json.load(handle)
        except Exception as exc:
            if len(rejected_carriers) < 25:
                rejected_carriers.append(
                    {"path": str(path), "reason": "JSON_READ_FAILED", "error": str(exc)[:240]}
                )
            continue

        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list):
            continue

        feature_count = len(features)
        if feature_count != CANONICAL_FEATURE_COUNT:
            if len(rejected_carriers) < 25:
                rejected_carriers.append(
                    {
                        "path": str(path),
                        "reason": "FEATURE_COUNT_MISMATCH",
                        "feature_count": feature_count,
                        "expected_feature_count": CANONICAL_FEATURE_COUNT,
                    }
                )
            continue

        accepted, reason, found, identity_summary = validate_identity_carrier(features)
        if not accepted:
            if len(rejected_carriers) < 25:
                rejected_carriers.append(
                    {
                        "path": str(path),
                        "reason": reason,
                        "feature_count": feature_count,
                        "identity_summary": identity_summary,
                    }
                )
            continue
        return (
            path,
            found,
            scanned_files,
            feature_count,
            rejected_carriers,
            identity_summary,
            inventory_fingerprint,
            len(candidate_paths),
            False,
        )

    return (
        None,
        {},
        scanned_files,
        None,
        rejected_carriers,
        {},
        inventory_fingerprint,
        len(candidate_paths),
        False,
    )


def compact_properties(props: dict) -> dict:
    keys = [
        "row_no",
        "matrix_record",
        "parcel_id",
        "security_parcel_id",
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
    (
        source_path,
        features,
        scanned_files,
        source_feature_count,
        rejected_carriers,
        identity_summary,
        inventory_fingerprint,
        candidate_inventory_count,
        negative_inventory_cache_hit,
    ) = locate_targets()
    rows = []
    polygon_rows = 0
    carrier_rows = 0

    for parcel_id in TARGET_IDS:
        feature = features.get(parcel_id)
        if not feature:
            rows.append(
                {
                    "parcel_id": parcel_id,
                    "candidate_status": "CANONICAL_FEATURE_NOT_FOUND_IN_STRICTLY_VALIDATED_92283_FEATURE_CARRIER",
                    "accuracy_score_4": 0,
                    "needs_manual_review": True,
                    "next_gate": "restore or expose a strictly identity-proven canonical 92,283-feature carrier",
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
                    "STRICTLY_VALIDATED_CANONICAL_POLYGON_CARRIER_FOUND_SOURCE_BINDING_PENDING"
                    if is_polygon
                    else "STRICTLY_VALIDATED_CANONICAL_POINT_CARRIER_FOUND_EXACT_GEOMETRY_PENDING"
                ),
                "source_file": str(source_path) if source_path else None,
                "source_feature_count": source_feature_count,
                "geometry_type": geometry_type,
                "geometry": geometry,
                "properties": compact_properties(feature.get("properties") or {}),
                "accuracy_score_4": 3 if is_polygon else 2,
                "needs_manual_review": True,
                "source_candidate_binding": "NOT_PERFORMED_NO_SPATIAL_OR_IDENTITY_PROOF",
            }
        )

    exact_count_gate_passed = source_feature_count == CANONICAL_FEATURE_COUNT
    strict_identity_gate_passed = bool(identity_summary.get("target_coordinate_plausibility_passed"))
    output = {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "parcel_partition": {"start": 30762, "end": 61522, "count": 30761},
        "target_ids": TARGET_IDS,
        "required_canonical_feature_count": CANONICAL_FEATURE_COUNT,
        "required_target_schema_keys": sorted(REQUIRED_TARGET_SCHEMA_KEYS),
        "required_row_no_parcel_id_alignment": True,
        "required_target_coordinate_ranges": {
            "longitude": list(ENGLAND_LONGITUDE_RANGE),
            "latitude": list(ENGLAND_LATITUDE_RANGE),
        },
        "required_target_geometry_types": sorted(ALLOWED_GEOMETRY_TYPES),
        "exact_feature_count_gate_passed": exact_count_gate_passed,
        "strict_identity_schema_coordinate_gate_passed": strict_identity_gate_passed,
        "identity_summary": identity_summary,
        "priority_carriers": [str(path) for path in PRIORITY_CARRIERS],
        "candidate_inventory_count": candidate_inventory_count,
        "candidate_inventory_fingerprint": inventory_fingerprint,
        "negative_inventory_cache_hit": negative_inventory_cache_hit,
        "scanned_file_count": scanned_files,
        "rejected_carrier_sample": rejected_carriers,
        "source_file": str(source_path) if source_path else None,
        "source_feature_count": source_feature_count,
        "source_file_sha256": file_sha256(source_path) if source_path else None,
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
    print(f"SCANNED_FILE_COUNT={scanned_files}")
    print(f"CANDIDATE_INVENTORY_COUNT={candidate_inventory_count}")
    print(f"NEGATIVE_INVENTORY_CACHE_HIT={str(negative_inventory_cache_hit).lower()}")
    print(f"SOURCE_FILE={source_path}")
    print(f"SOURCE_FEATURE_COUNT={source_feature_count}")
    print(f"EXACT_FEATURE_COUNT_GATE_PASSED={str(exact_count_gate_passed).lower()}")
    print(f"STRICT_IDENTITY_SCHEMA_COORDINATE_GATE_PASSED={str(strict_identity_gate_passed).lower()}")
    print(f"CANONICAL_CARRIER_ROWS_FOUND={carrier_rows}")
    print(f"POLYGON_ROWS_FOUND={polygon_rows}")
    print("ACTUAL_VERIFIED_SLOT_ROWS_WRITTEN=0")
    print("FINAL_READY=false")
    return 0 if carrier_rows and exact_count_gate_passed and strict_identity_gate_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
