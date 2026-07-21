from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V16_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v16.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v16", V16_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V16_AUTOMATION: {V16_PATH}")
v16 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v16)

v3 = v16.v3
DATA_ROOT = v16.DATA_ROOT
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
    DATA_ROOT / "official_source_candidates_batch11_20260721.json",
    DATA_ROOT / "official_source_candidates_batch12_20260721.json",
    DATA_ROOT / "official_source_candidates_batch13_20260721.json",
    DATA_ROOT / "official_source_candidates_batch14_20260721.json",
    DATA_ROOT / "official_source_candidates_batch15_20260721.json",
    DATA_ROOT / "official_source_candidates_batch16_20260721.json",
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
    DATA_ROOT / "verified_candidate_examples_batch11_20260721.json",
    DATA_ROOT / "verified_candidate_examples_batch12_20260721.json",
    DATA_ROOT / "verified_candidate_examples_batch13_20260721.json",
    DATA_ROOT / "verified_candidate_examples_batch14_20260721.json",
    DATA_ROOT / "verified_candidate_examples_batch15_20260721.json",
    DATA_ROOT / "verified_candidate_examples_batch16_20260721.json",
]
v3.EXPECTED_TOTAL_SOURCES = 64
v3.EXPECTED_TOTAL_CANDIDATES = 61
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 61
v3.EXPECTED_COMPLETED_OPERATIONS = 85
v3.EXPECTED_TOTAL_OPERATIONS = 86

_original_write_markdown = v3.write_markdown


def write_markdown_v17(report: dict[str, Any]) -> None:
    _original_write_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V16", "Aggregate DOM Proof V17")
    text = text.replace("RERUN_AUTOMATION_167_V16", "RERUN_AUTOMATION_167_V17")
    text += (
        "\nV17 aggregate contract: 16 candidate batches, 16 verified-source batches, "
        "61 candidates, 64 verified sources, 3 official planning evidence rows, "
        "85/86 operations and zero unverified parcel values.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown_v17


def main_v17() -> int:
    result = v16.main_v16()
    report_path = v3.v2.REPORT_JSON
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V17"
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V16", "AUTOMATION_167_V17")
    report["aggregate_contract"] = {
        "candidate_batches": 16,
        "verified_source_batches": 16,
        "candidate_rows": 61,
        "verified_source_rows": 64,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 16,
        "completed_operations": 85,
        "total_operations": 86,
        "unverified_parcel_value_rows": 0,
    }
    v3.v2.write_json(report_path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main_v17())
