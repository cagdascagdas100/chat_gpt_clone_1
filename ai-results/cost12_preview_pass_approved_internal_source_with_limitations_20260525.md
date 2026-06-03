# COST12 Preview Pass — Approved Internal Source With Limitations — 2026-05-25

Decision: COST12_PREVIEW_PASS_APPROVED_INTERNAL_SOURCE_WITH_LIMITATIONS

## Outcome

The COST12 retail / mid / UK / cost_uk_v1 preview now passes using the approved internal source with limitations path.

## Verified response highlights

- scenario_version: cost_uk_v1
- building_type: retail
- building_subtype: restaurant
- spec_grade: mid
- region: UK
- local_authority: Rugby
- rate_match_mode: csv_ratecard_fallback
- base_rate_gbp_per_gia_m2: 1200.0
- gross_internal_area_m2: 250.0
- base_cost: 300000.0
- total_cost: 507600.0
- cost_per_gia_m2: 2030.4
- material_cost_reference: 0.0
- materials: []
- source_reliability: 0.6
- confidence_score: 47.6
- confidence_band: VERY_LOW
- is_seed_based: true

## Safety flags

- db_write: false
- production_deploy: false
- integration_flags.fake_data: true
- final_ready_confirmed: false

## Interpretation

The task is technically complete for read-only preview validation using the approved internal source with limitations path.

This is not FINAL_READY_CONFIRMED because the rate is not a direct BCIS/RICS/QS/contractor verified source. It remains a project-owner-approved internal benchmark with seed/source limitations.

## Valid label

APPROVED_INTERNAL_SOURCE_WITH_LIMITATIONS_PREVIEW_PASS

## Invalid label for now

FINAL_READY_CONFIRMED

## Remaining production blocker

Replace the seed/internal benchmark with a stronger verified source to raise confidence and remove fake_data/seed limitations:

- BCIS/RICS extract
- QS benchmark
- contractor/supplier quote
- official procurement/source document

