# Local shared runner recovery required

PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
STATUS=LOCAL_RUNNER_NOT_REMOTELY_STARTABLE_FROM_CHATGPT
PRODUCT_COMPLETENESS_ESTIMATE=93
PRODUCT_100_READY=false

## Problem
The GitHub queue/current-task contract is present, but the local shared runner on the user's PC is not picking up the task. The latest user-provided terminal output shows `git pull` is blocked by unmerged files in the local worktree.

## Required local action
Run this in the existing local repository PowerShell window, not a second runner:

```powershell
cd C:\Users\cagda\Documents\GitHub\chat_gpt_clone_1
git status --short
git merge --abort 2>$null
git reset --hard HEAD
git clean -fd
git pull --ff-only
powershell -NoExit -ExecutionPolicy Bypass -File ".\docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1"
```

## Expected evidence after recovery
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_single_runner_contract_recovery_20260623T010000Z_v6_terminal_bridge_report.txt
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_output/topography_single_runner_contract_recovery_20260623T010000Z_v6_runner_output.txt
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_single_runner_contract_recovery_20260623T010000Z_final_report.txt
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/topography_single_runner_contract_recovery_20260623T010000Z_final.status.txt

## Guardrail
Do not manually create final evidence files. They must be created by the runner after it actually executes the task.
