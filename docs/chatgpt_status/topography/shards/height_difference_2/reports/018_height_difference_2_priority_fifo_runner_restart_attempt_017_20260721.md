# height_difference_2 — attempt 017 priority/FIFO and canonical runner restart

- SLOT_ID: `height_difference_2`
- Parcel partition: `30762-61522` (`30761` rows)
- Task ID: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt ID: `height-difference-2-20260721-017`
- Checkpoint target: `17`
- `final_ready=false`

## Confirmed progress

1. Reread checkpoint 16, slot heartbeat and expected real outputs.
2. Confirmed the slot remains unclaimed and candidate/HMLR/EA/OS/8012 outputs are absent.
3. Read the canonical stable shared-runner source. Queue selection is `priority`, then `created_at`, then `page_key`, then `task_id`; the filename prefix is not a selection criterion.
4. Compared the active height_difference_2 task with the competing priority-1 Security/Public Safety task. Height difference now uses priority `1` and preserves the older `created_at=2026-07-20T19:08:00Z`, so it precedes the competing task dated `2026-07-21T08:20:00+03:00` under the runner's FIFO contract.
5. Confirmed the canonical F daemon heartbeat is stale at `2026-07-16T13:45:53.0433295Z`; the latest multi-page scan evidence is dated `2026-07-07T18:25:04Z` and references an old C root.
6. Added a fail-closed helper that starts only `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd` when no canonical process is alive, preserves one live process and blocks multiple processes.
7. Published a reboot/start request for the existing canonical runner. No new runner architecture, task, worktree or parallel process was created.
8. Aligned JSON, slot, portable and legacy pickup views with attempt 017.
9. Revalidated HMLR INSPIRE July 2026, EA DTM 1m/WCS and OS Terrain 50 July 2026 official contracts.
10. Deterministic static contract validation passed `20/20`.

## Canonical source provenance

The Topography GeoJSON was integrated in commit `df4526fd6e1cfa18ce42df6eabf250de6192b383` with `77,970` features and later preserved as Git blob `ca95400a5644f77a79cbaf47b2c2d611d3777a55`. The connector can read the blob start but cannot seek inside the 61.98 MB single-line JSON. No candidate identity, coordinate or elevation was inferred from truncated content.

## Current metrics

- Planned operations: `281`
- Completed operations: `245`
- Blocked operations: `6`
- Pending operations: `10`
- Batch progress: `87.19%` (`+0.60` percentage points)
- Overall completion: `78%` (`+0%`)
- Website operation rows: `265`
- Target candidate seeds: `3`
- Real candidate seeds: `0`
- Exact HMLR polygons: `0`
- EA DTM1m polygon samples: `0`
- OS Terrain50 crosschecks: `0`
- Port 8012 acceptance rows: `0`
- Validation: `227/227 PASS`
- Source contract accuracy: `4.0/4`
- Parcel measurement accuracy: `0/4_not_produced`

## Real blocker

`EXISTING_CANONICAL_F_RUNNER_RESTART_NOT_OBSERVED;SLOT_CLAIM_NOT_OBSERVED;THREE_REAL_CANDIDATE_SEEDS_PENDING;THREE_EXACT_HMLR_POLYGONS_PENDING;THREE_EA_DTM1M_POLYGON_SAMPLES_PENDING;THREE_OS_TERRAIN50_CROSSCHECKS_PENDING;PORT_8012_HTTP_READBACK_PENDING`

## Next verified step

Run the fail-closed restart helper in the canonical F environment, observe one canonical process and a fresh shared heartbeat, then let the same task claim attempt 017 and produce the three official sample chains. No measurement or product row may be promoted before exact HMLR polygons and official numeric evidence exist.
