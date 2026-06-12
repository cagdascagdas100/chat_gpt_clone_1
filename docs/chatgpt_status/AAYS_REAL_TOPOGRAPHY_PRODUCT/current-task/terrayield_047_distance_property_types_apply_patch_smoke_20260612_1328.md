# Current task: 047 Distance Property Types apply patch and smoke evidence

Status: queued for the single local runner.

This file points to the continuation queue task:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/queue/terrayield_047_distance_property_types_apply_patch_smoke_20260612_1328.md`

The runner must not mark FINAL_READY unless a GitHub report proves:

1. `/map/distance-property-types?bbox=...&limit=...` returns parcel polygon GeoJSON features, not points only.
2. Required parcel properties are present: parcel_id, parcel_ref or inspire_id, layer_name, use6_code, building_type_label, color_hex, six distance metrics, score percent, class/level, source/evidence, source_date, accuracy/confidence, matching_method, calculation_explanation.
3. Frontend overlay and popup/right-panel binding are present.
4. Excel output schema has one parcel per row with the required four output columns.

Expected report:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`

Current ChatGPT estimate before runner evidence: 62/100, not FINAL_READY.

PowerShell requested from user: no.