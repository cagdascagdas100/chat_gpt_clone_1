#!/usr/bin/env python3
"""Static fail-closed checks for the runner eligibility web contract."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"


def main() -> int:
    results: list[str] = []
    html = (WEB / "index.html").read_text(encoding="utf-8")
    eligibility = json.loads((WEB / "runner_eligibility_latest.json").read_text(encoding="utf-8"))
    progress = json.loads((WEB / "progress_latest.json").read_text(encoding="utf-8"))
    operations = json.loads((WEB / "operations_latest.json").read_text(encoding="utf-8"))
    runner = json.loads((WEB / "runner_task_latest.json").read_text(encoding="utf-8"))
    examples = json.loads((WEB / "examples_latest.json").read_text(encoding="utf-8"))
    network = json.loads((WEB / "network_attempts_latest.json").read_text(encoding="utf-8"))

    assert "runner_eligibility_latest.json" in html; results.append("eligibility_json_loaded")
    assert 'id="eligibility"' in html and 'id="eligibilitySummary"' in html; results.append("eligibility_dom_markers")
    assert "Otomatik claim" in html and "queue" in html; results.append("read_only_notice_visible")
    assert "re.gates.forEach" in html; results.append("eligibility_rows_rendered")
    assert "Runner uygunluğu" in html; results.append("eligibility_metric_visible")
    assert eligibility["status"] == "BLOCKED_BY_OTHER_GLOBAL_RUNNER_TASK"; results.append("current_blocker_visible")
    assert eligibility["claim_eligible_for_manual_review"] is False; results.append("manual_claim_false")
    assert eligibility["auto_claim"] is False and eligibility["queue_submission"] is False; results.append("no_auto_claim_or_queue")
    assert len(eligibility["gates"]) == 8 and [g["gate_no"] for g in eligibility["gates"]] == list(range(1,9)); results.append("eight_ordered_gates")
    assert progress["overall_progress_percent"] == 76.56 and progress["final_ready"] is False; results.append("progress_truth")
    assert len(operations["operations"]) == 12 and operations["operations"][-1]["progress_weight"] == 0.5; results.append("operation_plan_truth")
    assert runner["current_eligibility"]["global_slot_id"] == "height_difference_2"; results.append("runner_blocker_bound")
    assert examples["example_count"] == 19 and examples["official_aggregate_qa_examples"] == 14; results.append("example_counts")
    assert network["attempts"][-1]["attempt_no"] == 6 and network["official_zip_bytes_downloaded"] is False; results.append("bounded_network_attempt_visible")
    assert len(results) == 14
    print(json.dumps({"result":"PASS","passed":14,"total":14,"tests":results}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
