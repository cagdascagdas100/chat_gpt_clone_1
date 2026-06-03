# TerraYield 076 Runner Stale Diagnosis

Project: TerraYield
ChatGPT page project: aays1

Current GitHub task:
terrayield-076-platform-check-5worker-retry

Expected script:
ai-task-scripts/terrayield_071_platform_finish_5worker_safe.ps1

Observed problem:
The GitHub task is ready, but local runner heartbeat still reports the old task terrayield-067-visible-5worker-progress.

Observed last-task-id:
terrayield-066-multi-page-5worker-pool

Conclusion:
The local runner or watchdog is stale. Adding more GitHub task files will not start real PC work until the local runner process is restarted and pulls origin/main.

Required local recovery:
1. Stop watchdog.
2. Stop any AAYS runner PowerShell process.
3. Remove .git/index.lock if present.
4. Fetch and reset bridge repo to origin/main.
5. Start watchdog again.
6. Confirm runner-v4.md changes from old 067 to current 076.

Success condition:
runner-v4.md shows started/running/finished terrayield-076-platform-check-5worker-retry, and a Runner V4 result commit appears for terrayield-076-platform-check-5worker-retry.
