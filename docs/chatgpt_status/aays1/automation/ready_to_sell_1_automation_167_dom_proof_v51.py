from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v50.py"
spec = importlib.util.spec_from_file_location("rts1_v50", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v50 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v50)

v3 = v50.v3
DATA_ROOT = v50.DATA_ROOT


def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"


v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [batch("official_source_candidates", n) for n in range(2, 51)]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [batch("verified_candidate_examples", n) for n in range(2, 51)]
v3.EXPECTED_TOTAL_SOURCES = 1295
v3.EXPECTED_TOTAL_CANDIDATES = 476
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 452
v3.EXPECTED_COMPLETED_OPERATIONS = 278
v3.EXPECTED_TOTAL_OPERATIONS = 279

previous_markdown = v3.write_markdown


def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V50", "Aggregate DOM Proof V51")
    text = text.replace("RERUN_AUTOMATION_167_V50", "RERUN_AUTOMATION_167_V51")
    text += (
        "\nV51 aggregate contract: 50 candidate/source batches, 488 raw candidate records, "
        "12 canonical-listing-URL duplicates excluded, 476 unique candidates, "
        "452 internet-reverified rows, 1295 verified sources, 3 official planning evidence rows, "
        "278/279 operations and zero unverified parcel values. Scotland, Aberdeen and the known "
        "Tottenham physical-property replay were excluded before publication. The progress page "
        "retains an eight-second timeout and one bounded retry. Only exact /favicon.ico noise is "
        "ignored. The same task, attempt, idempotency key and existing single coordinator remain mandatory.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown


def main() -> int:
    result = v50.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V51"
    aggregate = report.get("aggregate_batch_state", {})
    progress = report.get("progress_page_acceptance", {})
    geometry = report.get("automation_167_dom_proof", {})
    report["aggregate_contract"] = {
        "candidate_batches": 50,
        "verified_source_batches": 50,
        "raw_candidate_rows": 488,
        "duplicate_candidate_rows_excluded": 12,
        "candidate_rows": 476,
        "internet_reverified_rows": 452,
        "verified_source_rows": 1295,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 426,
        "completed_operations": 278,
        "total_operations": 279,
        "unverified_parcel_value_rows": 0,
    }
    report["candidate_preflight_contract"] = {
        "scotland_excluded": True,
        "aberdeen_excluded": True,
        "known_physical_property_replay_excluded": "500-508 High Road Tottenham",
        "historical_page_not_promoted_to_current_availability": True,
        "exact_title_or_geometry_not_inferred": True,
    }
    report["v51_contract_observed"] = {
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
        "progress_non_favicon_404_count": progress.get("non_favicon_404_count"),
        "geometry_non_favicon_404_count": geometry.get("non_favicon_404_count"),
        "progress_acceptance_error": progress.get("acceptance_error"),
    }
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V50", "AUTOMATION_167_V51")
    v3.v2.write_json(path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
