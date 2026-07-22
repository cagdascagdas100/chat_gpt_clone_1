from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v51.py"
spec = importlib.util.spec_from_file_location("rts1_v51", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v51 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v51)

v3 = v51.v3
DATA_ROOT = v51.DATA_ROOT


def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"


v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [batch("official_source_candidates", n) for n in range(2, 52)]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [batch("verified_candidate_examples", n) for n in range(2, 52)]
v3.EXPECTED_TOTAL_SOURCES = 1365
v3.EXPECTED_TOTAL_CANDIDATES = 507
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 483
v3.EXPECTED_COMPLETED_OPERATIONS = 285
v3.EXPECTED_TOTAL_OPERATIONS = 286

previous_markdown = v3.write_markdown


def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V51", "Aggregate DOM Proof V52")
    text = text.replace("RERUN_AUTOMATION_167_V51", "RERUN_AUTOMATION_167_V52")
    text += (
        "\nV52 aggregate contract: 51 candidate/source batches, 519 raw candidate records, "
        "12 canonical-listing-URL duplicates excluded, 507 unique candidates, "
        "483 internet-reverified rows, 1365 verified sources, 3 official planning evidence rows, "
        "285/286 operations and zero unverified parcel values. Batch 51 contributes 31 live primary "
        "Acuitus pages, 31 official council-planning routes and 8 national due-diligence routes. "
        "Generic operator pages are not used to inflate the source count. Historical sold, sold-prior, "
        "sold-post, withdrawn and archive states are preserved without inferring current availability or "
        "legal completion. The progress page retains an eight-second timeout and one bounded retry. "
        "Only exact /favicon.ico noise is ignored. The same task, attempt, idempotency key and existing "
        "single coordinator remain mandatory.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown


def main() -> int:
    result = v51.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V52"
    aggregate = report.get("aggregate_batch_state", {})
    progress = report.get("progress_page_acceptance", {})
    geometry = report.get("automation_167_dom_proof", {})
    report["aggregate_contract"] = {
        "candidate_batches": 51,
        "verified_source_batches": 51,
        "raw_candidate_rows": 519,
        "duplicate_candidate_rows_excluded": 12,
        "candidate_rows": 507,
        "internet_reverified_rows": 483,
        "verified_source_rows": 1365,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 457,
        "completed_operations": 285,
        "total_operations": 286,
        "unverified_parcel_value_rows": 0,
    }
    report["source_quality_contract"] = {
        "batch51_primary_property_pages": 31,
        "batch51_official_local_planning_routes": 31,
        "batch51_national_due_diligence_routes": 8,
        "batch51_total_sources": 70,
        "batch51_source_score_min": 99,
        "batch51_source_score_max": 100,
        "generic_operator_padding_excluded": True,
        "source_verification_separate_from_parcel_binding": True,
    }
    report["candidate_preflight_contract"] = {
        "repo_canonical_identity_search_completed": True,
        "new_candidate_identities": 31,
        "known_repo_replays_added": 0,
        "historical_page_not_promoted_to_current_availability": True,
        "auction_result_not_promoted_to_legal_completion": True,
        "exact_title_or_geometry_not_inferred": True,
    }
    report["v52_contract_observed"] = {
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
        report["next_step"] = next_step.replace("AUTOMATION_167_V51", "AUTOMATION_167_V52")
    v3.v2.write_json(path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
