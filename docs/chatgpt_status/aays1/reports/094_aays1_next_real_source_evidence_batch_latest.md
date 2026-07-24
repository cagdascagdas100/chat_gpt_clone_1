# 094 aays1 next real source evidence batch

status: source_candidates_fetched_manual_review_required
task_id: aays1-next-real-source-evidence-batch-20260708
candidate_rows: 10
verified_rows_added: 0
completion_percent: 35
remaining_percent: 65
blocker: candidate_rows_require_review_before_verified_merge
source_system: Police.uk Data API / data.police.uk
final_ready: false
fake_data: false
db_write: false
migration: false
production_deploy: false

Notes:
- This task never fabricates security evidence.
- Candidate rows are not merged into verified outputs until review/acceptance criteria are satisfied.
- If no non-verified candidate source rows exist, the blocker is explicit and metrics remain unchanged.
