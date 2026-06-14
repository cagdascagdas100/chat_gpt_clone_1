# Shared runner task — AAYS_REAL_TOPOGRAPHY_PRODUCT

PAGE_KEY: AAYS_REAL_TOPOGRAPHY_PRODUCT
BRANCH: aays-runner-v17-icon-work-20260603-232706
TASK_ID: topography-final-panel-smoke-20260614
TASK_TYPE: automation_script
PRIORITY: high
PARALLEL_SAFE: true
CONFLICT_GROUP: read_only_smoke

automation_script: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/topography_final_panel_smoke_20260614.ps1
expected_report_glob: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_final_panel_smoke_*.txt

Rules:
- Use the existing shared runner only.
- Do not open a separate PowerShell or runner.
- Do not run DB writes, migrations, imports, deploys, or fake data generation.
- Produce all evidence under docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports.
- This task is read-only smoke/contract verification and may run in parallel with unrelated read-only checks.
