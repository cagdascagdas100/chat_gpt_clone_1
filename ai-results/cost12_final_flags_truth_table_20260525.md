# COST12 Final Flags Truth Table — 2026-05-25

Decision: TECHNICAL_PREVIEW_COMPLETE_BUT_FINAL_SOURCE_QUALITY_NOT_COMPLETE

## Current verified preview status

The COST12 retail / mid / UK / cost_uk_v1 preview passes using the approved internal source with limitations path.

Verified preview highlights:

- PREVIEW_PASS
- rate_match_mode: csv_ratecard_fallback
- base_rate_gbp_per_gia_m2: 1200.0
- material_cost_reference: 0.0
- materials: []
- confidence_score: 47.6
- confidence_band: VERY_LOW
- is_seed_based: true
- integration_flags.fake_data: true
- db_write: false
- production_deploy: false

## Flag decision

The following flags must not be flipped by code-only change unless the underlying source quality changes:

| Flag | Current | Can be safely set to final? | Reason |
|---|---:|---:|---|
| integration_flags.fake_data | true | no | Seed/internal-source and seed cost items are still present. |
| is_seed_based | true | no | The base rate and cost-item chain still depend on seed/catalog/internal-source data. |
| confidence_band | VERY_LOW | no | Source reliability is 0.60, freshness is 0.30, specificity is 0.58, and seed penalty applies. |
| final_ready_confirmed | false | no | Direct BCIS/RICS/QS/contractor/official verified source is still missing. |

## What is 100% complete

- Approved internal source candidate preparation: complete
- CSV fallback for retail / mid / UK / cost_uk_v1: complete
- Base-rate-only material fallback without invented material rows: complete
- Preview validation: pass

## What remains incomplete for true production-final 100%

One of the following source upgrades is required:

- BCIS/RICS extract
- RICS/QS benchmark
- contractor/supplier quote
- official procurement/source document
- approved internal policy explicitly allowing limited internal source to count as final, while retaining limitations

## Safe final label

APPROVED_INTERNAL_SOURCE_WITH_LIMITATIONS_PREVIEW_PASS

## Unsafe label for now

FINAL_READY_CONFIRMED

## Safety note

Changing these flags without replacing the underlying source would create a false production-ready signal. The correct action is to keep the limitations visible until verified source replacement is completed.
