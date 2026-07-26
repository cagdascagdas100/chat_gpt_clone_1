# future_growth_3 — waves 272–275 — 24 Jul 2026

Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`.

## Result

- 4 authority groups, 35 official-source candidates.
- 53 direct-live calls including 18 one-time safe retries.
- 17 unique direct-live PASS; 18 unique direct-live FAIL after retry.
- 14 eligible at strict confidence >=98; 21 excluded.
- Average eligible confidence: 98.57/100.
- Search-only promotion: 0.
- Visible web evidence: 35 candidate rows and 245 operation rows.
- Eligible exact POINT + positive structured dwelling capacity: 14/14.

## Eligible examples

South Tyneside: SOS007 163; SHB004 110; SIS007 35; SIS062 20; SBC114 10; SHB112 6; SOS069 6.
North Tyneside: 284 31; 38 19; 326 6; 79 5.
Gateshead: HLC15 257–283; HLU17 7–11.
Sunderland: B467B 10–11.

## Fail-closed exclusions

18 candidates failed direct-live readback after one safe retry and were not promoted. Three direct-live PASS records were also excluded: HLS7 because its end date is 2019-12-30; Sunderland 054 because the source notes a lapsed permission; and Sunderland 729 because its end date is 2020-11-30.

## Canonical blocker

The canonical shard export for rows 61,523–92,283 is still absent. Stable parcel IDs, row-count receipt and CRS manifest are not available, so candidate-to-parcel intersection and future-growth scoring remain intentionally unstarted. This is `NO_DATA_CONTINUE`, not a user manual-action requirement.

`final_ready=false`; no fake data, database write, migration or production deployment.