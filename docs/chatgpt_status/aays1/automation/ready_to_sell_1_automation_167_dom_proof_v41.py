from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v40.py"
spec = importlib.util.spec_from_file_location("rts1_v40", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v40 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v40)

v3 = v40.v3
DATA_ROOT = v40.DATA_ROOT


def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"


v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [
    batch("official_source_candidates", n) for n in range(2, 41)
]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [
    batch("verified_candidate_examples", n) for n in range(2, 41)
]
v3.EXPECTED_TOTAL_SOURCES = 545
v3.EXPECTED_TOTAL_CANDIDATES = 226
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 202
v3.EXPECTED_COMPLETED_OPERATIONS = 213
v3.EXPECTED_TOTAL_OPERATIONS = 214

previous_markdown = v3.write_markdown


def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V40", "Aggregate DOM Proof V41")
    text = text.replace("RERUN_AUTOMATION_167_V40", "RERUN_AUTOMATION_167_V41")
    text += (
        "\nV41 aggregate contract: 40 candidate/source batches, 238 raw candidate records, "
        "12 canonical-listing-URL duplicates excluded, 226 unique candidates, "
        "202 internet-reverified rows, 545 verified sources, 3 official planning evidence rows, "
        "213/214 operations and zero unverified parcel values. Favicon-only noise remains ignored; "
        "every other HTTP, DOM or browser error remains blocking.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown


def main() -> int:
    result = v40.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V41"
    aggregate = report.get("aggregate_batch_state", {})
    progress = report.get("progress_page_acceptance", {})
    report["aggregate_contract"] = {
        "candidate_batches": 40,
        "verified_source_batches": 40,
        "raw_candidate_rows": 238,
        "duplicate_candidate_rows_excluded": 12,
        "candidate_rows": 226,
        "internet_reverified_rows": 202,
        "verified_source_rows": 545,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 176,
        "completed_operations": 213,
        "total_operations": 214,
        "unverified_parcel_value_rows": 0,
    }
    report["v41_contract_observed"] = {
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
        report["next_step"] = next_step.replace("AUTOMATION_167_V40", "AUTOMATION_167_V41")
    v3.v2.write_json(path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
