status=BLOCKED_WAITING_SINGLE_RUNNER_PICKUP
page_key=distance_property_types
active_branch=codex/aays-single-runner-v5-20260706
single_runner_only=true
new_runner=false
parallel_runner=false
final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false

Latest checked evidence:
- priority_queue_task: visible_status_queued_for_single_shared_runner
- priority_queue_script_path: exists_distance_property_types_batch_runner_ps1
- shared_runner_status_support: queued_for_single_shared_runner_is_recognized
- shared_runner_f_blocker_found: BLOCKED_F_DRIVE_NOT_CANONICAL_in_stable_script
- hotfix_script_added: docs/chatgpt_status/_shared/automation/APPLY_F_PORTABLE_SINGLE_RUNNER_HOTFIX_20260709.ps1
- distance_property_types_source_seed_priority_20260708_started: missing

Blocker:
- queue task and script path are visible/valid on repo side.
- stable runner script still needs the F portable hotfix applied locally before it can write real started/heartbeat/report evidence from F.

Next:
- continue with existing F single runner only
- do not create a second runner/worktree/clone
- apply the F portable hotfix on the existing runner repo root, then process queued tasks
- keep final_ready=false until real runner evidence appears
