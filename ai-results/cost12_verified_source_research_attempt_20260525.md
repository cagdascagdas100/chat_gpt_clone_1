# COST12 Verified Source Research Attempt — 2026-05-25

Decision: VERIFIED_EXTERNAL_SOURCE_NOT_OBTAINED_PUBLICLY

## Goal

Attempt to obtain a stronger external verified source for:

- scenario_version: cost_uk_v1
- building_type: retail
- spec_grade: mid
- region: UK
- unit: GBP per gross internal area m2

Target source classes:

- BCIS/RICS extract
- QS benchmark
- contractor/supplier quote
- official procurement/source document

## Public web research result

### BCIS/RICS

BCIS publicly confirms that CapX provides access to UK construction cost data and supports capital cost planning, but the actual detailed data is accessed through the BCIS online service / demonstration route. No public extract row was obtained for retail / mid / UK / cost_uk_v1.

Status: SOURCE_ROUTE_FOUND_BUT_EXTRACT_NOT_PUBLIC

### QS benchmark

No public QS benchmark was found that provides an attributable, dated, directly applicable retail / mid / UK GBP per GIA m2 row suitable for production-ready use.

Status: NOT_FOUND_PUBLICLY

### Contractor/supplier quote

No public contractor/supplier quote was found that provides retail / mid / UK GBP per GIA m2 with enough scope/date/source metadata for production-ready use.

Status: NOT_FOUND_PUBLICLY

### Official procurement/source document

No official procurement/source document was found that combines all required fields:

- retail/shop/restaurant scope
- UK region or UK-wide applicability
- contract value
- GIA/m2 basis or enough area evidence to calculate GBP/GIA m2
- source date/base month
- included/excluded scope

Status: NOT_FOUND_PUBLICLY

## Current technical state

The approved internal source with limitations preview has passed.

Known output:

- PREVIEW_PASS
- rate_match_mode: csv_ratecard_fallback
- base_rate_gbp_per_gia_m2: 1200.0
- total_cost: 507600.0
- cost_per_gia_m2: 2030.4
- confidence_band: VERY_LOW
- is_seed_based: true
- integration_flags.fake_data: true
- db_write: false
- production_deploy: false

## Valid current label

APPROVED_INTERNAL_SOURCE_WITH_LIMITATIONS_PREVIEW_PASS

## Not valid yet

FINAL_READY_CONFIRMED

## Remaining route to final production 100

Obtain one of:

- BCIS/RICS export/extract
- RICS/QS written benchmark
- contractor/supplier quote
- official procurement/source document with area and scope

Until then, the correct state remains preview-pass with limitations, not final-ready.
