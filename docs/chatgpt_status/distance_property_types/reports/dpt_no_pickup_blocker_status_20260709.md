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
- started_marker: missing
- completed_marker: missing
- shared_runner_f_blocker_found: BLOCKED_F_DRIVE_NOT_CANONICAL_in_stable_script
- hotfix_script_added: docs/chatgpt_status/_shared/automation/APPLY_F_PORTABLE_SINGLE_RUNNER_HOTFIX_20260709.ps1
- existing_f_runner_cmd_launcher_added: docs/chatgpt_status/_shared/automation/RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.cmd
- existing_f_runner_ps1_launcher_added: docs/chatgpt_status/_shared/automation/RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.ps1

Blocker:
- repo-side launcher/hotfix is ready.
- existing F runner must pull this branch and run the CMD or PS1 launcher before real started/heartbeat/report evidence can appear.

Next:
- continue with existing F single runner only
- do not create a second runner/worktree/clone
- run the hotfix-then-continue launcher on the existing F runner repo root
- process queued tasks sequentially with MaxTasks=5
- keep final_ready=false until real runner evidence appears
