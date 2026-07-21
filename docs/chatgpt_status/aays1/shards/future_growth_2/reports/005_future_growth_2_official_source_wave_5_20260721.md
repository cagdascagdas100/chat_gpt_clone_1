# future_growth_2 — Official source candidate wave 5

## Scope

- Slot: `future_growth_2`
- Parcel partition: `30762–61522` (`30,761` rows)
- Sources: official Planning Data brownfield entity pages and API documentation
- Product scores remain null; source confidence is not parcel-match confidence
- `final_ready=false`

## Completed

1. Re-read authoritative ownership, checkpoint, status, heartbeat and current-task.
2. Confirmed the slot remains unclaimed with no lease, heartbeat or task.
3. Researched nine additional official brownfield records.
4. Retained six current authoritative candidates.
5. Excluded two records with a `2024-10-15` end date.
6. Held Arena Retail Park because entity and CURIE views disagree on end-date/currentness.
7. Added a fail-closed Planning Data `period=current` entity validator.
8. Passed `8/8` manual remote evidence and invariant checks.
9. Published the fifth candidate wave and cumulative web progress.

## Eligible candidates

| Candidate | Site | Authority | Hectares | Capacity | Status | Source confidence |
|---|---|---|---:|---:|---|---:|
| FG2-W5-001 | Hale Wharf | Haringey | 6.32 | 505 | permissioned; stale outline review | 96 |
| FG2-W5-002 | Haringey Heartlands | Haringey | 4.59 | 1,080 | permissioned; stale outline review | 94 |
| FG2-W5-003 | Coppetts Wood Hospital | Haringey | 0.71 | 80 | permissioned; stale review | 96 |
| FG2-W5-004 | Bus Depot Hackney Central | Hackney | 0.80 | 142 | not permissioned; review | 98 |
| FG2-W5-005 | 316 High Road | Haringey | 0.03 | 6 | permissioned; stale review | 96 |
| FG2-W5-006 | 27–37 Well Street | Hackney | 0.43 | 44 | not permissioned; review | 98 |

## Excluded or held

- `NSP78`: ended `2024-10-15`.
- `15-AP-3508`: ended `2024-10-15`.
- `17140075` Arena Retail Park: entity view shows no end date while CURIE view shows `2022-05-13`; held fail-closed.

## Current cumulative preparation

- Researched candidates: **35**
- Eligible candidates: **30**
- Excluded or held: **5**
- Eligible candidates with source confidence ≥90: **30**
- Average eligible source confidence: **97.7/100**
- Canonical parcel matches: **0**
- Verified product rows: **0/30,761**
- Future Growth scores: **0**

## Remaining blocker

`REAL_CANONICAL_SHARD_EXTRACTION_REQUIRES_EXISTING_RUNTIME_ACCESS_TO_61MB_SECURITY_GEOJSON; LIVE_PERIOD_CURRENT_API_VALIDATION_NOT_EXECUTED; LIVE_HMLR_GML_AND_PLANNING_GEOJSON_EXACT_CROSSWALK_NOT_EXECUTED; VERIFIED_30761_ROW_MATRIX_NOT_EXECUTED; APPROVED_FUTURE_GROWTH_SCORE_DECISION_CONTRACT_NOT_PRESENT`
