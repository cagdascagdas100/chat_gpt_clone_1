# TerraYield 047 Runner Escalation Retry

page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: QUEUED_RUNNER_ESCALATION_RETRY
retry: 20260616T0125Z

current_task: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/current-task/terrayield_047_distance_property_types_fixed_20260614.md
automation: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1

reason: shared runner has not published final smoke report, raw output, or heartbeat after prior current-task retry.

runner_contract: execute the page-local automation path above through the existing shared runner queue/current-task intake. Do not start a separate runner. Do not move the C-side runner infrastructure. Write all evidence back to this page key's GitHub reports/status/runner_outputs folders.

expected_report: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md
expected_raw_output: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt
expected_heartbeat: docs/chatgpt_status/_shared/heartbeat/single_multi_page_runner_heartbeat.txt

parallelism_policy: do not run conflicting DB/router/runner tasks in parallel. Only this page key's 047 repair/smoke is requested.

final_ready_policy: do not mark FINAL_READY unless the smoke report proves the endpoint returned a FeatureCollection with parcel geometry, popup fields, and six distance metrics.
