# GitHub-Only Autonomous Scope Matrix - 2026-05-18

## Current mode

`GITHUB_ONLY_CONTINUATION`

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Fully autonomous through GitHub

These tasks can be completed without local PowerShell, Docker, provider dashboards, public URLs, or secrets:

| Area | Autonomous status | Output type |
|---|---|---|
| Documentation | completeable | Markdown docs |
| Cloud readiness manifests | completeable | JSON/Markdown manifests |
| Static validators | completeable | Python scripts |
| Hosted smoke scripts | completeable | Python scripts |
| Provider-neutral playbooks | completeable | Markdown docs |
| Safety summaries | completeable | Text/Markdown |
| GitHub issues/status tracking | completeable | Issues/docs |
| Handoff/checkpoint packages | completeable | Docs/checklists |
| Classification rules | completeable | Docs/manifests |
| CI workflow definitions | completeable | YAML workflows |

## Not fully autonomous through GitHub

These tasks require local PC, provider dashboard, public URLs, or credentials:

| Area | Why blocked | Required external input |
|---|---|---|
| Fresh local pytest | runs on user PC/local runner | local runner or PowerShell |
| Fresh local API smoke | requires local API runtime | Docker/API process |
| Fresh perf p95 | requires live API endpoint | local or hosted runtime |
| Cloud DB proof | provider-side secret/config | managed DB setup |
| Hosted backend proof | provider deploy/public URL | backend public HTTPS URL |
| Hosted frontend proof | provider deploy/public URL | frontend public URL |
| Hosted smoke 6/6 | public runtime required | public backend URL |
| Production deployment | approval required | explicit user approval |
| Migration/DDL/DB write | safety-restricted | explicit user approval |

## Stop condition

GitHub-only automation may continue preparing repo assets, but it must not upgrade classification beyond `CLOUD_READY_PENDING_PROVIDER` without provider/public runtime evidence.

## Safety invariant

- `db_write=none`
- `ddl=none`
- `migration_apply=none`
- `prod_deploy=none`
- `secret_values_printed=false`
