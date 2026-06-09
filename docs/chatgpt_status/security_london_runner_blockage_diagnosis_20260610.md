# Security London runner blockage diagnosis

Date: 2026-06-10
Scope: security/asayis London-only F-drive pilot

## Evidence

- Active task is `security-asayis-london-source-restore-20260609`.
- Expected source restore runner report is missing: `ai-results/security_london_source_restore_runner_latest.txt`.
- Expected source restore JSON is missing: `ai-results/security_london_source_restore_latest.json`.
- Current task is still queued for `security_asayis_london_source_restore_20260609.ps1`.
- Prior geodata inventory completed and found no usable local London parcel/security/boundary geodata.

## Diagnosis

The percentage is not increasing because there is no new runner output after the source-restore task was queued. The GitHub-side task and script are present; the missing element is local runner execution and push-back of evidence.

Likely causes:

1. Local PowerShell runner is not running.
2. Runner is running but skipped the task due to `.last-task-id` cache.
3. Runner executed but did not commit/push results.
4. Bridge was not synced to latest `origin/main`.

## Required unblock

Run the local bridge runner capture once from `C:\AAYS_GITHUB_BRIDGE_CLEAN2`, clear `.last-task-id`, run `ai-task-scripts\portable_queue_runner.ps1`, and push these expected files:

- `ai-results/security_london_source_restore_runner_latest.txt`
- `ai-results/security_london_source_restore_latest.json`
- `ai-results/security_london_source_restore_latest.md`
- `docs/chatgpt_status/security_london_source_restore_status_20260609.md`

## Safety

No DB write, no DDL, no migration, no production deploy, no fake data.
