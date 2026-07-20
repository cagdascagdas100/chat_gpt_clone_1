# ReadyToSell 3 — Research wave 6 and wave 3/4/5/6 worker expansion

- SLOT_ID: `ready_to_sell_3`
- Parcel partition: `61523-92283` (`30761` rows)
- New runner created: `false`
- Parallel runner created: `false`
- Existing secondary queue task reused: `true`
- Wave 6 research rows added: `8`
- Total visible candidate rows: `40`
- Total planned research targets including initial five: `45`
- Manually preverified source confidence >=90: `35`
- Planning cross-check targets: `10`
- Marketing-status revalidation rows: `3`
- Secondary worker candidate scope: `32`
- Concurrent request limit: `3`
- Runner SHA256 rows: `0` (`pending canonical coordinator pickup`)
- Promoted rows: `0`
- Parcel matches: `0`
- Geometry matches: `0`
- Primary queue: `pending`
- Secondary queue: `pending`
- Current task: `idle`
- Blocker: `WAITING_CANONICAL_SINGLE_COORDINATOR_PICKUP; HTTP_SHA256_DOM_AND_REMOTE_PUBLISH_PROOFS_NOT_YET_EXECUTED`
- final_ready: `false`
- fake_data: `false`
- db_write: `false`
- migration: `false`
- production_deploy: `false`

Wave 6 preserves current marketing caveats. Quinta Drive has a cross-market availability conflict. St Johns Road and Salmon Street require post-auction status confirmation. These rows are capped below high-confidence promotion by the runner even if their source documents remain reachable.
