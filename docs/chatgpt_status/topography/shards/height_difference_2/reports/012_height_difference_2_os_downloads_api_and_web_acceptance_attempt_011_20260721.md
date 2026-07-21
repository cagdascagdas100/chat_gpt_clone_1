# height_difference_2 — OS Downloads API and web acceptance — attempt 011

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Existing task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-011`
- Checkpoint target: `11`
- Final ready: `false`

## Completed in this checkpoint

1. Re-read checkpoint 10, heartbeat and expected outputs without replaying completed work.
2. Verified official OS Downloads API product and product-download endpoint contracts.
3. Added unique OS Terrain 50 product resolution and exact polygon-to-100km-area derivation.
4. Added safe, hashed ASCII/Grid ZIP download validation.
5. Added multi-archive preparation before the existing OS Terrain 50 polygon crosscheck.
6. Updated the official numeric orchestrator to use OS Downloads API automatically when no configured archive/root exists.
7. Added port `8012` HTTP acceptance for index, manifest, contiguous operation rows and candidate safety flags.
8. Passed `13/13` local positive and fail-closed tests; fixtures were not committed or promoted.
9. Aligned the same task and idempotency key through AAYS21 JSON, legacy text and portable `ai-tasks` pickup modes.
10. Published web operation rows `126-145`.

## Current evidence

- Planned operations: `161`
- Completed operations: `131`
- Batch progress: `81.37%`
- Batch increase: `+1.94%`
- Overall layer progress: `78%`
- Overall increase: `0%`
- Visible web rows: `145`
- Automation tests: `83/83 PASS`
- Source/endpoint contracts: `4`
- Real candidate seeds: `0`
- Exact HMLR polygon rows: `0`
- EA DTM 1m numeric rows: `0`
- OS Terrain 50 crosschecks: `0`
- Port 8012 acceptance rows: `0`

## Blocker

The existing F portable shared runner remains unclaimed. Real candidate extraction, current HMLR GML downloads, exact polygons, EA DTM 1m sampling, OS Terrain 50 downloads/crosschecks and port 8012 readback have not produced remote outputs.

No synthetic parcel, geometry or elevation value was written.
