from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v35.py"
spec = importlib.util.spec_from_file_location("rts1_v35", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v35 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v35)

v3 = v35.v3
DATA_ROOT = v35.DATA_ROOT


def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"


v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [
    batch("official_source_candidates", n) for n in range(2, 36)
]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [
    batch("verified_candidate_examples", n) for n in range(2, 36)
]
v3.EXPECTED_TOTAL_SOURCES = 351
v3.EXPECTED_TOTAL_CANDIDATES = 164
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 140
v3.EXPECTED_COMPLETED_OPERATIONS = 183
v3.EXPECTED_TOTAL_OPERATIONS = 184

previous_markdown = v3.write_markdown


def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V35", "Aggregate DOM Proof V36")
    text = text.replace("RERUN_AUTOMATION_167_V35", "RERUN_AUTOMATION_167_V36")
    text += (
        "\nV36 aggregate contract: 35 candidate/source batches, 176 raw candidate records, "
        "12 canonical-listing-URL duplicates excluded, 164 unique candidates, "
        "140 internet-reverified rows, 351 verified sources, 3 official planning evidence rows, "
        "183/184 operations and zero unverified parcel values. Favicon-only noise remains ignored; "
        "every other HTTP, DOM or browser error remains blocking.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown


def main() -> int:
    result = v35.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V36"
    aggregate = report.get("aggregate_batch_state", {})
    progress = report.get("progress_page_acceptance", {})
    report["aggregate_contract"] = {
        "candidate_batches": 35,
        "verified_source_batches": 35,
        "raw_candidate_rows": 176,
        "duplicate_candidate_rows_excluded": 12,
        "candidate_rows": 164,
        "internet_reverified_rows": 140,
        "verified_source_rows": 351,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 114,
        "completed_operations": 183,
        "total_operations": 184,
        "unverified_parcel_value_rows": 0,
    }
    report["v36_contract_observed"] = {
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
        report["next_step"] = next_step.replace("AUTOMATION_167_V35", "AUTOMATION_167_V36")
    v3.v2.write_json(path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
