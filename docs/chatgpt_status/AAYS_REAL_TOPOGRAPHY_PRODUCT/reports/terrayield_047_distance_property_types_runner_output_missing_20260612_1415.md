# 047 Distance Property Types runner output missing

status: RUNNER_OUTPUT_MISSING_NOT_FINAL_READY
completion_percent: 62
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
scope: existing 047 Distance to Nearby Property Types continuation

## GitHub evidence read by ChatGPT

- Queue file present: `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/queue/terrayield_047_distance_property_types_apply_patch_smoke_20260612_1328.md`
- Current-task file present: `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/current-task/terrayield_047_distance_property_types_apply_patch_smoke_20260612_1328.md`
- Handoff received report present: `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_handoff_received_20260612.md`

## Missing evidence

The expected runner output report was not found by GitHub search:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`

No matching status file was found by GitHub search:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md`

## Acceptance decision

Not FINAL_READY. The existing 047 acceptance gate requires runtime/static evidence for:

- read-only audit result,
- backend `/map/distance-property-types?bbox=...&limit=...`,
- frontend overlay and popup/right-panel binding,
- parcel polygon GeoJSON features or a data-blocked diagnostic,
- Excel output schema.

## Next concrete action

The single local runner should consume the existing queue/current-task file and write the required apply/smoke report. No new product scope should be created. Do not perform DB write, migration, import, backfill, or index creation without explicit approval.
