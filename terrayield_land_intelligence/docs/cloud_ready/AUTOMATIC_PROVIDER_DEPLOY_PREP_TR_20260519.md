# Automatic Provider Deploy Prep - 2026-05-19

## Current state

`CLOUD_READY_PENDING_PROVIDER`

Local and GitHub-side proof is complete for the current checkpoint:

- 012A static validation passed.
- 012B targeted pytest passed.
- 014 local API smoke/perf passed.
- 016 clean full pytest passed.
- Cloud smoke gate is hardened.
- Frontend API base URL gate is documented.
- Provider env placeholders are aligned.

## What can be automated without the user

The repository can prepare all deploy files, checks, smoke scripts, and evidence templates.

Already prepared:

- `Dockerfile.cloud`
- `render.example.yaml`
- `.env.cloud.example`
- `scripts/cloud_smoke_check.py`
- `docs/cloud_ready/FAST_PATH_DEPLOY_PLAYBOOK_TR_20260518.md`
- `docs/cloud_ready/PROVIDER_ENV_CHECKLIST_TR_20260518.md`
- `docs/cloud_ready/CURRENT_STATUS_MACHINE_20260518.json`

## What cannot be completed automatically from this chat alone

The following require an external provider account/dashboard or already-created public runtime values:

1. Backend public HTTPS service URL.
2. Managed cloud Postgres/PostGIS connection.
3. Public frontend URL.
4. Provider-side runtime confirmation that the backend uses the cloud DB.
5. Hosted smoke output against the public backend URL.
6. Hosted p95/performance output from the public backend URL.

## Why Codex/local proof is not enough

Codex/local runner proves that local code, tests, local smoke, and deploy scaffolding are valid. It cannot prove a public cloud runtime unless a public backend URL and cloud DB runtime exist.

## Automatic continuation rule

Do not rerun completed checks:

- 012A
- 012B
- 014
- 016

Continue only when one of these values exists outside the repository:

- `TERRAYIELD_PUBLIC_API_URL`
- `TERRAYIELD_FRONTEND_PUBLIC_URL`
- cloud DB runtime confirmation

## Next automatic action once provider values exist

Run hosted smoke:

```powershell
$env:TERRAYIELD_PUBLIC_API_URL="https://YOUR_PUBLIC_API_HOST"
$env:TERRAYIELD_FRONTEND_PUBLIC_URL="https://YOUR_PUBLIC_FRONTEND_HOST"
$env:TERRAYIELD_CLOUD_DB_VERIFIED="true"
python terrayield_land_intelligence/scripts/cloud_smoke_check.py
```

Expected classification remains `CLOUD_READY_PENDING_PROVIDER` until all public runtime gates pass.

## Safety

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
