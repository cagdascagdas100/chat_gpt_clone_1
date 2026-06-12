# AAYS_REAL_TOPOGRAPHY_PRODUCT dispatch bridge requirement

status: DISPATCH_BRIDGE_REQUIRED_NOT_PRODUCT_PATCH
branch: aays-runner-v17-icon-work-20260603-232706
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
created_by: ChatGPT
created_at_istanbul: 2026-06-12T17:44:00+03:00

## Evidence read from GitHub

1. `reports/local_runner_contract_diagnostic_20260612.txt` exists and was pushed to GitHub.
2. That diagnostic was run from `C:/Users/cagda`, not from the canonical repo root, so its final conclusion fields remain `unknown`.
3. The diagnostic nevertheless lists the page status tree and shows existing current-task and queue files.
4. `automation/POWERSHELL_BRIDGE_PROMPT_V2_20260609.txt` defines the dispatch bridge contract: copy a pending GitHub task into the existing single Kalife runner input queue and write all output to GitHub reports.
5. `automation/AUTONOMY_BRIDGE_MINIMAL_STATUS_20260609.txt` already records the root cause: GitHub tasks exist, but no confirmed local dispatch bridge copied the pending task into the active runner input queue.
6. `runner_tasks/RUN_SOURCE_INVENTORY_MINIMAL_20260609.ps1` is the confirmed executable task style: PowerShell runner task under `runner_tasks`, writing reports under `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports` and pushing to branch.

## Decision

Do not create a new product patch task yet. The next safe action is a single local dispatch bridge recovery/enablement action that writes a GitHub report, then ChatGPT can continue from GitHub reports only.

## Required next GitHub report

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/dispatch_bridge_recovery_20260612.txt`

Required fields:

```text
PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
BRANCH=aays-runner-v17-icon-work-20260603-232706
WORKTREE=F:\AAYS_GITHUB_WORK\AAYS
LOCAL_QUEUE=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue
RUNNER_TASK_SOURCE=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_tasks/RUN_SOURCE_INVENTORY_MINIMAL_20260609.ps1
COPIED_TO_LOCAL_QUEUE=<path or no>
RUNNER_PROCESS_COUNT=<number>
RUNNER_STARTED=<true|false|already_running|failed>
EXPECTED_REPORT=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/real_topography_source_inventory_*.txt
DISPATCH_RESULT=<queued|runner_started|blocked>
FAKE_DATA_CREATED=False
```

## Completion estimate

CHATGPT_ORCHESTRATION_PERCENT=43
PRODUCT_PROGRESS_ESTIMATE=84
FINAL_READY=false
