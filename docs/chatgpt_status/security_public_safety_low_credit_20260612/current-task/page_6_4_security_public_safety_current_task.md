# Page 6.4 Current Task

repo: cagdascagdas100/chat_gpt_clone_1
branch: main
page_key: security_public_safety_low_credit_20260612
status: QUEUED_FOR_SINGLE_SHARED_RUNNER
FINAL_READY: false
final: false
completion_percent: 35
created_at: 2026-06-17T13:06:00+03:00
runner_mode: SINGLE_SHARED_RUNNER_ONLY
separate_runner_allowed: false
powershell_required_from_user: false

## Task

Complete the Safety / Security layer as a parcel polygon thematic layer with real contract output.

## Automation script path

`docs/chatgpt_status/security_public_safety_low_credit_20260612/automation/security_public_safety_page6_4_single_runner_task.ps1`

The shared runner should pick this task and run the page-local automation script from the existing runner flow. Do not open a second runner.

## Locked scope

- Preferred worktree: `F:\chatgpt\AAYS_WORK\security_public_safety_20260617_clean`
- Fallback worktree: `D:\chatgpt\AAYS_WORK\security_public_safety_20260617_clean`
- Heavy data root: `D:\topografik_map\security_module\data_processed`

## Constraints

- No fake data.
- No database write.
- No schema or migration work.
- No production deploy.
- Do not push large GeoJSON files.
- Do not stage whole directories.
- Keep the layer as aggregate public-safety signal, not exact incident truth.

## Work order

1. Use the clean D/F worktree.
2. Find the parcel polygon carrier: `parcel-use-parcels`, `fallback-parcels`, `/map/parcels`, PMTiles/vector tile parcel source, or `parcels_inspire`.
3. Find the best real security lookup from D heavy data first, then repo local data.
4. Join security props to parcel polygons by `parcel_id` where possible.
5. If polygon export is too large, use lookup + existing polygon carrier instead of committing large data.
6. Complete popup or right-panel output for the required contract fields.
7. Run smoke checks and write page-key-local reports.

## Required output fields

`parcel_id`, `security_score`, `security_level`, `security_level_label`, `security_color_category`, `security_color_hex`, `source_name`, `source_url`, `source_date`, `evidence`, `matching_method`, `calculation_explanation`, `confidence_score`, `accuracy_rating`, plus optional police/density fields when present.

Legacy aliases may be normalized only when present in real data.

## Acceptance criteria

FINAL_READY may become true only when the Security UI renders parcel polygons in five levels and a parcel click shows the required contract fields with real source/evidence and runtime or browser proof.

## Required reports

- `docs/chatgpt_status/security_public_safety_low_credit_20260612/reports/security_df_worktree_apply_report_YYYYMMDD_HHMM.md`
- `docs/chatgpt_status/security_public_safety_low_credit_20260612/reports/security_df_worktree_smoke_report_YYYYMMDD_HHMM.md`
- `docs/chatgpt_status/security_public_safety_low_credit_20260612/reports/security_df_worktree_blockers_YYYYMMDD_HHMM.md`
- `docs/chatgpt_status/security_public_safety_low_credit_20260612/status/page_6_4_security_status_YYYYMMDD_HHMM.md`
- `docs/chatgpt_status/security_public_safety_low_credit_20260612/heartbeat/page_6_4_security_heartbeat_YYYYMMDD_HHMM.md`

## Current percent basis

35 percent: GitHub intake, runner format inference, and automation script publication are complete. It cannot be 100 until runner output proves polygon rendering and contract output.
