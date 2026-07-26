# ready_to_sell_3 — research waves 605–610

- Continuation key preserved: `6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a`
- Current official catalogue rows: 12
- Official lot identities: 12
- Full official detail readbacks: 3
- Average source confidence: 99.45/100
- Exact-address repository searches: 14; hits: 0
- Fail-closed exclusions: `136 Elswick` (catalogue/detail price conflict), `35 Townfield Gardens` (bedroom-count conflict)
- New research rows: 12; visible research rows: 3392
- Work items completed this turn: 26/26
- Visible operation progress: 3061/3063 (99.93%)
- Canonically promoted rows: 0
- Fake data, title inference, parcel inference, geometry inference: none

## Canonical recovery

`current_task_latest.json` was found regressed to wave 577 while the verified checkpoint remained at wave 604. With ownership unclaimed and the compatibility heartbeat stale, the safe action is to restore `current_task_latest.json` from the verified continuation state and then advance both current task and checkpoint to wave 610. No new task, runner or owner is created.

## Remaining gate

`AUTOMATION_167_DOM_PROOF` remains the first unverified step. No port-8012 headless DOM proof, canonical parcel match, or geometry proof was found. Research may continue, but promotion and final acceptance remain fail-closed.