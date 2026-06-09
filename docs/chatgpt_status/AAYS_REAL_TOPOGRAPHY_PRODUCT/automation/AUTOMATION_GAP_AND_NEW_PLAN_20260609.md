# AAYS_REAL_TOPOGRAPHY_PRODUCT - Automation Gap and New Plan

## Current product progress

PRODUCT_PROGRESS_ESTIMATE=84

## What is working

- ChatGPT can read and write files in GitHub.
- Product code/UI work reached the current staged state.
- GitHub status/report folders exist.
- A single local Kalife runner may exist.
- Existing runner output can be read by ChatGPT only after it is copied/pushed into GitHub under docs/chatgpt_status.

## What is not working

The missing automation link is not the number of runners. The missing link is the handoff from GitHub-updated task/prompt files to the local runner execution queue.

In the expected design:

1. ChatGPT writes updated task/prompt files to GitHub.
2. The local system detects those updated files.
3. The local system transfers the task into the single runner execution queue.
4. The runner executes the task.
5. The runner writes readable text output under docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports.
6. ChatGPT reads that output from GitHub and creates the next corrected task.

The failing step is step 2 or step 3: updated GitHub task files are not being picked up and transferred into the local runner queue.

## Why the percentage is not increasing

No new output report is being produced for:

- bridge_poller_status_*.txt
- real_topography_source_inventory_*.txt

Without one of those reports, ChatGPT has no new runner output to analyze and cannot safely claim progress beyond 84%.

## Required fix

Add a persistent bridge/poller on the local machine. It must:

- work from F drive for new heavy operations,
- pull the active branch into the F worktree,
- inspect docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_tasks for new task files,
- copy new runnable tasks into the existing single runner queue,
- ensure only the canonical runner process is active,
- write bridge_poller_status_*.txt to the GitHub reports folder every cycle,
- push that report back to GitHub.

## F drive policy

New clone/worktree/temp/artifact/output work must be under F drive. Existing C drive runner/queue infrastructure is not moved in this phase; it is only used as the already-existing runner control point.

## Next continuation behavior

When the user writes "devam et", ChatGPT should:

1. Search GitHub reports for latest bridge_poller_status_*.txt and real_topography_source_inventory_*.txt.
2. If a new report exists, read it, identify success/failure/blocker, update the product percentage, and create the next task/prompt file in GitHub.
3. If no report exists, state that the bridge/poller is not active or is not pushing reports.
4. Give PowerShell only if local runner/bridge start is unavoidable.

## Acceptance for automation fixed

AUTOMATION_FIXED when GitHub contains at least one fresh report like:

- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/bridge_poller_status_*.txt

and that report includes:

- MODE=F_DRIVE_GITHUB_TASK_BRIDGE_POLLER
- PRODUCT_PROGRESS_ESTIMATE=85 or higher
- QUEUED_TASK or BRIDGE_POLLER_ACTIVE status
