from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V4_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v4.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v4", V4_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V4_AUTOMATION: {V4_PATH}")
v4 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v4)

v3 = v4.v3
DATA_ROOT = v4.DATA_ROOT
v3.SOURCE_FILES = [
    DATA_ROOT / "official_source_candidates_20260720.json",
    DATA_ROOT / "official_source_candidates_batch2_20260720.json",
    DATA_ROOT / "official_source_candidates_batch3_20260720.json",
    DATA_ROOT / "official_source_candidates_batch4_20260720.json",
    DATA_ROOT / "official_source_candidates_batch5_20260720.json",
]
v3.CANDIDATE_FILES = [
    DATA_ROOT / "verified_candidate_examples_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch2_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch3_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch4_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch5_20260720.json",
]
v3.EXPECTED_TOTAL_SOURCES = 14
v3.EXPECTED_TOTAL_CANDIDATES = 16
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 16
v3.EXPECTED_COMPLETED_OPERATIONS = 27
v3.EXPECTED_TOTAL_OPERATIONS = 28

_original_write_markdown = v3.write_markdown


def write_markdown_v5(report: dict[str, Any]) -> None:
    _original_write_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V4", "Aggregate DOM Proof V5")
    text = text.replace("RERUN_AUTOMATION_167_V4", "RERUN_AUTOMATION_167_V5")
    text += (
        "\nV5 aggregate contract: 5 candidate batches, 5 official-source batches, "
        "16 candidates, 14 official sources, 27/28 operations.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown_v5


def main_v5() -> int:
    result = v4.main_v4()
    report_path = v3.v2.REPORT_JSON
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V5"
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V4", "AUTOMATION_167_V5")
    report["aggregate_contract"] = {
        "candidate_batches": 5,
        "official_source_batches": 5,
        "candidate_rows": 16,
        "official_source_rows": 14,
        "completed_operations": 27,
        "total_operations": 28,
        "unverified_parcel_value_rows": 0,
    }
    v3.v2.write_json(report_path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main_v5())
