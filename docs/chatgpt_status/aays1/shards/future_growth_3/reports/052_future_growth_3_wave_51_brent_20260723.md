# future_growth_3 — Wave 51 Brent official-source report

- Generated: 2026-07-23T04:54:00+03:00
- Authority: London Borough of Brent
- Official platform: MHCLG Planning Data
- Verification rule: direct live entity page required for eligibility
- Researched: 35
- Eligible: 19
- Excluded: 16 direct-live failures
- High source confidence: 12
- Average eligible source confidence: 97.16/100
- Visible candidate rows: 35
- Visible operation rows: 194
- Exact official POINT and structured capacity: 19/19 eligible rows
- Source families added: 0; cumulative remains 112

## Quality findings

Direct live values were treated as source of truth. Search-cache values were not promoted when they differed from live pages or when the live page failed. BR00183 and BR00064 show material cache/live drift. BR00050 retains a very old permission date with pending-S106 semantics. BR00189, BR00190 and BR00053 retain phase/capacity caveats from the source notes. Sixteen failed direct reads remain excluded with no inferred POINT, capacity, canonical parcel ID or score.

## Canonical blocker

Two additional exact repository searches found no 30,761-row canonical export for rows 61,523–92,283, stable parcel identifier, row-count/range receipt or CRS manifest. Cumulative canonical search count is 189 with zero indexed matches. Manual action remains OPEN. Candidate-to-parcel crosswalk and scoring were not started.

## Evidence

- `england_map_web/data/aays_21_slots/future_growth_3/candidates_wave_51_20260723.json`
- `england_map_web/data/aays_21_slots/future_growth_3/rows_wave_51_brent_20260723.json`
- `england_map_web/data/aays_21_slots/future_growth_3/quality_wave_51_20260723.json`
- `england_map_web/data/aays_21_slots/future_growth_3/source_family_audit_wave_51_20260723.json`
- `england_map_web/data/aays_21_slots/future_growth_3/source_semantics_review_wave_51_20260723.json`
- `england_map_web/data/aays_21_slots/future_growth_3/source_url_readback_wave_51_20260723.json`
- `england_map_web/data/aays_21_slots/future_growth_3/readback_fallback_audit_wave_51_20260723.json`
- `england_map_web/data/aays_21_slots/future_growth_3/wave_51_20260723.html`
- `england_map_web/data/aays_21_slots/future_growth_3/operations_wave_51_20260723.html`

`canonical_parcel_id=null`, `future_growth_score=null`, `actual_business_data_rows_written=0`, `fake_data=false`, `final_ready=false`.
