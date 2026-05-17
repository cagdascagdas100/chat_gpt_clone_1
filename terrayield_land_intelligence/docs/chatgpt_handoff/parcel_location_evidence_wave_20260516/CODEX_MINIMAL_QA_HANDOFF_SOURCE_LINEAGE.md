# Codex Minimal QA Handoff - Source Lineage Guard

## Purpose

This handoff is for a minimal Codex QA pass only. The main implementation, targeted tests, dual local worktree sync, and runtime API smoke have already completed through ChatGPT + local runner automation.

## Final implementation status

- Final source lineage patch commit: `b8bfc8bc7e4c`
- Final review summary commit: `49d4079c107c529f7047b7981aa985e3b6fefdba`
- Runtime/API smoke task commit: `95d1119c6fe42cf9267d350636c3e2759ec01429`

## Files changed / validated

- `terrayield_land_intelligence/app/etl/match/parcel_matcher.py`
- `terrayield_land_intelligence/tests/test_parcel_matcher_source_confidence.py`

## Behavior added

`_build_match_source_confidence_fields(...)` now exposes explicit source-lineage metadata:

- `source_lineage_status`
- `source_lineage_fields_present`
- `source_lineage_missing_reason`

Expected behavior:

- If `source_url` exists: `source_lineage_status=verified_source_url`
- If partial lineage exists but `source_url` is missing: `source_lineage_status=partial_lineage_no_source_url`
- If no lineage exists: `source_lineage_status=missing_source_lineage`
- Records without `source_url` must not become high confidence.
- `missing_source_url_high_confidence_withheld` is emitted as the explicit reason where appropriate.

## Test evidence

### 007 source-lineage runner

Report:

- `docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_REPORT.txt`

Result:

- `final_classification=COPY_SNAPSHOT_PATCH_BOTH_REPOS_READY`
- `import_exit_code=0`
- `diff_check_exit_code=0`
- `pytest_exit_code=0`
- `commit_status=committed`
- `commit_hash=b8bfc8bc7e4c`
- `push_status=pushed`

Targeted pytest:

- `15 passed in 1.66s`

Blockers:

- `docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/007_COPY_SNAPSHOT_PATCH_BOTH_REPOS_BLOCKERS.md`
- Result: `none`

### 009 runtime/API smoke

Report:

- `docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/009_RUNTIME_API_SMOKE_REPORT.txt`

Result:

- `final_classification=RUNTIME_API_SMOKE_READY`
- `pytest_exit_code=0`
- `api_smoke_ok_count=5`
- `api_smoke_total=5`
- `next_single_action=done`

API smoke endpoints:

- `/ops/storage-registry` -> 200 OK
- `/ops/consistency-check` -> 200 OK
- `/handoff/status` -> 200 OK
- `/map/listings?limit=1` -> 200 OK
- `/map/sales-history/combined?limit=1` -> 200 OK

Blockers:

- `docs/chatgpt_handoff/parcel_location_evidence_wave_20260516/009_RUNTIME_API_SMOKE_BLOCKERS.md`
- Result: `none`

## Safety assertions

All automation reports preserve the following safety constraints:

- `db_write=none`
- `ddl=none`
- `migration_apply=none`
- `prod_deploy=none`
- `secret_values_printed=false`

## Codex minimal QA request

Please perform only a lightweight verification pass:

1. Confirm the final branch is `security-accuracy-expansion-20260508`.
2. Confirm `parcel_matcher.py` contains `source_lineage_status`, `source_lineage_fields_present`, and `source_lineage_missing_reason`.
3. Confirm test `test_parcel_matcher_reports_partial_lineage_without_source_url` exists.
4. Confirm 007 and 009 reports both show no blockers.
5. Do not change code unless a concrete regression is found.
6. Do not print secrets.
7. Do not run migrations or production deployment.

## Final classification

`READY_FOR_MINIMAL_CODEX_QA_OR_USER_ACCEPTANCE`
