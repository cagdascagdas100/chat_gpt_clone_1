# Sold Buildings Historical Sales — Runner / Branch Blocker

Generated: 2026-06-12
Page key: `sold_buildings_historical_sales_low_credit_20260612`
Task id: `sold-buildings-historical-sales-min-apply-audit-20260612`

## Current GitHub evidence

- `ai-tasks/current-task.json` exists on `main` and points to `ai-task-scripts\sold_buildings_historical_sales_min_apply_audit_20260612.ps1`.
- The expected runner result file is still missing: `ai-results/sold-buildings-historical-sales-min-apply-audit-20260612.result.json`.
- The expected page report/status/heartbeat files are still missing under `docs/chatgpt_status/sold_buildings_historical_sales_low_credit_20260612/`.
- Product frontend file `england_map_web/app.js` is present on `feature/terrayield-aays-integration`, not on `main`.
- In `feature/terrayield-aays-integration`, the historical sales menu still uses `./assets/icons/map-mode-sales.svg`; it has not yet been changed to `./assets/icons/terrayield_icons/sold_buildings.png`.

## Diagnosis

This is no longer a product-spec ambiguity. The task contract exists, but the runner has not produced any result/report/status/heartbeat output. Additionally, the product code branch is `feature/terrayield-aays-integration`, while the runner contract files are on `main`. The runner must either already checkout the product branch internally or the task script must explicitly target that branch before modifying `england_map_web/app.js`.

## Required next action

Do not create a second product task. Keep the same task id and page key. Fix runner execution/branch targeting so the existing task is consumed and writes:

```text
ai-results/sold-buildings-historical-sales-min-apply-audit-20260612.result.json
docs/chatgpt_status/sold_buildings_historical_sales_low_credit_20260612/reports/sold-buildings-historical-sales-min-apply-audit-20260612.md
docs/chatgpt_status/sold_buildings_historical_sales_low_credit_20260612/status/latest.md
docs/chatgpt_status/sold_buildings_historical_sales_low_credit_20260612/heartbeat/latest.md
```

## Product acceptance remains

- Historical Sales / Sold Buildings icon must use `sold_buildings.png`.
- `/map/sales-history/status` must be surfaced in UI.
- `/map/sales-history/parcels` must remain verified-only.
- Popup/right panel must show all linked sales in table form.
- Production must not be marked complete while verified rows/parcels are 0.
- Known data gate remains `BLOCKED_MISSING_OFFICIAL_BRIDGE`.

## Current completion

`FINAL_READY=false` until the runner publishes the expected result/report files.
