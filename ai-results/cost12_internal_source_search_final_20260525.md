# COST12 Internal Source Search Final — 2026-05-25

Decision: INTERNAL_PRODUCTION_READY_SOURCE_NOT_FOUND

## Search result

The local internal source search found 90 candidate files, but content review did not find a production-ready source row for:

- scenario_version=cost_uk_v1
- building_type=retail
- spec_grade=mid
- region=UK
- unit=GBP per gross internal area square metre

## Reviewed top candidates

### cost_item_catalog_12cost.csv

Contains a retail fit-out item:

- category: Fit-out / Retail
- building_group: retail
- cost_item: Retail fit-out shopfront signage
- unit: m2
- price_type: gbp_per_m2
- min/default/max: 400 / 1200 / 3500
- source_id: SRC_BCIS
- source_url_or_path: generic RICS/BCIS page
- accuracy_score_4: 1
- is_seed_based: true

Conclusion: useful as a low-confidence seed/catalog item, but not a production-ready building_type rate-card row. It lacks a specific BCIS extract/reference, date basis, scope definition and source reliability suitable for FINAL_READY_CONFIRMED.

### building_type_options_12cost.csv

Confirms retail is supported as an option with subtypes:

- small_shop
- supermarket
- showroom
- restaurant

Conclusion: options support exists, but this is not a rate source.

### historical_sales_parcel_matched CSV files

Contain Land Registry price-paid transaction records.

Conclusion: sale prices are market transaction data, not construction cost GBP/GIA m2 rates. Not valid for COST12 production rate-card.

### cost12_review_mode_ratecard_candidate_row_20260524.csv

Contains the already prepared public_proxy review-mode row.

Conclusion: valid only for COST12_READY_FOR_HUMAN_REVIEW_PUBLIC_PROXY, not production-ready.

## Final production blocker

Production-ready remains blocked by verified source requirement.

Required strong source:

- BCIS/RICS extract or direct reference
- QS written benchmark
- contractor/supplier quote
- official rate/fee schedule
- approved internal source with traceable path and adequate scope/date basis

## Safe completion state

- Review-mode: 100% complete
- Production-ready: 99%
- label: BLOCKED_SOURCE_REQUIRED

## Safety flags

- db_write=false
- production_deploy=false
- fake_data=false
- migration=false
- production_release=false
