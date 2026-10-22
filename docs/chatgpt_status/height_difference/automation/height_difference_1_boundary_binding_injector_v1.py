#!/usr/bin/env python3
"""Inject strict polygon-interior binding and reject boundary-only point matches."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.0-strict-interior-boundary-touch-rejection-injector"

EXPECTED_INSERTION_MARKER = """  $patched = Replace-ExactlyOnce -Text $patched -Old $oldBusinessIdentityGate -New $newBusinessIdentityGate -Label 'BUSINESS_ROW_INSPIRE_IDENTITY_PROVENANCE_GATE'

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
"""

INJECTED_BLOCK = r"""  $patched = Replace-ExactlyOnce -Text $patched -Old $oldBusinessIdentityGate -New $newBusinessIdentityGate -Label 'BUSINESS_ROW_INSPIRE_IDENTITY_PROVENANCE_GATE'

  $oldExactPolygonMatcher = @'
def exact_polygon_match_positions(gdf: Any, point: Any) -> tuple[list[int], list[int]]:
    try:
        exact = [int(i) for i in gdf.sindex.query(point, predicate="intersects")]
        nearby = [int(i) for i in gdf.sindex.query(point.buffer(15.0), predicate="intersects")]
    except Exception:
        exact_mask = gdf.geometry.intersects(point).to_numpy()
        nearby_mask = gdf.geometry.intersects(point.buffer(15.0)).to_numpy()
        exact = [int(i) for i, value in enumerate(exact_mask) if bool(value)]
        nearby = [int(i) for i, value in enumerate(nearby_mask) if bool(value)]
    return exact, nearby
'@
  $newExactPolygonMatcher = @'
def exact_polygon_match_positions(gdf: Any, point: Any) -> tuple[list[int], list[int], list[int]]:
    try:
        intersecting = sorted({int(i) for i in gdf.sindex.query(point, predicate="intersects")})
        nearby = sorted({int(i) for i in gdf.sindex.query(point.buffer(15.0), predicate="intersects")})
    except Exception:
        intersect_mask = gdf.geometry.intersects(point).to_numpy()
        nearby_mask = gdf.geometry.intersects(point.buffer(15.0)).to_numpy()
        intersecting = [int(i) for i, value in enumerate(intersect_mask) if bool(value)]
        nearby = [int(i) for i, value in enumerate(nearby_mask) if bool(value)]
    interior = [
        position for position in intersecting
        if bool(gdf.geometry.iloc[position].contains(point))
    ]
    boundary = [
        position for position in intersecting
        if bool(gdf.geometry.iloc[position].touches(point))
    ]
    return interior, boundary, nearby
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldExactPolygonMatcher -New $newExactPolygonMatcher -Label 'STRICT_INTERIOR_POLYGON_MATCHER'

  $oldExactPolygonUse = @'
                exact_positions, near_positions = exact_polygon_match_positions(gdf, point)
                item["exact_polygon_candidate_count"] = len(exact_positions)
                item["within_15m_candidate_count"] = len(near_positions)
                if len(exact_positions) != 1:
                    raise EvidenceError(f"UNIQUE_EXACT_POLYGON_REQUIRED:found={len(exact_positions)}")
                row = gdf.iloc[exact_positions[0]]
'@
  $newExactPolygonUse = @'
                interior_positions, boundary_positions, near_positions = exact_polygon_match_positions(gdf, point)
                item["interior_polygon_candidate_count"] = len(interior_positions)
                item["boundary_touch_candidate_count"] = len(boundary_positions)
                item["within_15m_candidate_count"] = len(near_positions)
                if boundary_positions:
                    raise EvidenceError(
                        f"POINT_ON_POLYGON_BOUNDARY_NOT_CANONICAL:found={len(boundary_positions)}"
                    )
                if len(interior_positions) != 1:
                    raise EvidenceError(
                        f"UNIQUE_STRICT_INTERIOR_POLYGON_REQUIRED:found={len(interior_positions)}"
                    )
                row = gdf.iloc[interior_positions[0]]
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldExactPolygonUse -New $newExactPolygonUse -Label 'BOUNDARY_TOUCH_REJECTION_GATE'

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
"""


class InjectionError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_carrier_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    count = normalized.count(EXPECTED_INSERTION_MARKER)
    if count != 1:
        raise InjectionError(f"BOUNDARY_BINDING_INSERTION_MARKER_COUNT_INVALID:{count}")
    patched = normalized.replace(EXPECTED_INSERTION_MARKER, INJECTED_BLOCK, 1)
    required = (
        "STRICT_INTERIOR_POLYGON_MATCHER",
        "BOUNDARY_TOUCH_REJECTION_GATE",
        'gdf.geometry.iloc[position].contains(point)',
        'gdf.geometry.iloc[position].touches(point)',
        "POINT_ON_POLYGON_BOUNDARY_NOT_CANONICAL",
        "UNIQUE_STRICT_INTERIOR_POLYGON_REQUIRED",
        "boundary_touch_candidate_count",
        "interior_polygon_candidate_count",
    )
    missing = [token for token in required if token not in patched]
    if missing:
        raise InjectionError(f"BOUNDARY_BINDING_TOKEN_MISSING:{missing}")
    return patched


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def run_self_test() -> dict[str, Any]:
    fixture = "header\n" + EXPECTED_INSERTION_MARKER + "\nfooter\n"
    patched = patch_carrier_text(fixture)
    checks = {
        "insertion_marker_replaced": EXPECTED_INSERTION_MARKER not in patched,
        "strict_interior_patch_present": "STRICT_INTERIOR_POLYGON_MATCHER" in patched,
        "boundary_rejection_patch_present": "BOUNDARY_TOUCH_REJECTION_GATE" in patched,
        "contains_predicate_present": ".contains(point)" in patched,
        "touches_predicate_present": ".touches(point)" in patched,
        "boundary_error_present": "POINT_ON_POLYGON_BOUNDARY_NOT_CANONICAL" in patched,
        "unique_interior_error_present": "UNIQUE_STRICT_INTERIOR_POLYGON_REQUIRED" in patched,
        "interior_count_telemetry_present": "interior_polygon_candidate_count" in patched,
        "boundary_count_telemetry_present": "boundary_touch_candidate_count" in patched,
    }
    duplicate_rejected = False
    try:
        patch_carrier_text(EXPECTED_INSERTION_MARKER + fixture)
    except InjectionError:
        duplicate_rejected = True
    checks["duplicate_marker_rejected"] = duplicate_rejected
    if not all(checks.values()):
        raise InjectionError(f"SELF_TEST_FAILED:{checks}")
    return {
        "slot_id": SLOT_ID,
        "state": "PASS",
        "script_version": SCRIPT_VERSION,
        "checks": len(checks),
        "check_results": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--carrier", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0
    if not args.carrier or not args.output or not args.receipt:
        raise InjectionError("CARRIER_OUTPUT_AND_RECEIPT_REQUIRED")
    source = args.carrier.read_bytes()
    patched = patch_carrier_text(source.decode("utf-8")).encode("utf-8")
    atomic_write(args.output, patched)
    receipt = {
        "slot_id": SLOT_ID,
        "state": "COMPLETED_STRICT_INTERIOR_BOUNDARY_GUARD_INJECTED",
        "script_version": SCRIPT_VERSION,
        "runtime_patch_count": 2,
        "runtime_patch_labels": [
            "STRICT_INTERIOR_POLYGON_MATCHER",
            "BOUNDARY_TOUCH_REJECTION_GATE",
        ],
        "source_path": str(args.carrier.resolve()),
        "output_path": str(args.output.resolve()),
        "source_bytes": len(source),
        "output_bytes": len(patched),
        "source_sha256": sha256_bytes(source),
        "output_sha256": sha256_bytes(patched),
        "binding_semantics": "strict_polygon_interior_only",
        "boundary_touch_policy": "reject_canonical_binding",
    }
    atomic_write(args.receipt, (json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
