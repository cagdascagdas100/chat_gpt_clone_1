# future_growth_3 — waves 510–525

- continuation_key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- source: MHCLG Planning Data brownfield entities; official-web research only
- authorities researched: London Borough of Bexley; London Borough of Lewisham; North Warwickshire Borough Council; London Borough of Hounslow; Erewash Borough Council
- researched rows: 20
- eligible: 6
- excluded: 14
- eligible confidence: 99.00/100
- direct entity pages/candidates: 14 unique; 16 calls = 12 PASS / 4 FAIL; 2 safe retries
- fail-after-retry exclusions: 2
- direct-pass quality exclusions: 6
- official-search quality controls: 6
- search-only promotions: 0
- visible operation rows: 140

## Accuracy gates

Six rows passed the strict direct gate: Bexley `BLR055`; Lewisham `FH015`, `TH015`; North Warwickshire `BFR005`, `BFR008`, `BFR027`.

Lewisham `GP015` and `RG023` remained unavailable on the direct entity surface after exactly one safe retry and were not promoted. Bexley `BLR226` and `BLR257` were excluded for lapsed permissions. North Warwickshire `BFR029` and `BFR037`, Hounslow `HOBR262` and `HOBR236`, and official-search controls `BFR010`, `RG012`, `LC015`, `BLR47`, `BLR1`, `BK001` were fail-closed for temporal, structured-capacity, phase/masterplan, started-development, or multi-phase uncertainty. POINT evidence is not treated as canonical parcel geometry.

## Progress

Cumulative source research becomes 4,090 researched / 2,144 eligible / 1,946 excluded. High-confidence eligible rows become 2,056. Three authority/source channels are added to the verified current research set, bringing the cumulative source/authority upgrade count to 122. Main pipeline remains 7/12 complete plus 1 partial (58.33%) because the canonical 61,523–92,283 parcel shard export is still unavailable.

Two new exact repository searches returned no canonical shard/export candidate. Bounded audit becomes 209 queries / 0 matches. This remains data-not-found, not a user manual action. Source research continues under `NO_DATA_CONTINUE`; no candidate is assigned to a canonical parcel and no future-growth product score is produced.

`final_ready=false`; fake_data=false; db_write=false; migration=false; production_deploy=false.