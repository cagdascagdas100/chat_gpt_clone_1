# future_growth_3 — waves 454–461

- continuation_key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- source: MHCLG Planning Data brownfield entities; official-web research only
- scope: Kent authorities not promoted in the immediately preceding wave, plus strict negative/temporal controls
- researched rows: 40
- direct candidates attempted: 37
- direct live calls: 47 = 27 PASS / 20 FAIL
- safe retries: 10
- unique direct PASS / FAIL: 27 / 10
- eligible: 14
- excluded: 26
- visible operation rows: 280
- strict eligible confidence: 98.86/100
- search-only promotions: 0
- newly eligible authority channels: Tunbridge Wells; Dartford; Canterbury

## Accuracy gates

Three superficially usable rows were deliberately rejected after direct readback:
- Tunbridge Wells `BFR_0012`: structured min/max says 8 while the official notes describe 9 apartments.
- Dartford `4`: official notes say “Permissioned 21/00413/FUL” while the structured permission status is `not-permissioned`.
- Thanet `/050158`: 2005 permission with no current progress evidence; retained as a temporal control rather than promoted.

Historic end dates, under-construction evidence, large/partly implemented masterplans, direct misses after exactly one retry, and discovery-only search results were fail-closed.

## Progress

Cumulative source research becomes 3,986 researched / 2,105 eligible / 1,881 excluded. High-confidence eligible rows become 2,017. Three authority/source channels were upgraded in this wave. Main pipeline remains 7/12 complete plus 1 partial (58.33%) because the canonical 61,523–92,283 parcel shard export is still not available.

Two new exact repository searches returned no canonical shard/export candidate. This remains data-not-found, not a user manual action. Source research continues under `NO_DATA_CONTINUE`; no candidate is assigned to a canonical parcel and no future-growth product score is produced.

`final_ready=false`; fake_data=false; db_write=false; migration=false; production_deploy=false.
