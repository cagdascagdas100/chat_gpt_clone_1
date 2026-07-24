# future_growth_1 — Official Source Registry Wave 2

## Scope

- Slot: `future_growth_1`
- Canonical parcel range: `1-30761`
- Canonical matrix: `92283` London rows, not an all-England parcel inventory
- Calculation version: `future_growth_v1`
- `final_ready=false`

## Completed source work

The original 16-source Future Growth registry was read from the merged Stage 1 contract and every registry row was checked against its official public endpoint and stated use boundary.

- Registry endpoint/scope readback: `16/16`
- Source URLs present: `16/16`
- Purpose and mode contracts present: `16/16`
- Remaining registry entries completed in this wave: `11`
- Loader executions completed: `0/16`
- Parcel-specific rows promoted from this source wave: `0/30761`
- Future Growth scores emitted: `0/30761`

The completed registry covers:

1. HM Land Registry Price Paid Data
2. Planning Data API
3. Brownfield land
4. Conservation areas
5. Listed buildings
6. Green Belt
7. ONS subnational population projections
8. ONS internal migration projections
9. NaPTAN
10. Bus Open Data Service
11. National Rail Darwin feeds
12. TfL WebCAT PTAL/TIM
13. Get Information about Schools
14. NHS ODS ORD API
15. OS Open Greenspace
16. Environment Agency Flood Zones plus Climate Change

## Accuracy boundary

`16/16` means that the official endpoint, scope, update/correction caveat and intended model role were read back. It does **not** mean that all loaders ran, that all datasets were joined to a parcel, or that a score can be emitted.

Important fail-closed rules remain:

- local-authority projections are `AREA_LEVEL_PROXY`, not parcel measurements;
- listed-building points do not by themselves prove affected extent;
- conservation-area coverage is incomplete and duplicate reconciliation is ongoing;
- Green Belt is an annual snapshot and may lag later boundary changes;
- transport/service sources require current coordinates and route/service binding;
- flood, greenspace and planning constraints require parcel-polygon overlay;
- source confidence never substitutes for parcel-match confidence.

## Website outputs

- `england_map_web/data/aays_21_slots/future_growth_1/official_source_registry_wave_2_latest.json`
- `england_map_web/data/aays_21_slots/future_growth_1/source_registry_wave_2.html`
- `england_map_web/data/aays_21_slots/future_growth_1/index.html`

## Existing candidate evidence retained

- Canonical sample parcels: `3`
- Official candidate rows: `6`
- Current candidates: `5`
- Stale/completed rejection: `1`
- Official entity readback: `4/4`
- Candidate/source field checks: `72/72`
- Geometry self-test: `7/7`
- Verified official polygon relations: `0`
- Actual business rows written: `0`

## First unverified step

`WAIT_FOR_SINGLE_SHARED_RUNNER_PICKUP_THEN_EXECUTE_EXACT_OFFICIAL_GEOMETRY_ATTEMPT_3`

The existing global shared task remains ahead of this slot. No new runner was created and the global control alias was not replaced.

Safety flags remain false: `fake_data`, `db_write`, `migration`, `production_deploy`, `final_ready`.
