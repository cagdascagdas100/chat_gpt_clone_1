# height_difference_3 — Transactional website acceptance and F-worktree freshness

- Slot: `height_difference_3`
- Parcel rows: `61523-92283` (`30,761`)
- Canonical source: `92,283` features; Git blob `8afd1d2bac414cf0f6b9484014e7878a4ceff877`
- State: real execution pending; `final_ready=false`

## Added this cycle

1. `033_transactional_website_acceptance.py` snapshots website JSON, GeoJSON, runtime and acceptance evidence before invoking `031`.
2. Failed acceptance restores existing targets byte-for-byte and removes targets that did not previously exist.
3. `034_verify_existing_f_worktree.py` rejects wrong/detached branch state, a HEAD before the minimum commit, dirty required pipeline files, unsafe paths and worktree/HEAD blob mismatches.
4. `032` now runs `034` before any official network work and runs `031` only through transactional `033`.
5. The existing `012` task was updated; no runner, queue, lease, owner or parallel task was created.

## Verification

- New tests: `39/39` passed.
- Cumulative tests: `208/208` passed.
- Transaction rollback accuracy: `4/4`.
- Worktree freshness accuracy: `4/4`.
- Fixture values were not published and no real measurement was generated.

## Official source refresh

- HM Land Registry INSPIRE polygons: current monthly release published `5 July 2026`.
- Environment Agency LIDAR Composite DTM 1m: persistent WCS and EPSG:27700 contract retained.
- OS Terrain 50: `July 2026` version; ASCII Grid/GML Grid supply retained.
- OS Downloads API: file name, format, subformat, area and redirect filters retained.

## Real counters

- Canonical shard rows exported: `0/30,761`
- Real candidates: `0`
- HMLR matches: `0`
- EA DTM samples: `0`
- Terrain 50 samples: `0`
- Verified website examples: `0`
- Port 8012 accepted: `false`

## First unverified step

`RUN_032_WITH_034_WORKTREE_GATE_THEN_029_030_026_027_AND_TRANSACTIONAL_033_031_PORT_8012_ACCEPTANCE_ON_EXISTING_F_RUNNER`

## Blockers

- Existing F portable shared runner has not executed updated `032`.
- Three real canonical and official cross-checked results do not exist.
- Port `8012` exact JSON, GeoJSON and runtime readback has not passed.
