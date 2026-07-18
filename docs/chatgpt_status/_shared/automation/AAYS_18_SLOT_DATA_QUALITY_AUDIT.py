from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FEATURE_PATTERN = re.compile(rb'"type"\s*:\s*"Feature"')


def count_features(path: Path) -> int:
    total = 0
    tail = b""
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            payload = tail + chunk
            boundary = len(tail)
            total += sum(match.end() > boundary for match in FEATURE_PATTERN.finditer(payload))
            tail = payload[-128:]
    return total


def first_feature(path: Path) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    buffer = ""
    feature_offset: int | None = None
    with path.open("r", encoding="utf-8") as handle:
        while len(buffer) < 4 * 1024 * 1024:
            chunk = handle.read(64 * 1024)
            if not chunk:
                break
            buffer += chunk
            if feature_offset is None:
                marker = buffer.find('"features"')
                if marker >= 0:
                    bracket = buffer.find("[", marker)
                    if bracket >= 0:
                        feature_offset = bracket + 1
            if feature_offset is None:
                continue
            start = feature_offset
            while start < len(buffer) and buffer[start] in " \t\r\n":
                start += 1
            if start < len(buffer) and buffer[start] == "]":
                return {}
            try:
                feature, _end = decoder.raw_decode(buffer, start)
                return feature if isinstance(feature, dict) else {}
            except json.JSONDecodeError:
                continue
    return {}


def property_quality(properties: dict[str, Any]) -> dict[str, Any]:
    keys = {str(key).casefold() for key in properties}
    text = " ".join(str(value) for value in properties.values()).casefold()
    return {
        "has_parcel_identity": any(
            token in key
            for key in keys
            for token in ("parcel_id", "hmlr", "inspire", "row_no")
        ),
        "has_source_or_evidence": any(
            token in key
            for key in keys
            for token in ("source", "evidence", "dataset")
        ),
        "has_accuracy_or_confidence": any(
            token in key for key in keys for token in ("accuracy", "confidence")
        ),
        "labels_proxy_or_estimation": any(
            token in text for token in ("proxy", "estimate", "estimated", "interpolat")
        ),
        "has_time_or_version": any(
            token in key
            for key in keys
            for token in ("date", "year", "time", "version", "snapshot", "generated")
        ),
    }


def audit(web_root: Path) -> dict[str, Any]:
    data_root = web_root / "data" / "program_layer_matrix"
    manifest_path = data_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    topic_results: dict[str, Any] = {}
    blockers: list[str] = []

    for topic_id, topic in manifest.get("topics", {}).items():
        path = data_root / str(topic.get("file"))
        if not path.is_file():
            topic_results[topic_id] = {"status": "MISSING_FILE", "file": str(path)}
            blockers.append(f"MISSING_TOPIC_FILE:{topic_id}")
            continue
        actual_count = count_features(path)
        declared_count = int(topic.get("feature_count") or 0)
        sample = first_feature(path)
        properties = sample.get("properties") if isinstance(sample, dict) else {}
        properties = properties if isinstance(properties, dict) else {}
        geometry = sample.get("geometry") if isinstance(sample, dict) else {}
        geometry = geometry if isinstance(geometry, dict) else {}
        mismatch = actual_count != declared_count
        if mismatch:
            blockers.append(
                f"FEATURE_COUNT_MISMATCH:{topic_id}:declared={declared_count}:actual={actual_count}"
            )
        topic_results[topic_id] = {
            "status": "COUNT_MISMATCH" if mismatch else "COUNT_MATCH",
            "file": str(path.relative_to(web_root)).replace("\\", "/"),
            "file_size": path.stat().st_size,
            "declared_feature_count": declared_count,
            "actual_feature_count": actual_count,
            "geometry_type": geometry.get("type"),
            "sample_property_keys": sorted(map(str, properties.keys())),
            "sample_properties": properties,
            "quality_fields": property_quality(properties),
        }

    source_text = str(manifest.get("source_jsonl") or "")
    output_text = str(manifest.get("output_dir") or "")
    hardcoded_c_paths = source_text.casefold().startswith("c:\\") or output_text.casefold().startswith("c:\\")
    if hardcoded_c_paths:
        blockers.append("NON_PORTABLE_C_PATHS_IN_MATRIX_MANIFEST")

    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "web_root": str(web_root),
        "manifest": str(manifest_path),
        "hardcoded_c_paths": hardcoded_c_paths,
        "topics": topic_results,
        "blockers": blockers,
        "business_files_written": 0,
        "fake_data": False,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.web_root.resolve())
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
