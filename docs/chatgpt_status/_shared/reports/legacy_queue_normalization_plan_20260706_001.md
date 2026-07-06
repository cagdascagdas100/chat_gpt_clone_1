# Legacy queue normalization plan 20260706-001

Generated: 2026-07-06T00:00:00Z
Repo: cagdascagdas100/chat_gpt_clone_1
Branch: main
Active page_key: topography
Target evidence source: docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json

## Scope

This is a plan-only evidence file. It does not execute old queues, does not mark completed, does not set final_ready=true, and does not start a new runner.

## Observed invalid queue contract examples

The shared runner status shows aays1 queue files skipped with `INVALID_QUEUE_CONTRACT`.

Observed examples:

```text
docs/chatgpt_status/aays1/queue/0000_115_security_batch_join_backoff_force_pickup.task.json
docs/chatgpt_status/aays1/queue/052_publish_2of4_geometry_review_to_f_site_20260629.json
docs/chatgpt_status/aays1/queue/065_progress_report.task.json
docs/chatgpt_status/aays1/queue/068_batch_001.task.json
docs/chatgpt_status/aays1/queue/078_parcel_column_format.task.txt
docs/chatgpt_status/aays1/queue/078_relative.task.json
docs/chatgpt_status/aays1/queue/086.txt
docs/chatgpt_status/aays1/queue/087_photo_ai_boundary_review.txt
```

## Contract errors to normalize

```text
MISSING_allowed_paths
MISSING_script_path_OR_automation_script
MISSING_OR_FALSE_no_fake_final_ready
MISSING_OR_FALSE_no_db_write
MISSING_OR_FALSE_no_migration
MISSING_OR_FALSE_no_production_deploy
```

## Normalization rules

For each invalid legacy queue:

```text
1. Do not delete or mutate the original legacy queue evidence.
2. Create a normalized alias only if the intended automation_script or script_path can be resolved from existing repo evidence.
3. If script_path and automation_script are both missing, do not create an executable alias; write BLOCKED_MISSING_SCRIPT_PATH_OR_AUTOMATION_SCRIPT.
4. Add allowed_paths only under the owning page path, normally docs/chatgpt_status/aays1/.
5. Add no_fake_final_ready=true, no_db_write=true, no_migration=true, no_production_deploy=true.
6. Keep final_ready=false.
7. Keep status queued only for aliases that have a real script path.
8. For .txt legacy task files, preserve the original file as evidence and create a separate JSON alias only after script path is proven.
```

## Planned alias path pattern

```text
docs/chatgpt_status/aays1/queue/normalized_<legacy_task_id>_20260706.json
```

## Current decision

No alias was created in this pass because the underlying script paths for the `.txt` legacy queues are not proven by the shared status excerpt. This pass records the normalization plan and blocker instead of fabricating executable queue tasks.

## Safety

```text
new_parallel_runner_started=false
fake_completed_written=false
fake_final_ready_written=false
fake_percent_100_written=false
fake_data=false
db_write=false
migration=false
production_deploy=false
allowed_paths_escape=false
```

## Next action

Fetch each legacy queue file content and resolve real script_path or automation_script. Create normalized aliases only for queues whose script path is proven and whose allowed_paths can be constrained safely.
