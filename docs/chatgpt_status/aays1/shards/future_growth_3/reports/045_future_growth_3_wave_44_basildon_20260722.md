# future_growth_3 — Wave 44 Basildon official source validation

- Date: 2026-07-22
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Authority: Basildon Borough Council
- Official platform: MHCLG Planning Data, brownfield-land

## Result

19 official discovery records were researched. Ten direct live entity pages opened and passed the eligibility gate. Nine entity pages returned retrieval cache misses; the official JSON-extension fallback could not be opened under the current web-runtime safe-URL restriction, so those rows were excluded rather than promoted from search snippets.

- Researched: 19
- Eligible: 10
- Excluded: 9
- High source confidence: 10
- Eligible average confidence: 97.50/100
- Direct live readback: 10 PASS / 9 FAIL-EXCLUDED
- Structured capacity: 10/10 eligible rows
- Visible candidate rows: 19
- Visible operation rows: 88
- Source families added: 0

## Quality decisions

- Live official entity pages control promoted fields.
- Search discovery snippets do not independently qualify a row.
- Passed expiry dates appearing only in notes were retained as review flags; no synthetic end date was created.
- POINT values remain official source locations only and were not promoted to canonical parcel polygons.
- Canonical parcel assignment, future-growth score and business product rows remain null/zero.

## Canonical blocker

Two new exact repository searches found no exact 30,761-row canonical export, stable parcel identifier, row-count/range receipt or CRS declaration. The cumulative canonical search count is 175 with zero indexed matches. Manual action remains OPEN.

## Evidence

- `england_map_web/data/aays_21_slots/future_growth_3/rows_wave_44_basildon_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/candidates_wave_44_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/quality_wave_44_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/source_family_audit_wave_44_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/source_semantics_review_wave_44_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/source_url_readback_wave_44_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/readback_fallback_audit_wave_44_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/wave_44_20260722.html`
- `england_map_web/data/aays_21_slots/future_growth_3/operations_wave_44_20260722.html`

`final_ready=false`, `fake_data=false`, no database write, migration or production deployment.