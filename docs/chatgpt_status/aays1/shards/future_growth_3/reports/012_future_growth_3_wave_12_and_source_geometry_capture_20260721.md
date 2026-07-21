# future_growth_3 — Wave 12 + source geometry capture

Date: 2026-07-21

## Completed work
- Revalidated slot checkpoint/status/heartbeat/current-task on `codex/aays-single-runner-v5-20260706`.
- Re-ran repository search for canonical shard rows 61,523–92,283; no export was found.
- Added 16 official brownfield records from RBKC, OPDC/GLA, LLDC and City of London.
- Kept 9 as source candidates and excluded 7 historical, removed or temporally conflicting records.
- Verified the Planning Data API contract for `/entity/{entity}.geojson` and WKT `point`/`geometry` fields.
- Consolidated 12 source waves: 145/145 researched rows and 129/129 eligible rows have an official point or polygon source reference.
- Marked `SOURCE_GEOMETRY_CAPTURE` complete at official point-or-polygon source level.

## Accuracy controls
- Three RBKC records with entity/CURIE temporal disagreement were excluded pending refresh.
- LLDC3 was excluded because the official current LLDC register states it was removed, despite the Planning Data record retaining a blank end date.
- Four OPDC records with 2027 start dates remain review candidates, not current parcel assignments.
- Note-derived unit counts remain separate from structured maximum-net-dwellings.
- Official points are not promoted to canonical parcel polygons or nearest parcels.

## Progress
- Completed operations: 7/12.
- Operational progress: 58.33%, increase +8.33 percentage points.
- Research rows: 145; eligible 129; excluded 16; high source confidence 133.
- Average eligible source confidence: 97.2/100.
- Source families: 36.
- Canonical rows matched: 0/30,761.

## Remaining blocker
`CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY`.

No score, parcel ID, DB write, migration, deployment or FINAL_READY claim was produced.
