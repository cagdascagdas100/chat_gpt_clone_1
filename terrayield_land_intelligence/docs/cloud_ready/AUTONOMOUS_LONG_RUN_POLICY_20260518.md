# Autonomous Long Run Policy - 2026-05-18

## User instruction

The user does not want to type `devam` repeatedly for every small step. GitHub-side autonomous work should be batched into larger runs.

## Operating rule

When the operator can continue safely through GitHub-only actions, it should do so in long batches instead of stopping after each small check.

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Continue automatically for

- documentation updates
- status file updates
- manifest/index maintenance
- provider-neutral playbooks
- smoke-test templates
- static validator improvements
- watchdog/runner preparation files
- GitHub-only handoff files
- issue/status tracking documents

## Stop and ask only for

- local PowerShell/Docker execution
- provider account selection
- public backend URL
- cloud DB/PostGIS configuration
- frontend public host choice
- hosted smoke approval
- production deploy approval
- migration/DDL/DB write approval
- real secret/config values outside repo

## Avoid repetitive loops

Do not repeatedly check missing 012A/012B reports unless there is a reason to believe the runner published new evidence. Treat those as known gaps until watchdog/local runner is enabled.

## Safety invariant

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
