# Runner Revival Ready - 2026-05-18

## Current diagnosis

The GitHub-side automation is working. The local runner side has not published 012A/012B evidence.

## Prepared fix

A safe one-shot watchdog start wrapper has been added:

`docs/chatgpt_handoff/local_runner_queue/START_WATCHDOG_SAFE_ONCE.ps1`

## Purpose

When executed on the local PC, it will:

- pull `security-accuracy-expansion-20260508`
- start `AAYS_LOCAL_RUNNER_WATCHDOG_SAFE.ps1`
- process allowlisted 012A/012B tasks
- write heartbeat and logs
- publish safe evidence back to GitHub where possible

## Safety

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Operational note

GitHub-only work can continue, but fresh local pytest/API smoke/perf evidence requires this local runner revival or another execution surface.
