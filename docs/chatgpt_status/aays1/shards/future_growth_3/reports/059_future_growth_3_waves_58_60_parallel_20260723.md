# future_growth_3 — Parallel waves 58–60

- Verified: 2026-07-23T15:16:30Z
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Authorities: Leeds City Council; Sheffield City Council; Newcastle City Council
- Official family: MHCLG Planning Data `brownfield-land`
- Researched: 29
- Direct live PASS: 17
- Direct live FAIL/cache miss: 12
- Eligible source candidates: 13
- Excluded controls: 16
- High confidence: 13
- Average eligible confidence: 98.31/100
- Eligible exact POINT coverage: 13/13
- Visible candidate rows: 29
- Visible operation rows: 203
- Source families added: 0; cumulative remains 112

## Parallel wave results

- Wave 58 Leeds: 12 researched; 6 eligible; 6 excluded; 7 live PASS / 5 cache-miss FAIL; eligible confidence 99.00/100.
- Wave 59 Sheffield: 8 researched; 3 eligible; 5 excluded; 5 live PASS / 3 cache-miss FAIL; eligible confidence 97.33/100.
- Wave 60 Newcastle: 9 researched; 4 eligible; 5 excluded; 5 live PASS / 4 cache-miss FAIL; eligible confidence 98.00/100.

## Strong examples

- Leeds `SHL00065`: 1,010–1,010 net dwellings, exact official POINT, current entity.
- Leeds `SHL02031`: 89–89 net dwellings, exact official POINT, full planning permission.
- Sheffield `S01467`: official notes state 272 houses; exact official POINT; not-permissioned.
- Newcastle `1674`: 289–353 net dwellings, exact official POINT, permissioned.
- Newcastle `4430`: 66–80 net dwellings, exact official POINT, not-permissioned.
- Newcastle `6132`: official notes preserve 973-bed renewal / 960-bed outline variants without collapsing them into a fabricated structured range.

## QA findings

Twelve direct-live cache misses were excluded without promoting search-cache values. Three records with explicit historical end dates were excluded. Newcastle `5658` passed live readback and point verification but had no positive residential capacity on the live page, so it was excluded rather than inferred. Notes-only capacity is preserved as notes-only and is not silently converted into structured minimum/maximum fields.

## Guardrails

No official source POINT was treated as a canonical parcel polygon. Canonical parcel ID and future-growth score remain null. No business/product row, database write, migration, or production deployment was performed.

## Canonical blocker

The exact 30,761-row canonical export for rows 61,523–92,283, stable parcel identifier, row-count/range receipt, and CRS manifest remain unavailable. Candidate-to-canonical parcel geometry crosswalk and verified 30,761-row future-growth evidence matrix therefore remain blocked. Manual action stays OPEN.
