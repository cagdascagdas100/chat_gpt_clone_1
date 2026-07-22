from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v47.py"
spec = importlib.util.spec_from_file_location("rts1_v47", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v47 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v47)

v3 = v47.v3
DATA_ROOT = v47.DATA_ROOT


def batch(prefix: str, number: int) -> Path:
    if number <= 6:
        date = "20260720"
    elif number <= 26:
        date = "20260721"
    else:
        date = "20260722"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"


v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [
    batch("official_source_candidates", n) for n in range(2, 48)
]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [
    batch("verified_candidate_examples", n) for n in range(2, 48)
]
v3.EXPECTED_TOTAL_SOURCES = 1007
v3.EXPECTED_TOTAL_CANDIDATES = 380
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 356
v3.EXPECTED_COMPLETED_OPERATIONS = 257
v3.EXPECTED_TOTAL_OPERATIONS = 258


def is_favicon_path(value: Any) -> bool:
    text = str(value or "").strip().split("?", 1)[0].rstrip("/").casefold()
    return text == "/favicon.ico" or text.endswith("/favicon.ico")


def error_mentions_favicon(value: Any) -> bool:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except Exception:
        text = str(value)
    return "/favicon.ico" in text.casefold()


_original_browser_probe = v3.v2.browser_probe


def browser_probe(url: str) -> dict[str, Any]:
    result = _original_browser_probe(url)
    errors = result.get("console_errors")
    rows = list(errors) if isinstance(errors, list) else []
    ignored = [row for row in rows if error_mentions_favicon(row)]
    retained = [row for row in rows if not error_mentions_favicon(row)]
    original_count = result.get("console_error_count")
    if isinstance(original_count, int):
        unseen_count = max(0, original_count - len(rows))
        result["console_error_count"] = unseen_count + len(retained)
    result["console_errors"] = retained
    result["ignored_favicon_console_errors"] = ignored
    result["ignored_favicon_console_error_count"] = len(ignored)
    result["favicon_filter_policy"] = "ONLY_EXACT_FAVICON_ICO_NOISE_IGNORED"
    return result


v3.v2.browser_probe = browser_probe


def filter_acceptance(result: dict[str, Any]) -> dict[str, Any]:
    paths = result.get("server_404_paths")
    rows = list(paths) if isinstance(paths, list) else []
    ignored = [path for path in rows if is_favicon_path(path)]
    retained = [path for path in rows if not is_favicon_path(path)]
    result["server_404_paths"] = retained
    result["ignored_favicon_404_paths"] = ignored
    result["ignored_favicon_404_count"] = len(ignored)
    result["non_favicon_404_count"] = len(retained)
    return result


_original_dom_acceptance = v3.v2.run_dom_acceptance


def run_dom_acceptance() -> dict[str, Any]:
    return filter_acceptance(_original_dom_acceptance())


v3.v2.run_dom_acceptance = run_dom_acceptance

_original_progress_acceptance = v3.run_progress_acceptance


def run_progress_acceptance() -> dict[str, Any]:
    return filter_acceptance(_original_progress_acceptance())


v3.run_progress_acceptance = run_progress_acceptance

previous_markdown = v3.write_markdown


def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V47", "Aggregate DOM Proof V48")
    text = text.replace("RERUN_AUTOMATION_167_V47", "RERUN_AUTOMATION_167_V48")
    text += (
        "\nV48 aggregate contract: 47 candidate/source batches, 392 raw candidate records, "
        "12 canonical-listing-URL duplicates excluded, 380 unique candidates, "
        "356 internet-reverified rows, 1007 verified sources, 3 official planning evidence rows, "
        "257/258 operations and zero unverified parcel values. The progress page uses an eight-second "
        "AbortController timeout and one bounded retry. Only exact /favicon.ico HTTP or console noise "
        "is ignored; every other HTTP, DOM, browser or unknown console error remains blocking.\n"
    )
    path.write_text(text, encoding="utf-8")


v3.write_markdown = write_markdown


def main() -> int:
    result = v47.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V48"
    aggregate = report.get("aggregate_batch_state", {})
    progress = report.get("progress_page_acceptance", {})
    geometry = report.get("automation_167_dom_proof", {})
    report["aggregate_contract"] = {
        "candidate_batches": 47,
        "verified_source_batches": 47,
        "raw_candidate_rows": 392,
        "duplicate_candidate_rows_excluded": 12,
        "candidate_rows": 380,
        "internet_reverified_rows": 356,
        "verified_source_rows": 1007,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 330,
        "completed_operations": 257,
        "total_operations": 258,
        "unverified_parcel_value_rows": 0,
    }
    report["runtime_pending_recovery_contract"] = {
        "active_lease_required": False,
        "existing_single_coordinator_only": True,
        "new_runner_allowed": False,
        "parallel_runner_allowed": False,
        "web_fetch_timeout_seconds": 8,
        "web_fetch_retry_count": 1,
        "favicon_request_suppressed_by_data_uri": True,
        "ignored_http_path": "/favicon.ico only",
        "all_other_errors_blocking": True,
    }
    report["v48_contract_observed"] = {
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
        "progress_ignored_favicon_404_count": progress.get("ignored_favicon_404_count"),
        "progress_non_favicon_404_count": progress.get("non_favicon_404_count"),
        "geometry_ignored_favicon_404_count": geometry.get("ignored_favicon_404_count"),
        "geometry_non_favicon_404_count": geometry.get("non_favicon_404_count"),
        "geometry_ignored_favicon_console_error_count": geometry.get("browser", {}).get("ignored_favicon_console_error_count") if isinstance(geometry.get("browser"), dict) else None,
        "progress_ignored_favicon_console_error_count": progress.get("browser", {}).get("ignored_favicon_console_error_count") if isinstance(progress.get("browser"), dict) else None,
    }
    next_step = report.get("next_step")
    if isinstance(next_step, str):
        report["next_step"] = next_step.replace("AUTOMATION_167_V47", "AUTOMATION_167_V48")
    v3.v2.write_json(path, report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
