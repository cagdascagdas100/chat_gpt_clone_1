from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V7_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v7.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v7", V7_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V7_AUTOMATION: {V7_PATH}")
v7 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v7)

v3 = v7.v3
DATA_ROOT = v7.DATA_ROOT
v3.SOURCE_FILES = [
    DATA_ROOT / "official_source_candidates_20260720.json",
    DATA_ROOT / "official_source_candidates_batch2_20260720.json",
    DATA_ROOT / "official_source_candidates_batch3_20260720.json",
    DATA_ROOT / "official_source_candidates_batch4_20260720.json",
    DATA_ROOT / "official_source_candidates_batch5_20260720.json",
    DATA_ROOT / "official_source_candidates_batch6_20260720.json",
    DATA_ROOT / "official_source_candidates_batch7_20260721.json",
]
v3.CANDIDATE_FILES = [
    DATA_ROOT / "verified_candidate_examples_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch2_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch3_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch4_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch5_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch6_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch7_20260721.json",
]
v3.EXPECTED_TOTAL_SOURCES = 21
v3.EXPECTED_TOTAL_CANDIDATES = 23
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 23
v3.EXPECTED_COMPLETED_OPERATIONS = 38
v3.EXPECTED_TOTAL_OPERATIONS = 40

_original_write_markdown = v3.write_markdown


def write_markdown_v8(report: dict[str, Any]) -> None:
    _original_write_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V7", "Aggregate DOM Proof V8")
    text = text.replace("RERUN_AUTOMATION_167_V7", "RERUN_AUTOMATION_167_V8")
    text += (
        "\nV8 aggregate contract: 7 candidate batches, 7 official-source batches, "
        "23 candidates, 21 official sources, 3 official planning evidence rows, "
        "38/40 operations and zero unverified parcel values.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown_v8


def main_v8() -> int:
    result = v7.main_v7()
    report_path = v3.v2.REPORT_JSON
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V8"
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V7", "AUTOMATION_167_V8")
    report["aggregate_contract"] = {
        "candidate_batches": 7,
        "official_source_batches": 7,
        "candidate_rows": 23,
        "official_source_rows": 21,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 3,
        "completed_operations": 38,
        "total_operations": 40,
        "unverified_parcel_value_rows": 0,
    }
    v3.v2.write_json(report_path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main_v8())
