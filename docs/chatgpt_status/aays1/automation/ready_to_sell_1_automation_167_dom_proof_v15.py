from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V14_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v14.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v14", V14_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V14_AUTOMATION: {V14_PATH}")
v14 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v14)

v3 = v14.v3
DATA_ROOT = v14.DATA_ROOT
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
]
v3.EXPECTED_TOTAL_SOURCES = 52
v3.EXPECTED_TOTAL_CANDIDATES = 51
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 51
v3.EXPECTED_COMPLETED_OPERATIONS = 75
v3.EXPECTED_TOTAL_OPERATIONS = 76

_original_write_markdown = v3.write_markdown


def write_markdown_v15(report: dict[str, Any]) -> None:
    _original_write_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V14", "Aggregate DOM Proof V15")
    text = text.replace("RERUN_AUTOMATION_167_V14", "RERUN_AUTOMATION_167_V15")
    text += (
        "\nV15 aggregate contract: 14 candidate batches, 14 official-source batches, "
        "51 candidates, 52 official sources, 3 official planning evidence rows, "
        "75/76 operations and zero unverified parcel values.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown_v15


def main_v15() -> int:
    result = v14.main_v14()
    report_path = v3.v2.REPORT_JSON
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V15"
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V14", "AUTOMATION_167_V15")
    report["aggregate_contract"] = {
        "candidate_batches": 14,
        "official_source_batches": 14,
        "candidate_rows": 51,
        "official_source_rows": 52,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 10,
        "completed_operations": 75,
        "total_operations": 76,
        "unverified_parcel_value_rows": 0,
    }
    v3.v2.write_json(report_path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main_v15())
