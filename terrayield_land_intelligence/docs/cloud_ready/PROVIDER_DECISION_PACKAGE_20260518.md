# TerraYield AI Provider Decision Package - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Recommended fast path

Use a low-cost/free-tier best-effort stack:

- Backend API: Render-style Docker web service or equivalent Docker-capable web host.
- Cloud DB/PostGIS: Supabase-style managed Postgres/PostGIS or equivalent managed Postgres with PostGIS support.
- Frontend: Vercel/Netlify-style static hosting or equivalent static web host.

This is a best-effort free-tier target, not an unlimited-free production guarantee.

## Required provider decisions

The user must choose or provide:

1. Backend hosting provider.
2. Cloud Postgres/PostGIS provider.
3. Frontend public hosting provider.
4. Public backend HTTPS URL after backend deployment.
5. Approval to run hosted smoke against the public backend URL.

## Backend deployment input files already in repo

- `terrayield_land_intelligence/Dockerfile.cloud`
- `terrayield_land_intelligence/render.example.yaml`
- `terrayield_land_intelligence/.env.cloud.example`
- `terrayield_land_intelligence/scripts/cloud_smoke_check.py`

## Provider environment variables

The provider dashboard should define values equivalent to:

- `APP_HOST=0.0.0.0`
- `APP_PORT=8010`
- `ALLOWED_ORIGINS=<frontend public origin or controlled wildcard during early test>`
- `DATABASE_URL=<provider secret value; never commit real value>`
- `AAYS_DEPLOYMENT_MODE=cloud`
- `TERRAYIELD_PUBLIC_API_URL=<public backend URL; outside repo>`

## Frontend requirements

- The frontend must call the hosted backend URL, not `127.0.0.1`.
- No private secret should be embedded in frontend code.
- Browser tests should cover desktop and mobile browser.

## Hosted smoke command

After the backend public HTTPS URL exists:

```powershell
$env:TERRAYIELD_PUBLIC_API_URL="https://YOUR_PUBLIC_API_HOST"
python terrayield_land_intelligence/scripts/cloud_smoke_check.py
```

## Hosted smoke acceptance

The smoke must pass these endpoints from the public URL:

- `/`
- `/ops/storage-registry`
- `/ops/consistency-check`
- `/handoff/status`
- `/map/listings?limit=1`
- `/map/sales-history/combined?limit=1`

## Classification update rules

Keep:

`CLOUD_READY_PENDING_PROVIDER`

until:

- public backend HTTPS URL exists,
- cloud DB provider is configured outside repo,
- hosted smoke passes.

Then update to:

`CLOUD_RUNTIME_READY`

If free-tier constraints are documented and accepted, the user-facing business classification may be:

`FREE_TIER_BEST_EFFORT_READY`

Never claim unlimited free hosting.

## Safety constraints

- No real secrets in repo.
- No `.env` or `.env.local` commit.
- No DB write.
- No DDL.
- No migration apply.
- No production deploy without explicit approval.
- No secret values printed.

## Current stop condition

The repository-side cloud readiness package is prepared. Further progress requires the user/provider decision above.
