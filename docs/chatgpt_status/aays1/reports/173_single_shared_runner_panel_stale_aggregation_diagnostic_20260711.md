# AAYS Single Shared Runner Panel - Stale Aggregation Diagnostic

Date: 2026-07-11
Page key: aays1
Layer: Parcel Label / Distance Property Types

## Finding

The supplied panel snapshot is dated 2026-07-08T10:22:59.2526616Z and is stale relative to the current persistent F portable runner panel observed on 2026-07-11. It must not be used as a live queue-completion source.

## Confirmed panel defects

1. The panel reports 45 pages, but many rows are infrastructure directories rather than product/page keys: automation, continue_requests, control, heartbeat, queue, reports, runner_inputs, runner_outputs, runner_tasks, runner_work, status and similar folders.
2. The aays1 row still points to the obsolete task `security-batch-join-backoff-force-pickup-20260704-0430` and blocker `git_status_unavailable`; it does not show Task 169.
3. Every row defaults to 0 percent and 100 remaining, including unrelated infrastructure folders. These values are fallback placeholders, not authoritative progress metrics.
4. `Runner Aktif` only indicates process/heartbeat visibility. It does not prove queue pickup, task execution, output creation, Git push or remote readback.
5. The distance_property_types row has no task and still shows 0 percent, despite the authoritative Parcel Label matrix tracking 98 rows. Therefore the panel aggregation is disconnected from the current layer artifacts.

## Root cause

The panel generator is aggregating stale per-directory/per-page status files and treating infrastructure directories as page keys. It is not enforcing freshness, a canonical page whitelist, or output/readback precedence. At the same time the queue control plane is not completing the fetch -> clean worktree -> task execution -> push cycle for Task 169.

## Required correction

- Keep the same single shared runner.
- Filter page discovery through the canonical product/page registry; exclude infrastructure directories.
- Add a freshness threshold and mark stale rows explicitly.
- Separate process health from queue execution health.
- Derive task and progress only from the current branch runner output, gate, browser/HTTP proof and GitHub remote readback.
- Repair the controller/task-worktree Git state and require Task 169 processed output before increasing progress.

## Safety

single_runner_only=true
new_runner=false
parallel_runner=false
final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false
