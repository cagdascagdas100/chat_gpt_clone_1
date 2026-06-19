# AAYS_REAL_TOPOGRAPHY_PRODUCT Runner Contract Probe — 2026-06-12

## Scope
- repo: cagdascagdas100/chat_gpt_clone_1
- branch: aays-runner-v17-icon-work-20260603-232706
- page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
- status_root: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT

## Purpose
Detect the real single-runner work intake contract before any new product/code task is issued.

## Hard constraints
- Do not modify product code.
- Do not run DB write, migration, import, index creation, or production deploy.
- Do not move existing C-drive runner/bridge infrastructure.
- If heavy local temp/artifact output is needed, use the existing page-specific heavy work root or F-drive work root configured for this page.
- Preserve the existing single runner/bridge/queue infrastructure.

## Required read-only checks
1. Enumerate and report files under:
   - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/control
   - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/queue
   - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/current-task
   - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_tasks
   - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation
   - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports
   - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status
   - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/heartbeat
2. Identify which location/filename/schema the current runner actually polls.
3. Identify latest runner output/report/heartbeat timestamps and whether the runner is alive, idle, stuck, or not polling.
4. Inspect only runner intake/contract files; do not create product tasks yet.

## Required GitHub output
Write exactly one report file:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/runner_contract_probe_20260612_istanbul.txt`

The report must include:
- status = CONTRACT_FOUND | CONTRACT_NOT_FOUND | RUNNER_NOT_POLLING | ERROR
- runner_alive = true/false/unknown
- intake_location = exact path or unknown
- intake_schema = exact observed schema or unknown
- latest_heartbeat_path and timestamp if found
- latest_runner_output_path and timestamp if found
- safe_next_task_path = exact path where ChatGPT should write the next Topography task, or unknown
- evidence paths read

## Completion rule
This task is complete only when the report file above exists in GitHub with a clear `safe_next_task_path` or a clear reason why the runner contract could not be detected.
