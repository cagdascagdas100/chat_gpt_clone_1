# future_growth_3 — waves 281–283 official-source research

- Date: 2026-07-24
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Scope: Middlesbrough, Redcar and Cleveland, North Yorkshire negative controls.
- Strict promotion threshold: >=98.
- Official source: MHCLG Planning Data (`https://www.planning.data.gov.uk/entity/<entity>`).
- Search-only promotion: 0.
- Canonical parcel assignment: 0; canonical shard export remains unavailable.

## Batch result

31 unique candidates were researched. 12 passed all gates; 19 were excluded. There were 40 direct-live calls: 30 PASS and 10 FAIL, including 5 single safe retries. Unique direct-live result: 26 PASS / 5 FAIL. Fourteen direct-PASS records were excluded by historical-date, structured-capacity, semantic, or source-quality gates.

Average confidence across promoted rows: 98.83/100.

## High-value promoted examples

- Middlesbrough BR47 (entity 1707566): 196–235 dwellings, confidence 98.
- Middlesbrough BR36 (1707545): 91–109, confidence 99.
- Redcar and Cleveland 503 (1733831): 63–79, confidence 99.
- Middlesbrough BR12 (1707539): 40, confidence 99.
- Middlesbrough BR55 (1707551): 26, confidence 99.
- Redcar and Cleveland 337 (1733832): 25, confidence 99.
- Redcar and Cleveland 394 (1712650): 23, confidence 99.
- Redcar and Cleveland 405 (1712628): 10, confidence 99.
- Middlesbrough BR38 (1707546): 8, confidence 98.
- Redcar and Cleveland 562 (1733829): 6, confidence 99.
- Redcar and Cleveland 532 (1712642): 5, confidence 99.
- Redcar and Cleveland 547 (1712649): 5, confidence 99.

## Negative controls and exclusions

North Yorkshire records marked `quality=some` were retained as negative controls and were not promoted under the strict authoritative >=98 gate. Historical end dates, non-PDL/student-accommodation semantics, missing positive structured minimum, and direct cache misses after one safe retry were fail-closed.

## Cumulative state

- Researched: 2,644
- Eligible: 1,592
- Excluded: 1,052
- High source confidence: 1,504
- Average eligible source confidence: 98.18/100
- Verified official source families: 112
- Eligible source geometry: 1,592 / 1,592
- Canonical rows matched: 0 / 30,761
- Main pipeline: 7 completed + 1 partial / 12 = 58.33%

Blocker remains `CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY`. Missing export is not a user-action blocker; public official-source research can continue under the same continuation key. `final_ready=false`.
