# AAYS 156 Persistent Single Runner 12h Watchdog

Status: PASS

## Root cause

- The old continuation launcher invoked the one-shot scanner with `-MaxTasks 5` and exited with the scanner (`RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.cmd`, pre-fix lines 22-29).
- The old scanner removed its short scan lock and exited `0/1` after one run (pre-fix scanner lines 607-611).
- The old daemon decided staleness from file age and wrote heartbeat only before waiting synchronously for the worker. A live PID could therefore look stale during a long worker.
- `single_runner.lock` and `MULTI_PAGE.lock` represented different process scopes but did not carry reliable process-start/scope identity. Stale bootstrap PID 15156, later worker PID 10108, a missing daemon lock, and a zero-byte heartbeat were consequences of those independent stale artifacts, not proof of a live shared runner.

## Implemented

- Existing daemon is the canonical persistent supervisor; no new runner system was created.
- Authoritative lock validates PID, process start, command and `single_shared_runner_daemon` scope and is written atomically.
- Short scan lock uses `single_scan_worker` scope and owner-aware cleanup.
- Heartbeat is updated while a child worker runs and includes sequence, uptime, supervisor/worker/app PID, refresh and site state.
- Workers run sequentially with `MaxTasks=8`, exponential backoff and degraded-but-alive behavior.
- Safe refresh defaults to 43200 seconds. Dirty non-runtime files produce `blocked_dirty_repo`; no reset or destructive pull occurs.
- Site watchdog checks health and ReadyToSell, preserves an existing listener, and only uses the canonical app launcher after three failures.
- Scheduled Task `AAYS_TerraYield_SingleRunner` uses `IgnoreNew`, unlimited execution time, one-minute retry and logon persistence.

## Real tests

- Single instance: second launcher kept one daemon and returned `already_running`.
- Soak: PID 696 / instance `220210abba3a46fdb6a12bda51392f26` stayed unchanged for about 16 minutes and completed 26 loops.
- Resource samples: CPU 1.796875s -> 6.484375s; working set 137539584 -> 87494656 bytes.
- Recovery: loop 1 child exited 7; loop 2 exited 0 under the same supervisor PID.
- Refresh self-test: PID 17180 / instance `d85cb01155bb4d3d82f46368cf5d2268`, heartbeat sequence 51, two 120-second refresh attempts, result `blocked_dirty_repo`, same PID preserved.
- Production: PID 1000 / instance `51ab94e102304e3fafb281939d814174`, production refresh 43200, three real scanner loops, heartbeat sequence 20, last exit 0, failures 0.
- Site: health 200, ReadyToSell 200, one listener PID 10648, canonical portable Python/uvicorn command verified.
- Power: S3 sleep is available; hibernation is disabled. Windows cannot run the task while the computer is asleep.

## Safety

- `parallel_runner=false`
- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`

Proof nonce: `aays156-20260711-140402-51ab94e1`

