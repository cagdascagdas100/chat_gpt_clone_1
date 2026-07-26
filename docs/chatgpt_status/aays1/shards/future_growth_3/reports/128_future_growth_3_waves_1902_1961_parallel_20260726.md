# future_growth_3 — waves 1902–1961 official direct-readback research

- Slot: `future_growth_3`
- Continuation: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Source: MHCLG Planning Data — Brownfield land
- Researched: **60**
- Strict eligible: **37**
- Fail-closed: **23**
- Average eligible source confidence: **98.88/100**
- Candidate delta: **+37 / +1.44%**
- Promoted duplicate checks: **37/37 clean**
- Search-only promotions: **0**
- New source families: **+8**
- Canonical export recovery: **+3 queries; 263 cumulative / 0 matches**

## Exact gates
Promotion required a current/blank `end-date`, positive structured `minimum-net-dwellings` and `maximum-net-dwellings`, official POINT, exact authoritative Planning Data entity readback, and no repo duplicate.

Direct tracked promotion/retry pool: 44 unique entities, 51 calls, 37 PASS, 7 unique FAIL after one safe retry, 0 third retries. Remaining 16 rows were fail-closed at discovery because temporal or structured-capacity incomplete.

A brief Planning Data service incident recovered during research. No promotion was made while the source service was unavailable.

## Cumulative
- Researched: **5,530**
- Eligible: **2,615**
- Excluded: **2,915**
- High confidence: **2,527**
- Average eligible confidence: **98.31/100**
- Source families: **208**
- Eligible official-source location: **2,615 / 2,615 = 100%**
- Canonical rows matched: **0**
- Product/business rows: **0 / 30,761**
- Main operations: **7/12 complete + 1 partial = 58.33%**

## Safety
No canonical parcel assignment, future-growth score, DB write, migration, deployment, or synthetic product row was created. Official POINT is not a canonical parcel polygon. Canonical export absence remains `NO_DATA_CONTINUE`.
