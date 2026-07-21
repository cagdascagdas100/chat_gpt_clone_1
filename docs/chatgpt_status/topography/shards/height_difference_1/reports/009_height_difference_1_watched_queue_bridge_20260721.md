# height_difference_1 watched queue bridge — 2026-07-21

## Scope

- SLOT_ID: `height_difference_1`
- Parcel partition: `1-30761`
- Existing logical task: `height-difference-1-official-boundary-elevation-samples-20260720`
- Payload revision: `4`
- No other slot was claimed or modified.

## Root cause verified

The repo-to-bridge watcher contract records its scanned queue as `docs/chatgpt_status/aays1/queue`. The existing logical task was only present under `docs/chatgpt_status/topography/queue`, so it was not visible to that legacy bridge path.

The global JSON current-task record still referenced the old ready-to-sell task, whose latest status proves 13 of 13 jobs completed with fresh output, zero failed jobs, child exit code 0, and no blockers. The current shared control alias now points to `height_difference_2`; that active sequential selection was not overwritten.

## Safe correction

The same task ID and idempotency key were mirrored into the watched queue without creating a new logical task:

- `docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json`
- `docs/chatgpt_status/aays1/queue/aays1-height-difference-1-official-boundary-elevation-samples-20260720.queue.txt`
- `docs/chatgpt_status/aays1/current-task/aays1-height-difference-1-official-boundary-elevation-samples-20260720.current.txt`

The bridge is explicitly sequential after the currently selected shared-control task and does not modify `docs/chatgpt_status/aays1/control/current_task.txt`, `docs/chatgpt_status/aays1/queue/current.task.json`, or `ai-tasks/current-task.json`.

## Acceptance state

- HMLR real boundary rows: 0
- EA official numeric rows: 0
- OS Terrain 50 independent numeric rows: 0
- Strict measured rows: 0
- Accuracy remains `2.5/4 fallback`
- Output semantics remain `NO_DATA_NOT_INFERRED`

## Safety

- new runner: false
- parallel runner: false
- fake data: false
- database write: false
- migration: false
- production deploy: false
- final ready: false
