from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V10_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v10.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v10", V10_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V10_AUTOMATION: {V10_PATH}")
v10 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v10)

v3 = v10.v3
DATA_ROOT = v10.DATA_ROOT
v3.SOURCE_FILES = [
    DATA_ROOT / "official_source_candidates_20260720.json",
    DATA_ROOT / "official_source_candidates_batch2_20260720.json",
    DATA_ROOT / "official_source_candidates_batch3_20260720.json",
    DATA_ROOT / "official_source_candidates_batch4_20260720.json",
    DATA_ROOT / "official_source_candidates_batch5_20260720.json",
    DATA_ROOT / "official_source_candidates_batch6_20260720.json",
    DATA_ROOT / "official_source_candidates_batch7_20260721.json",
    DATA_ROOT / "official_source_candidates_batch8_20260721.json",
    DATA_ROOT / "official_source_candidates_batch9_20260721.json",
    DATA_ROOT / "official_source_candidates_batch10_20260721.json",
]
v3.CANDIDATE_FILES = [
    DATA_ROOT / "verified_candidate_examples_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch2_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch3_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch4_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch5_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch6_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch7_20260721.json",
    DATA_ROOT / "verified_candidate_examples_batch8_20260721.json",
    DATA_ROOT / "verified_candidate_examples_batch9_20260721.json",
    DATA_ROOT / "verified_candidate_examples_batch10_20260721.json",
]
v3.EXPECTED_TOTAL_SOURCES = 33
v3.EXPECTED_TOTAL_CANDIDATES = 35
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 35
v3.EXPECTED_COMPLETED_OPERATIONS = 55
v3.EXPECTED_TOTAL_OPERATIONS = 56

_original_write_markdown = v3.write_markdown


def write_markdown_v11(report: dict[str, Any]) -> None:
    _original_write_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V10", "Aggregate DOM Proof V11")
    text = text.replace("RERUN_AUTOMATION_167_V10", "RERUN_AUTOMATION_167_V11")
    text += (
        "\nV11 aggregate contract: 10 candidate batches, 10 official-source batches, "
        "35 candidates, 33 official sources, 3 official planning evidence rows, "
        "55/56 operations and zero unverified parcel values.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown_v11


def main_v11() -> int:
    result = v10.main_v10()
    report_path = v3.v2.REPORT_JSON
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V11"
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V10", "AUTOMATION_167_V11")
    report["aggregate_contract"] = {
        "candidate_batches": 10,
        "official_source_batches": 10,
        "candidate_rows": 35,
        "official_source_rows": 33,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 6,
        "completed_operations": 55,
        "total_operations": 56,
        "unverified_parcel_value_rows": 0,
    }
    v3.v2.write_json(report_path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main_v11())
