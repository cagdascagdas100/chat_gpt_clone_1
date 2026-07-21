#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
WEB = ROOT / "england_map_web/data/aays_18_slots/internet_access_2"
html = (WEB / "index.html").read_text(encoding="utf-8")
examples = json.loads((WEB / "candidate_integrity_examples_latest.json").read_text(encoding="utf-8"))
progress = json.loads((WEB / "progress_latest.json").read_text(encoding="utf-8"))
contract = json.loads((WEB / "provenance_contract_latest.json").read_text(encoding="utf-8"))
ops = []
for name in ("operations_latest.json", "scope_operations_latest.json", "operations_provenance_latest.json"):
    ops.extend(json.loads((WEB / name).read_text(encoding="utf-8"))["operations"])
id_counts = Counter(row["id"] for row in ops)
duplicate_ids = {operation_id for operation_id, count in id_counts.items() if count > 1}
by_id = {row["id"]: row for row in ops}
blocked = [row for row in by_id.values() if row["status"] != "DONE"]
resolution_ids = {x["id"] for x in examples["examples"] if x.get("postcode_resolution")}

checks = {
    "candidate_examples_fetch": "candidate_integrity_examples_latest.json" in html,
    "candidate_examples_table": "candidateIntegrityExamples" in html,
    "candidate_audit_table_and_fetch": "candidateAudit" in html and "candidate_jsonl_integrity_latest.json" in html,
    "consistency_table": "reviewConsistency" in html,
    "consistency_audit_fetch": "review_contract_consistency_latest.json" in html,
    "twelve_examples": len(examples.get("examples", [])) == 12,
    "examples_not_real": examples.get("real_parcel_rows") == 0 and examples.get("actual_business_data_rows_written") == 0,
    "no_data_methods": {x["required_method"] for x in examples["examples"] if x["candidate_class"] == "NO_DATA"} == {"NO_POSTCODE", "POSTCODE_NOT_IN_CURRENT_R2"},
    "coverage_examples_and_rejects": {11, 12}.issubset(resolution_ids) and sum(x["decision"] == "REJECT_FAIL_CLOSED" for x in examples["examples"]) == 3 and "Coverage fallback" in html,
    "validation_404": contract["combined_validation"] == {"passed": 404, "total": 404},
    "candidate_tests_25": contract["candidate_integrity_selftest"] == {"passed": 25, "total": 25},
    "resolution_tests_24": contract["postcode_resolution_selftest"] == {"passed": 24, "total": 24},
    "consistency_tests_14": contract["review_contract_consistency_selftest"] == {"passed": 14, "total": 14},
    "wrapper_tests_50": contract["run_and_audit_wrapper_contract"] == {"passed": 50, "total": 50},
    "zip_container_tests_18": contract["zip_container_safety_selftest"] == {"passed": 18, "total": 18},
    "extended_provenance_tests_20_and_chain_16": contract["provenance_selftest"] == {"passed": 20, "total": 20} and len(contract["required_chain"]) == 16 and "sixteen-artifact" in html,
    "historical_override_ids_exact": duplicate_ids == {55, 90} and by_id[55]["status"] == "DONE" and by_id[90]["status"] == "DONE",
    "operation_range_145": sorted(by_id) == list(range(1, 146)),
    "single_current_blocker": len(blocked) == 1 and blocked[0]["id"] == 145,
    "review_only": progress.get("actual_business_data_rows_written") == 0 and progress.get("final_ready") is False and contract.get("final_ready") is False,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError(f"failed: {failed}")
print(json.dumps({
    "status": "PASS",
    "tests_passed": len(checks),
    "tests_total": len(checks),
    "test_names": list(checks),
    "actual_business_data_rows_written": 0,
    "final_ready": False,
}, sort_keys=True))
