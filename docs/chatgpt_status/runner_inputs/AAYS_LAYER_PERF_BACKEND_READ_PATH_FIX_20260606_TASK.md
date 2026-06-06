# AAYS Layer Performance Backend Read-Path Fix Task

```text
timestamp=2026-06-06T16:00:00+03:00
project_name=AAYS_LAYER_PERF_BACKEND_READ_PATH_FIX
task_id=aays-layer-perf-backend-read-path-fix-20260606
status=queued_for_kalife_runner
runner_requirement=use_existing_single_kalife_runner_only
```

## Current known state

The previous local automatic check completed but its generated report is not yet present in GitHub. The pasted local result says:

```text
AUTO_CHECK_STATUS=PARTIAL_PASS_ENDPOINT_BLOCKED
completion_percent_after_auto=65
MANUAL_REQUIRED=NO_YET
full_england_parcel_coverage=PARTIAL
```

Static checks already passed locally:

```text
app_js_exists=PASS
runtime_guard_present=PASS
contains=/map/parcels PASS
contains=/map/listings PASS
contains=/map/sales-history/combined PASS
contains=/api/contractor/parcel PASS
contains=/cost/building-types/options PASS
contains=/cost/estimate/preview PASS
obvious_fake_demo_appjs=PASS
node_check=PASS
```

Endpoint blockers from local automatic check:

```text
health p95=776.1ms target=200 status=FAIL
parcels_limit_200 p95=30828.7ms target=700 status=FAIL payload=2259163 bytes
listings_limit_200 p95=16337.6ms target=1200 status=FAIL timeout_observed payload=1199341 bytes
sales_history_combined_limit_200 p95=10596.6ms target=1300 status=FAIL payload=1266815 bytes
internet_access_limit_200 p95=1027.6ms target=500 status=FAIL
headless_browser_load=FAIL timeout
```

## Mandatory runner protocol

1. Check local runner count.
2. Use exactly one existing canonical/Kalife runner.
3. If zero runner processes are active, recover or start only the canonical runner.
4. If multiple runner processes are active, do not start the task; write a blocked report.
5. Do not request pasted PowerShell output from the user.
6. Write all outputs into GitHub-readable text files under the report paths below.
7. Commit and push generated reports only if the local runner is already configured for safe sync.

## Strict safety

- No database writes.
- No production deployment.
- No schema migration or DDL.
- No invented/fake/demo/sample parcel, listing, sales, contact, cost, or planned-asset data.
- No destructive Git operations.
- No force push.
- No secret, token, or environment value printing.
- Preserve existing user changes.

## Required work

Run the companion script:

```powershell
powershell -ExecutionPolicy Bypass -File .\docs\chatgpt_status\runner_inputs\aays_layer_perf_backend_read_path_fix_20260606.ps1
```

Then inspect generated reports and apply only safe code-level fixes when the script identifies exact route/frontend blockers that can be corrected without schema/data changes.

## Required outputs

- docs/chatgpt_status/AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606/RUNNER_STATE_AND_QUEUE_REPORT.txt
- docs/chatgpt_status/AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606/BACKEND_READ_PATH_FIX_REPORT.txt
- docs/chatgpt_status/AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606/FRONTEND_LAZY_LOAD_AND_PMTILES_REPORT.txt
- docs/chatgpt_status/AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606/POST_FIX_PERF_SMOKE.txt
- docs/chatgpt_status/AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606/CHANGED_FILES_AND_VALIDATION.txt
- docs/chatgpt_status/runner_outputs/aays-layer-perf-backend-read-path-fix-latest.txt

## Completion rules

- Current full-plan progress is 65%.
- Raise only to 70-75 if endpoint/read-path blockers are fixed or map non-blocking PMTiles/lazy-load behavior is proven by report.
- Raise to 75-80 only after browser/UI behaviour is confirmed.
- Do not claim 100 while full England parcel source coverage remains PARTIAL.
