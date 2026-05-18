# Next Autonomous Action Queue - 2026-05-18

## Current mode

`GITHUB_ONLY_CONTINUATION`

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Queue policy

Do not repeat missing 012A/012B checks without new runner evidence. Proceed only when new evidence or an external execution surface appears.

## Queue

### Q1 - New GitHub-only evidence appears

Action:

- ingest evidence using `EVIDENCE_INGESTION_PLAN_20260518.md`
- update status and manifest files
- keep classification pending unless runtime proof exists

### Q2 - 012A/012B reports appear

Action:

- update runtime proof gap register
- update current status machine JSON
- keep cloud classification pending unless provider evidence exists

### Q3 - Watchdog is enabled locally

Action:

- read heartbeat
- read 012A/012B reports
- update evidence gap register
- update final manifest

### Q4 - Public backend URL appears

Action:

- prepare hosted smoke command
- run/record hosted smoke only with approval
- update classification per `CLASSIFICATION_UPDATE_PLAYBOOK_20260518.md`

### Q5 - Cloud DB provider proof appears

Action:

- record secret-safe proof only
- do not commit credentials
- update runtime proof gap register

### Q6 - Frontend public URL appears

Action:

- record browser/UI smoke status
- ensure frontend uses hosted backend, not local `127.0.0.1`

## Stop conditions

Stop and ask user only for:

- provider selection
- public backend URL
- cloud DB confirmation
- hosted smoke approval
- local runner enablement
- any migration/DDL/DB write/prod deploy approval

## Safety invariant

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
