# ReadyToSell Shard 2 — Automation 167 Non-Regression Preflight

## Scope

- Slot: `ready_to_sell_2`
- Parcel partition: `30762-61522`
- Existing task only: `aays1-ready-to-sell-2-automation-167-dom-proof-20260720`
- No duplicate queue task, no new runner, no parallel runner.

## Remote readback before change

- Remote checkpoint sequence: `10`
- Status: queued
- Current task: idle
- Slot heartbeat: unclaimed, stale, no timestamp
- Automation truth path: absent
- Preserved candidate aggregate: `32`
- Preserved progress: `37/38`, overall `98.08%`

## First unverified-step work performed

The existing Automation 167 worker was audited before pickup. It rebuilt `progress_latest.json` from event-list counts and the base candidate file, which could overwrite the current wave-8 aggregate with old progress and candidate metrics.

The existing worker was patched to:

1. Preserve the canonical progress baseline.
2. Select the latest `candidate_wave_*_latest.json` aggregate.
3. Change progress only when a real DOM acceptance result exists.
4. Preserve `final_ready=false` and all safety flags.
5. Record baseline hashes and regression-guard fields in the runner output.

The same pending queue file was refreshed as attempt `ready-to-sell-2-20260721-003-non-regression`; no second task was created. The acceptance contract now forbids progress and candidate-aggregate regression.

## Canonical progress after preflight

- Completed operations: `38/39`
- Batch progress: `97.44%` (`+0.07`)
- Overall evidence progress: `52/53 = 98.11%` (`+0.03`)
- Candidate aggregate: `32`
- High-confidence candidates: `32`
- Current/upcoming/available: `30`
- Promoted product rows: `0`

## Remaining blocker

`AUTOMATION_167_DOM_PROOF` remains unverified because the existing canonical shared runner has not claimed the task and no real port-8012 headless-browser truth file has been published.

`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.
