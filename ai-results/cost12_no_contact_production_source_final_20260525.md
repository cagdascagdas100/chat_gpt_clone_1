# COST12 No-Contact Production Source Final — 2026-05-25

Decision: NO_CONTACT_PRODUCTION_READY_SOURCE_NOT_FOUND

## Selected no-contact method

The best no-contact method was applied:

- official procurement / tender-document search
- public project cost/floor-area search
- local/internal candidate source search

## Requirement

Production-ready source row required for:

- scenario_version=cost_uk_v1
- building_type=retail
- spec_grade=mid
- region=UK
- unit=GBP per gross internal area square metre

## Search outcome

No no-contact source was found that satisfies all production-ready criteria:

- retail/shop/restaurant scope
- mid-spec or mappable mid-spec scope
- UK or UK region
- GBP per GIA m2 or enough evidence to calculate it
- source date/base month
- source identity and traceability
- included/excluded scope
- confidence suitable for production_ready=true

## Local/internal source review outcome

The internal search found candidate files, but content review showed:

1. cost_item_catalog_12cost.csv contains a retail fit-out seed/catalog item, not a production rate-card row.
2. building_type_options_12cost.csv confirms retail is supported, but it is not a cost source.
3. historical sales CSV files contain Land Registry sale transaction data, not construction cost GBP/GIA m2 rates.
4. cost12_review_mode_ratecard_candidate_row_20260524.csv is already labelled public_proxy, production_ready=false, review_mode=true.

## Safe current state

- Review-mode: 100% complete
- Production-ready: 99%
- label: BLOCKED_SOURCE_REQUIRED

## Valid current label

COST12_READY_FOR_HUMAN_REVIEW_PUBLIC_PROXY

## Not valid yet

FINAL_READY_CONFIRMED

## Safety flags

- db_write=false
- production_deploy=false
- fake_data=false
- migration=false
- production_release=false

## Only remaining route to production 100

Attach one verified source row from one of:

- BCIS/RICS extract or direct reference
- QS written benchmark
- contractor/supplier quote
- official procurement/rate/fee document containing value and GIA/scope
- approved internal source with traceable path, date, scope and rate
