from __future__ import annotations

import importlib.util
import json
import mmap
import os
import re
from pathlib import Path
from collections.abc import Iterable

BASE_PATH = Path(__file__).with_name("stream_inspire_payload_v1.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_streaming_v1", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_STREAMING_V1_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

_PARCEL_ID = re.compile(r"parcel_([1-9][0-9]*)\Z")


def _parcel_number(parcel_id: object, expected_feature_count: int) -> int:
    if not isinstance(parcel_id, str):
        raise RuntimeError("CANONICAL_PARCEL_ID_NOT_STRING")
    match = _PARCEL_ID.fullmatch(parcel_id)
    if match is None:
        raise RuntimeError(f"CANONICAL_PARCEL_ID_INVALID:{parcel_id}")
    number = int(match.group(1))
    if number < 1 or number > expected_feature_count:
        raise RuntimeError(f"CANONICAL_PARCEL_ID_OUT_OF_RANGE:{parcel_id}")
    return number


def _row_number(value: object, parcel_id: str) -> int:
    if isinstance(value, bool):
        raise RuntimeError(f"ROW_NO_INVALID:{parcel_id}")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"ROW_NO_INVALID:{parcel_id}") from exc
    return number


def canonical_targets(
    path: Path,
    *,
    expected_blob_sha: str,
    expected_feature_count: int,
    target_ids: Iterable[str],
) -> tuple[dict[str, dict], dict]:
    observed = previous.git_blob_sha1(path)
    if observed != expected_blob_sha:
        raise RuntimeError(f"CANONICAL_BLOB_MISMATCH:{observed}")
    if expected_feature_count < 1:
        raise RuntimeError("CANONICAL_EXPECTED_FEATURE_COUNT_INVALID")

    target_tuple = tuple(target_ids)
    wanted = set(target_tuple)
    if len(wanted) != len(target_tuple):
        raise RuntimeError("TARGET_ID_INPUT_DUPLICATE")
    wanted_numbers = {_parcel_number(parcel_id, expected_feature_count): parcel_id for parcel_id in wanted}
    if len(wanted_numbers) != len(wanted):
        raise RuntimeError("TARGET_ID_NUMERIC_DUPLICATE")

    rows: dict[str, dict] = {}
    target_inspire_ids: set[str] = set()
    seen = bytearray(expected_feature_count + 1)
    feature_count = 0
    maximum_feature_bytes = 0

    fd = os.open(path, os.O_RDONLY)
    try:
        mapped = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        try:
            cursor = previous._locate_features_array(mapped)
            while True:
                while cursor < len(mapped) and mapped[cursor] in b" \t\r\n,":
                    cursor += 1
                if cursor >= len(mapped):
                    raise RuntimeError("CANONICAL_FEATURES_ARRAY_UNTERMINATED")
                if mapped[cursor] == ord("]"):
                    break
                if mapped[cursor] != ord("{"):
                    raise RuntimeError(f"CANONICAL_FEATURE_OBJECT_EXPECTED_AT:{cursor}")
                end = previous._scan_json_object(mapped, cursor)
                raw = mapped[cursor:end]
                maximum_feature_bytes = max(maximum_feature_bytes, len(raw))
                try:
                    feature = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"CANONICAL_FEATURE_JSON_INVALID:{feature_count + 1}:{exc.msg}") from exc
                if not isinstance(feature, dict):
                    raise RuntimeError(f"CANONICAL_FEATURE_NOT_OBJECT:{feature_count + 1}")
                properties = feature.get("properties")
                if not isinstance(properties, dict):
                    raise RuntimeError(f"CANONICAL_PROPERTIES_NOT_OBJECT:{feature_count + 1}")
                parcel_id = properties.get("parcel_id") or properties.get("security_parcel_id")
                number = _parcel_number(parcel_id, expected_feature_count)
                if seen[number]:
                    raise RuntimeError(f"CANONICAL_PARCEL_ID_DUPLICATE:{parcel_id}")
                seen[number] = 1
                feature_count += 1

                row_no = _row_number(properties.get("row_no"), parcel_id)
                if row_no != number:
                    raise RuntimeError(f"ROW_NO_MISMATCH:{parcel_id}")

                if number in wanted_numbers:
                    expected_id = wanted_numbers[number]
                    if parcel_id != expected_id:
                        raise RuntimeError(f"TARGET_ID_CANONICAL_FORM_MISMATCH:{parcel_id}:{expected_id}")
                    inspire_id = str(properties.get("hmlr_inspire_id") or "").strip()
                    if not inspire_id.isdigit() or inspire_id in target_inspire_ids:
                        raise RuntimeError(f"INSPIRE_ID_INVALID_OR_DUPLICATE:{parcel_id}")
                    target_inspire_ids.add(inspire_id)
                    rows[parcel_id] = {
                        "parcel_id": parcel_id,
                        "row_no": row_no,
                        "hmlr_inspire_id": inspire_id,
                        "hmlr_lon": properties.get("hmlr_lon"),
                        "hmlr_lat": properties.get("hmlr_lat"),
                        "hmlr_area_m2": properties.get("hmlr_area_m2"),
                        "london_authority": properties.get("london_authority"),
                    }
                cursor = end
        finally:
            mapped.close()
    finally:
        os.close(fd)

    if feature_count != expected_feature_count:
        raise RuntimeError(f"CANONICAL_FEATURE_COUNT_MISMATCH:{feature_count}")
    seen_count = sum(seen)
    if seen_count != expected_feature_count:
        raise RuntimeError(f"CANONICAL_UNIQUE_PARCEL_COUNT_MISMATCH:{seen_count}")
    if set(rows) != wanted:
        raise RuntimeError(f"TARGETS_MISSING:{sorted(wanted - set(rows))}")

    return rows, {
        "observed_git_blob_sha": observed,
        "feature_count": feature_count,
        "unique_parcel_id_count": seen_count,
        "parcel_id_min": 1,
        "parcel_id_max": expected_feature_count,
        "parcel_id_span_complete": True,
        "all_row_numbers_aligned": True,
        "target_count": len(rows),
        "unique_inspire_id_count": len(target_inspire_ids),
        "canonical_streaming_mmap": True,
        "canonical_full_inventory_bitset": True,
        "maximum_feature_object_bytes": maximum_feature_bytes,
    }
