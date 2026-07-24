# ReadyToSell 3 — Research Wave 4 and Combined Wave 3+4 Worker

- SLOT_ID: `ready_to_sell_3`
- Parcel partition: `61523-92283`
- Overall progress: `81.25%`
- Increase: `+4.33` percentage points
- Completed operations: `13 / 16`
- Visible candidate rows: `24`
- Planned research targets including initial worker targets: `29`
- Manually preverified source-confidence >=90: `22`
- Planning cross-checks: `4` (`3` council/authority records, `1` independent planning-register index)
- Runner-scored high-confidence rows: `0` pending execution
- Source hashes: `0` pending execution
- Promoted rows: `0`
- Parcel matches: `0`
- Geometry matches: `0`

## Wave 4 candidates

1. Priory Road, W4
2. Manor Park Road, NW10
3. Former Brockley Social Club, SE4
4. Marshalsea Road, SE1
5. Blackheath Road, SE10
6. Hanworth Road, TW4
7. Scrutton Street, EC2A
8. Wagon Road, EN5

Brockley Social Club was cross-checked against the Lewisham Council committee decision for `DC/24/135847`. Priory Road was cross-checked against planning-register entry `253309FUL`. Marketing and planning caveats are retained per row.

## Worker expansion

The existing secondary queue task was expanded instead of creating another queue item. It now reads wave 3 and wave 4, processes 16 candidates with a maximum of three concurrent HTTP requests, stores SHA256 evidence for successful responses, checks expected text markers, and performs four planning cross-checks. It cannot promote any row without canonical parcel and geometry proof.

## Remote state

- Primary Automation 167 queue: `pending`
- Secondary wave 3+4 HTTP/SHA256 queue: `pending`
- Current slot task: `idle`
- Current owner: `null`

## Blocker

`WAITING_CANONICAL_SINGLE_COORDINATOR_PICKUP; CURRENT_TASK_IDLE; TWO_QUEUE_TASKS_PENDING; HTTP_SHA256_DOM_AND_REMOTE_PUBLISH_PROOFS_NOT_YET_EXECUTED`

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` remain unchanged.
