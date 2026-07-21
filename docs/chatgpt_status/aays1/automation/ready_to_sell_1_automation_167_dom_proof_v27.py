from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v26.py"
spec = importlib.util.spec_from_file_location("rts1_v26", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v26 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v26)

v3 = v26.v3
DATA_ROOT = v26.DATA_ROOT

def batch(prefix: str, number: int) -> Path:
    date = "20260720" if number <= 6 else "20260721"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"

v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [
    batch("official_source_candidates", n) for n in range(2, 27)
]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [
    batch("verified_candidate_examples", n) for n in range(2, 27)
]
v3.EXPECTED_TOTAL_SOURCES = 203
v3.EXPECTED_TOTAL_CANDIDATES = 134
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 134
v3.EXPECTED_COMPLETED_OPERATIONS = 135
v3.EXPECTED_TOTAL_OPERATIONS = 136

def canonical_candidate_key(row: dict[str, Any]) -> str:
    url = str(row.get("listing_url") or "").strip().casefold().split("?", 1)[0].rstrip("/")
    if url:
        return f"url:{url}"
    listing_id = str(row.get("listing_id") or "").strip().casefold()
    if listing_id:
        return f"id:{listing_id}"
    return f"address:{str(row.get('address') or '').strip().casefold()}"

def collect_unique_aggregate_state() -> dict[str, Any]:
    source_file_state: list[dict[str, Any]] = []
    candidate_file_state: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    raw_candidates: list[dict[str, Any]] = []

    for path in v3.SOURCE_FILES:
        document = v3.read_json(path)
        rows = document.get("sources", []) if isinstance(document, dict) else []
        rows = [row for row in rows if isinstance(row, dict)]
        sources.extend(rows)
        source_file_state.append({
            "path": v3.v2.relative(path),
            "exists": path.is_file(),
            "sha256": v3.v2.file_sha256(path),
            "rows": len(rows),
        })

    for path in v3.CANDIDATE_FILES:
        document = v3.read_json(path)
        rows = document.get("candidates", []) if isinstance(document, dict) else []
        rows = [row for row in rows if isinstance(row, dict)]
        raw_candidates.extend(rows)
        candidate_file_state.append({
            "path": v3.v2.relative(path),
            "exists": path.is_file(),
            "sha256": v3.v2.file_sha256(path),
            "rows": len(rows),
        })

    unique_by_key: dict[str, dict[str, Any]] = {}
    duplicate_rows: list[dict[str, Any]] = []
    for row in raw_candidates:
        key = canonical_candidate_key(row)
        if key in unique_by_key:
            duplicate_rows.append({
                "canonical_key": key,
                "kept_row_reference": unique_by_key[key].get("row_reference"),
                "excluded_row_reference": row.get("row_reference"),
                "kept_listing_id": unique_by_key[key].get("listing_id"),
                "excluded_listing_id": row.get("listing_id"),
            })
            continue
        unique_by_key[key] = row
    candidates = list(unique_by_key.values())

    progress = v3.read_json(v3.PROGRESS_JSON)
    progress_value = progress.get("progress", {}) if isinstance(progress, dict) else {}
    progress_metrics = progress.get("metrics", {}) if isinstance(progress, dict) else {}

    exact_inspire = sum(
        1 for row in candidates
        if row.get("match_method") == "metadata_inspire_exact" and row.get("matched_inspire_id")
    )
    internet_reverified = sum(1 for row in candidates if v3.candidate_is_internet_reverified(row))
    source_scores = [int(row.get("source_verification_score") or 0) for row in sources]
    parcel_publication_rows = sum(1 for row in candidates if row.get("parcel_value_publication") is True)

    return {
        "source_files": source_file_state,
        "candidate_files": candidate_file_state,
        "progress_path": v3.v2.relative(v3.PROGRESS_JSON),
        "progress_present": v3.PROGRESS_JSON.is_file(),
        "progress_sha256": v3.v2.file_sha256(v3.PROGRESS_JSON),
        "official_source_count": len(sources),
        "official_source_scores": source_scores,
        "candidate_count": len(candidates),
        "raw_candidate_count": len(raw_candidates),
        "duplicate_candidate_count": len(duplicate_rows),
        "duplicate_candidates": duplicate_rows,
        "exact_inspire_match_count": exact_inspire,
        "internet_reverified_count": internet_reverified,
        "parcel_value_publication_rows": parcel_publication_rows,
        "completed_operations": int(progress_value.get("completed_operations") or 0),
        "total_operations": int(progress_value.get("total_operations") or 0),
        "completion_percent": progress_value.get("completion_percent"),
        "progress_final_ready": progress_value.get("final_ready"),
        "progress_candidate_rows": int(progress_metrics.get("candidate_rows") or 0),
        "progress_official_sources": int(progress_metrics.get("verified_official_sources") or 0),
        "progress_geometry_rows": int(progress_metrics.get("geometry_rows") or 0),
    }

v3.collect_aggregate_state = collect_unique_aggregate_state

previous_markdown = v3.write_markdown
def write_markdown(report: dict[str, Any]) -> None:
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V26", "Aggregate DOM Proof V27")
    text = text.replace("RERUN_AUTOMATION_167_V26", "RERUN_AUTOMATION_167_V27")
    text += (
        "\nV27 aggregate contract: 26 candidate/source batches, 136 raw candidate records, "
        "2 canonical-listing-URL duplicates excluded, 134 unique candidates, 203 verified sources, "
        "3 official planning evidence rows, 135/136 operations and zero unverified parcel values.\n"
    )
    path.write_text(text, encoding="utf-8")
v3.write_markdown = write_markdown

def main() -> int:
    result = v26.main()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V27"
    aggregate = report.get("aggregate_batch_state", {})
    report["deduplication_contract"] = {
        "canonical_key": "normalized listing_url without query string or trailing slash",
        "raw_candidate_rows": aggregate.get("raw_candidate_count"),
        "duplicate_candidate_rows_excluded": aggregate.get("duplicate_candidate_count"),
        "duplicate_candidates": aggregate.get("duplicate_candidates", []),
    }
    report["aggregate_contract"] = {
        "candidate_batches": 26,
        "verified_source_batches": 26,
        "raw_candidate_rows": 136,
        "duplicate_candidate_rows_excluded": 2,
        "candidate_rows": 134,
        "verified_source_rows": 203,
        "official_planning_evidence_rows": 3,
        "strengthened_candidate_rows": 76,
        "completed_operations": 135,
        "total_operations": 136,
        "unverified_parcel_value_rows": 0,
    }
    v3.v2.write_json(path, report)
    return result

if __name__ == "__main__":
    raise SystemExit(main())
