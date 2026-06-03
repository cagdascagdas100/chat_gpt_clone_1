# TerraYield Active Context Compact

This file replaces long ChatGPT-page context for faster continuation.

## Project

```text
Project: TerraYield
Project folder: terrayield_land_intelligence
Project root: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
Bridge root: C:\Users\cagda\Documents\chat_gpt_clone_1
Bridge repo: cagdascagdas100/chat_gpt_clone_1
```

## Current active package

```text
Task ID: terrayield-078-platform-expand-5worker-safe
Progress: 80%
Mode: TerraYield 5-worker safe platform expansion
Script: ai-task-scripts/terrayield_078_platform_expand_5worker_safe.ps1
Command: powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_078_platform_expand_5worker_safe.ps1
```

## Runner status

```text
Runner status: polling
Runner log: C:\Users\cagda\Documents\chat_gpt_clone_1\ai-runner-logs\runner-v4-20260506_163931.log
PipelineStoppedHandling: enabled
FileLockRetry: enabled
PageJobTracking: enabled
```

## Working model

```text
User command: devam et
Do not rely on old long chat context.
Read current-task.json first.
Read runner-v4.md second.
Search result commit third.
If a package is running, do not overwrite it.
If the package finished, read the result and queue the next TerraYield-named package.
If stuck, use TerraYield-prefixed recovery only.
```

## Naming rules

```text
Every task starts with: terrayield-
Every script starts with: terrayield_
Every result folder includes: terrayield
Every slot output includes: PROJECT=terrayield and DISPLAY_PROJECT=TerraYield
```

## 5-worker standard

```text
slot_1_backend
slot_2_frontend
slot_3_ops
slot_4_data_cache
slot_5_tests_validation
```

## Confirmed working evidence

```text
terrayield-064-five-slot-parallel-dispatcher:
ACTIVE_SLOTS=5
SLOTS_COMPLETED=5
SLOTS_TIMEOUT=0
SLOTS_ERROR=0

terrayield-066-multi-page-5worker-pool:
WORKERS=5
DONE_JOBS=6
ACTIVE_JOBS=0
POOL_READINESS=90/100
PROGRAM_COMPLETION=60/100

terrayield-070-named-apply-5worker-safe:
Local runner log showed ExitCode=0 and result file was created.
```

## Next response format

```text
Project: TerraYield / terrayield_land_intelligence
Active package: <task-id>
Parallel capacity: 5 workers
Completed workers/jobs: <n>
Blocked workers/jobs: <n>
Timeout workers/jobs: <n>
Program completion: <x>%
Next wait: <x-y minutes>
Next command: devam et
```

## Cleanup policy

```text
Do not delete current-task.json.
Do not delete runner/watchdog scripts.
Do not delete latest ai-results.
Do not delete active ai-task-scripts.
Archive old context instead of deleting.
Prefer compact context files for new ChatGPT pages.
```
