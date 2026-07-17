# Gas Emissions England Parcel Continuation

Read `docs/chatgpt_status/_shared/contracts/AAYS_ENGLAND_PARCEL_COVERAGE_AND_POLYGON_CLICK_CONTRACT_20260717.md` first.

Continue the existing `gas_emissions` work only. Do not create a new runner or duplicate task. Replace the 3,533-value subset model with one row per authoritative parcel-registry ID. Spatially assign real official emissions area/grid values only to parcels contained by the source geography. Preserve geography ID, source date, resolution, join method and confidence. Keep unmatched parcels as `data_status=no_data`; do not fabricate values. Report total registry rows, verified-value rows, no-data rows, duplicates and unmatched rows separately. England completion is forbidden until remote output and browser polygon-click proof pass.

Immediate target: create and maintain exactly 92,283 unique `parcel_id` rows, preserving the canonical order. Continue filling only the first unverified rows from GitHub HEAD; do not repeat terminal batches.

`final_ready=false`
