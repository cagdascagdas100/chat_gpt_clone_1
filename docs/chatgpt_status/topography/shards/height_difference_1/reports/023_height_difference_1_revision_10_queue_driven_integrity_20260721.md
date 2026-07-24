# Height Difference 1 revision 10 explicit-identity, evidence and queue-driven recovery report

- Task ID: `height-difference-1-official-boundary-elevation-samples-20260720`
- Idempotency key: `height_difference_1-004-20260720`
- Payload revision: `10`
- Candidate rows: `3`
- Official measured rows: `0`
- Accuracy: `2.5/4 fallback`
- Source-contract assertions: `96/96`
- Runtime network execution: `not performed`; canonical F portable single shared runner is required.

## Resolved accuracy and execution risks

1. Revision 9 output identity depended on inherited upstream fields. Revision 10 explicitly writes task, payload revision, attempt, idempotency, script path and runtime script SHA-256.
2. The metric gate revalidates official monthly HMLR bulk-GML source digest, Barnet/Enfield authority, INSPIRE identifier, EPSG:27700 geometry and candidate point-in-polygon evidence.
3. EA DTM 1m statistics require at least three valid pixels, EPSG:27700, EPSG:5701/Ordnance Datum Newlyn, 1m-class resolution and ordered min/median/max/IQR values.
4. Parcel height difference is `maximum - minimum` EA DTM 1m elevation inside the official parcel polygon.
5. OS Terrain 50 requires numeric elevation, EPSG:27700, EPSG:5701/ODN, a 200x200 header, 50m cell size, valid row/column and non-NoData evidence. MD5 must match when supplied.
6. EA versus OS absolute elevation difference greater than 8m is human-review-only and cannot be promoted.
7. Runner, web and snapshot identities, hashes and counts must agree before terminal trust.
8. Watcher recovery v5 derives exact identity from the queue, verifies the Git blob of the script and does not hardcode the payload revision.
9. Existing shared control is not replaced. Existing portable runner is not stopped. Runner restoration is opt-in only.

## Current blocker

`QUEUE_DRIVEN_WATCHER_RECOVERY_V5_NOT_RUNTIME_APPLIED_ON_F_HOST; HEIGHT_DIFFERENCE_1_SLOT_UNCLAIMED; REVISION_10_OUTPUT_NOT_PRESENT; REVISION_10_INTEGRITY_READBACK_NOT_PRESENT`

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
