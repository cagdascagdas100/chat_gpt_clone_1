#!/usr/bin/env python3
"""Deterministic EA WCS GeoTIFF byte/value guard for height_difference_1.

This helper does not download data or produce parcel measurements. It validates the
classic TIFF header contract and filters Environment Agency NoData values before a
measurement runner is allowed to compute min/max statistics.
"""
from __future__ import annotations

import argparse
import json
import math
from typing import Iterable

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.0-ea-classic-tiff-and-nodata-guard"
EA_WCS_NODATA_SENTINEL = -3.4028235e38
CLASSIC_TIFF_HEADERS = {b"II*\x00", b"MM\x00*"}


class EvidenceError(RuntimeError):
    pass


def validate_classic_tiff_header(data: bytes, content_type: str | None = None) -> str:
    if len(data) < 8:
        raise EvidenceError("WCS_RESPONSE_TOO_SMALL_FOR_TIFF")
    header = data[:4]
    if header not in CLASSIC_TIFF_HEADERS:
        raise EvidenceError(f"WCS_RESPONSE_NOT_CLASSIC_TIFF:{header.hex()}")
    if content_type:
        lowered = content_type.lower()
        if "tiff" not in lowered and "octet-stream" not in lowered:
            raise EvidenceError(f"UNEXPECTED_WCS_CONTENT_TYPE:{content_type}")
    return "LITTLE_ENDIAN" if header == b"II*\x00" else "BIG_ENDIAN"


def filter_ea_wcs_values(
    values: Iterable[float],
    *,
    metadata_nodata: float | None = None,
    sentinel_relative_tolerance: float = 1e-6,
) -> list[float]:
    filtered: list[float] = []
    for raw in values:
        value = float(raw)
        if not math.isfinite(value):
            continue
        if metadata_nodata is not None and math.isclose(value, float(metadata_nodata), rel_tol=0.0, abs_tol=0.0):
            continue
        if math.isclose(value, EA_WCS_NODATA_SENTINEL, rel_tol=sentinel_relative_tolerance, abs_tol=0.0):
            continue
        filtered.append(value)
    if not filtered:
        raise EvidenceError("NO_VALID_EA_WCS_VALUES_AFTER_NODATA_FILTER")
    return filtered


def run_self_test() -> dict[str, object]:
    checks = 0
    assert validate_classic_tiff_header(b"II*\x00\x08\x00\x00\x00", "image/tiff") == "LITTLE_ENDIAN"
    checks += 1
    assert validate_classic_tiff_header(b"MM\x00*\x00\x00\x00\x08", "application/octet-stream") == "BIG_ENDIAN"
    checks += 1
    for bad in (b"II+\x00\x08\x00\x00\x00", b"MM\x00+\x00\x00\x00\x08", b"NOTTIFF!"):
        try:
            validate_classic_tiff_header(bad, "image/tiff")
        except EvidenceError:
            checks += 1
        else:
            raise AssertionError("invalid or BigTIFF header accepted")
    result = filter_ea_wcs_values(
        [EA_WCS_NODATA_SENTINEL, float("nan"), -9999.0, 1.25, 2.75],
        metadata_nodata=-9999.0,
    )
    assert result == [1.25, 2.75]
    checks += 1
    try:
        filter_ea_wcs_values([EA_WCS_NODATA_SENTINEL, float("inf")])
    except EvidenceError:
        checks += 1
    else:
        raise AssertionError("all-nodata input accepted")
    assert min(result) == 1.25 and max(result) == 2.75 and round(max(result) - min(result), 3) == 1.5
    checks += 1
    return {
        "state": "PASS",
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "checks": checks,
        "official_nodata_sentinel": EA_WCS_NODATA_SENTINEL,
        "business_rows_written": 0,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        raise SystemExit("--self-test is required; this helper does not download or measure parcels")
    print(json.dumps(run_self_test(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
