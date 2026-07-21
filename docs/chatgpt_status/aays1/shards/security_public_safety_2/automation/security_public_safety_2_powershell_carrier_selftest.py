from __future__ import annotations

import json
from pathlib import Path

SLOT_ID = "security_public_safety_2"
HERE = Path(__file__).resolve().parent
CARRIER = HERE / "security_public_safety_2_runner_pipeline_v1.ps1"
OUTPUT = HERE.parent / "validation/security_public_safety_2_powershell_carrier_selftest_latest.json"

def main() -> int:
    text = CARRIER.read_text(encoding="utf-8")
    lower = text.lower()
    cases = [
        ("exact_slot", "$expectedSlot = 'security_public_safety_2'" in text),
        ("exact_branch", "$expectedBranch = 'codex/aays-single-runner-v5-20260706'" in text),
        ("wrong_slot_fail_closed", 'throw "WRONG_SLOT:$SlotId"' in text),
        ("wrong_branch_fail_closed", 'throw "WRONG_BRANCH:$TargetBranch"' in text),
        ("pipeline_exists_guard", "PIPELINE_SCRIPT_MISSING" in text),
        ("python_required", "PYTHON_EXECUTABLE_NOT_FOUND" in text),
        ("repo_env_forwarded", "$env:AAYS_REPO_ROOT = $RepoRoot" in text),
        ("slot_env_forwarded", "$env:AAYS_SLOT_ID = $expectedSlot" in text),
        ("branch_env_forwarded", "$env:AAYS_TARGET_BRANCH = $expectedBranch" in text),
        ("pipeline_args_forwarded", "--repo-root $RepoRoot --slot-id $expectedSlot --target-branch $expectedBranch" in text),
        ("exit_code_propagated", "exit $exitCode" in text),
        ("single_runner_declared", "SINGLE_SHARED_RUNNER_ONLY=true" in text),
        ("new_runner_false", "NEW_RUNNER=false" in text),
        ("parallel_runner_false", "PARALLEL_RUNNER=false" in text),
        ("global_task_mutation_false", "GLOBAL_TASK_MUTATION=false" in text),
        ("no_git_push", "git push" not in lower),
        ("no_git_commit", "git commit" not in lower),
        ("no_current_task_write", "ai-tasks/current-task.json" not in lower),
        ("final_false", "FINAL_READY=false" in text),
    ]
    payload = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "test_type": "POWERSHELL_CARRIER_FAIL_CLOSED_SELFTEST",
        "cases": [{"name": name, "pass": passed} for name, passed in cases],
        "passed": sum(bool(passed) for _, passed in cases),
        "total": len(cases),
        "pass": all(passed for _, passed in cases),
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
