# Auto Continue Operator Policy - 2026-05-18

## Current instruction

Continue GitHub-side work without interrupting the user unless user-side action is strictly required.

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Do not interrupt the user for

- Re-checking GitHub files.
- Updating docs, manifests, indexes, or status files.
- Adding safe handoff reports.
- Adding issue/status tracking.
- Preparing provider-neutral playbooks.
- Preparing smoke-test instructions.
- Preparing static validation files.

## Interrupt the user only for

- Provider account selection.
- Public backend HTTPS URL.
- Cloud DB/PostGIS provider selection or confirmation.
- Frontend public hosting provider selection.
- Secret/config values that must be entered outside the repo.
- Approval for hosted smoke against a public URL.
- Approval for migrations, DB writes, DDL, or production deployment.
- Local PowerShell/Docker action if the local runner does not publish and fresh local evidence is mandatory.

## Current repo-side status

Prepared:

- Cloud scaffold.
- Hosted smoke script.
- Static validator.
- Provider decision package.
- Fast path deploy playbook.
- Provider environment checklist.
- Current status file.
- Operator stop condition.
- Parallel execution board.
- 012C GitHub-native fallback report.

Pending outside repo:

- Public hosted backend URL.
- Cloud database provider configuration.
- Hosted smoke 6/6.
- Public frontend URL.

## Safety

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false

## Rule

Keep working silently on GitHub-safe preparation tasks. Ask the user only when external provider, credential, public URL, hosted smoke approval, or local PC execution is required.
