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
- existing_f_runner_start_request_added: docs/chatgpt_status/_shared/status/reboot_runner_start_request_20260709_f_portable_hotfix_continue.json
- site_status_json_added: england_map_web/data/distance_property_types/distance_property_types_site_status.json
- site_status_truthful: verified_output_rows_0_geojson_feature_count_0_waiting_for_runner_pickup

Blocker:
- repo-side launcher/hotfix/request is ready.
- site-readable status exists, but real parcel CSV/GeoJSON/site layer still requires existing F runner pickup.

Next:
- continue with existing F single runner only
- do not create a second runner/worktree/clone
- run/honor the hotfix-then-continue launcher on the existing F runner repo root
- process queued tasks sequentially with MaxTasks=5
- keep final_ready=false until real runner evidence appears
