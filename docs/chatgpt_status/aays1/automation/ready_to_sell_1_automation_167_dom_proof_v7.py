from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V6_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v6.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v6", V6_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V6_AUTOMATION: {V6_PATH}")
v6 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v6)

v3 = v6.v3
DATA_ROOT = v6.DATA_ROOT
PLANNING_EVIDENCE = DATA_ROOT / "official_planning_corroboration_batch7_20260721.json"
EXPECTED_PLANNING_EVIDENCE_ROWS = 3
EXPECTED_STRENGTHENED_CANDIDATE_ROWS = 3

v3.EXPECTED_COMPLETED_OPERATIONS = 34
v3.EXPECTED_TOTAL_OPERATIONS = 35

_original_collect_aggregate_state = v3.collect_aggregate_state
_original_aggregate_blockers = v3.aggregate_blockers
_original_write_markdown = v3.write_markdown


def collect_aggregate_state_v7() -> dict[str, Any]:
    state = _original_collect_aggregate_state()
    document = v3.read_json(PLANNING_EVIDENCE)
    rows = document.get("evidence_rows", []) if isinstance(document, dict) else []
    rows = [row for row in rows if isinstance(row, dict)]
    candidate_refs = {
        int(row.get("candidate_row_reference"))
        for row in rows
        if str(row.get("candidate_row_reference") or "").isdigit()
    }
    parcel_value_rows = sum(1 for row in rows if row.get("parcel_value_publication") is True)
    state.update(
        {
            "official_planning_evidence_path": v3.v2.relative(PLANNING_EVIDENCE),
            "official_planning_evidence_present": PLANNING_EVIDENCE.is_file(),
            "official_planning_evidence_sha256": v3.v2.file_sha256(PLANNING_EVIDENCE),
            "official_planning_evidence_count": len(rows),
            "official_planning_strengthened_candidate_count": len(candidate_refs),
            "official_planning_evidence_parcel_value_rows": parcel_value_rows,
        }
    )
    return state


def aggregate_blockers_v7(
    aggregate: dict[str, Any], progress_acceptance: dict[str, Any]
) -> list[str]:
    blockers = _original_aggregate_blockers(aggregate, progress_acceptance)
    if not aggregate.get("official_planning_evidence_present"):
        blockers.append("OFFICIAL_PLANNING_EVIDENCE_BATCH7_MISSING")
    if aggregate.get("official_planning_evidence_count") != EXPECTED_PLANNING_EVIDENCE_ROWS:
        blockers.append("OFFICIAL_PLANNING_EVIDENCE_ROW_COUNT_NOT_3")
    if (
        aggregate.get("official_planning_strengthened_candidate_count")
        != EXPECTED_STRENGTHENED_CANDIDATE_ROWS
    ):
        blockers.append("OFFICIAL_PLANNING_STRENGTHENED_CANDIDATE_COUNT_NOT_3")
    if aggregate.get("official_planning_evidence_parcel_value_rows") != 0:
        blockers.append("OFFICIAL_PLANNING_EVIDENCE_UNVERIFIED_VALUE_PUBLICATION_DETECTED")
    return list(dict.fromkeys(blockers))


def write_markdown_v7(report: dict[str, Any]) -> None:
    _original_write_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V6", "Aggregate DOM Proof V7")
    text = text.replace("RERUN_AUTOMATION_167_V6", "RERUN_AUTOMATION_167_V7")
    aggregate = report.get("aggregate_batch_state", {})
    text += (
        "\nV7 evidence contract: 20 candidates, 18 official sources, "
        f"{aggregate.get('official_planning_evidence_count')} official planning evidence rows, "
        "34/35 operations and zero unverified parcel values.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.collect_aggregate_state = collect_aggregate_state_v7
v3.aggregate_blockers = aggregate_blockers_v7
v3.write_markdown = write_markdown_v7


def main_v7() -> int:
    result = v6.main_v6()
    report_path = v3.v2.REPORT_JSON
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V7"
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V6", "AUTOMATION_167_V7")
    report["aggregate_contract"] = {
        "candidate_batches": 6,
        "official_source_batches": 6,
        "candidate_rows": 20,
        "official_source_rows": 18,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 3,
        "completed_operations": 34,
        "total_operations": 35,
        "unverified_parcel_value_rows": 0,
    }
    v3.v2.write_json(report_path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main_v7())
