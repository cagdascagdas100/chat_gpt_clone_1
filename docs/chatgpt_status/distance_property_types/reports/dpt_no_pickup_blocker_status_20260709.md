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
- problem_resolution_plan_added: docs/chatgpt_status/distance_property_types/reports/dpt_problem_resolution_plan_20260709.md
- panel_source_found: england_map_web/data/runner_panel/page_status_index.json_has_stale_dpt_status
- site_status_json_added: england_map_web/data/distance_property_types/distance_property_types_site_status.json
- site_panel_patch_script_added: docs/chatgpt_status/distance_property_types/automation/patch_dpt_site_panel_status_20260709.ps1
- cmd_launcher_now_runs_panel_patch: docs/chatgpt_status/_shared/automation/RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.cmd
- ps1_launcher_now_runs_panel_patch: docs/chatgpt_status/_shared/automation/RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.ps1
- started_marker: missing
- completed_marker: missing

Blocker:
- the site panel was stale because page_status_index.json still had the old DPT problem/task status.
- repo-side patch and launchers are ready, but the existing F runner must pull/run them to refresh the live site-visible panel and produce real CSV/GeoJSON.

Next:
- continue with existing F single runner only
- do not create a second runner/worktree/clone
- run/honor the hotfix-then-continue launcher on the existing F runner repo root
- patch site panel first, then process queued tasks sequentially with MaxTasks=5
- keep final_ready=false until real runner evidence appears
