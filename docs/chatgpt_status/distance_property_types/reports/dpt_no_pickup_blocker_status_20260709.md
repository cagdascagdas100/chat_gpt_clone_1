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
- shared_runner_status_support: queued_for_single_shared_runner_is_recognized
- shared_runner_f_blocker_found: BLOCKED_F_DRIVE_NOT_CANONICAL_in_stable_script
- hotfix_script_added: docs/chatgpt_status/_shared/automation/APPLY_F_PORTABLE_SINGLE_RUNNER_HOTFIX_20260709.ps1
- existing_f_runner_continue_launcher_added: docs/chatgpt_status/_shared/automation/RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.cmd
- distance_property_types_source_seed_priority_20260708_started: missing

Blocker:
- queue task and script path are visible/valid on repo side.
- existing F runner must pull this branch and run the hotfix-then-continue launcher before real started/heartbeat/report evidence can appear.

Next:
- continue with existing F single runner only
- do not create a second runner/worktree/clone
- run the hotfix-then-continue launcher on the existing F runner repo root
- process queued tasks sequentially with MaxTasks=5
- keep final_ready=false until real runner evidence appears
