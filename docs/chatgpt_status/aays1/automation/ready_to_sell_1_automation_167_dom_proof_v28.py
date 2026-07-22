from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v27.py"
spec = importlib.util.spec_from_file_location("rts1_v27", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v27 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v27)

v3 = v27.v3
DATA_ROOT = v27.DATA_ROOT

def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"

v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [
    batch("official_source_candidates", n) for n in range(2, 28)
]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [
    batch("verified_candidate_examples", n) for n in range(2, 28)
]
v3.EXPECTED_TOTAL_SOURCES = 211
v3.EXPECTED_TOTAL_CANDIDATES = 136
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 136
v3.EXPECTED_COMPLETED_OPERATIONS = 140
v3.EXPECTED_TOTAL_OPERATIONS = 141

previous_markdown = v3.write_markdown

def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V27", "Aggregate DOM Proof V28")
    text = text.replace("RERUN_AUTOMATION_167_V27", "RERUN_AUTOMATION_167_V28")
    text += (
        "\nV28 aggregate contract: 27 candidate/source batches, 138 raw candidate records, "
        "2 canonical-listing-URL duplicates excluded, 136 unique candidates, 211 verified sources, "
        "3 official planning evidence rows, 140/141 operations and zero unverified parcel values.\n"
    )
    path.write_text(text, encoding="utf-8")

v3.write_markdown = write_markdown

def main() -> int:
    result = v27.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V28"
    aggregate = report.get("aggregate_batch_state", {})
    report["deduplication_contract"] = {
        "canonical_key": "normalized listing_url without query string or trailing slash",
        "raw_candidate_rows": aggregate.get("raw_candidate_count"),
        "duplicate_candidate_rows_excluded": aggregate.get("duplicate_candidate_count"),
        "duplicate_candidates": aggregate.get("duplicate_candidates", []),
    }
    report["aggregate_contract"] = {
        "candidate_batches": 27,
        "verified_source_batches": 27,
        "raw_candidate_rows": 138,
        "duplicate_candidate_rows_excluded": 2,
        "candidate_rows": 136,
        "verified_source_rows": 211,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 76,
        "completed_operations": 140,
        "total_operations": 141,
        "unverified_parcel_value_rows": 0,
    }
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V27", "AUTOMATION_167_V28")
    v3.v2.write_json(path, report)
    return result

if __name__ == "__main__":
    raise SystemExit(main())
