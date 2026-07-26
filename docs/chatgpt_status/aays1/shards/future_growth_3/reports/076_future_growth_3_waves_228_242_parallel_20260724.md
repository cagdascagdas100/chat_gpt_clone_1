# future_growth_3 — waves 228–242 parallel research

Date: 2026-07-24
Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`

## Result
- 15 authority groups researched.
- 75 real Planning Data entity rows retained for audit.
- 13 eligible, 62 excluded.
- 13/13 eligible rows are >=98 confidence; average 98.77.
- 38 direct-live calls: 17 PASS / 21 FAIL; 9 safe retries.
- 28 unique direct candidates: 16 PASS / 12 FAIL.
- 47 pre-gate exclusions; 3 direct-PASS rows excluded by the structured-minimum quality gate.
- Search snapshot promotions: 0.
- Visible web rows: 75 candidate rows + 525 operation rows.
- Source families added/upgraded: 0; cumulative official source families remain 112.

## Eligible direct-live rows
| Authority | Reference | Entity | Structured dwellings | Confidence |
|---|---|---:|---:|---:|
| Salford City Council | H/QYS/009 | 1736353 | 275 | 99 |
| Salford City Council | H/KBP/016 | 1736296 | 20 | 99 |
| Salford City Council | H/KBP/038 | 1737456 | min 4 | 99 |
| Oldham Metropolitan Borough Council | HLA4010 | 1736144 | 6 | 99 |
| Oldham Metropolitan Borough Council | HLA3761 | 1720707 | 13 | 99 |
| Cheshire East Council | 6434 | 1706168 | 100 | 99 |
| Cheshire East Council | LPS 14 | 1706178 | 80 | 98 |
| Cheshire West and Chester Council | NET/0023 | 1734542 | min 9 | 99 |
| Cheshire West and Chester Council | CHG/0346 | 1734486 | 10 | 99 |
| Cheshire West and Chester Council | WOV/0069 | 1734649 | 26 | 98 |
| Cheshire West and Chester Council | NES/0035 | 1734538 | 5–10 | 99 |
| Halton Borough Council | H1719 | 1735851 | 18–26 | 98 |
| Knowsley Metropolitan Borough Council | BR091 | 1741678 | 53 | 99 |

## Strict exclusions
- Historical end date: 20.
- Notes-only capacity: 11.
- Missing structured minimum: 10.
- Direct cache miss after one safe retry: 9.
- Missing exact POINT: 4.
- Direct PASS but missing structured minimum: 3.
- Direct cache miss/no promotion: 2.
- Search-only not promoted: 2.
- Semantic conflict/expired: 1.

`NO_DATA_CONTINUE` authority groups: Manchester, Trafford, Stockport, Tameside, Rochdale, Bury, Bolton, Wigan, Warrington.

## Canonical guard
The 61,523–92,283 canonical shard export, stable parcel IDs, row-count receipt and CRS manifest are still absent. POINT is not a canonical parcel polygon. No parcel crosswalk, future-growth score, business-data row, DB write, migration or production deployment was produced.

Canonical export audit remains the already-completed 199-query audit with zero indexed matches; it was not repeated in this wave.

`final_ready=false`.
