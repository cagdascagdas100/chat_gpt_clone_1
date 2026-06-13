# Runner self-test task

status: QUEUED_FOR_SINGLE_LOCAL_RUNNER
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
created_at: 2026-06-14

active_automation_artifact: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_RUNNER_SELF_TEST_20260614.ps1

expected_report: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/runner_self_test_<timestamp>.md
expected_status: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/runner_self_test_status_<timestamp>.md

acceptance: A local single runner is working only if it executes the automation artifact and pushes RUNNER_SELF_TEST_OK report/status files to GitHub.
