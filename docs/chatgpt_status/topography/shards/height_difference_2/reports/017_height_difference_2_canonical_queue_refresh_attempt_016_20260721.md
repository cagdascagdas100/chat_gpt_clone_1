# height_difference_2 — canonical queue refresh attempt 016

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Task ID preserved: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Idempotency key preserved: `height-difference-2-canonical-export-official-sampling-v3`
- Attempt: `height-difference-2-20260721-016`
- Final ready: `false`

## Completed

1. Reread checkpoint 15, claim heartbeat and candidate output.
2. Confirmed the slot remained unclaimed and the candidate output remained absent.
3. Read the existing schema-v5 queue-refresh model used by the shared runner.
4. Moved the same task to the canonical early-order queue path `0000_001_height_difference_2_...task.json`.
5. Removed the superseded unprefixed queue file so no duplicate task remains at branch HEAD.
6. Published `request_queue_refresh.json` for the same task and existing single runner.
7. Preserved the prior Security/Public Safety request and its older Gas Emissions history.
8. Aligned global current task, slot current task, portable current task and legacy views.
9. Added a fail-closed refresh verifier and passed 14/14 checks.
10. Attempted direct raw canonical GeoJSON retrieval through the internet layer; it returned a cache miss, so no sample row was inferred or fabricated.

## Current evidence

- Canonical queue task: schema v5, priority 2, pickup requested.
- Queue refresh: requested and waiting for the existing runner scan.
- Canonical source contract: 77,970 committed features, blob `ca95400a...`.
- Real candidate seeds: 0.
- Exact HMLR polygons: 0.
- EA DTM1m polygon samples: 0.
- OS Terrain50 crosschecks: 0.
- Port 8012 acceptance rows: 0.

## Blocker

The existing TerraYield portable single shared runner has not produced a claim heartbeat after the canonical queue refresh. No new runner or process was started.
