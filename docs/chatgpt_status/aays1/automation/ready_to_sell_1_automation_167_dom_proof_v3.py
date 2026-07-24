from __future__ import annotations

import importlib.util
import json
import os
import threading
import time
from functools import partial
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V2_PATH = HERE / "ready_to_sell_1_automation_167_dom_proof_v2.py"
SPEC = importlib.util.spec_from_file_location("ready_to_sell_1_automation_167_v2", V2_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"CANNOT_LOAD_V2_AUTOMATION: {V2_PATH}")
v2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v2)

ROOT = v2.ROOT
SLOT_ID = v2.SLOT_ID
TASK_STEP = v2.TASK_STEP
DATA_ROOT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID
PROGRESS_HTML = DATA_ROOT / "progress.html"
PROGRESS_JSON = DATA_ROOT / "progress_latest.json"
SOURCE_FILES = [
    DATA_ROOT / "official_source_candidates_20260720.json",
    DATA_ROOT / "official_source_candidates_batch2_20260720.json",
    DATA_ROOT / "official_source_candidates_batch3_20260720.json",
]
CANDIDATE_FILES = [
    DATA_ROOT / "verified_candidate_examples_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch2_20260720.json",
    DATA_ROOT / "verified_candidate_examples_batch3_20260720.json",
]
EXPECTED_TOTAL_SOURCES = 8
EXPECTED_TOTAL_CANDIDATES = 9
EXPECTED_EXACT_INSPIRE = 2
EXPECTED_INTERNET_REVERIFIED = 9
EXPECTED_COMPLETED_OPERATIONS = 19
EXPECTED_TOTAL_OPERATIONS = 20


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def candidate_is_internet_reverified(row: dict[str, Any]) -> bool:
    readback = row.get("internet_readback")
    if not isinstance(readback, dict):
        return False
    positive_keys = (
        "listing_page_live",
        "rightmove_page_live",
        "onthemarket_page_live",
        "auctioneer_page_live",
        "selling_agent_page_live",
        "secondary_channels_live",
        "primary_channel_live",
        "marketplace_page_live",
    )
    return any(readback.get(key) is True for key in positive_keys)


def collect_aggregate_state() -> dict[str, Any]:
    source_documents = [read_json(path) for path in SOURCE_FILES]
    candidate_documents = [read_json(path) for path in CANDIDATE_FILES]
    progress = read_json(PROGRESS_JSON)

    sources: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    source_file_state: list[dict[str, Any]] = []
    candidate_file_state: list[dict[str, Any]] = []
    parcel_publication_rows = 0

    for path, document in zip(SOURCE_FILES, source_documents):
        rows = document.get("sources", []) if isinstance(document, dict) else []
        rows = [row for row in rows if isinstance(row, dict)]
        sources.extend(rows)
        source_file_state.append(
            {
                "path": v2.relative(path),
                "exists": path.is_file(),
                "sha256": v2.file_sha256(path),
                "rows": len(rows),
            }
        )

    for path, document in zip(CANDIDATE_FILES, candidate_documents):
        rows = document.get("candidates", []) if isinstance(document, dict) else []
        rows = [row for row in rows if isinstance(row, dict)]
        candidates.extend(rows)
        summary = document.get("summary", {}) if isinstance(document, dict) else {}
        parcel_publication_rows += int(summary.get("parcel_value_publication_rows") or 0)
        candidate_file_state.append(
            {
                "path": v2.relative(path),
                "exists": path.is_file(),
                "sha256": v2.file_sha256(path),
                "rows": len(rows),
            }
        )

    exact_inspire = sum(
        1
        for row in candidates
        if row.get("match_method") == "metadata_inspire_exact" and row.get("matched_inspire_id")
    )
    internet_reverified = sum(1 for row in candidates if candidate_is_internet_reverified(row))
    source_scores = [int(row.get("source_verification_score") or 0) for row in sources]
    progress_value = progress.get("progress", {}) if isinstance(progress, dict) else {}
    progress_metrics = progress.get("metrics", {}) if isinstance(progress, dict) else {}

    return {
        "source_files": source_file_state,
        "candidate_files": candidate_file_state,
        "progress_path": v2.relative(PROGRESS_JSON),
        "progress_present": PROGRESS_JSON.is_file(),
        "progress_sha256": v2.file_sha256(PROGRESS_JSON),
        "official_source_count": len(sources),
        "official_source_scores": source_scores,
        "candidate_count": len(candidates),
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


def run_progress_acceptance() -> dict[str, Any]:
    v2.CaptureHandler.events = []
    handler = partial(v2.CaptureHandler, directory=str(ROOT))
    server = v2.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = int(server.server_port)

    targets = {"progress_html": PROGRESS_HTML, "progress_json": PROGRESS_JSON}
    for index, path in enumerate(SOURCE_FILES, start=1):
        targets[f"source_batch_{index}"] = path
    for index, path in enumerate(CANDIDATE_FILES, start=1):
        targets[f"candidate_batch_{index}"] = path
    urls = {key: f"http://127.0.0.1:{port}/{v2.relative(path)}" for key, path in targets.items()}

    try:
        http = {key: v2.http_get(url) for key, url in urls.items()}
        browser = v2.browser_probe(urls["progress_html"])
        time.sleep(0.5)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    dom = str(browser.get("dom") or "")
    candidate_count = v2.parse_int(v2.html_data_attribute(dom, "candidate-count"))
    official_source_count = v2.parse_int(v2.html_data_attribute(dom, "official-source-count"))
    completed_operations = v2.parse_int(v2.html_data_attribute(dom, "completed-operations"))
    total_operations = v2.parse_int(v2.html_data_attribute(dom, "total-operations"))
    semantic_valid = v2.html_data_attribute(dom, "semantic-valid")
    server_404_paths = [event.get("path") for event in v2.CaptureHandler.events if event.get("status") == 404]

    return {
        "targets": {
            key: {
                "path": v2.relative(path),
                "exists": path.is_file(),
                "sha256": v2.file_sha256(path),
                "http": http[key],
            }
            for key, path in targets.items()
        },
        "browser": {key: value for key, value in browser.items() if key != "dom"},
        "dom_bytes": len(dom.encode("utf-8")),
        "dom_sha256": browser.get("dom_sha256"),
        "candidate_count": candidate_count,
        "official_source_count": official_source_count,
        "completed_operations": completed_operations,
        "total_operations": total_operations,
        "semantic_valid": semantic_valid,
        "blocked_text_present": "BLOCKED:" in dom,
        "operations_panel_present": "Operasyonlar" in dom,
        "candidates_panel_present": "Adaylar" in dom,
        "sources_panel_present": "Resmî kaynaklar" in dom,
        "server_events": v2.CaptureHandler.events,
        "server_404_paths": server_404_paths,
    }


def aggregate_blockers(aggregate: dict[str, Any], progress_acceptance: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if aggregate["official_source_count"] != EXPECTED_TOTAL_SOURCES:
        blockers.append("AGGREGATE_OFFICIAL_SOURCE_COUNT_NOT_8")
    if aggregate["official_source_scores"] and min(aggregate["official_source_scores"]) < 90:
        blockers.append("AGGREGATE_OFFICIAL_SOURCE_SCORE_BELOW_90")
    if aggregate["candidate_count"] != EXPECTED_TOTAL_CANDIDATES:
        blockers.append("AGGREGATE_CANDIDATE_COUNT_NOT_9")
    if aggregate["exact_inspire_match_count"] != EXPECTED_EXACT_INSPIRE:
        blockers.append("AGGREGATE_EXACT_INSPIRE_COUNT_NOT_2")
    if aggregate["internet_reverified_count"] != EXPECTED_INTERNET_REVERIFIED:
        blockers.append("AGGREGATE_INTERNET_REVERIFIED_COUNT_NOT_9")
    if aggregate["parcel_value_publication_rows"] != 0:
        blockers.append("AGGREGATE_UNVERIFIED_PARCEL_VALUE_PUBLICATION_DETECTED")
    if aggregate["completed_operations"] != EXPECTED_COMPLETED_OPERATIONS:
        blockers.append("PROGRESS_COMPLETED_OPERATIONS_NOT_19")
    if aggregate["total_operations"] != EXPECTED_TOTAL_OPERATIONS:
        blockers.append("PROGRESS_TOTAL_OPERATIONS_NOT_20")
    if aggregate["progress_final_ready"] is not False:
        blockers.append("PROGRESS_FINAL_READY_FALSE_CONTRACT_MISSING")
    if aggregate["progress_candidate_rows"] != EXPECTED_TOTAL_CANDIDATES:
        blockers.append("PROGRESS_METRIC_CANDIDATE_ROWS_NOT_9")
    if aggregate["progress_official_sources"] != EXPECTED_TOTAL_SOURCES:
        blockers.append("PROGRESS_METRIC_OFFICIAL_SOURCES_NOT_8")
    if aggregate["progress_geometry_rows"] != v2.EXPECTED_GEOMETRY_ROWS:
        blockers.append("PROGRESS_METRIC_GEOMETRY_ROWS_NOT_1264")

    for key, target in progress_acceptance["targets"].items():
        if not target["exists"]:
            blockers.append(f"PROGRESS_{key.upper()}_MISSING")
        if target["http"].get("status") != 200:
            blockers.append(f"PROGRESS_{key.upper()}_HTTP_NOT_200")

    browser = progress_acceptance["browser"]
    if browser.get("exit_code") != 0:
        blockers.append("PROGRESS_BROWSER_SESSION_NOT_ACCEPTED")
    if browser.get("console_error_count") not in (0, None):
        blockers.append("PROGRESS_BROWSER_CONSOLE_ERRORS")
    if progress_acceptance["candidate_count"] != EXPECTED_TOTAL_CANDIDATES:
        blockers.append("PROGRESS_DOM_CANDIDATE_COUNT_NOT_9")
    if progress_acceptance["official_source_count"] != EXPECTED_TOTAL_SOURCES:
        blockers.append("PROGRESS_DOM_OFFICIAL_SOURCE_COUNT_NOT_8")
    if progress_acceptance["completed_operations"] != EXPECTED_COMPLETED_OPERATIONS:
        blockers.append("PROGRESS_DOM_COMPLETED_OPERATIONS_NOT_19")
    if progress_acceptance["total_operations"] != EXPECTED_TOTAL_OPERATIONS:
        blockers.append("PROGRESS_DOM_TOTAL_OPERATIONS_NOT_20")
    if str(progress_acceptance["semantic_valid"]).casefold() != "true":
        blockers.append("PROGRESS_DOM_SEMANTIC_VALID_FALSE")
    if progress_acceptance["blocked_text_present"]:
        blockers.append("PROGRESS_DOM_BLOCKED_TEXT_PRESENT")
    if not progress_acceptance["operations_panel_present"]:
        blockers.append("PROGRESS_OPERATIONS_PANEL_MISSING")
    if not progress_acceptance["candidates_panel_present"]:
        blockers.append("PROGRESS_CANDIDATES_PANEL_MISSING")
    if not progress_acceptance["sources_panel_present"]:
        blockers.append("PROGRESS_SOURCES_PANEL_MISSING")
    if progress_acceptance["server_404_paths"]:
        blockers.append("PROGRESS_HTTP_404_OBSERVED")
    return list(dict.fromkeys(blockers))


def write_markdown(report: dict[str, Any]) -> None:
    aggregate = report["aggregate_batch_state"]
    progress = report["progress_page_acceptance"]
    lines = [
        "# Ready to Sell 1 — Automation 167 Aggregate DOM Proof V3",
        "",
        f"- SLOT_ID: `{SLOT_ID}`",
        f"- Task step: `{TASK_STEP}`",
        f"- Status: `{report['status']}`",
        f"- Geometry rows: `{report['remote_business_state']['geojson_feature_count']}`",
        f"- Aggregate official sources: `{aggregate['official_source_count']}`",
        f"- Aggregate candidates: `{aggregate['candidate_count']}`",
        f"- Exact INSPIRE matches: `{aggregate['exact_inspire_match_count']}`",
        f"- Internet reverified: `{aggregate['internet_reverified_count']}`",
        f"- Completed operations: `{aggregate['completed_operations']}/{aggregate['total_operations']}`",
        f"- Progress DOM candidates: `{progress['candidate_count']}`",
        f"- Progress DOM sources: `{progress['official_source_count']}`",
        f"- Main browser exit: `{report['automation_167_dom_proof']['browser'].get('exit_code')}`",
        f"- Progress browser exit: `{progress['browser'].get('exit_code')}`",
        "",
        "## Blockers",
        "",
        *([f"- `{value}`" for value in report["blockers"]] or ["- none"]),
        "",
        "## Safety",
        "",
        "`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.",
        "",
        "Market availability, planning evidence, exact parcel identity and source verification remain separate row-level signals.",
        "No unbound candidate is promoted to a parcel value.",
    ]
    v2.REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    v2.REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError(f"SLOT_ID_MISMATCH: {os.environ.get('AAYS_SLOT_ID')}")

    business = v2.collect_business_state()
    aggregate = collect_aggregate_state()
    business.update(
        {
            "official_source_count": aggregate["official_source_count"],
            "official_source_scores": aggregate["official_source_scores"],
            "candidate_count": aggregate["candidate_count"],
            "exact_inspire_match_count": aggregate["exact_inspire_match_count"],
            "internet_reverified_count": aggregate["internet_reverified_count"],
            "parcel_value_publication_rows": aggregate["parcel_value_publication_rows"],
        }
    )
    main_acceptance = v2.run_dom_acceptance()
    progress_acceptance = run_progress_acceptance()
    _, main_blockers = v2.determine_status(business, main_acceptance)
    blockers = list(dict.fromkeys(main_blockers + aggregate_blockers(aggregate, progress_acceptance)))
    status = "PASS" if not blockers else "BLOCKED"

    report = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "base_slot_id": "ready_to_sell",
        "shard_index": 1,
        "parcel_partition": {"start": 1, "end": 30761, "count": 30761, "canonical_count": 92283},
        "task_id": os.environ.get("AAYS_TASK_ID"),
        "task_step": TASK_STEP,
        "status": status,
        "blockers": blockers,
        "remote_business_state": business,
        "aggregate_batch_state": aggregate,
        "automation_167_dom_proof": main_acceptance,
        "progress_page_acceptance": progress_acceptance,
        "first_unverified_step_remains": TASK_STEP if status != "PASS" else None,
        "next_step": (
            "FIX_REPORTED_MAIN_OR_PROGRESS_DOM_BLOCKERS_THEN_RERUN_AUTOMATION_167_V3"
            if blockers
            else "REMOTE_READBACK_THEN_ADVANCE_READY_TO_SELL_1_CHECKPOINT"
        ),
        "generated_at": v2.utc_now(),
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    v2.write_json(v2.REPORT_JSON, report)
    write_markdown(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
