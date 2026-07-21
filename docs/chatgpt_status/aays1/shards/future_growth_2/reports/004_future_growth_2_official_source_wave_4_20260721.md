# future_growth_2 — Official source candidate wave 4

- Slot: `future_growth_2`
- Parcel partition: `30762–61522` (`30,761` rows)
- Scope: source candidates only; no canonical parcel assignment
- Source: MHCLG Planning Data Brownfield land
- Generated: `2026-07-21T07:10:00+03:00`
- `final_ready=false`

## Source freshness

The official dataset readback reported `37,666` brownfield entities from `354` providers. The collector last ran on `2026-07-20`; new data was last found on `2026-07-16`. The dataset states that its data originates from authoritative sources, while warning that national coverage may still be incomplete.

## Candidate work

Six current Tower Hamlets records were normalized:

1. Bishopsgate Goods Yard
2. Leven Road Gas Works
3. Hercules Wharf / Castle Wharf / Union Wharf
4. Millharbour South
5. Land adjacent railway viaduct, Mantus Road
6. 42–44 Thomas Road

Every record has an official entity ID, authoritative quality, a London point coordinate and a blank end date. All six remain source candidates only. Older permission dates and pending decisions are retained as explicit review flags rather than hidden.

## Audit

- Candidates researched: **6**
- Eligible source candidates: **6**
- Remote evidence/invariant checks: **8/8 PASS**
- Average source-evidence confidence: **97.7/100**
- Overlap with prior 20 entity IDs: **0**
- Canonical parcel matches: **0**
- Future Growth scores: **0**
- Actual business rows written: **0**

This audit is a manual remote official-evidence and JSON-invariant review. It is not represented as local software execution.

## Guardrails

Source confidence is not parcel-match confidence. No nearest-point promotion is allowed. Canonical parcel IDs and Future Growth scores remain null/0 until current HMLR polygon intersection, explicit INSPIRE-ID shard identity and an approved score-decision contract are all proven.

Safety flags remain false: `fake_data`, `db_write`, `migration`, `production_deploy`, `final_ready`.
