# AAYS real topography automation gap and fix

## Current product status

- PRODUCT_PROGRESS_ESTIMATE: 84
- PRODUCT_RESULT: BLOCKED_WAITING_FOR_LOCAL_RUNNER_TRIGGER
- Scope: real two-metric parcel topography product

## What is already ready

The GitHub-side task exists and is ready:

```text
docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_tasks/RUN_SOURCE_INVENTORY_MINIMAL_20260609.ps1
```

It is designed to:

- use `F:\AAYS_GITHUB_WORK\AAYS`
- avoid fake data
- avoid DB write, migration, and deploy
- search for real elevation / DTM / LIDAR / terrain source files
- write a report to:

```text
docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/real_topography_source_inventory_*.txt
```

## Why the automation is not autonomous yet

The missing link is not the task file. The missing link is the bridge from GitHub `runner_tasks` into the local runner queue.

Current situation:

```text
ChatGPT can write GitHub task files.
The local Kalife runner reads local queue files.
But the runner does not automatically pull GitHub runner_tasks into C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue.
```

So the automation stops here:

```text
GitHub task created -> local queue not populated -> runner does not execute -> no report -> ChatGPT has nothing new to read -> percentage does not increase.
```

## What must be fixed

A small always-on bridge/poller is needed. It should do this loop:

1. Pull or fetch the GitHub branch.
2. Look inside:

```text
docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_tasks
```

3. Copy unprocessed `*.ps1` jobs into:

```text
C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue
```

4. Ensure the single canonical runner is running:

```text
C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\portable_queue_runner.ps1
```

5. Wait for reports in:

```text
docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports
```

6. Commit and push reports back to GitHub.

## User-visible rule after the bridge is running

After that bridge runs once and stays alive, the user only writes:

```text
devam et
```

Then ChatGPT checks GitHub reports and creates the next GitHub task if needed.

## Why the percentage is stuck

The percentage is stuck at 84 because no new source inventory report exists. The next expected report is:

```text
real_topography_source_inventory_*.txt
```

When that report exists:

- inventory report present: 84 -> 86
- real artifact found: 86 -> 88
- API smoke passed: 88 -> 92
- browser popup proof passed: 92 -> 100

## Manual output policy

The user should not paste PowerShell output into chat. The bridge and tasks must write text reports into GitHub so ChatGPT can read them.