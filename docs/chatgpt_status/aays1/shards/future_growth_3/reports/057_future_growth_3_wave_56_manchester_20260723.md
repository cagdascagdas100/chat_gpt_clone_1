# future_growth_3 — Wave 56 Manchester

- Verified: 2026-07-23T06:52:00+03:00
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Authority: Manchester City Council
- Official family: MHCLG Planning Data brownfield-land
- Researched: 30
- Direct live PASS: 21
- Direct live FAIL/cache miss: 9
- Eligible source candidates: 19
- Excluded controls: 11
- High confidence: 12
- Average eligible confidence: 97.68/100
- Eligible exact POINT coverage: 19/19
- Visible operation rows: 192
- Source families added: 0; cumulative 112
- Authority coverage added: 1

## QA findings

Three current records preserve minimum values above maximum values exactly as shown by the live official page: `Mile1900`, `Anco_Cap_711`, and `Mile_Cap_701`. Seven records preserve search/live capacity drift without silently choosing the search-cache value. Nine cache-miss records were excluded without promotion. Two direct-live records with official end date `2024-01-12` were retained only as historical controls.

## Guardrails

No source POINT was treated as a canonical parcel polygon. Canonical parcel ID and future-growth score remain null. No business/product row, database write, migration, or production deployment was performed.

## Canonical blocker

Two additional exact repository searches expanded the cumulative canonical search count to 199 with zero indexed matches. The exact 30,761-row canonical export for rows 61,523–92,283, stable parcel identifier, row-count/range receipt, and CRS manifest remain unavailable. Manual action stays OPEN.
