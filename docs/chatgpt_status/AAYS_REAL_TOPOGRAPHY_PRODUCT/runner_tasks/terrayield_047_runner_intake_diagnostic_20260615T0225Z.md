page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: DIAGNOSTIC_REQUESTED
retry: 20260615T0225Z
purpose: diagnose why the single shared runner has not produced heartbeat, smoke report, or raw runner output after valid queue/current-task pickup files
must_read:
  - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/current-task/terrayield_047_distance_property_types_pickup_20260615T0215Z.md
  - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/queue/terrayield_047_distance_property_types_pickup_20260615T0200Z.md
  - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1
  - docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1
expected_diagnostic_report: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_runner_intake_diagnostic_<timestamp>.md
expected_primary_smoke_report: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md
parallelism: diagnostic_only_no_db_mutation_no_runner_conflict
notes: do not start a second runner; only inspect why the existing shared runner has not picked this page task or has not pushed output
