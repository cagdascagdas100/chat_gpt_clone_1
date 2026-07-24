#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
SLOT = "height_difference_1"
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
PAYLOAD_REVISION = 11
ATTEMPT_ID = "official-source-batch-004-revision-11-pixel-center-sampling-provenance"
IDEMPOTENCY_KEY = "height_difference_1-004-20260720"
SCRIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_1/automation/032_height_difference_1_revision_11_pixel_center_sampling_provenance_20260721.py"
REV10_ENTRY = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/027_height_difference_1_revision_10_explicit_identity_evidence_gate_20260721.py"
REV10_OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/012_revision_10_explicit_identity_evidence_gate_latest.json"
OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/013_revision_11_pixel_center_sampling_provenance_latest.json"
WEB_OUT = REPO / "england_map_web/data/aays_21_slots/height_difference_1/revision_11_pixel_center_sampling_provenance_latest.json"
SNAPSHOT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/013_revision_11_pixel_center_sampling_provenance_manifest_latest.json"
REPORT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/018_height_difference_1_revision_11_pixel_center_sampling_provenance_result.md"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def first_value(mapping: Any, *keys: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if mapping.get(key) is not None:
            return mapping.get(key)
    return None


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def flatten_ring(value: Any) -> list[list[float]]:
    if isinstance(value, dict):
        value = value.get("coordinates")
    while isinstance(value, list) and value and isinstance(value[0], list) and value[0] and isinstance(value[0][0], list):
        value = value[0]
    ring: list[list[float]] = []
    if isinstance(value, list):
        for point in value:
            if isinstance(point, (list, tuple)) and len(point) >= 2 and finite_number(point[0]) and finite_number(point[1]):
                ring.append([float(point[0]), float(point[1])])
    if len(ring) >= 3 and ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def polygon_area_m2(ring: list[list[float]]) -> float | None:
    if len(ring) < 4:
        return None
    area2 = 0.0
    for index in range(len(ring) - 1):
        x1, y1 = ring[index]
        x2, y2 = ring[index + 1]
        area2 += x1 * y2 - x2 * y1
    area = abs(area2) / 2.0
    return area if math.isfinite(area) and area > 0 else None


def boundary_ring(row: dict[str, Any]) -> list[list[float]]:
    boundary = row.get("boundary")
    if not isinstance(boundary, dict):
        return []
    child = first_value(boundary, "bulk_match", "gml_match", "monthly_gml")
    geometry = first_value(boundary, "ring", "polygon", "coordinates")
    if geometry is None and isinstance(child, dict):
        geometry = first_value(child, "ring", "polygon", "coordinates")
    return flatten_ring(geometry)


def sampling_provenance(row: dict[str, Any]) -> dict[str, Any]:
    stats = row.get("ea_dtm_1m_polygon")
    metric = row.get("height_difference")
    if not isinstance(stats, dict) or not isinstance(metric, dict) or not bool(metric.get("ok")):
        return {"ok": False, "reasons": ["EA_METRIC_OR_STATS_MISSING"]}

    provenance_candidates = [stats.get("sampling_provenance"), stats.get("mask_provenance"), row.get("ea_sampling_provenance"), row.get("raster_sampling_provenance")]
    provenance = next((item for item in provenance_candidates if isinstance(item, dict)), {})
    reasons: list[str] = []

    policy = str(first_value(provenance, "pixel_inclusion_policy", "sampling_policy", "mask_policy") or "").strip().lower()
    all_touched = first_value(provenance, "all_touched", "raster_mask_all_touched")
    centers_verified = first_value(provenance, "pixel_centers_inside_polygon", "valid_pixel_centers_inside_polygon", "pixel_center_inclusion_verified")
    valid_count = first_value(provenance, "valid_pixel_count", "pixel_count", "sampled_pixel_count")
    mask_sha256 = first_value(provenance, "mask_sha256", "sample_mask_sha256", "pixel_selection_sha256")
    declared_area = first_value(provenance, "polygon_area_m2", "parcel_area_m2")

    if "pixel_center" not in policy and "pixel-centre" not in policy and "pixel centre" not in policy:
        reasons.append("PIXEL_CENTER_POLICY_NOT_DECLARED")
    if all_touched is not False:
        reasons.append("ALL_TOUCHED_NOT_EXPLICITLY_FALSE")
    if centers_verified is not True:
        reasons.append("PIXEL_CENTERS_INSIDE_POLYGON_NOT_VERIFIED")
    metric_count = metric.get("pixel_count")
    if not finite_number(valid_count) or not finite_number(metric_count) or int(valid_count) != int(metric_count):
        reasons.append("SAMPLING_PIXEL_COUNT_MISMATCH")
    if not isinstance(mask_sha256, str) or not SHA256_RE.fullmatch(mask_sha256.strip()):
        reasons.append("SAMPLING_MASK_SHA256_INVALID")

    ring = boundary_ring(row)
    computed_area = polygon_area_m2(ring)
    if computed_area is None:
        reasons.append("PARCEL_POLYGON_AREA_NOT_COMPUTABLE")
    if not finite_number(declared_area) or computed_area is None:
        reasons.append("DECLARED_PARCEL_AREA_MISSING")
    else:
        tolerance = max(0.01, computed_area * 1e-6)
        if abs(float(declared_area) - computed_area) > tolerance:
            reasons.append("DECLARED_PARCEL_AREA_MISMATCH")

    return {"ok": not reasons, "reasons": reasons, "pixel_inclusion_policy": policy, "all_touched": all_touched, "pixel_centers_inside_polygon": centers_verified, "valid_pixel_count": int(valid_count) if finite_number(valid_count) else None, "mask_sha256": str(mask_sha256 or ""), "declared_polygon_area_m2": round(float(declared_area), 3) if finite_number(declared_area) else None, "computed_polygon_area_m2": round(computed_area, 3) if computed_area is not None else None, "purpose": "prevent_outside_parcel_elevation_contamination"}


def apply_gate(result: dict[str, Any]) -> dict[str, Any]:
    rows = result.get("rows") if isinstance(result.get("rows"), list) else []
    accepted = 0
    provenance_ok = 0
    provenance_missing = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        prior_accept = bool(row.get("accepted_measured_row"))
        provenance = sampling_provenance(row)
        if provenance.get("ok"):
            provenance_ok += 1
        else:
            provenance_missing += 1
        accepted_row = prior_accept and bool(provenance.get("ok"))
        row["revision_11_sampling_provenance_gate"] = {"upstream_revision_10_accepted": prior_accept, "sampling_provenance": provenance, "accepted": accepted_row}
        row["accepted_measured_row"] = accepted_row
        if accepted_row:
            accepted += 1
            row["output_semantics"] = "MEASURED_OFFICIAL_PARCEL_GROUND_HEIGHT_DIFFERENCE_PIXEL_CENTER_GATED"
            row["accuracy_score_4"] = "3.5/4"
        elif prior_accept:
            row["output_semantics"] = "NO_DATA_NOT_INFERRED_PIXEL_CENTER_PROVENANCE_MISSING"
            row["accuracy_score_4"] = "2.5/4 fallback"
        elif bool(row.get("human_review_required")):
            row["output_semantics"] = "HUMAN_REVIEW_REQUIRED_NOT_MEASURED"
            row["accuracy_score_4"] = "2.5/4 not_measured"
        else:
            row["output_semantics"] = "NO_DATA_NOT_INFERRED"
            row["accuracy_score_4"] = "2.5/4 fallback"

    digest = script_sha256()
    counts = result.setdefault("counts", {})
    counts["candidate_rows"] = len(rows)
    counts["pixel_center_sampling_provenance_rows"] = provenance_ok
    counts["pixel_center_sampling_provenance_missing_rows"] = provenance_missing
    counts["official_three_source_height_difference_rows"] = accepted
    counts["official_three_source_measured_rows"] = accepted
    result.update({"schema_version": max(int(result.get("schema_version", 0) or 0), 11), "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": digest, "status": "MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED", "sampling_contract": {"pixel_inclusion_policy": "pixel_center_inside_official_hmlr_polygon", "all_touched": False, "pixel_center_verification_required": True, "sampling_mask_sha256_required": True, "declared_and_recomputed_polygon_area_required": True, "purpose": "prevent_outside_parcel_elevation_contamination", "reference_implementation": "rasterio.mask all_touched=False"}, "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False})
    return result


def main() -> int:
    if not REV10_ENTRY.exists():
        raise SystemExit(f"revision_10_entry_missing:{REV10_ENTRY}")
    completed = subprocess.run([sys.executable, str(REV10_ENTRY)], cwd=str(REPO), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    if not REV10_OUT.exists():
        raise SystemExit(f"revision_10_output_missing:{REV10_OUT}")
    source = json.loads(REV10_OUT.read_text(encoding="utf-8-sig"))
    if not isinstance(source, dict):
        raise SystemExit("revision_10_output_root_not_object")
    result = apply_gate(source)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    for path in (OUT, WEB_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    output_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    snapshot = {"schema_version": 1, "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": result["script_sha256"], "runner_web_output_sha256": output_sha, "candidate_rows": result.get("counts", {}).get("candidate_rows", 0), "pixel_center_sampling_provenance_rows": result.get("counts", {}).get("pixel_center_sampling_provenance_rows", 0), "accepted_official_height_difference_rows": result.get("counts", {}).get("official_three_source_height_difference_rows", 0), "sampling_contract": result["sampling_contract"], "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("# Height Difference 1 revision 11 pixel-center sampling provenance gate\n\n" f"- Candidate rows: `{snapshot['candidate_rows']}`\n" f"- Rows with verified pixel-center sampling provenance: `{snapshot['pixel_center_sampling_provenance_rows']}`\n" f"- Accepted official height-difference rows: `{snapshot['accepted_official_height_difference_rows']}`\n" "- Measured promotion requires all_touched=false, pixel-center inclusion verification, a sampling-mask SHA-256, and matching declared/recomputed parcel area.\n" "- `final_ready=false`\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result.get("counts", {}), "output": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
