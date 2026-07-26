# future_growth_3 — Parallel Waves 61–65

- Verified: 2026-07-23T15:39:09Z
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Authorities: Coventry, Nottingham, Bristol, Leicester, Liverpool
- Official platform: MHCLG Planning Data brownfield-land
- Researched: 64
- Eligible source candidates: 46
- Excluded controls: 18
- High confidence: 35
- Average eligible confidence: 98.07/100
- Official page/dataset-table readback: 62 PASS / 2 cache-miss FAIL
- Eligible exact POINT coverage: 46/46
- Capacity evidence: 40 complete structured + 1 partial structured + 5 official-notes
- Visible candidate rows: 64
- Visible operation rows: 448

## QA findings

Eleven Bristol rows with explicit historical end dates were excluded. Five Liverpool rows were retained only as excluded controls because POINT and capacity were absent and the authority brownfield endpoint currently reports a 404. Nottingham 2476 and 2468 were not promoted because direct entity open returned cache-miss and POINT could not be reverified in this wave. Coventry BLR25 and BLR44 preserve structured-versus-notes capacity differences without silently choosing one value.

## Product guardrails

No official POINT was treated as a canonical parcel polygon. Canonical parcel ID and future-growth score remain null. No business/product row, database write, migration, or production deployment was performed.

## Canonical blocker

The exact 30,761-row canonical export for rows 61,523–92,283, stable parcel identifier, row-count/range receipt and CRS manifest remain unavailable in the remote repository. Candidate-to-parcel geometry crosswalk and 30,761-row evidence matrix remain blocked.
