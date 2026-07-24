from __future__ import annotations

import copy
import importlib.util
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
MODULE_PATH = BASE / "security_public_safety_2_runner_pipeline_v6.py"
spec = importlib.util.spec_from_file_location("slot2_pipeline_v6", MODULE_PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

cases: list[dict[str, object]] = []
def check(name: str, value: object) -> None:
    cases.append({"name": name, "pass": bool(value)})

now = datetime.now(timezone.utc)
base = {
    "slot_id": m.SLOT_ID,
    "state": "LIVE_SOURCE_ATTESTATION_PASSED",
    "pass": True,
    "exit_code": 0,
    "generated_at": now.isoformat(),
    "completed_at": (now + timedelta(seconds=1)).isoformat(),
    "actual_business_rows_written": 0,
    "fake_data": False,
    "final_ready": False,
}
check("receipt_valid", m.validate_fresh_receipt(base, started_at=now - timedelta(seconds=1), expected_state="LIVE_SOURCE_ATTESTATION_PASSED")["pass"])
mutations = {
    "wrong_slot": lambda p: p.update(slot_id="other"),
    "wrong_state": lambda p: p.update(state="BAD"),
    "missing_exit": lambda p: p.pop("exit_code"),
    "exit_nonzero": lambda p: p.update(exit_code=1),
    "stale_generated": lambda p: p.update(generated_at=(now - timedelta(hours=1)).isoformat()),
    "stale_completed": lambda p: p.update(completed_at=(now - timedelta(hours=1)).isoformat()),
    "missing_business": lambda p: p.pop("actual_business_rows_written"),
    "business_nonzero": lambda p: p.update(actual_business_rows_written=1),
    "fake": lambda p: p.update(fake_data=True),
    "final": lambda p: p.update(final_ready=True),
}
for name, mutate in mutations.items():
    bad = copy.deepcopy(base); mutate(bad)
    check(f"reject_{name}", not m.validate_fresh_receipt(bad, started_at=now - timedelta(seconds=1), expected_state="LIVE_SOURCE_ATTESTATION_PASSED")["pass"])
bad = copy.deepcopy(base); bad["pass"] = False
check("reject_pass_false", not m.validate_fresh_receipt(bad, started_at=now - timedelta(seconds=1), expected_state="LIVE_SOURCE_ATTESTATION_PASSED")["pass"])

python_text = MODULE_PATH.read_text(encoding="utf-8")
ps_text = (BASE / "security_public_safety_2_runner_pipeline_v6.ps1").read_text(encoding="utf-8")
source_text = (BASE / "security_public_safety_2_runner_pipeline_v4_source_bound.py").read_text(encoding="utf-8")
static = {
    "attestation_stale_removed": "stale_attestation_removed" in python_text and "remove_stale(attestation_output)" in python_text,
    "attestation_fresh_gate": "validate_fresh_receipt(attestation" in python_text,
    "source_bound_called": "security_public_safety_2_runner_pipeline_v4_source_bound.py" in python_text,
    "source_bound_stale_removed": "stale_source_bound_receipt_removed" in python_text,
    "source_bound_fresh_gate": "validate_fresh_receipt(source_bound" in python_text,
    "no_global_task_write": "ai-tasks/current-task.json" not in python_text and "ai-tasks/current-task.json" not in ps_text,
    "no_git_push": "git push" not in python_text.lower() and "git push" not in ps_text.lower(),
    "no_git_commit": "git commit" not in python_text.lower() and "git commit" not in ps_text.lower(),
    "no_runner_start": "start-process" not in ps_text.lower() and "new runner" not in python_text.lower(),
    "ps_slot_guard": "WRONG_SLOT" in ps_text,
    "ps_branch_guard": "WRONG_BRANCH" in ps_text,
    "ps_repo_root": "rev-parse --show-toplevel" in ps_text,
    "source_binding_police": "police_month_current" in source_text,
    "source_binding_iod": "iod_sha_current" in source_text,
    "source_binding_mps": "mps_sha_current" in source_text,
    "artifact_csv_hash": "csv_sha_current" in source_text,
    "artifact_geo_hash": "geojson_sha_current" in source_text,
    "artifact_html_hash": "html_sha_current" in source_text,
    "web_json_equality": "runner_web_json_equal" in source_text,
    "score4_evidence": "score4_full_evidence" in source_text,
    "missing_exit_rejected": "exit_code_present" in source_text and 'payload.get("exit_code") == 0' in source_text,
    "missing_business_rejected": "business_rows_present" in source_text,
}
for name, value in static.items():
    check(f"static_{name}", value)

result = {"schema_version": 1, "slot_id": m.SLOT_ID, "test_type": "PIPELINE_V6_SOURCE_BOUND_SELFTEST", "cases": cases, "passed": sum(item["pass"] for item in cases), "total": len(cases), "pass": all(item["pass"] for item in cases), "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["pass"] else 1)
