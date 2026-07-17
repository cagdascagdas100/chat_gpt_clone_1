# Security England Parcel Continuation

Read `docs/chatgpt_status/_shared/contracts/AAYS_ENGLAND_PARCEL_COVERAGE_AND_POLYGON_CLICK_CONTRACT_20260717.md` first.

Continue the existing `security_public_safety` work only. Do not create a new runner or duplicate task. Produce one row per authoritative parcel-registry ID. Join real official LSOA or equivalent public-safety geography to parcels by official ID, centroid containment or documented polygon intersection. Preserve geography ID, source date, method and confidence. Keep unmatched parcels as `data_status=no_data`; do not copy a neighbouring parcel's value. Report registry, verified, no-data, duplicate and unmatched counts separately. England completion is forbidden until remote output and browser polygon-click proof pass.

Immediate target: preserve exactly 92,283 unique `parcel_id` rows in canonical order and verify that all 92,283 values retain source-zone provenance. Continue only from the first unverified remote row/batch.

`final_ready=false`
