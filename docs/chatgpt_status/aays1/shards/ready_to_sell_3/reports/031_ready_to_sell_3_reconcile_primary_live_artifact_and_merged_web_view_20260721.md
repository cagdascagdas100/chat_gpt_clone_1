# ready_to_sell_3 — Reconcile primary live artifact and merged web view

- SLOT_ID: `ready_to_sell_3`
- Parcel partition: `61523-92283`
- Final ready: `false`

## Reconciled remote evidence

A concurrent remote write replaced the preload-oriented web page with the primary Automation 167 live-evidence page. The primary artifact was therefore re-read before further writes.

Verified primary artifact facts:

- 5 source targets were attempted.
- 3 sources returned HTTP 200, matched all expected markers and have response SHA256 values.
- 1 source returned HTTP 410 but still has a response-body hash; it is not counted as live verified.
- 1 official planning endpoint timed out and has no hash.
- 3 rows reached source confidence >=90.
- 0 rows were promoted because canonical parcel and geometry matching were not run.
- Browser health/page HTTP were 200/200, but headless Edge timed out and DOM acceptance remained blocked with rows/live `0/0`.
- Serial remote publisher readback remained pending.

## Merged web view

The web page now loads:

- 264 research-preload candidates from waves 2-34;
- 5 primary live-evidence candidates;
- primary progress events including live fetch, hash proof, promotion gate, DOM blocker and publisher pending state.

Expected combined rows: 269. The view includes filters for live evidence, >=90 confidence, revalidation and concept-only records.

## Counters

- preparation operations: 107 / 110
- preparation progress: 97.27%
- increase from prior checkpoint: +0.18 points
- manually preverified >=90: 234
- live runner >=90: 3
- combined >=90: 237
- response hashes present: 4
- successful live source hashes: 3
- promotions: 0
- parcel matches: 0
- geometry matches: 0

## Remaining blocker

`NO_ACTIVE_CANONICAL_COORDINATOR_EXECUTION; TWO_QUEUE_TASKS_PENDING; PRIMARY_LIVE_FETCH_ARTIFACT_PRESENT_3_OF_5_VERIFIED; AUTOMATION_167_DOM_PROOF_BLOCKED_TIMEOUT_ROWS_0_LIVE_0; SECONDARY_256_CANDIDATE_HTTP_SHA256_NOT_EXECUTED; REMOTE_SERIAL_PUBLISH_READBACK_PENDING`
