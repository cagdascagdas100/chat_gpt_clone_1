#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
SLOT = "height_difference_1"
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
REV8_ENTRY = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/012_height_difference_1_revision_8_entry_20260721.py"
REV8_OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/010_geometry_datum_quality_gate_latest.json"
OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/011_height_difference_metric_gate_latest.json"
WEB_OUT = REPO / "england_map_web/data/aays_21_slots/height_difference_1/height_difference_metric_gate_latest.json"
SNAPSHOT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/011_height_difference_metric_gate_manifest_latest.json"
REPORT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/016_height_difference_1_height_difference_metric_gate_result.md"

EA_VERTICAL_RMSE_M = 0.15
RANGE_ENDPOINT_RSS_RMSE_M = round(math.sqrt(2.0) * EA_VERTICAL_RMSE_M, 3)
MIN_VALID_PIXELS = 3


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def range_from_stats(stats: Any) -> dict[str, Any]:
    if not isinstance(stats, dict) or not bool(stats.get("ok")):
        return {"ok": False, "error": "ea_polygon_statistics_missing"}
    required = ("min_m", "max_m", "median_m", "iqr_m", "pixel_count")
    if not all(finite_number(stats.get(k)) for k in required):
        return {"ok": False, "error": "ea_polygon_statistics_non_numeric"}
    minimum = float(stats["min_m"])
    maximum = float(stats["max_m"])
    median = float(stats["median_m"])
    iqr = float(stats["iqr_m"])
    pixel_count = int(stats["pixel_count"])
    if not (minimum <= median <= maximum and 0.0 <= iqr <= maximum - minimum):
        return {"ok": False, "error": "ea_polygon_statistics_order_invalid"}
    if pixel_count < MIN_VALID_PIXELS:
        return {"ok": False, "error": "ea_polygon_pixel_count_below_3", "pixel_count": pixel_count}
    return {
        "ok": True,
        "minimum_elevation_m_odn": round(minimum, 3),
        "maximum_elevation_m_odn": round(maximum, 3),
        "median_elevation_m_odn": round(median, 3),
        "height_difference_m": round(maximum - minimum, 3),
        "iqr_m": round(iqr, 3),
        "pixel_count": pixel_count,
        "source_vertical_rmse_m": EA_VERTICAL_RMSE_M,
        "range_endpoint_rss_rmse_m": RANGE_ENDPOINT_RSS_RMSE_M,
        "horizontal_crs": "EPSG:27700",
        "vertical_reference": "Ordnance Datum Newlyn",
        "metric_definition": "maximum_minus_minimum_EA_DTM_1m_pixels_inside_official_HMLR_polygon",
    }


def apply_metric_gate(result: dict[str, Any]) -> dict[str, Any]:
    rows = result.get("rows") if isinstance(result.get("rows"), list) else []
    accepted = 0
    valid_ranges = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        ea1 = row.get("ea_dtm_1m_polygon", {})
        metric = range_from_stats(ea1)
        row["height_difference"] = metric
        prior_quality_accept = bool(row.get("accepted_measured_row"))
        os_sample = row.get("os_terrain50", {})
        os_baseline_ok = isinstance(os_sample, dict) and bool(os_sample.get("ok"))
        source_conflict = bool(row.get("human_review_required"))
        accepted_row = prior_quality_accept and bool(metric.get("ok")) and os_baseline_ok and not source_conflict
        row["accepted_measured_row"] = accepted_row
        row["metric_name"] = "parcel_ground_height_difference"
        row["metric_unit"] = "metre"
        row["independent_os_role"] = "absolute_elevation_and_vertical_datum_crosscheck_not_parcel_range_measurement"
        row["same_provider_resolution_checks_role"] = "EA_2m_and_10m_are_consistency_checks_not_independent_sources"
        if metric.get("ok"):
            valid_ranges += 1
        if accepted_row:
            accepted += 1
            row["output_semantics"] = "MEASURED_OFFICIAL_PARCEL_GROUND_HEIGHT_DIFFERENCE"
            row["accuracy_score_4"] = "3.5/4"
        elif prior_quality_accept and not metric.get("ok"):
            row["output_semantics"] = "NO_DATA_NOT_INFERRED_HEIGHT_DIFFERENCE_METRIC_GATE_FAILED"
            row["accuracy_score_4"] = "2.5/4 fallback"
        else:
            row["output_semantics"] = row.get("output_semantics") or "NO_DATA_NOT_INFERRED"
            row["accuracy_score_4"] = row.get("accuracy_score_4") or "2.5/4 fallback"

    counts = result.setdefault("counts", {})
    counts["candidate_rows"] = len(rows)
    counts["ea_1m_valid_height_difference_rows"] = valid_ranges
    counts["official_three_source_height_difference_rows"] = accepted
    counts["official_three_source_measured_rows"] = accepted
    result["schema_version"] = max(int(result.get("schema_version", 0) or 0), 9)
    result["payload_revision"] = 9
    result["attempt_id"] = "official-source-batch-004-revision-9-height-difference-metric"
    result["status"] = "MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED"
    result["metric_contract"] = {
        "layer_key": "height_difference",
        "metric_name": "parcel_ground_height_difference",
        "definition": "maximum minus minimum EA DTM 1m elevation among valid pixels inside the official HMLR parcel polygon",
        "unit": "metre",
        "primary_numeric_source": "Environment Agency LIDAR Composite DTM 1m",
        "primary_source_role": "parcel_range_measurement",
        "independent_source": "OS Terrain 50",
        "independent_source_role": "absolute elevation and shared ODN datum crosscheck; 50m grid is not treated as parcel-range measurement",
        "same_provider_checks": ["EA DTM 2m", "EA DTM 10m"],
        "same_provider_checks_role": "resolution consistency only, not source independence",
        "minimum_valid_ea_pixels": MIN_VALID_PIXELS,
        "ea_source_vertical_rmse_m": EA_VERTICAL_RMSE_M,
        "indicative_range_endpoint_rss_rmse_m": RANGE_ENDPOINT_RSS_RMSE_M,
        "horizontal_crs": "EPSG:27700",
        "vertical_reference": "Ordnance Datum Newlyn",
        "no_data_policy": "NO_DATA_NOT_INFERRED",
    }
    acceptance = result.setdefault("acceptance", {})
    acceptance["height_difference_metric_required"] = True
    acceptance["height_difference_definition"] = "ea_1m_polygon_max_m_minus_min_m"
    acceptance["minimum_valid_ea_1m_pixels"] = MIN_VALID_PIXELS
    acceptance["os_terrain50_parcel_range_promotion_forbidden"] = True
    acceptance["ea_2m_10m_independent_source_claim_forbidden"] = True
    result["final_ready"] = False
    result["product_final_ready"] = False
    result["fake_data"] = False
    result["db_write"] = False
    result["migration"] = False
    result["production_deploy"] = False
    return result


def main() -> int:
    if not REV8_ENTRY.exists():
        raise SystemExit(f"revision_8_entry_missing:{REV8_ENTRY}")
    completed = subprocess.run([sys.executable, str(REV8_ENTRY)], cwd=str(REPO), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    if not REV8_OUT.exists():
        raise SystemExit(f"revision_8_output_missing:{REV8_OUT}")
    result = apply_metric_gate(json.loads(REV8_OUT.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    for path in (OUT, WEB_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    snapshot = {
        "schema_version": 1,
        "slot_id": SLOT,
        "task_id": TASK_ID,
        "payload_revision": 9,
        "metric_contract": result["metric_contract"],
        "valid_height_difference_rows": result.get("counts", {}).get("ea_1m_valid_height_difference_rows", 0),
        "accepted_official_height_difference_rows": result.get("counts", {}).get("official_three_source_height_difference_rows", 0),
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Height Difference 1 revision 9 parcel height-difference metric result\n\n"
        f"- Candidate rows: `{result.get('counts', {}).get('candidate_rows', 0)}`\n"
        f"- Valid EA 1m parcel height-difference rows: `{result.get('counts', {}).get('ea_1m_valid_height_difference_rows', 0)}`\n"
        f"- Accepted official three-source height-difference rows: `{result.get('counts', {}).get('official_three_source_height_difference_rows', 0)}`\n"
        "- Metric: maximum minus minimum valid EA DTM 1m pixel elevation inside the official HMLR parcel polygon.\n"
        "- OS Terrain 50 is an independent absolute-elevation/datum crosscheck, not a parcel-range measurement.\n"
        "- `final_ready=false`\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "counts": result.get("counts", {}), "output": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
