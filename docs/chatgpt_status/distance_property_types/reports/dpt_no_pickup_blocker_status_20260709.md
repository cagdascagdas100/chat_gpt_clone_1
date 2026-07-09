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
- priority_queue_script_safety: bootstrap_validation_no_fake_evidence
- distance_property_types_source_seed_priority_20260708_started: missing
- recheck_status: unchanged_waiting_for_existing_F_runner
- queue_addition_status: paused_until_pickup_changes

Blocker:
- queue task and script path are visible/valid on repo side.
- existing F single runner has not yet written real started/heartbeat/report evidence for this page.

Next:
- continue with existing F single runner only
- do not create a second runner/worktree/clone
- keep queued tasks pending until real pickup evidence appears
- avoid adding more queue tasks until pickup evidence changes
