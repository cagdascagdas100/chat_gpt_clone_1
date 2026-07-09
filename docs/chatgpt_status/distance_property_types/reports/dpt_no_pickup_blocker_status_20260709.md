status=PILOT_SITE_DATA_PUBLISHED_RUNNER_PICKUP_STILL_PENDING
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
- verified_csv_rows: 6
- verified_geojson_features: 6
- program_layer_features: 6
- site_status: six_real_web_source_features_published
- source_audit_rows: 6
- source_audit_passed_accuracy_target_rows: 6
- data_manifest_added: england_map_web/data/distance_property_types/distance_property_types_data_manifest_20260709.json
- panel_override_added: england_map_web/data/runner_panel/distance_property_types_status_override_20260709.json
- panel_latest_index_added: england_map_web/data/runner_panel/distance_property_types_panel_index_latest.json
- site_refresh_marker_added: england_map_web/data/distance_property_types/distance_property_types_site_refresh_marker_20260709.json
- bulk_expand_ready_script_added: docs/chatgpt_status/distance_property_types/automation/expand_dpt_from_existing_pilot_features_20260709.ps1
- bulk_expand_ready_queue_added: docs/chatgpt_status/distance_property_types/queue/0029_dpt_bulk_expand_ready_check_20260709.task.json
- covered_property_types: Industrial Unit; Detached Home; Retail Property; Apartment Building; Office Building; Mixed Building
- started_marker: missing
- completed_marker: missing

Blocker:
- pilot site-visible data is now written directly to CSV/GeoJSON/program layer.
- source audit, data manifest, panel override, panel latest index, refresh marker, and bulk expansion ready check are written.
- existing F runner pickup is still pending for full parcel-distance matrix expansion and automated refresh.

Next:
- continue with existing F single runner only
- do not create a second runner/worktree/clone
- let existing runner validate six visible outputs, then expand to full parcel-distance matrix
- keep final_ready=false until real runner evidence and bulk output appear
