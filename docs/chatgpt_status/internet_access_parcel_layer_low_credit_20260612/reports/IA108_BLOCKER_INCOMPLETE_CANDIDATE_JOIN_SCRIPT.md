# IA108 blocker: incomplete candidate join script

- task_id: internet-access-108-real-parcel-final-gate
- page_key: internet_access_parcel_layer_low_credit_20260612
- blocker_type: incomplete_candidate_join_automation
- fake_geometry: false
- db_write: false
- production_deploy: false

## What was found

The repository contains the candidate join queue:

`docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/queue/ia108_real_geometry_join_from_candidates.txt`

The queue points to:

`docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/ia108_real_geometry_join_from_candidates.ps1`

However, the current automation file is only the initial setup/heartbeat part and does not contain the full candidate scanning, key selection, geometry assignment, ready output generation, and final gate update logic required to close IA108.

## Why the percentage is stuck

The final gate is blocked because the current score GeoJSON still has null geometries and no real Polygon/MultiPolygon parcel layer. The missing reports are execution outputs and must not be fabricated.

Expected real reports:

- `docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/reports/ia108_real_geometry_join_report.json`
- `docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/reports/ia108_real_geometry_join_v2_schema_probe_report.json`
- `docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/reports/ia108_runner_watchdog_v2_execute_report.json`
- `docs/chatgpt_status/reports/internet-access-108-real-parcel-final-gate.json`

## Next real action

Replace `ia108_real_geometry_join_from_candidates.ps1` with a complete real-geometry join implementation, then run the queued candidate join task. The implementation must:

1. Read `parcel_internet_access_scores.geojson` and its CSV/factor breakdown source.
2. Scan existing real geometry candidates under F:/D: AAYS work roots.
3. Select a real Polygon/MultiPolygon source by matching a real join key.
4. Assign only real geometry; never synthesize coordinates.
5. Write ready CSV/GeoJSON/detail/factor artifacts under F:/D: heavy root.
6. Write page join report and rerun/finalize the IA108 final gate only if null geometry count is zero.

## Current safe progress

- Infrastructure/files: 99.6%
- Product/final acceptance: 68%

This file documents the next blocker without faking completion.