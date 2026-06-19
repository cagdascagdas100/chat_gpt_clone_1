# Runner task 047 continuation: apply patch and produce smoke evidence

Date: 2026-06-12 13:28 UTC
Page key: AAYS_REAL_TOPOGRAPHY_PRODUCT
Branch: aays-runner-v17-icon-work-20260603-232706
Priority: high
Mode: single-runner continuation of existing 047 task, not a new product scope.

## Inputs already verified by ChatGPT

- Handoff ZIP hash: `6647321CD9A0F5E9C66BEA93B162DCC8E2EEDBA5ED3162B6ED6501A890614761`
- Existing queue task: `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/queue/terrayield_047_distance_property_types_parcel_popup_20260612.md`
- Existing current-task file: `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/current-task/terrayield_047_distance_property_types_parcel_popup_20260612.md`

## Objective

Continue the same 047 Distance to Nearby Property Types work until there is GitHub evidence for the narrow completion gate:

1. Read-only audit evidence exists.
2. Backend route `/map/distance-property-types?bbox=west,south,east,north&limit=n` is implemented or confirmed already implemented.
3. Frontend Distance Property Types overlay is implemented or confirmed already implemented.
4. Parcel popup/right-panel fields meet the handoff contract.
5. Smoke test output is written to GitHub reports.
6. If the endpoint returns zero features because DB/cache data is missing, write a diagnostic blocker report and do not claim FINAL_READY.

## Required local execution constraints

- Use existing local repo root: `C:\Users\cagda\Documents\GitHub\AAYS`.
- Do not move the C-drive bridge/runner infrastructure.
- Heavy/temp/smoke artifacts should go under an F-drive work root if available, for example `F:\chatgpt\AAYS_WORK\AAYS_REAL_TOPOGRAPHY_PRODUCT\distance_property_types_047`; otherwise use a small local temp folder and write final evidence to GitHub.
- Do not perform DB write, migration, import, backfill, or index creation without explicit user approval.
- Use bbox and limit in every endpoint smoke call.

## Required runner steps

1. Pull branch `aays-runner-v17-icon-work-20260603-232706` safely.
2. Confirm the handoff folder exists:
   `terrayield_land_intelligence\docs\chatgpt_handoff\distance_property_types_parcel_popup_low_credit_20260612\`
3. Run the read-only audit script if present:
   `terrayield_land_intelligence\docs\chatgpt_handoff\distance_property_types_parcel_popup_low_credit_20260612\07_LOCAL_READONLY_AUDIT.ps1`
4. Inspect current source files for:
   - `terrayield_land_intelligence\app\api\routes\map_layers.py`
   - `england_map_web\index.html`
   - `england_map_web\distance_property_types_overlay.js`
5. If `/map/distance-property-types` or the frontend overlay is missing, apply the narrow patch generated from the 047 handoff contract. The implementation must be real-only: no fake/demo features.
6. Run static checks:
   - `python -m py_compile terrayield_land_intelligence\app\api\routes\map_layers.py`
   - `node --check england_map_web\distance_property_types_overlay.js` when node is available.
7. If the app is available on 8010, run:
   `/map/distance-property-types?bbox=-0.55,51.28,0.35,51.75&limit=10`
8. Write all results to:
   `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`
9. Also write/update a concise status file under:
   `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md`

## Acceptance decision rules

- FINAL_READY is allowed only if the report proves parcel polygon features renderable by the endpoint and required popup/right-panel fields are present.
- If route exists but `features: []`, status must be `DATA_BLOCKED_NOT_FINAL_READY`, with missing table/cache/import-ready fixture details.
- If route is missing or syntax checks fail, status must be `PATCH_BLOCKED_NOT_FINAL_READY`, with exact error.
- If local app is not running, status must be `SMOKE_BLOCKED_APP_NOT_RUNNING`, with static check results still included.

## Expected report content

The report must include:

```text
status: FINAL_READY | DATA_BLOCKED_NOT_FINAL_READY | PATCH_BLOCKED_NOT_FINAL_READY | SMOKE_BLOCKED_APP_NOT_RUNNING
completion_percent: <0-100>
read_only_audit: PASS | FAIL | NOT_FOUND
backend_route: PRESENT | ADDED | MISSING | ERROR
frontend_overlay: PRESENT | ADDED | MISSING | ERROR
static_python: PASS | FAIL | SKIPPED
static_js: PASS | FAIL | SKIPPED
endpoint_smoke: PASS_WITH_FEATURES | PASS_EMPTY | FAIL | APP_NOT_RUNNING
feature_count: <number or unknown>
required_popup_fields: PASS | FAIL | NOT_TESTED
excel_schema: PASS | FAIL | NOT_TESTED
next_action: <single concrete action>
```

This is a continuation task for the existing 047 scope. Do not create unrelated page keys, branches, folders, or product tasks.