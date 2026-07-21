#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
SLOT = "height_difference_1"
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
REV6_ENTRY = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/009_height_difference_1_revision_6_entry_20260721.py"
REV6_OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/008_official_api_evidence_reconciled_samples_latest.json"
OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/009_official_bulk_gml_authority_gate_latest.json"
WEB_OUT = REPO / "england_map_web/data/aays_21_slots/height_difference_1/official_bulk_gml_authority_gate_latest.json"
REPORT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/014_height_difference_1_official_bulk_gml_authority_gate_result.md"
SNAPSHOT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/009_official_bulk_gml_authority_gate_manifest_latest.json"

HMLR_ATTRIBUTION = (
    "This information is subject to Crown copyright and database rights 2026 "
    "and is reproduced with the permission of HM Land Registry."
)
OS_GEOMETRY_ATTRIBUTION = (
    "The polygons (including the associated geometry, namely x, y co-ordinates) "
    "are subject to Crown copyright and database rights 2026 "
    "Ordnance Survey AC0000851063."
)

def source_text(boundary: Any) -> str:
    if not isinstance(boundary, dict):
        return ""
    parts = []
    for key in ("source", "authority", "method", "provider", "source_type"):
        value = boundary.get(key)
        if value is not None:
            parts.append(str(value))
    for key in ("bulk_match", "gml_match", "monthly_gml"):
        value = boundary.get(key)
        if isinstance(value, dict):
            parts.extend(str(value.get(k, "")) for k in ("source", "authority", "method"))
    return " ".join(parts).upper()

def has_bulk_gml_evidence(boundary: Any) -> bool:
    if not isinstance(boundary, dict):
        return False
    text = source_text(boundary)
    has_source_marker = "HMLR_INSPIRE_GML" in text or "MONTHLY_GML" in text or "BULK_GML" in text
    has_hash = bool(boundary.get("source_sha256") or boundary.get("gml_sha256") or boundary.get("bulk_sha256") or (isinstance(boundary.get("bulk_match"), dict) and boundary["bulk_match"].get("source_sha256")))
    has_geometry = bool(boundary.get("ring") or boundary.get("polygon") or boundary.get("coordinates"))
    return has_source_marker and has_hash and has_geometry

def wfs_only(boundary: Any) -> bool:
    text = source_text(boundary)
    return "WFS" in text and not has_bulk_gml_evidence(boundary)

def apply_gate(result: dict[str, Any]) -> dict[str, Any]:
    rows = result.get("rows") if isinstance(result.get("rows"), list) else []
    accepted = 0
    bulk_boundaries = 0
    wfs_only_rejected = 0
    conflict_rows = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        boundary = row.get("boundary", {})
        bulk_ok = has_bulk_gml_evidence(boundary)
        if bulk_ok:
            bulk_boundaries += 1
        if wfs_only(boundary):
            wfs_only_rejected += 1
        conflict = bool(row.get("human_review_required") or row.get("hmlr_bulk_wfs_conflict") or (isinstance(boundary, dict) and boundary.get("conflict")))
        if conflict:
            conflict_rows += 1
        ea = row.get("ea_dtm_1m_polygon", {})
        os_sample = row.get("os_terrain50", {})
        ea_ok = isinstance(ea, dict) and bool(ea.get("ok"))
        os_ok = isinstance(os_sample, dict) and bool(os_sample.get("ok"))
        numeric_conflict = bool(row.get("human_review_required"))
        accepted_row = bulk_ok and ea_ok and os_ok and not conflict and not numeric_conflict
        row["hmlr_official_bulk_gml_required"] = True
        row["hmlr_bulk_gml_evidence_valid"] = bulk_ok
        row["hmlr_wfs_diagnostic_only"] = wfs_only(boundary)
        row["accepted_measured_row"] = accepted_row
        if accepted_row:
            accepted += 1
            row["output_semantics"] = "MEASURED_OFFICIAL_THREE_SOURCE_BULK_GML_GATED"
            row["accuracy_score_4"] = "3.5/4"
        elif wfs_only(boundary):
            row["output_semantics"] = "NO_DATA_NOT_INFERRED_HMLR_WFS_ONLY_REJECTED"
            row["accuracy_score_4"] = "2.5/4 fallback"
        elif conflict:
            row["output_semantics"] = "HUMAN_REVIEW_HMLR_SOURCE_CONFLICT"
            row["accuracy_score_4"] = "2.5/4 not_measured"
        else:
            row["output_semantics"] = "NO_DATA_NOT_INFERRED"
            row["accuracy_score_4"] = "2.5/4 fallback"
    counts = result.setdefault("counts", {})
    counts["candidate_rows"] = len(rows)
    counts["official_bulk_gml_boundary_rows"] = bulk_boundaries
    counts["wfs_only_boundary_rows_rejected"] = wfs_only_rejected
    counts["hmlr_source_conflict_rows"] = conflict_rows
    counts["official_three_source_measured_rows"] = accepted
    result["schema_version"] = max(int(result.get("schema_version", 0) or 0), 7)
    result["payload_revision"] = 7
    result["attempt_id"] = "official-source-batch-004-revision-7-bulk-gml-authority-gate"
    result["status"] = "MEASURED_OFFICIAL_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED"
    result["hmlr_access_contract"] = {
        "accepted_geometry_delivery": "monthly_local_authority_GML",
        "api_available_for_free_inspire_product": False,
        "wfs_role": "diagnostic_crosscheck_only_not_acceptance_source",
        "publication_date": "2026-07-05",
        "authorities_requested": ["London Borough of Barnet", "London Borough of Enfield"],
        "boundary_duplicate_rule": "polygons_on_local_authority_boundaries_may_appear_in_both_files",
    }
    result["attribution"] = {"hmlr": HMLR_ATTRIBUTION, "os_geometry": OS_GEOMETRY_ATTRIBUTION, "conditions_url": "https://use-land-property-data.service.gov.uk/datasets/inspire/#conditions"}
    acceptance = result.setdefault("acceptance", {})
    acceptance["requires_official_monthly_hmlr_bulk_gml"] = True
    acceptance["wfs_only_promotion_forbidden"] = True
    acceptance["real_hmlr_polygon_required"] = True
    result["final_ready"] = False
    result["product_final_ready"] = False
    result["fake_data"] = False
    result["db_write"] = False
    result["migration"] = False
    result["production_deploy"] = False
    return result

def main() -> int:
    if not REV6_ENTRY.exists():
        raise SystemExit(f"revision_6_entry_missing:{REV6_ENTRY}")
    completed = subprocess.run([sys.executable, str(REV6_ENTRY)], cwd=str(REPO), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    if not REV6_OUT.exists():
        raise SystemExit(f"revision_6_output_missing:{REV6_OUT}")
    result = apply_gate(json.loads(REV6_OUT.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    for path in (OUT, WEB_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    snapshot = {"schema_version": 1, "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": 7, "hmlr_publication_date": "2026-07-05", "hmlr_delivery": "monthly_local_authority_GML", "hmlr_free_inspire_api_available": False, "wfs_role": "diagnostic_only", "bulk_gml_boundary_rows": result.get("counts", {}).get("official_bulk_gml_boundary_rows", 0), "wfs_only_rows_rejected": result.get("counts", {}).get("wfs_only_boundary_rows_rejected", 0), "accepted_rows": result.get("counts", {}).get("official_three_source_measured_rows", 0), "attribution": result["attribution"], "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("# Height Difference 1 revision 7 official bulk-GML authority gate result\n\n" f"- Candidate rows: `{result.get('counts', {}).get('candidate_rows', 0)}`\n" f"- Official monthly bulk-GML boundary rows: `{result.get('counts', {}).get('official_bulk_gml_boundary_rows', 0)}`\n" f"- WFS-only boundary rows rejected: `{result.get('counts', {}).get('wfs_only_boundary_rows_rejected', 0)}`\n" f"- Accepted official three-source measured rows: `{result.get('counts', {}).get('official_three_source_measured_rows', 0)}`\n" "- WFS is diagnostic-only and cannot independently promote a parcel measurement.\n" "- `final_ready=false`\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result.get("counts", {}), "output": str(OUT)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
