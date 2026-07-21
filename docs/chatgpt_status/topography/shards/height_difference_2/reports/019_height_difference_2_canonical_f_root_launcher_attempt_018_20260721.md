# height_difference_2 — canonical F-root launcher repair, attempt 018

- SLOT_ID: `height_difference_2`
- Parcel range: `30762-61522`
- Task ID unchanged: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Idempotency key unchanged: `height-difference-2-canonical-export-official-sampling-v3`
- `final_ready=false`

## Remote diagnosis

The current F daemon heartbeat remains dated `2026-07-16T13:45:53.0433295Z`. The latest committed multi-page heartbeat is dated `2026-07-07T00:58:42Z` and records the old `C:\AAYS_WT\AAYS_REPAIR_20260706_1738` repo root and `C:\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES` work root.

The repo-root `devam.ps1` previously invoked the shared launcher without explicit `-RepoRoot` or `-WorkRoot`. The launcher also had C-drive defaults and considered the requested default before its repo-local path. This allowed an existing C checkout to win resolution.

## Repairs

1. `devam.ps1` now requires the canonical portable F prefix and explicitly passes:
   - canonical F repo root,
   - derived F work root,
   - exact codex branch,
   - `MaxTasks=1`,
   - `NoPanel`.
2. `START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1` now:
   - has no C repo/work defaults,
   - resolves the repo-local checkout,
   - blocks C repo/work roots,
   - derives the work root from the selected repo,
   - defaults to one task per scan.
3. The restart helper now:
   - preserves one existing canonical process,
   - blocks multiple processes,
   - starts the canonical `.cmd` first,
   - uses repo `devam.ps1` only when no canonical process appears after the `.cmd` attempt.
4. Attempt 018 queue, portable and legacy pickup contracts were aligned without creating a new logical task.

## Validation

`CANONICAL_F_LAUNCHER_CHAIN_20_OF_20_PASS`.

C-drive defaults, omitted explicit roots, `MaxTasks>1`, duplicate canonical processes and missing repo fallback gates are fail-closed. Fixtures were not promoted.

## Current evidence state

- Real candidate seeds: `0/3`
- Exact HMLR polygons: `0/3`
- EA DTM1m polygon samples: `0/3`
- OS Terrain50 crosschecks: `0/3`
- Port 8012 acceptance output: absent
- Restart receipt: absent

The first unverified step is execution of the repaired existing canonical F launcher chain, followed by a fresh daemon heartbeat, claim and the three official sample chains. No parcel elevation was produced without exact polygon and official numeric source evidence.
