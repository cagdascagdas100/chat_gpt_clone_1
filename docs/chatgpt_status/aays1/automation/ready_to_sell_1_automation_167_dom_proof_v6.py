from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V5_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v5.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v5", V5_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V5_AUTOMATION: {V5_PATH}")
v5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v5)

v3 = v5.v3
DATA_ROOT = v5.DATA_ROOT
v3.SOURCE_FILES = [
    DATA_ROOT / "official_source_candidates_20260720.json",
    DATA_ROOT / "official_source_candidates_batch2_20260720.json",
    DATA_ROOT / "official_source_candidates_batch3_20260720.json",
    DATA_ROOT / "official_source_candidates_batch4_20260720.json",
    DATA_ROOT / "official_source_candidates_batch5_20260720.json",
    DATA_ROOT / "official_source_candidates_batch6_20260720.json",
]
v3.CANDIDATE_FILES = [
    DATA_ROOT / "verified_candidate_examples_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch2_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch3_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch4_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch5_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch6_20260720.json",
]
v3.EXPECTED_TOTAL_SOURCES = 18
v3.EXPECTED_TOTAL_CANDIDATES = 20
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 20
v3.EXPECTED_COMPLETED_OPERATIONS = 31
v3.EXPECTED_TOTAL_OPERATIONS = 32

_original_write_markdown = v3.write_markdown


def write_markdown_v6(report: dict[str, Any]) -> None:
    _original_write_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V5", "Aggregate DOM Proof V6")
    text = text.replace("RERUN_AUTOMATION_167_V5", "RERUN_AUTOMATION_167_V6")
    text += (
        "\nV6 aggregate contract: 6 candidate batches, 6 official-source batches, "
        "20 candidates, 18 official sources, 31/32 operations.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown_v6


def main_v6() -> int:
    result = v5.main_v5()
    report_path = v3.v2.REPORT_JSON
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V6"
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V5", "AUTOMATION_167_V6")
    report["aggregate_contract"] = {
        "candidate_batches": 6,
        "official_source_batches": 6,
        "candidate_rows": 20,
        "official_source_rows": 18,
        "completed_operations": 31,
        "total_operations": 32,
        "unverified_parcel_value_rows": 0,
    }
    v3.v2.write_json(report_path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main_v6())
