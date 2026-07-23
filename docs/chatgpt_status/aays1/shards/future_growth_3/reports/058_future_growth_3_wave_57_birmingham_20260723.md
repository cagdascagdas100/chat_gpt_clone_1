# future_growth_3 — Wave 57 Birmingham

- Verified: 2026-07-23T14:58:32Z
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Authority: Birmingham City Council
- Official family: MHCLG Planning Data brownfield-land
- Researched: 30
- Direct live PASS: 20
- Direct live FAIL/cache miss: 10
- Eligible source candidates: 20
- Excluded controls: 10
- High confidence (>=98): 20
- Average eligible confidence: 98.85/100
- Eligible exact POINT coverage: 20/20
- Complete capacity evidence: 20/20
- Visible candidate rows: 30
- Visible operation rows: 230
- Source families added: 0; cumulative 112
- Authority coverage increment: 0 (not asserted without full cross-wave authority registry re-derivation)

## QA findings

Ten direct-live cache misses were excluded and no search-cache value was promoted. Three permissioned live records (`2624`, `2489`, `2543`) expose no planning-permission date on the live entity page; the date remains null and confidence is reduced to 98 rather than inferred. All other eligible rows have an official live POINT and complete minimum/maximum capacity evidence.

## Guardrails

No source POINT was treated as a canonical parcel polygon. Canonical parcel ID and future-growth score remain null. No business/product row, database write, migration, or production deployment was performed.

## Canonical blocker

The exact 30,761-row canonical export for rows 61,523–92,283, stable parcel identifier, row-count/range receipt, and CRS manifest remain unavailable. The prior bounded search count remains 199; the same unsuccessful repository search was not repeated. Canonical geometry intersection and the 30,761-row evidence matrix therefore remain blocked while parallel-safe official-source research continues.

- `fake_data=false`
- `final_ready=false`
