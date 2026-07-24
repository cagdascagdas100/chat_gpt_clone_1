from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent / "security_public_safety_2_runner_pipeline.py"
spec = importlib.util.spec_from_file_location("pipeline", MODULE_PATH)
assert spec and spec.loader
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def row(number: int, score: int = 3) -> dict[str, object]:
    return {
        "parcel_id": f"parcel_{number}",
        "candidate_status": "CANONICAL_API_VERIFIED",
        "accuracy_score_4": score,
    }


cases: list[tuple[str, bool]] = []
with tempfile.TemporaryDirectory() as temp_dir:
    repo = Path(temp_dir)
    shared = repo / "docs/chatgpt_status/_shared/slots_18/security_public_safety_2"
    shared.mkdir(parents=True)
    allowed = ["england_map_web/data/aays_18_slots/security_public_safety_2"]
    (shared / "status_latest.json").write_text(json.dumps({"slot_id": pipeline.SLOT_ID}))
    (shared / "ownership_latest.json").write_text(json.dumps({"slot_id": pipeline.SLOT_ID}))
    (shared / "current_task_latest.json").write_text(json.dumps({
        "slot_id": pipeline.SLOT_ID,
        "allowed_paths": allowed,
        "direct_push_forbidden": True,
    }))
    cases.append(("positive_contract", pipeline.validate_contract(repo, pipeline.SLOT_ID, pipeline.TARGET_BRANCH)["pass"]))
    cases.append(("wrong_slot_rejected", not pipeline.validate_contract(repo, "other", pipeline.TARGET_BRANCH)["pass"]))
    cases.append(("wrong_branch_rejected", not pipeline.validate_contract(repo, pipeline.SLOT_ID, "main")["pass"]))

sample = {
    "canonical_sample_count": 3,
    "accuracy_score_3_count": 3,
    "rows": [row(number) for number in range(30762, 30765)],
}
cases.append(("positive_sample", pipeline.sample_gate(sample)[0]))
bad_sample = dict(sample)
bad_sample["canonical_sample_count"] = 2
cases.append(("sample_2_of_3_rejected", not pipeline.sample_gate(bad_sample)[0]))

rows = [row(number) for number in range(30762, 31062)]
hydrated = {"rows": rows, "canonical_rows": 300, "artifacts": {"parity_pass": True}}
cases.append(("positive_hydration", pipeline.hydration_gate(hydrated)[0]))
bad_hydrated = {"rows": rows[:-1], "canonical_rows": 299, "artifacts": {"parity_pass": True}}
cases.append(("hydration_299_rejected", not pipeline.hydration_gate(bad_hydrated)[0]))
bad_ids = {"rows": rows.copy(), "canonical_rows": 300, "artifacts": {"parity_pass": True}}
bad_ids["rows"][0] = row(30763)
cases.append(("duplicate_noncontiguous_rejected", not pipeline.hydration_gate(bad_ids)[0]))

cases.append(("acceptance_true_passes", pipeline.acceptance_gate({"all_checks_pass": True, "passed": 30, "total": 30})[0]))
cases.append(("acceptance_false_rejected", not pipeline.acceptance_gate({"all_checks_pass": False, "passed": 29, "total": 30})[0]))
text = MODULE_PATH.read_text(encoding="utf-8")
for forbidden in ["git push", "git commit", "ai-tasks/current-task.json"]:
    cases.append((f"forbidden_token_absent:{forbidden}", forbidden not in text))

passed = sum(ok for _, ok in cases)
result = {
    "schema_version": 1,
    "slot_id": pipeline.SLOT_ID,
    "test_type": "RUNNER_PIPELINE_FAIL_CLOSED_SELFTEST",
    "cases": [{"name": name, "pass": ok} for name, ok in cases],
    "passed": passed,
    "total": len(cases),
    "pass": passed == len(cases),
    "actual_business_rows_written": 0,
    "fake_data": False,
    "final_ready": False,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["pass"] else 1)
