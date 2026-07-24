# ReadyToSell 3 — Research wave 5 and wave345 worker

- SLOT_ID: `ready_to_sell_3`
- Parcel partition: `61523-92283`
- Remote authority: `codex/aays-single-runner-v5-20260706`
- Completed operations: `16 / 19`
- Overall progress: `84.21%`
- Progress increase: `+2.96` percentage points
- Research targets: `37`
- Candidate rows currently visible in slot web view: `32`
- Manually preverified source-confidence >=90: `30`
- Verified planning cross-checks: `5`
- Planning register/search targets visible: `7`
- Runner-scored high-confidence rows: `0` pending execution
- SHA256 rows: `0` pending execution
- Promoted rows: `0`
- Parcel matches: `0`
- Geometry matches: `0`

## Wave 5

Eight candidate-only rows were added from current direct listings and official-agent auction pages: Clissold Crescent, 4 Beech Hill, Tudor Road, 68 Fulham Palace Road, Clapham Manor Street, Wells Park Road, St Andrew's Road and 2c King Edwards Gardens.

Planning states are preserved exactly: granted, submitted, pending and post-auction-revalidation states are not collapsed into a completed permission or live-sale claim. Clapham Manor Street has a separate planning-record cross-check. No candidate is promoted without canonical parcel and geometry proof.

## Worker and queue

The existing secondary queue was expanded without creating a third queue. Its entry now invokes `ready_to_sell_3_wave345_live_hash_worker.py`, which processes wave 3, wave 4 and wave 5: 24 candidates, at most three concurrent network requests, response SHA256, marker checks and planning-record checks where a record URL exists.

Both queue tasks remain pending because the canonical single coordinator has not claimed the slot. Current task remains idle. The remaining gates are live HTTP/SHA256 execution, Automation 167 real-browser DOM acceptance and serial publisher commit/push/remote readback.

- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
