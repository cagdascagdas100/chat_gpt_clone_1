# height_difference_3 — alias-safe resumable validator ready

- Slot: `height_difference_3`
- Parcel range: `61523-92283` (`30,761` rows)
- Canonical source: `security.geojson`, `92,283` explicit features
- Final ready: `false`

## Completed

1. Re-read remote HEAD, sequence 12 checkpoint/status and stale unclaimed heartbeat.
2. Confirmed no real `026` runtime output, canonical shard, official measurement or port 8012 acceptance evidence exists.
3. Reconfirmed the canonical blob and explicit identity schema.
4. Audited `020`, `025`, `026` and `004` together.
5. Found a real execution-blocking contract mismatch: `020` permits explicitly linked same-coordinate London-authority overlap aliases, while `025` rejected every repeated HMLR INSPIRE identity.
6. Added `027_validate_resumable_alias_safe.py`.
7. Preserved all downstream HMLR, EA DTM, Terrain 50, measurement and publication gates from `025`.
8. Added fail-closed checks for one primary identity, identical source coordinates, explicit alias status, unique parcel IDs, contiguous rows and coordinate extents.
9. Passed `16/16` positive and negative fixture tests; cumulative automation tests are `104/104 PASS`.
10. Rewired the existing `012` task contract to call `026` with `--validator-script 027`.
11. No queue, owner, lease, heartbeat, new runner, candidate, geometry or elevation was fabricated.

## Current truthful counts

- Canonical source features: `92,283`
- Real shard rows exported: `0/30,761`
- Real candidates: `0`
- HMLR matches: `0`
- EA DTM samples: `0`
- Terrain 50 crosschecks: `0`
- Published real examples: `0`

## Next step

`RUN_026_WITH_ALIAS_SAFE_VALIDATOR_027_ON_EXISTING_F_RUNNER_THEN_VERIFY_PORT_8012`

## Blocker

`EXISTING_F_RUNNER_MUST_EXECUTE_026_WITH_VALIDATOR_027; THREE_REAL_CANONICAL_ROWS_AND_OFFICIAL_NETWORK_RESULTS_REQUIRED; PORT_8012_LIVE_READBACK_REQUIRED`

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` remain enforced.
