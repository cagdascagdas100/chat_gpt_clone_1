# future_growth_3 — waves 366–377

- continuation_key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- scope: official public-source research only; no canonical parcel assignment
- candidate rows: **100**
- eligible: **50**
- excluded: **50**
- visible operation rows: **700**
- latest eligible confidence: **98.58/100**
- direct candidates: **77**
- valid direct calls: **92 = 62 PASS / 30 FAIL**
- one-safe-retry calls: **15**
- discovery-only negative controls: **23**
- direct PASS but quality-excluded: **12**
- search-only promotions: **0**

## Authorities
Watford, Oxford, North Hertfordshire, Buckinghamshire, Milton Keynes, Welwyn Hatfield, St Albans, Dacorum, Central Bedfordshire, Stevenage and Bedford were researched. Seven authorities produced strict ≥98 eligible candidates.

## Top eligible candidates
1. Oxford `076` — 450
2. Dacorum `BLR/009` — 350
3. Watford `B059` — 330
4. Dacorum `BLR/035` — 250–300
5. Oxford `014` — 225
6. Watford `B076` — 220
7. Oxford `018` — 160
8. Watford `B072` — 120
9. Watford `B053` — 110
10. Dacorum `BLR/017` — 100

## Quality gates
Promotion required an authoritative Planning Data entity readback, current/blank end-date, exact source POINT, positive structured `minimum-net-dwellings`, semantic consistency and confidence ≥98. Direct cache misses received exactly one safe retry and then failed closed. Historical/end-dated, missing structured minimum, geography anomalies and semantic/source anomalies were excluded.

Milton Keynes records with capacities appearing only in notes or maximum fields were not promoted. North Hertfordshire `BR31` was excluded because its direct source POINT materially conflicted with authority geography. Dacorum `BLR/022` was retained only as a negative control because structured minimum exceeded maximum.

## Cumulative after this batch
- researched: **3,264**
- eligible: **1,872**
- excluded: **1,392**
- high-source-confidence: **1,784**
- eligible source locations: **1,872 / 1,872**
- canonical rows matched: **0 / 30,761**
- future-growth scores: **0**
- operational progress: **58.33% (7 complete + 1 partial / 12)**

## Blocker
`CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY` remains. This is `NO_DATA_CONTINUE`, not a user-action blocker. No canonical parcel crosswalk or score is claimed.
