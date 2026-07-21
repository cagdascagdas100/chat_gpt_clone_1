# Height Difference 2 — Watcher Visibility Diagnosis, Attempt 012

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-012`
- Final ready: `false`

## Verified diagnosis

The existing repo-to-bridge watcher installer at commit `e06d84a4c62830702577ff883fb2a35ca465c6a0` resets a clean worktree to `origin/main`, scans `docs/chatgpt_status/aays1/queue/*.task.json`, copies `automation`, `queue`, and `control` into the active repo, and ensures the existing portable queue runner is present.

The remote watcher heartbeat on `main` remains `status=WATCHING`, but its last timestamp is `20260703_225536`. The latest matching heartbeat commit is `2b82e3783b98c20186ea93fcead1f8bb07eb70e6`, dated 3 July 2026. Therefore the watcher is not proven live on 21 July 2026.

The authoritative task and its automation are on `codex/aays-single-runner-v5-20260706`; the watcher reads `main`. The primary entrypoint is not present on `main`. A queue-only mirror to `main` was deliberately rejected because it would expose an incomplete task and could create a false pickup/failure cycle.

## Work completed

- Added `018_diagnose_watcher_runner_visibility.py`.
- Added read-only `019_read_existing_runner_health.ps1`.
- Passed `20/20` fail-closed tests.
- Recorded the watcher contract, stale heartbeat, branch mismatch, and absent-main-automation evidence.
- Aligned the same task ID and idempotency key to attempt `012` across JSON, legacy plain-text, and portable task views.
- Published website operation rows `146-165`; manifest total is `165`.

## Current truthful state

- Real candidate seeds: `0`
- Exact HMLR polygons: `0`
- EA DTM 1 m polygon samples: `0`
- OS Terrain 50 crosschecks: `0`
- Port 8012 acceptance rows: `0`
- Official numeric rows: `0`
- Automation validation: `103/103 PASS`
- Overall layer progress: `78%`

## Blocker

`REPO_TO_BRIDGE_WATCHER_HEARTBEAT_STALE; TASK_SOURCE_BRANCH_NOT_WATCHER_VISIBLE; TASK_AUTOMATION_ABSENT_ON_WATCHER_BRANCH; EXISTING_SINGLE_SHARED_RUNNER_CLAIM_NOT_OBSERVED`

No new runner, parallel runner, duplicate task, fabricated heartbeat, fabricated geometry, or fabricated elevation value was created.
