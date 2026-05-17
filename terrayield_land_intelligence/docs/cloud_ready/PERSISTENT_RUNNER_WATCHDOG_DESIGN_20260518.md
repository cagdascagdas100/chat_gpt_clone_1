# Persistent Runner Watchdog Design - 2026-05-18

## Purpose

Design a safer runner that can continue work after the user types only `devam`.

## Current problem

The queued 012A/012B tasks were added to GitHub, but their reports were not published. A watchdog runner should make this failure visible and self-recover where safe.

## Watchdog loop

Every cycle:

1. Pull the target branch.
2. Check `docs/chatgpt_handoff/local_runner_queue/inbox`.
3. Validate task safety class.
4. Execute only approved task classes.
5. Write heartbeat status.
6. Move completed task to `done`.
7. Move failed task to `failed`.
8. Publish outputs to GitHub.

## Heartbeat outputs

The runner should write:

- `docs/chatgpt_handoff/local_runner_queue/outputs/WATCHDOG_HEARTBEAT.txt`
- current branch
- current head
- last task started
- last task status
- last publish time
- safe-mode status

## Recovery behavior

If a task fails:

- record exit code
- keep stdout/stderr logs
- write blocker report
- do not retry unsafe tasks
- retry safe transient failures only once

## Safe mode defaults

Default state must be safe:

- no DB write
- no DDL
- no migration apply
- no production deploy
- no secret printing

## Expected result

With the watchdog enabled, queued evidence tasks such as 012A and 012B should eventually publish their reports automatically.

## Current classification until runtime evidence changes

`CLOUD_READY_PENDING_PROVIDER`
