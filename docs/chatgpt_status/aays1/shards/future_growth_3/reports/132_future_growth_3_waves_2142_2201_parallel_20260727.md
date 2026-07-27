# future_growth_3 — wave 2142–2201

- Generated: 2026-07-27T15:09:00+03:00
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Primary source: MHCLG Planning Data — Brownfield land
- Researched: **60**
- Strict eligible: **34**
- Fail-closed: **26**
- Average eligible source confidence: **99.00/100**
- Direct calls: **72** = 60 initial + 12 one-safe-retry
- Unique direct PASS: **48**
- Unique retry FAIL: **12**
- Temporal exclusions: **14**
- Search-only promotions: **0**
- Promoted repo duplicate checks: **34/34 clean**
- New official authority/source families: **6**

## Strict promotion gate

Promotion requires an exact authoritative Planning Data entity readback with blank/current `end-date`, positive structured `minimum-net-dwellings` and `maximum-net-dwellings`, an official POINT, and a clean repository duplicate check. A direct cache miss receives at most one safe retry. Search snippets are discovery-only and never promoted.

## Eligible authority groups

- Borough Council of King's Lynn and West Norfolk
- Ipswich Borough Council
- Great Yarmouth Borough Council
- North Norfolk District Council
- Fenland District Council
- West Suffolk Council

## High-signal examples

- King's Lynn ref 66 / entity 1738891: 76–76 dwellings, current exact POINT.
- King's Lynn ref 64 / entity 1704965: 62–70 dwellings, current exact POINT.
- Ipswich BLR/IP132 / entity 1702642: 73–73 dwellings, current exact POINT.
- Ipswich BLR/IP041 / entity 1726936: 58–58 dwellings, current exact POINT.
- Great Yarmouth BFR102 / entity 1737141: 50–50 dwellings, current exact POINT.
- North Norfolk BLR03 / entity 1705767: 20–23 dwellings, current exact POINT.

## Fail-closed controls

- 14 exact pages were temporal/end-dated.
- 12 exact pages remained unavailable after one safe retry.
- Third direct retry: **0**.

## Cumulative after this wave

- Researched: **5,770**
- Eligible: **2,721**
- Excluded: **3,049**
- High source confidence: **2,633**
- Average eligible confidence: **98.35/100**
- Official source/authority families: **225**
- Eligible official location coverage: **2,721 / 2,721 = 100%**
- Candidate delta: **+34 / +1.27%**
- Completed operations: **7/12**, plus 1 partial = **58.33% operational**

## Canonical export blocker

Bounded recovery audit added 3 searches, cumulative **275 queries / 0 indexed matches**. The canonical 61,523–92,283 shard export, stable parcel ID receipt, row-count receipt and CRS manifest remain absent. This is `NO_DATA_CONTINUE`, not a user action. Canonical parcel matches, future-growth scores and business/product rows remain **0**; POINT is not a canonical parcel polygon.
