# future_growth_3 — Wave 47

- Date: 2026-07-22
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Authorities: Nottingham City Council, Newcastle City Council, Leicester City Council
- Researched: 47
- Direct live readback: 17 PASS / 30 cache-miss
- Eligible: 16
- Excluded: 31 (30 cache-miss, 1 live-page capacity absent)
- High confidence (>=95): 8
- Mean confidence: 94.44/100
- Exact official POINT and capacity evidence: 16/16
- Historical controls: 5
- Visible operation rows: 221
- New source families promoted: 0

## QA findings

Live entity pages controlled all promoted values. Missing fields remained null. Structured-versus-notes capacity conflicts, an inverted min/max capacity pair, historical end dates, old permissions, student-bedspace semantics and permission field/status conflicts were retained as explicit flags. Cache-miss search fragments were not promoted.

## Canonical blocker

Two new exact repository searches returned no canonical rows 61523–92283 export, stable parcel ID, 30,761-row receipt or CRS manifest. Canonical parcel assignment and future-growth scores remain null. Manual action remains OPEN.

## Evidence

- `england_map_web/data/aays_21_slots/future_growth_3/candidates_wave_47_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/rows_wave_47_nottingham_newcastle_leicester_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/source_url_readback_wave_47_20260722.json`
- `england_map_web/data/aays_21_slots/future_growth_3/operations_wave_47_20260722.html`
- `england_map_web/data/aays_21_slots/future_growth_3/wave_47_20260722.html`

`final_ready=false`, `fake_data=false`, no DB write, migration or production deployment.