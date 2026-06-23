# Internet Access Parcel Gap Closure - Open Blockers

Status: QUEUED_FOR_SINGLE_SHARED_RUNNER
Percent: 45

## Why percent increased from 35 to 45

The previous handoff only had summary, minimal queue, and minimal status files. This update adds a page-key scoped automation script and a runner-readable queue task that points at that script.

## Why percent is not 100

FINAL_READY cannot be claimed until the runner or local Codex produces GitHub-visible evidence for all gates below.

## Blocking gates

1. P0_geometry_missing
   - Existing heavy GeoJSON evidence shows `geometry: null`.
   - Required closure: real renderable parcel polygons.

2. P0_postcode_level_only
   - Existing package is postcode/source-unit level, not proven parcel-level.
   - Required closure: parcel_id keyed output with real geometry or a verified join to parcel geometry.

3. P1_factor_breakdown_schema_partial
   - Existing factor CSV header is too small for value/contribution/confidence display.
   - Required closure: factor_name, measured_value, normalized_value, weight, contribution, confidence, source fields.

4. P1_endpoint_empty_or_unproven
   - Endpoint response exists but non-empty parcel features are not proven.
   - Required closure: `/map/internet-access` returns non-empty FeatureCollection with parcel geometry.

5. P1_browser_smoke_missing
   - Browser evidence is not in GitHub reports.
   - Required closure: Internet icon, colored parcels, color scale, popup/right-panel and factor table verified.

## Expected next GitHub evidence

- `docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/status/internet-access-parcel-gap-closure-runner-status-*.json`
- `docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/reports/internet-access-parcel-gap-closure-runner-output-*.md`

## PowerShell required from user

No separate PowerShell is required from the user in this step if the existing shared runner is polling GitHub queue files. If no runner status appears, the only acceptable manual action is a one-time runner/contract probe that writes its output back to this same page-key reports/status folder.
