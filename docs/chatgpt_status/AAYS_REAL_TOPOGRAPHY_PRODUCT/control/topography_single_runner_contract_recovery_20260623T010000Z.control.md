# AAYS_REAL_TOPOGRAPHY_PRODUCT - Single Runner Contract Recovery Control

TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
REPO=cagdascagdas100/chat_gpt_clone_1
BRANCH_USED_BY_CHATGPT=main
REQUESTED_HANDOFF_BRANCH=aays-runner-v17-icon-work-20260603-232706
MODE=single_runner_only
STATUS=CONTROL_CREATED_BY_CHATGPT
CREATED_AT_UTC=2026-06-23T01:00:00Z

## Why this control exists

GitHub was checked before writing new product work. The handoff branch name was not found through branch search, and the canonical shared runner script path returned 404 on `main`:

`docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1`

Therefore this page-key now contains a controlled recovery task whose first job is to detect the actual runner contract from the local worktree and write evidence under this same page-key only.

## Non-negotiable rules

- Do not start a second runner.
- Do not force-push.
- Do not write DB, migrations, seed data, or production deploys.
- Do not reduce the previously proven local technical 100 status.
- Do not emit FINAL_READY unless all final evidence tokens are verified from reports.
- All outputs must be written under `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/`.

## Expected automation path for the single runner

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/topography_single_runner_contract_recovery_20260623T010000Z.ps1`
