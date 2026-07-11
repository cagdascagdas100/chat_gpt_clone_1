# AAYS1 Parcel Label / Distance Property Types — Large Batch 164 Queued

## Scope

One larger batch of eight real-internet-source candidates was added behind Tasks 162 and 163 for processing by the existing F portable canonical shared runner only.

## Candidates

1. Meadowhall Shopping Centre — Retail Property — provisional accuracy 3.75/4
2. Television Centre White City — Mixed Building — provisional accuracy 3.85/4
3. Chatsworth House — Detached Home — provisional accuracy 3.80/4
4. Castle Howard — Detached Home — provisional accuracy 3.65/4
5. Principal Tower — Apartment Building — provisional accuracy 3.65/4
6. One Crown Place — Mixed Building — provisional accuracy 3.85/4
7. 20 Fenchurch Street — Office Building — provisional accuracy 3.55/4
8. SEGRO Logistics Park East Midlands Gateway — Industrial Unit candidate — provisional accuracy 3.35/4, manual review required until a specific unit/parcel is bound

Provisional batch average: 3.68/4.

## Processing contract

- No new or parallel runner.
- Remote-validate each source URL.
- Refine or reject approximate geometry.
- Do not mark any row completed without runner output and browser proof.
- Publish each row individually to the matrix as pending or completed with evidence paths.
- Keep `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, and `final_ready=false`.

## Counts

- Candidate rows added to queue in this batch: 8
- Tracked-row target after queue: 110
- Program-layer target if Tasks 163 and 164 are all accepted: 26
- Current completed-visible matrix count before runner acceptance: 6

## Required proof

- `docs/chatgpt_status/aays1/runner_outputs/164_aays1_distance_property_types_real_source_large_batch_20260711_output.json`
- `docs/chatgpt_status/aays1/status/164_aays1_distance_property_types_real_source_large_batch_20260711_completed.json`
- `docs/chatgpt_status/aays1/reports/164_aays1_distance_property_types_real_source_large_batch_completion_report_20260711.md`
- Browser proof JSON

Final: false
