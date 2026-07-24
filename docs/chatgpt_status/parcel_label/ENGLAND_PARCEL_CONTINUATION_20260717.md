# Parcel Label England Parcel Continuation

Read `docs/chatgpt_status/_shared/contracts/AAYS_ENGLAND_PARCEL_COVERAGE_AND_POLYGON_CLICK_CONTRACT_20260717.md` first.

Continue the existing `parcel_label` work only. Do not create a new runner or duplicate task. Reconcile the 99,783 legacy London points with the 92,283 canonical rows, then produce one row per authoritative England parcel-registry ID. Prefer official parcel and land-use identifiers; otherwise use a verified polygon overlay with documented method and confidence. Keep unknown labels as `data_status=no_data`; do not infer from an unrelated nearest point. Report registry, verified, no-data, duplicate and unmatched counts separately. England completion is forbidden until remote output and browser polygon-click proof pass.

Immediate target: exactly 92,283 unique canonical `parcel_id` rows. Task 214 and every terminal predecessor are evidence-only and must not be replayed. Continue from the first unverified reconciliation/source batch recorded in GitHub HEAD.

`final_ready=false`
