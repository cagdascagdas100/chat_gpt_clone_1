# COST12 Final Source Required Blocker — 2026-05-24

Decision: COST12_FINAL_BLOCKED_SOURCE_REQUIRED
Overall progress: 99

## Evidence

The local targeted probe found the direct known rate-card file:

- `C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tools\cost_uk_real_engine\config\building_type_rate_card_uk.csv`

The file contains mid-rate rows for:

- `residential_house`
- `residential_apartment`
- `warehouse_light_industrial`

The visible rows use:

- `source_id=engineering_seed_assumptions_v1`
- `source_url=N/A`
- `source_reliability=0.35`
- `notes=seed_replace_required`

The options file confirms that `retail` is a supported building type in the menu/options layer:

- `tools\cost_uk_real_engine\config\building_type_options_12cost.csv`
- `building_type_key=retail`
- allowed subtypes: `small_shop;supermarket;showroom;restaurant`

But the visible rate-card rows do not include a matching rate-card source row for:

- `building_type=retail`
- `spec_grade=mid`
- `region=UK`
- `scenario_version=cost_uk_v1`

The API confirms the same blocker:

`No cost rate row found for building_type=retail, spec_grade=mid, region=UK, scenario=cost_uk_v1`

## Final blocker

The remaining blocker is a verified source-data blocker, not a runner problem and not a route-mount problem.

A real 100% close requires a verified rate-card row for retail/mid/UK/cost_uk_v1 from one of:

- BCIS / RICS source
- official fee/rate table
- supplier or contractor quote evidence
- approved internal source document with traceable source URL/path and reliability metadata

## Not allowed

Do not invent a fake retail rate.
Do not copy warehouse/residential rates into retail unless there is a verified mapping source.
Do not mark FINAL_READY_CONFIRMED while the retail rate row is missing.

## Safety flags

- db_write=false
- production_deploy=false
- fake_data=false
- no_migration=true
- no_production_release=true

## Next required action

Provide or import a verified retail/mid/UK/cost_uk_v1 rate row, then rerun:

POST /cost/estimate/preview

with:

- `building_type=retail`
- `building_subtype=restaurant`
- `quality_level=mid`
- `gross_internal_area_m2=250`
- `sales_area_m2=200`
- `fit_out_level=mid`
- `cooling_kitchen_need=true`
- `db_write=false`
- `production_deploy=false`
