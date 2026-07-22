# future_growth_3 — Wave 29

- Slot: `future_growth_3`
- Partition: 61,523–92,283 (30,761 rows)
- Scope: source candidates only; no canonical parcel assignment
- New candidates: 24 researched / 24 eligible / 0 excluded
- New source families: South Oxfordshire District Council; City of Wolverhampton Council
- Average source confidence: 97.83/100
- Visible web rows: 24 candidates + 36 operations
- Provider validation issues: 24 rows retain `PLANNING_HISTORY_URI_INVALID_AT_PROVIDER`
- Canonical matches: 0
- Scores: 0
- Fake rows: 0

## Source handling

The rows were transcribed from official MHCLG Planning Data provider validation tables. South Oxfordshire records were selected only where a stated positive dwelling capacity, official point, status and entry date were visible. Wolverhampton selection was restricted to four positive-capacity rows with recognised permission status. Invalid PlanningHistory URIs were not repaired or hidden. Entity IDs were not inferred.

## Blocker

`CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY`

Without the canonical shard export and CRS manifest, point-to-parcel intersection, row assignment and future-growth scoring remain blocked. `final_ready=false`.