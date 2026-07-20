from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V3_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v3.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v3", V3_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V3_AUTOMATION: {V3_PATH}")
v3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v3)

DATA_ROOT = v3.DATA_ROOT
v3.SOURCE_FILES = [
    DATA_ROOT / "official_source_candidates_20260720.json",
    DATA_ROOT / "official_source_candidates_batch2_20260720.json",
    DATA_ROOT / "official_source_candidates_batch3_20260720.json",
    DATA_ROOT / "official_source_candidates_batch4_20260720.json",
]
v3.CANDIDATE_FILES = [
    DATA_ROOT / "verified_candidate_examples_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch2_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch3_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch4_20260720.json",
]
v3.EXPECTED_TOTAL_SOURCES = 10
v3.EXPECTED_TOTAL_CANDIDATES = 12
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 12
v3.EXPECTED_COMPLETED_OPERATIONS = 23
v3.EXPECTED_TOTAL_OPERATIONS = 24

_original_write_markdown = v3.write_markdown


def write_markdown_v4(report: dict[str, Any]) -> None:
    _original_write_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V3", "Aggregate DOM Proof V4")
    text = text.replace("RERUN_AUTOMATION_167_V3", "RERUN_AUTOMATION_167_V4")
    text += "\nV4 aggregate contract: 4 candidate batches, 4 official-source batches, 12 candidates, 10 official sources, 23/24 operations.\n"
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown_v4


def main_v4() -> int:
    result = v3.main()
    report_path = v3.v2.REPORT_JSON
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V4"
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V3", "AUTOMATION_167_V4")
    v3.v2.write_json(report_path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main_v4())
