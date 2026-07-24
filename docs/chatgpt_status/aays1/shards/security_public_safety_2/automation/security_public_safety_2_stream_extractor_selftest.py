from __future__ import annotations

import json
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Iterator

START = 30762
END = 31061
EXPECTED = 300
TOTAL = 92283
TARGET = {f"parcel_{number}" for number in range(START, END + 1)}


def stream_features(path: Path, chunk: int = 1 << 20) -> Iterator[dict[str, Any]]:
    decoder = json.JSONDecoder()
    with path.open("r", encoding="utf-8-sig") as handle:
        buffer = ""
        started = False
        eof = False
        while True:
            if not eof and (not started or len(buffer) < chunk // 2):
                value = handle.read(chunk)
                buffer += value
                eof = not bool(value)
            if not started:
                marker = buffer.find('"features"')
                if marker < 0:
                    if eof:
                        raise ValueError("FEATURES_NOT_FOUND")
                    buffer = buffer[-64:]
                    continue
                opening = buffer.find("[", marker)
                if opening < 0:
                    if eof:
                        raise ValueError("FEATURES_OPEN_NOT_FOUND")
                    buffer = buffer[marker:]
                    continue
                buffer = buffer[opening + 1 :]
                started = True
            buffer = buffer.lstrip()
            if not buffer:
                if eof:
                    raise ValueError("UNEXPECTED_EOF")
                continue
            if buffer[0] == "]":
                return
            if buffer[0] == ",":
                buffer = buffer[1:]
                continue
            try:
                item, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                if eof:
                    raise
                value = handle.read(chunk)
                buffer += value
                eof = not bool(value)
                continue
            buffer = buffer[end:]
            if isinstance(item, dict):
                yield item


def parcel_id(feature: dict[str, Any]) -> str:
    properties = feature.get("properties") or {}
    return str(properties.get("security_parcel_id") or properties.get("parcel_id") or "")


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir:
        fixture = Path(temp_dir) / "fixture.geojson"
        with fixture.open("w", encoding="utf-8") as handle:
            handle.write('{"type":"FeatureCollection","features":[')
            for number in range(1, TOTAL + 1):
                if number > 1:
                    handle.write(",")
                json.dump(
                    {
                        "type": "Feature",
                        "properties": {
                            "security_parcel_id": f"parcel_{number}",
                            "security_lsoa_code": "E01000001",
                        },
                        "geometry": {"type": "Point", "coordinates": [-0.1, 51.5]},
                    },
                    handle,
                    separators=(",", ":"),
                )
            handle.write("]}")
        fixture_bytes = fixture.stat().st_size
        tracemalloc.start()
        started_at = time.perf_counter()
        found: dict[str, dict[str, Any]] = {}
        scanned = 0
        for feature in stream_features(fixture):
            scanned += 1
            current_id = parcel_id(feature)
            if current_id in TARGET:
                found[current_id] = feature
            if len(found) == EXPECTED:
                break
        elapsed = time.perf_counter() - started_at
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "schema_version": 1,
            "slot_id": "security_public_safety_2",
            "test_type": "SYNTHETIC_STREAM_EXTRACTOR_SELFTEST",
            "synthetic_fixture_is_business_data": False,
            "fixture_total_features": TOTAL,
            "fixture_bytes": fixture_bytes,
            "target_start": START,
            "target_end": END,
            "expected_target_count": EXPECTED,
            "found_target_count": len(found),
            "first_target_present": "parcel_30762" in found,
            "last_target_present": "parcel_31061" in found,
            "features_scanned_until_complete": scanned,
            "elapsed_seconds": round(elapsed, 3),
            "peak_tracemalloc_bytes": peak,
            "peak_tracemalloc_mib": round(peak / 1048576, 3),
            "pass": len(found) == EXPECTED and "parcel_30762" in found and "parcel_31061" in found,
            "fake_data": False,
            "actual_business_rows_written": 0,
            "final_ready": False,
        }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
