# height_difference_2 — Runner Preparation and Queue Readback

- SLOT_ID: `height_difference_2`
- Parcel partition: `30762-61522` (`30761` rows)
- Branch: `codex/aays-single-runner-v5-20260706`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Checkpoint resumed: `2`
- Readback time: `2026-07-20T19:12:00Z`
- Result: `QUEUED_UNCLAIMED_RUNNER_OUTPUT_PENDING`

## Work completed in this continuation

1. Created a bounded Python payload for canonical shard export, three real-candidate selection, HMLR INSPIRE matching, EA DTM 1 m polygon statistics, OS Terrain 50 crosscheck, web operation publication and port 8012 readback.
2. Created a PowerShell wrapper that validates branch/page context and reuses the existing F portable Python package root.
3. Created one consolidated 16-stage queue task for the existing canonical single shared runner.
4. Selected that task in the global `current.task.json` because the previous task was already terminal `done`.
5. Updated only the `height_difference_2` slot current-task state from `idle` to `queued`.
6. Published preparation and source-verification operations to the shard website JSON.

## Progress

- planned operation count: `45`
- completed preparation/source operations: `18`
- blocked operations: `2`
- queued runner operation: `1`
- preparation batch percent: `40.0%`
- overall layer percent: `78%`
- percent increase: `0%`
- visible web operation rows: `21`

## Sources and accuracy

- source candidates: `3`
- upgraded source contracts: `3`
- source readiness accuracy: `3.8/4`
- current layer accuracy: `2.5/4 fallback`
- real parcel candidates: `0`
- measured parcel rows: `0`

Source hierarchy:

1. HMLR INSPIRE monthly GML — indicative real-boundary match in native EPSG:27700.
2. Environment Agency LIDAR Composite DTM 1 m — primary official numeric elevation; polygon median and Q1/Q3.
3. OS Terrain 50 — independent secondary official numeric crosscheck.

## Remote readback

- global current task: `queued`
- slot current task: `queued_for_existing_single_shared_runner`
- slot heartbeat: `unclaimed`, no owner, no heartbeat
- expected runner output: not present
- runner claim proof: not present
- port 8012 runner HTTP readback: pending

No execution result, runner heartbeat, parcel identifier, coordinate, geometry or elevation was synthesized.

## Next verified action

The existing canonical shared runner must claim the queued task. Its first work is to discover/export canonical matrix rows `30762-61522`; only then may up to three real candidates be selected and official measurements attempted.

## Safety state

- `single_runner_only=true`
- `new_runner=false`
- `parallel_runner=false`
- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
