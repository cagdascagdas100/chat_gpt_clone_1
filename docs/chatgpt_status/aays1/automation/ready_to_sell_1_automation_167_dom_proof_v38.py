from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v37.py"
spec = importlib.util.spec_from_file_location("rts1_v37", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v37 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v37)

v3 = v37.v3
DATA_ROOT = v37.DATA_ROOT


def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"


v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [
    batch("official_source_candidates", n) for n in range(2, 38)
]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [
    batch("verified_candidate_examples", n) for n in range(2, 38)
]
v3.EXPECTED_TOTAL_SOURCES = 423
v3.EXPECTED_TOTAL_CANDIDATES = 186
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 162
v3.EXPECTED_COMPLETED_OPERATIONS = 195
v3.EXPECTED_TOTAL_OPERATIONS = 196

previous_markdown = v3.write_markdown


def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V37", "Aggregate DOM Proof V38")
    text = text.replace("RERUN_AUTOMATION_167_V37", "RERUN_AUTOMATION_167_V38")
    text += (
        "\nV38 aggregate contract: 37 candidate/source batches, 198 raw candidate records, "
        "12 canonical-listing-URL duplicates excluded, 186 unique candidates, "
        "162 internet-reverified rows, 423 verified sources, 3 official planning evidence rows, "
        "195/196 operations and zero unverified parcel values. Favicon-only noise remains ignored; "
        "every other HTTP, DOM or browser error remains blocking.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown


def main() -> int:
    result = v37.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V38"
    aggregate = report.get("aggregate_batch_state", {})
    progress = report.get("progress_page_acceptance", {})
    report["aggregate_contract"] = {
        "candidate_batches": 37,
        "verified_source_batches": 37,
        "raw_candidate_rows": 198,
        "duplicate_candidate_rows_excluded": 12,
        "candidate_rows": 186,
        "internet_reverified_rows": 162,
        "verified_source_rows": 423,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 136,
        "completed_operations": 195,
        "total_operations": 196,
        "unverified_parcel_value_rows": 0,
    }
    report["v38_contract_observed"] = {
        "raw_candidate_rows": aggregate.get("raw_candidate_count"),
        "duplicate_candidate_rows_excluded": aggregate.get("duplicate_candidate_count"),
        "candidate_rows": aggregate.get("candidate_count"),
        "internet_reverified_rows": aggregate.get("internet_reverified_count"),
        "verified_source_rows": aggregate.get("official_source_count"),
        "completed_operations": aggregate.get("completed_operations"),
        "total_operations": aggregate.get("total_operations"),
        "progress_dom_candidate_rows": progress.get("candidate_count"),
        "progress_dom_source_rows": progress.get("official_source_count"),
        "progress_dom_semantic_valid": progress.get("semantic_valid"),
    }
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V37", "AUTOMATION_167_V38")
    v3.v2.write_json(path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
