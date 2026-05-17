# Safe Runner Task Protocol - 2026-05-18

## Purpose

Define which queued tasks a persistent local runner may execute automatically.

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Allowed automatic task classes

The runner may execute tasks that are explicitly read-only or test-only:

- static file validation
- Python syntax checks
- targeted pytest
- local API smoke
- hosted smoke if public URL is already provided outside repo
- curl-based performance measurement
- Git status/report generation
- report publishing

## Forbidden automatic task classes

The runner must reject tasks involving:

- production deployment
- migration apply
- DB write
- DDL
- index create/drop
- secret printing
- committing real `.env` or `.env.local`
- writing real credentials into repo

## Required task metadata

Every future runner task should declare:

- task_name
- safety_class
- expected_outputs
- forbidden_actions
- final_classification_rule
- next_single_action_rule

## Valid safety classes

- `static_validation`
- `local_test_only`
- `local_smoke_only`
- `hosted_smoke_only`
- `report_publish_only`

## Invalid safety classes

- `prod_deploy`
- `migration_apply`
- `db_write`
- `ddl`
- `secret_dump`

## Runner behavior

If a task has an invalid or missing safety class, the runner should mark it failed and write a blocker report.

## Current pending evidence tasks

- `012A_STATIC_CLOUD_READY_VALIDATE_AND_PUBLISH.ps1`
- `012B_LOCAL_TEST_SMOKE_PERF_AND_PUBLISH.ps1`

These are intended to be safe local evidence tasks, but they have not yet published reports.
