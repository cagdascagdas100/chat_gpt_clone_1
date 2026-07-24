# height_difference_3 — combined runtime stream ready

- Slot: `height_difference_3`
- Parcel rows: `61523-92283` (`30,761`)
- Checkpoint target: `16`
- Final ready: `false`

## Completed in this cycle

1. Re-read remote HEAD, checkpoint, status, heartbeat and website runtime.
2. Confirmed the existing F runner has not executed `029`; all real result counts remain zero.
3. Revalidated the official HMLR July 2026 release, OS Terrain 50 annual July supply/API filters and EA DTM 1m WCS contract.
4. Found that `026` replaced the website runtime JSON and therefore removed the eight preflight rows written by `028`.
5. Added `030_stream_combined_runtime.py` to preserve the preflight prefix and atomically stream `026` operations after it.
6. Updated `029` so `026` writes an internal runtime file while `030` publishes the combined website runtime.
7. Kept monotonic operation numbering, child exit-code propagation and fail-closed missing-runtime handling.
8. Updated the existing `012` single-runner task contract. No queue, lease, owner, heartbeat, new runner or parallel runner was created.
9. Passed `22/22` new fixture tests; cumulative result is `155/155`.

## Real-data state

- Canonical shard exported: `0/30,761`
- Real candidates selected: `0`
- HMLR polygon matches: `0`
- EA DTM samples: `0`
- OS Terrain 50 samples: `0`
- Verified website examples: `0`

## First unverified step

`RUN_029_WITH_030_COMBINED_RUNTIME_THEN_026_WITH_VALIDATOR_027_ON_EXISTING_F_RUNNER_THEN_VERIFY_PORT_8012`

## Blockers

- Existing F portable shared runner has not executed the updated `029` bootstrap.
- Three real canonical candidates and official HMLR/EA/OS crosschecked measurements are required.
- Port `8012` live runtime and result readback is required.

Safety flags remain false and `final_ready=false`.
