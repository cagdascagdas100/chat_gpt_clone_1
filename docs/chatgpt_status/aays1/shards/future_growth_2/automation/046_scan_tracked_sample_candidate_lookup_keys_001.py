#!/usr/bin/env python3
"""Bounded repository scan for explicit lookup keys on three tracked sample candidates.

No linkage is inferred. A lookup key is accepted only when the same JSON object
contains a direct candidate identity field, or when a non-JSON text line contains
the exact row/parcel token and an explicit allow-listed key/value pair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

CANDIDATES = {30762: "parcel_30762", 46142: "parcel_46142", 61522: "parcel_61522"}
TEXT_EXTENSIONS = {".json", ".jsonl", ".csv", ".tsv", ".txt", ".md", ".yaml", ".yml"}
MAX_FILE_BYTES = 8_000_000
MAX_OCCURRENCES_PER_CANDIDATE = 250
EXCLUDED_PREFIXES = (".git/", ".github/workflows/")
EXCLUDED_BASENAMES = {"046_scan_tracked_sample_candidate_lookup_keys_001.py"}
ROW_KEYS = {"row_no", "row", "row_number", "source_row", "parcel_row"}
PARCEL_KEYS = {"parcel_id", "parcel"}
ALLOWED_CHILD_KEYS = {
    "identity", "lookup", "location", "address", "property", "site",
    "parcel_identity", "position", "point", "centroid", "spatial"
}
KEY_ALIASES = {
    "uprn": "uprn",
    "unique_property_reference_number": "uprn",
    "uniquepropertyreferencenumber": "uprn",
    "title_number": "title_number",
    "title-number": "title_number",
    "title_no": "title_number",
    "titlenumber": "title_number",
    "postcode": "postcode",
    "post_code": "postcode",
    "postal_code": "postcode",
    "address": "address",
    "full_address": "address",
    "property_address": "address",
    "formatted_address": "address",
    "address_line_1": "address",
    "address1": "address",
    "latitude": "latitude",
    "lat": "latitude",
    "longitude": "longitude",
    "lon": "longitude",
    "lng": "longitude",
    "easting": "easting",
    "northing": "northing",
    "x": "x",
    "y": "y",
    "coordinates": "coordinates",
    "geometry": "geometry",
}
LOOKUP_CATEGORIES = set(KEY_ALIASES.values())


def _normalise_key(key: Any) -> str:
    return str(key).strip().lower().replace(" ", "_")


def _direct_identity_match(obj: dict[str, Any], row_no: int, parcel_id: str) -> bool:
    for key, value in obj.items():
        nk = _normalise_key(key)
        if nk in ROW_KEYS and not isinstance(value, (dict, list, bool)) and str(value).strip() == str(row_no):
            return True
        if nk in PARCEL_KEYS and not isinstance(value, (dict, list, bool)) and str(value).strip() == parcel_id:
            return True
    return False


def _bounded_value(category: str, value: Any) -> Any | None:
    if value is None or isinstance(value, bool):
        return None
    if category in {"geometry", "coordinates"}:
        if not isinstance(value, (dict, list)):
            return None
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        if not raw or raw in {b"{}", b"[]", b"null"}:
            return None
        return {"present": True, "sha256": hashlib.sha256(raw).hexdigest(), "byte_count": len(raw)}
    if isinstance(value, (str, int, float)):
        text = str(value).strip()
        if not text or len(text) > 240:
            return None
        return value
    return None


def _collect_from_mapping(obj: dict[str, Any], *, include_allowed_children: bool) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    for key, value in obj.items():
        nk = _normalise_key(key)
        category = KEY_ALIASES.get(nk)
        if category:
            bounded = _bounded_value(category, value)
            if bounded is not None:
                result.setdefault(category, []).append(bounded)
        if include_allowed_children and nk in ALLOWED_CHILD_KEYS and isinstance(value, dict):
            nested = _collect_from_mapping(value, include_allowed_children=False)
            for nested_category, values in nested.items():
                result.setdefault(nested_category, []).extend(values)
    for category, values in list(result.items()):
        deduped: list[Any] = []
        seen: set[str] = set()
        for item in values:
            marker = json.dumps(item, sort_keys=True, separators=(",", ":"), default=str)
            if marker not in seen:
                seen.add(marker)
                deduped.append(item)
        result[category] = deduped[:10]
    return result


def _walk_json(value: Any, pointer: str = "") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield pointer or "/", value
        for key, item in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from _walk_json(item, f"{pointer}/{escaped}")
    elif isinstance(value, list):
        for index, item in enumerate(value[:100_000]):
            yield from _walk_json(item, f"{pointer}/{index}")


def _summary(row_no: int, parcel_id: str) -> dict[str, Any]:
    return {
        "row_no": row_no,
        "parcel_id": parcel_id,
        "occurrence_count": 0,
        "lookup_occurrence_count": 0,
        "lookup_categories": [],
        "official_lookup_key_available": False,
        "occurrences": [],
    }


def _line_lookup_fields(line: str) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    for raw_key, category in KEY_ALIASES.items():
        pattern = re.compile(rf"(?i)(?:^|[,;\t\s]){re.escape(raw_key)}\s*[:=]\s*([^,;\t]+)")
        match = pattern.search(line)
        if not match:
            continue
        bounded = _bounded_value(category, match.group(1).strip().strip('"\''))
        if bounded is not None:
            result.setdefault(category, []).append(bounded)
    return result


def scan_repository(root: Path) -> dict[str, Any]:
    summaries = {row: _summary(row, parcel) for row, parcel in CANDIDATES.items()}
    metrics = {
        "scanned_files": 0,
        "parsed_json_files": 0,
        "text_fallback_files": 0,
        "skipped_large_files": 0,
        "decode_failures": 0,
        "max_file_bytes": MAX_FILE_BYTES,
        "max_occurrences_per_candidate": MAX_OCCURRENCES_PER_CANDIDATE,
    }

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(EXCLUDED_PREFIXES) or path.name in EXCLUDED_BASENAMES or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                metrics["skipped_large_files"] += 1
                continue
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            metrics["decode_failures"] += 1
            continue
        except OSError:
            continue
        metrics["scanned_files"] += 1
        parsed: Any | None = None
        if path.suffix.lower() == ".json":
            try:
                parsed = json.loads(text)
                metrics["parsed_json_files"] += 1
            except json.JSONDecodeError:
                parsed = None

        if parsed is not None:
            for pointer, obj in _walk_json(parsed):
                for row_no, parcel_id in CANDIDATES.items():
                    summary = summaries[row_no]
                    if len(summary["occurrences"]) >= MAX_OCCURRENCES_PER_CANDIDATE:
                        continue
                    if not _direct_identity_match(obj, row_no, parcel_id):
                        continue
                    lookup = _collect_from_mapping(obj, include_allowed_children=True)
                    occurrence = {
                        "path": rel,
                        "json_pointer": pointer,
                        "object_sha256": hashlib.sha256(
                            json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
                        ).hexdigest(),
                        "available_fields": sorted(str(key) for key in obj.keys())[:100],
                        "lookup_fields": lookup,
                    }
                    summary["occurrences"].append(occurrence)
                    summary["occurrence_count"] += 1
                    if lookup:
                        summary["lookup_occurrence_count"] += 1
        else:
            metrics["text_fallback_files"] += 1
            for line_no, line in enumerate(text.splitlines(), 1):
                for row_no, parcel_id in CANDIDATES.items():
                    summary = summaries[row_no]
                    if len(summary["occurrences"]) >= MAX_OCCURRENCES_PER_CANDIDATE:
                        continue
                    row_pattern = re.compile(rf"(?<!\d){row_no}(?!\d)")
                    parcel_pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(parcel_id)}(?![A-Za-z0-9_])")
                    if not row_pattern.search(line) and not parcel_pattern.search(line):
                        continue
                    lookup = _line_lookup_fields(line)
                    occurrence = {
                        "path": rel,
                        "line_number": line_no,
                        "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                        "lookup_fields": lookup,
                    }
                    summary["occurrences"].append(occurrence)
                    summary["occurrence_count"] += 1
                    if lookup:
                        summary["lookup_occurrence_count"] += 1

    available_count = 0
    for summary in summaries.values():
        categories = sorted({category for item in summary["occurrences"] for category in item["lookup_fields"]})
        summary["lookup_categories"] = categories
        summary["official_lookup_key_available"] = bool(set(categories) & LOOKUP_CATEGORIES)
        available_count += int(summary["official_lookup_key_available"])

    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "state": "PUBLISHED" if available_count else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "progress_percent": 100.0,
        "produced_business_rows": 0,
        "validated_candidate_count": len(CANDIDATES),
        "official_lookup_key_available_count": available_count,
        "candidate_summaries": [summaries[row] for row in sorted(summaries)],
        "scan_metrics": metrics,
        "fake_data": False,
        "inferred_linkage_persisted": False,
        "next_unverified_step": "VALIDATE_FOUND_OFFICIAL_LOOKUP_KEYS" if available_count else "OBTAIN_OFFICIAL_LOOKUP_KEY_FROM_NEW_TRACKED_SOURCE",
        "blocker": None if available_count else "NO_TRACKED_OFFICIAL_LOOKUP_KEY_FOUND_ACROSS_PRECISION_REPOSITORY_SCAN",
    }


def self_test() -> dict[str, Any]:
    positive = {"row_no": 30762, "parcel_id": "parcel_30762", "identity": {"uprn": "100012345678", "postcode": "SW1A 1AA"}}
    negative = {"row_no": 46142, "parcel_id": "parcel_46142", "source_codes": ["OFFICIAL_SOURCE"]}
    sibling_root = {"candidates": [{"row_no": 61522, "parcel_id": "parcel_61522"}], "unrelated": {"latitude": 51.5, "longitude": -0.1}}
    tests = [
        ("direct_candidate_detected", _direct_identity_match(positive, 30762, "parcel_30762")),
        ("positive_uprn", _collect_from_mapping(positive, include_allowed_children=True).get("uprn") == ["100012345678"]),
        ("positive_postcode", _collect_from_mapping(positive, include_allowed_children=True).get("postcode") == ["SW1A 1AA"]),
        ("negative_candidate_detected", _direct_identity_match(negative, 46142, "parcel_46142")),
        ("negative_has_no_lookup", _collect_from_mapping(negative, include_allowed_children=True) == {}),
        ("wrong_candidate_rejected", not _direct_identity_match(positive, 61522, "parcel_61522")),
        ("sibling_container_not_direct_match", not _direct_identity_match(sibling_root, 61522, "parcel_61522")),
        ("scalar_geometry_rejected", _bounded_value("geometry", 1) is None),
        ("geometry_hashed", bool(_bounded_value("geometry", {"type": "Point", "coordinates": [1, 2]})["sha256"])),
        ("generic_id_not_identity", not _direct_identity_match({"id": "parcel_30762", "latitude": 1}, 30762, "parcel_30762")),
        ("oversized_scalar_rejected", _bounded_value("address", "x" * 241) is None),
        ("boolean_rejected", _bounded_value("uprn", True) is None),
    ]
    passed = sum(bool(ok) for _, ok in tests)
    return {"tests": [{"name": name, "passed": bool(ok)} for name, ok in tests], "passed": passed, "target": len(tests), "result": f"PASS_{passed}_OF_{len(tests)}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    if not args.output:
        parser.error("--output is required")
    result = scan_repository(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
