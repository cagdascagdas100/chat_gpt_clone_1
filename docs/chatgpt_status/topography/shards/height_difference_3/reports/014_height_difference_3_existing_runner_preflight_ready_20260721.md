# Height Difference 3 — Existing F Runner Preflight Ready

- Slot: `height_difference_3`
- Parcel range: `61523-92283` (`30,761` rows)
- Checkpoint target: `14`
- Final ready: `false`

## Completed in this cycle

1. Re-read sequence 13 checkpoint, status and runtime JSON.
2. Confirmed that real `026+027` execution has not started and all real counters remain zero.
3. Revalidated current official source contracts:
   - HMLR INSPIRE publication dated 5 July 2026 and monthly local-authority GML delivery.
   - OS Terrain 50 version `2026-07`.
   - Environment Agency persistent LIDAR Composite DTM 1m WCS.
4. Added `028_preflight_existing_f_runner.py`.
5. Added `029_preflight_then_execute_resumable.py`.
6. Rewired the existing `012` task contract to execute `029`, which runs preflight before `026` with validator `027`.
7. Passed 14 of 14 fixture tests; cumulative tests are 118 of 118.
8. Preserved one existing shared runner, maximum two bounded network checks/stages, and no queue/lease creation.

## Preflight gates

- Python `>=3.10`.
- Importable `requests`, `pyproj`, `fiona`, `rasterio`, `shapely`, and `numpy`.
- Twelve required pipeline scripts present and compilable.
- Canonical `security.geojson` Git blob SHA-1 equals `8afd1d2bac414cf0f6b9484014e7878a4ceff877`.
- At least 4 GiB free space and successful atomic write/rename probe.
- HMLR download page signature.
- OS Terrain 50 product API with July version.
- EA DTM 1m WCS capabilities signature.

Any required failure stops before `026` and publishes the failing check to the website runtime JSON.

## Real-result state

- Canonical shard rows exported: `0`
- Real candidate rows: `0`
- HMLR boundary matches: `0`
- EA DTM samples: `0`
- OS Terrain 50 samples: `0`
- Verified website examples: `0`

No parcel geometry or elevation value was fabricated.

## First unverified step

`RUN_029_PREFLIGHT_THEN_026_WITH_VALIDATOR_027_ON_EXISTING_F_RUNNER_THEN_VERIFY_PORT_8012`

## Blockers

- Existing F portable shared runner has not executed `029`.
- Three real canonical candidates and official HMLR/EA/OS results are still required.
- Port 8012 live readback remains unverified.

Safety flags remain `false`: fake data, database write, migration, and production deployment.