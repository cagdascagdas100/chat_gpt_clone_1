# COST12 Final Review-Mode Closure — 2026-05-24

Decision: COST12_READY_FOR_HUMAN_REVIEW_PUBLIC_PROXY

Production final decision: BLOCKED_SOURCE_REQUIRED

## What is complete

The COST12 technical workflow has been completed as far as it can be completed without a stronger commercial cost source.

Completed items:

- Runner status checked.
- Endpoint mount checked.
- Options endpoint passed.
- Cost history endpoint passed.
- Payload schema issue isolated and resolved by using gross_internal_area_m2.
- Rate-card lookup blocker isolated.
- Local rate-card file found.
- Retail option support confirmed.
- Retail rate-card row confirmed missing from available local rate-card data.
- Public web proxy research completed.
- Public proxy candidate row prepared for human review.
- Review-mode handoff ZIP prepared.
- DB write stayed false.
- Production deploy stayed false.
- Fake data stayed false.

## Remaining production blocker

A production-ready close still requires a verified rate source for:

- scenario_version: cost_uk_v1
- building_type: retail
- spec_grade: mid
- region: UK
- unit: GBP per gross internal area square metre

Accepted strong source types:

- BCIS / RICS extract or reference
- official public authority rate / fee schedule
- supplier or contractor quote
- approved internal cost source with traceable path or URL

## Review-mode candidate

The review-mode public proxy candidate is:

- scenario_version: cost_uk_v1
- building_type: retail
- spec_grade: mid
- region: UK
- base_rate_gbp_per_gia_m2: 4736.84
- base_rate_range_gbp_per_gia_m2: 4036.6-5209.9
- source_type: public_proxy
- source_reliability: 0.35
- confidence_band: LOW
- production_ready: false
- review_mode: true
- db_write: false
- production_deploy: false
- fake_data: false

## Public proxy sources used

- Selfridges Birmingham public project cost/floor-area proxy.
- Trafford Palazzo / Barton Square public project cost/floor-area proxy.
- St David's Cardiff public project cost/floor-area proxy.
- One New Change outlier reference only.

## Required label

Use this label for review-mode handoff:

COST12_READY_FOR_HUMAN_REVIEW_PUBLIC_PROXY

Do not use FINAL_READY_CONFIRMED until a strong source replaces the public proxy row.

## Safety confirmation

- db_write=false
- production_deploy=false
- fake_data=false
- no_migration=true
- no_production_release=true

## Final state

Review-mode: 100% complete.
Production-ready: 99%, blocked by verified source requirement.
