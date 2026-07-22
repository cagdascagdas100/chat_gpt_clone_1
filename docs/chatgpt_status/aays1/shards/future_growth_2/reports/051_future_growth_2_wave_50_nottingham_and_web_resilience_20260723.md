# future_growth_2 — Wave 50 Nottingham and web resilience

## Scope

Only `future_growth_2` was changed. This is source-candidate preparation, not parcel matching or product scoring. No runner, ownership, heartbeat, current-task, database, migration, deployment or merge state was changed.

## Pending/stuck audit and repair

The remote branch was reread after an apparent Wave 46/Wave 49 state discrepancy. The authoritative checkpoint, status and web manifest were already at Wave 49; no active stuck/pending task and no workflow run on the checked PR head were found. The website loader still had a real resilience defect: one missing optional JSON file inside `Promise.all` could blank the complete operation and candidate view. Wave 50 changes the loader to per-file fail-closed reads, preserves available rows and surfaces missing-file warnings.

## Official Nottingham review

Twenty official Nottingham City Council brownfield records were reviewed. Three current records were retained for point-only review: `2427` (16), `669` (387) and `138` (30). Twelve current records were held for missing status, capacity/delivery conflict, low capacity, permission status/date/type conflict or missing spatial locator. Five explicit-end records were excluded as historical. Narrative-only capacity on historical reference `1945` was normalized to null because no structured maximum was proven.

The documented API `period` filter was reviewed and a direct `period=current` response was attempted, but no valid direct response was obtained; the gate remains fail-closed at zero.

## Validation

- Nottingham structural checks: `96/96 PASS`
- official remote field checks: `80/80 PASS`
- grouped repository duplicate screens: `4/4`, zero indexed matches
- website manifest resilience checks: `8/8 PASS`
- real canonical rows, parcel matches, product scores and business rows: `0`

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.