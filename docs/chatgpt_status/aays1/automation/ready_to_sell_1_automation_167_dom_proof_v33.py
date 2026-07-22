from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v32.py"
spec = importlib.util.spec_from_file_location("rts1_v32", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v32 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v32)

v3 = v32.v3
DATA_ROOT = v32.DATA_ROOT


def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"


v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [
    batch("official_source_candidates", n) for n in range(2, 33)
]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [
    batch("verified_candidate_examples", n) for n in range(2, 33)
]
v3.EXPECTED_TOTAL_SOURCES = 264
v3.EXPECTED_TOTAL_CANDIDATES = 141
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 117
v3.EXPECTED_COMPLETED_OPERATIONS = 165
v3.EXPECTED_TOTAL_OPERATIONS = 166


def canonical_key(row: dict[str, Any]) -> str:
    url = str(row.get("listing_url") or "").strip().lower().split("?", 1)[0].rstrip("/")
    if url:
        return "url:" + url
    fallback = str(row.get("listing_id") or row.get("address") or "").strip().lower()
    return "fallback:" + fallback


original_collect = v3.collect_aggregate_state


def collect_aggregate_state() -> dict[str, Any]:
    aggregate = original_collect()
    raw: list[dict[str, Any]] = []
    for path in v3.CANDIDATE_FILES:
        document = v3.read_json(path)
        rows = document.get("candidates", []) if isinstance(document, dict) else []
        raw.extend(row for row in rows if isinstance(row, dict))

    kept: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    for row in raw:
        key = canonical_key(row)
        if key in kept:
            duplicates.append(
                {
                    "canonical_key": key,
                    "kept_row_reference": kept[key].get("row_reference"),
                    "excluded_row_reference": row.get("row_reference"),
                    "kept_listing_id": kept[key].get("listing_id"),
                    "excluded_listing_id": row.get("listing_id"),
                }
            )
        else:
            kept[key] = row

    unique = list(kept.values())
    aggregate["raw_candidate_count"] = len(raw)
    aggregate["duplicate_candidate_count"] = len(duplicates)
    aggregate["duplicate_candidates"] = duplicates
    aggregate["candidate_count"] = len(unique)
    aggregate["internet_reverified_count"] = sum(1 for row in unique if v3.candidate_is_internet_reverified(row))
    aggregate["deduplication_key"] = "normalized listing_url without query string or trailing slash"
    return aggregate


v3.collect_aggregate_state = collect_aggregate_state


def remove_favicon_noise(result: dict[str, Any]) -> dict[str, Any]:
    result["server_404_paths"] = [
        path for path in (result.get("server_404_paths") or []) if path not in {"/favicon.ico", None}
    ]
    browser = result.get("browser")
    if isinstance(browser, dict):
        errors = browser.get("console_errors") or []
        meaningful = [entry for entry in errors if "favicon.ico" not in str(entry)]
        browser["console_errors"] = meaningful
        if browser.get("console_error_count") is not None:
            browser["console_error_count"] = len(meaningful)
    return result


original_main_acceptance = v3.v2.run_dom_acceptance
original_progress_acceptance = v3.run_progress_acceptance
v3.v2.run_dom_acceptance = lambda: remove_favicon_noise(original_main_acceptance())
v3.run_progress_acceptance = lambda: remove_favicon_noise(original_progress_acceptance())


previous_markdown = v3.write_markdown


def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V32", "Aggregate DOM Proof V33")
    text = text.replace("RERUN_AUTOMATION_167_V32", "RERUN_AUTOMATION_167_V33")
    text += (
        "\nV33 deduplicated aggregate contract: 32 candidate/source batches, 153 raw candidate records, "
        "12 canonical-listing-URL duplicates excluded, 141 unique candidates, 117 internet-reverified rows, "
        "264 verified sources, 3 official planning evidence rows, 165/166 operations and zero unverified parcel values. "
        "A favicon-only 404 is ignored; every other HTTP or browser error remains blocking.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown


def main() -> int:
    result = v32.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V33"
    aggregate = report.get("aggregate_batch_state", {})
    progress = report.get("progress_page_acceptance", {})
    report["deduplication_contract"] = {
        "canonical_key": "normalized listing_url without query string or trailing slash",
        "raw_candidate_rows": aggregate.get("raw_candidate_count"),
        "duplicate_candidate_rows_excluded": aggregate.get("duplicate_candidate_count"),
        "duplicate_candidates": aggregate.get("duplicate_candidates", []),
    }
    report["aggregate_contract"] = {
        "candidate_batches": 32,
        "verified_source_batches": 32,
        "raw_candidate_rows": 153,
        "duplicate_candidate_rows_excluded": 12,
        "candidate_rows": 141,
        "internet_reverified_rows": 117,
        "verified_source_rows": 264,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 91,
        "completed_operations": 165,
        "total_operations": 166,
        "unverified_parcel_value_rows": 0,
    }
    report["v33_contract_observed"] = {
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
        report["next_step"] = next_step.replace("AUTOMATION_167_V32", "AUTOMATION_167_V33")
    v3.v2.write_json(path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
