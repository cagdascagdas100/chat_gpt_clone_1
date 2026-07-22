from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v49.py"
spec = importlib.util.spec_from_file_location("rts1_v49", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v49 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v49)

v3 = v49.v3
DATA_ROOT = v49.DATA_ROOT


def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"


v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [batch("official_source_candidates", n) for n in range(2, 50)]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [batch("verified_candidate_examples", n) for n in range(2, 50)]
v3.EXPECTED_TOTAL_SOURCES = 1193
v3.EXPECTED_TOTAL_CANDIDATES = 442
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 418
v3.EXPECTED_COMPLETED_OPERATIONS = 271
v3.EXPECTED_TOTAL_OPERATIONS = 272

previous_markdown = v3.write_markdown


def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V49", "Aggregate DOM Proof V50")
    text = text.replace("RERUN_AUTOMATION_167_V49", "RERUN_AUTOMATION_167_V50")
    text += (
        "\nV50 aggregate contract: 49 candidate/source batches, 454 raw candidate records, "
        "12 canonical-listing-URL duplicates excluded, 442 unique candidates, "
        "418 internet-reverified rows, 1193 verified sources, 3 official planning evidence rows, "
        "271/272 operations and zero unverified parcel values. The progress page retains an "
        "eight-second timeout and one bounded retry. Only exact /favicon.ico noise is ignored. "
        "The queue publishes status=queued, queue_status=queued_for_shared_coordinator_browser_acceptance, "
        "current_task=idle, claimable=true and ready_for_claim=true for backward-compatible pickup. "
        "The same task, attempt, idempotency key and existing single coordinator are mandatory.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown


def main() -> int:
    result = v49.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V50"
    aggregate = report.get("aggregate_batch_state", {})
    progress = report.get("progress_page_acceptance", {})
    geometry = report.get("automation_167_dom_proof", {})
    report["aggregate_contract"] = {
        "candidate_batches": 49,
        "verified_source_batches": 49,
        "raw_candidate_rows": 454,
        "duplicate_candidate_rows_excluded": 12,
        "candidate_rows": 442,
        "internet_reverified_rows": 418,
        "verified_source_rows": 1193,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 392,
        "completed_operations": 271,
        "total_operations": 272,
        "unverified_parcel_value_rows": 0,
    }
    report["queue_compatibility_contract"] = {
        "status": "queued",
        "queue_status": "queued_for_shared_coordinator_browser_acceptance",
        "current_task": "idle",
        "claimable": True,
        "ready_for_claim": True,
        "existing_single_coordinator_only": True,
        "new_runner_allowed": False,
        "parallel_runner_allowed": False,
        "same_task_attempt_idempotency_required": True,
        "does_not_claim_execution_without_heartbeat": True,
    }
    report["v50_contract_observed"] = {
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
        report["next_step"] = next_step.replace("AUTOMATION_167_V49", "AUTOMATION_167_V50")
    v3.v2.write_json(path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
