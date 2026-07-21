# height_difference_3 — resumable targeted official-source pipeline — checkpoint 12

- Slot: `height_difference_3`
- Parcel range: `61523-92283` (`30,761` rows)
- Canonical carrier: `security.geojson` (`92,283` explicit rows)
- Final ready: `false`

## Completed

1. Re-read branch HEAD, sequence 11 checkpoint/status and the unclaimed heartbeat.
2. Confirmed no real `024` runner output, shard export, candidate, measurement or verified web example exists.
3. Added `025_validate_resumable_targeted_sources.py`.
4. Added `026_execute_resumable_targeted_sources.py`.
5. Locked eight resumable stages from canonical extraction through verified JSON/GeoJSON publication.
6. Added SHA-256, official MD5, explicit row registry, HMLR identity, EPSG:27700, EA resolution, Terrain50 grid, confidence and polygon publication gates.
7. Kept bounded in-process concurrency at two network stages; no new runner, parallel runner, queue or lease was created.
8. Added atomic runtime progress JSON for line-by-line website visibility.
9. Passed 16/16 non-production fail-closed and resume-path tests; fixtures were not published.
10. Refreshed official HMLR, Environment Agency and Ordnance Survey source contracts.

## Current truthful state

- Canonical source resolved: `1 / 92,283 features`
- Real shard export: `0 / 30,761`
- Real candidates: `0`
- HMLR matches: `0`
- EA DTM samples: `0`
- Terrain50 samples: `0`
- Verified web examples: `0`
- Cumulative tests: `88 / 88`
- Website operation rows after publication: `300`
- Overall completion after publication: `85%`

## First unverified step

`RUN_026_RESUMABLE_TARGETED_SOURCES_ON_EXISTING_F_RUNNER_THEN_VERIFY_PORT_8012`

## Blocker

`EXISTING_F_RUNNER_MUST_EXECUTE_026_ON_COMMITTED_SECURITY_GEOJSON; THREE_REAL_CANONICAL_ROWS_AND_OFFICIAL_NETWORK_RESULTS_REQUIRED; PORT_8012_LIVE_READBACK_REQUIRED`

No synthetic parcel identity, geometry, coordinate, elevation or completion state was written.
