# future_growth_1 — Official Source Wave 1 and Canonical Sample Candidates

## Remote authority

- Branch: `codex/aays-single-runner-v5-20260706`
- Branch HEAD readback before publication: `c3b093daacca4a8bb3688958b23f6443034db101`
- Slot: `future_growth_1`
- Parcel range: `1-30761`
- Remote checkpoint sequence before work: `1`
- Remote ownership: `UNCLAIMED`
- Remote current task: `IDLE`
- Remote heartbeat: `IDLE`
- `final_ready=false`

## Canonical source resolved

The committed canonical source is:

`england_map_web/data/program_layer_matrix/security.geojson`

- Blob SHA: `8afd1d2bac414cf0f6b9484014e7878a4ceff877`
- Features: `92,283`
- Identity fields: `row_no`, `parcel_id`, `hmlr_inspire_id`
- Coordinate fields: `hmlr_lon`, `hmlr_lat`, `geometry.coordinates`
- Scope: `LONDON_CANONICAL_92283_NOT_ALL_ENGLAND`

The first three explicit rows in this shard were read as `parcel_1`, `parcel_2`, and `parcel_3`. Feature order was not used as inferred identity.

## Official internet source validation

Validated official sources: `5/16 = 31.25%`.

1. Planning Data brownfield land: 37,666 entities, 354 providers, collector last ran 2026-07-17, new data last found 2026-07-16.
2. HM Land Registry Price Paid Data: May 2026 current-month release; page updated 2026-06-26; monthly update on the 20th working day.
3. ONS 2022-based subnational population projections: released 2025-06-24; affected single-year datasets corrected on 2025-06-25; migration category variant guidance retained.
4. OS Open Greenspace: official six-monthly product; spatial loader still pending.
5. Environment Agency Flood Zones plus Climate Change: official dataset updated 2026-07-06; spatial loader still pending.

## Candidate examples

Six row-level official Planning Data candidates were prepared for the first three canonical parcels.

- Current official point candidates: `5`
- Stale/completed source rejected as active growth: `1`
- Source URL present: `6/6`
- Canonical parcel identity present: `6/6`
- Point distance recomputed: `6/6`
- Official site polygon verified: `0/6`
- Future Growth scores emitted: `0/6`

Notable candidates:

- `parcel_1` → Former Ford Stamping Plant (`LBBD49/XJ`): 753.9 m point distance; current, permissioned, development commenced; polygon verification pending.
- `parcel_2` → Former Ford Stamping Plant (`LBBD49/XJ`): 668.6 m point distance; current, permissioned, development commenced; polygon verification pending.
- `parcel_2` → GSR and Gill Sites (`LBBD72/ZZ`): 981.9 m point distance; current, permissioned, 707 dwellings; polygon verification pending.
- `parcel_3` → Ilchester Road Garages (`LBBD23`): 308.7 m point distance but the entity is out of date and development complete; rejected as an active growth signal.

## Output boundary

These are official source candidates, not completed Future Growth business rows. No polygon intersection, popup eligibility, factor score, weighted score, or confidence score was claimed. `actual_business_data_rows_written=0`.

## Published website files

- `england_map_web/data/aays_21_slots/future_growth_1/index.html`
- `england_map_web/data/aays_21_slots/future_growth_1/candidates_latest.json`
- `england_map_web/data/aays_21_slots/future_growth_1/progress_latest.json`

## Next unverified step

`FETCH_OFFICIAL_SITE_GEOMETRIES_FOR_FIRST_THREE_PARCELS_THEN_BUILD_30761_ROW_EVIDENCE_MATRIX`

## Blockers

- `OFFICIAL_BROWNFIELD_SITE_POLYGONS_NOT_READ_BACK`
- `FULL_30761_ROW_FACTOR_MATRIX_NOT_BUILT`
- `NON_PLANNING_FACTOR_LOADERS_NOT_EXECUTED`

Safety flags remain false: `fake_data`, `db_write`, `migration`, `production_deploy`. “Kesin fiyat tahmini değildir.”
