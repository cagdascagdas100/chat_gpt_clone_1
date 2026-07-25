# future_growth_3 — waves 494–509

- continuation_key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- source: MHCLG Planning Data brownfield entities; official-web research only
- authorities: Medway Council; Sevenoaks District Council
- researched rows: 20
- eligible: 8
- excluded: 12
- direct promotion candidates: 17
- direct live calls: 24 = 10 PASS / 14 FAIL
- safe retries: 7
- eligible confidence: 98.75/100
- search-only promotions: 0
- visible operation rows: 140

## Accuracy gates

Eight rows passed the strict current/direct gate: Medway `MC619`, `MC615`, `530`; Sevenoaks `BFR131`, `BFR162`, `BFR133`, `BFR120`, `BFR135`.

`BFR112` was rejected because the official current record says “Not Carried forward”. `BFR187` was rejected because the official record says “Under Construction”. `MC558`, `MC634` and `MC649` were retained only as out-of-date/temporal controls. Seven search-visible candidate pages failed direct retrieval after exactly one safe retry and were not promoted; Medway ref `663` was included in that fail-closed set after its final direct retry returned a cache miss.

## Progress

Cumulative source research becomes 4,070 researched / 2,138 eligible / 1,932 excluded. High-confidence eligible rows become 2,050. Two authority/source channels are added to the verified current research set. Main pipeline remains 7/12 complete plus 1 partial (58.33%) because the canonical 61,523–92,283 parcel shard export is still unavailable.

Two new exact repository searches returned no canonical shard/export candidate. Bounded audit becomes 207 queries / 0 matches. This remains data-not-found, not a user manual action. Source research continues under `NO_DATA_CONTINUE`; no candidate is assigned to a canonical parcel and no future-growth product score is produced.

`final_ready=false`; fake_data=false; db_write=false; migration=false; production_deploy=false.
