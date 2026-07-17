# Height Difference England Parcel Continuation

Read `docs/chatgpt_status/_shared/contracts/AAYS_ENGLAND_PARCEL_COVERAGE_AND_POLYGON_CLICK_CONTRACT_20260717.md` first.

Continue the existing `height_difference` work only. Do not create a new runner or duplicate task. Produce one row per authoritative parcel-registry ID. Derive height from a verified DEM at the parcel centroid or from documented polygon statistics, then compute sea-level and regional-average differences with source, resolution, method and confidence. Keep unavailable parcels as `data_status=no_data`; do not fill them with an arbitrary nearest sample. Report registry, verified, no-data, duplicate and unmatched counts separately. England completion is forbidden until remote output and browser polygon-click proof pass.

Immediate target: expand the current verified subset to exactly 92,283 unique canonical `parcel_id` rows. Sample only the missing parcel IDs and never recompute already verified terminal rows.

`final_ready=false`
