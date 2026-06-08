# SECURITY / ASAYIS AUTONOMOUS STATUS TRACKER

DATE_UTC=2026-06-09
MODE=RUNNER_QUEUE_CONTROLLED
PROJECT=AAYS security/asayis parcel layer
LAST_CHECK_UTC=2026-06-09
LAST_CHECK_STATUS=RUNNER_OUTPUT_PENDING

## User Operating Model
The user will type only: `devam et`.
On each continuation, ChatGPT must:
1. Read `ai-results/security_asayis_latest_status.md` and `.json` if present.
2. Read `ai-tasks/current-task.json`.
3. Read relevant repo files only as needed.
4. Decide the next smallest safe runner task.
5. Update/create only explicit files, never `git add .` style behavior.
6. Keep all guardrails false unless the user explicitly authorizes a later frontend patch.
7. Report progress percent and state from actual GitHub/runner outputs, not from assumptions.

## Guardrails
DB_WRITE=false
DDL=false
MIGRATION=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false

## Current Queue State
CURRENT_TASK_ID=security-asayis-001-readonly-inventory-20260609
CURRENT_SCRIPT=ai-task-scripts/security_asayis_001_readonly_inventory_20260609.ps1
CURRENT_TASK_JSON=ai-tasks/current-task.json
EXPECTED_OUTPUT_MD=ai-results/security_asayis_latest_status.md
EXPECTED_OUTPUT_JSON=ai-results/security_asayis_latest_status.json

## Current Verified Status
- Security inventory task has been queued in GitHub.
- The task script exists and is read-only.
- `current-task.json` points to the security inventory task.
- Expected output files are still not present in GitHub after the latest continuation check.
- `ai-heartbeat/latest.json` was not found in GitHub.
- This indicates the currently open local runner has not polled/pushed this task yet, is stopped, or is running from a different bridge/result path.
- Active task was not overwritten during this check.

## Latest Continuation Check
CHECK_NAME=security_asayis_runner_output_probe
CHECK_RESULT=OUTPUT_NOT_FOUND
MD_OUTPUT_FOUND=false
JSON_OUTPUT_FOUND=false
CURRENT_TASK_UNCHANGED=true
HEARTBEAT_FOUND=false
ACTION_TAKEN=status_tracker_updated_only
NEXT_COMMAND=devam et
PROGRESS_PERCENT=12
ETA_MINUTES_NEXT=5-10 if runner is active; unknown if runner is stopped or pointed at a different bridge

## Next Continuation Logic
If `ai-results/security_asayis_latest_status.md` exists:
- Read it.
- Parse BLOCKERS and PROGRESS_PERCENT.
- Create SECURITY_ASAYIS_002 as a patch-plan/diff-report task only.

If the output does not exist:
- Do not overwrite active task unless there is clear evidence it is stale.
- Re-check current-task and heartbeat/log paths.
- Report `RUNNER_OUTPUT_PENDING`.
- If needed, create a non-destructive diagnostic task only after preserving the current task details.

## Completion Definition
Final acceptance is not reached until:
- Security button uses `security.png`.
- Five safety levels show correctly.
- Parcels are colored as polygons or explicitly labeled fallback.
- Popup includes safety score, level, confidence, source vintage, and approximate police.uk warning.
- Reports confirm no DB write, no migration, no DDL, no deploy, no fake data.
