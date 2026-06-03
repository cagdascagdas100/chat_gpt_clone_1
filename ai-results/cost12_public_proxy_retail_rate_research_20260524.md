# COST12 Public Proxy Retail Rate Research — 2026-05-24

Decision: COST12_READY_FOR_HUMAN_REVIEW_PUBLIC_PROXY

This is not FINAL_READY_CONFIRMED.

## Summary

ChatGPT completed open-web source research for the missing COST12 retail rate-card row.

The missing row is:

- scenario_version: cost_uk_v1
- building_type: retail
- spec_grade: mid
- region: UK
- unit: GBP per gross internal area square metre

No open primary BCIS/RICS/current official rate-card row was found that can be treated as production-ready.

## Public proxy candidate

A review-mode public proxy candidate was produced from public UK retail-related project cost and floor-area records.

Recommended review-mode row:

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
- db_write: false
- production_deploy: false
- fake_data: false

## Source candidates

1. Selfridges Birmingham public project page
   - public record: cost and floor area
   - derived proxy: 4036.6 GBP/m2
   - confidence: LOW

2. Trafford Palazzo / Barton Square public project page
   - public record: cost and floor area
   - derived proxy: 4736.84 GBP/m2
   - confidence: LOW

3. St David's Cardiff public project page
   - public record: cost and floor area
   - derived proxy: 5209.9 GBP/m2
   - confidence: LOW

4. One New Change public project page
   - outlier reference only
   - mixed office and retail prime London scheme
   - not included in median candidate

## Constraints

- Do not use this row as production verified data.
- Do not mark FINAL_READY_CONFIRMED from this source alone.
- Use only for human review / public proxy mode.
- Keep db_write=false.
- Keep production_deploy=false.
- Keep fake_data=false.

## Next safe step

Codex may stage this as a review-only candidate row, not as a production rate-card row.
If a BCIS/RICS/official/supplier quote source is later attached, replace the public proxy row and rerun preview validation.
