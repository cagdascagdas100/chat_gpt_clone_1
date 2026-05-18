# TerraYield AI Fast Path Deploy Playbook - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Goal

Move from repo-ready state to public hosted runtime after the user chooses providers and supplies external provider settings.

## Recommended fast path

- Backend: Docker-capable hosted web service.
- Database: Managed Postgres with PostGIS support.
- Frontend: Static web hosting.

This is a free-tier best-effort route, not unlimited free production hosting.

## Phase 1 - Backend provider

1. Create a new hosted web service from this repository/branch.
2. Use `terrayield_land_intelligence/Dockerfile.cloud` as the Dockerfile.
3. Set provider runtime port to `8010` or map provider `$PORT` to app port if required.
4. Define config values in provider dashboard, not in repo.
5. Set `TERRAYIELD_PUBLIC_API_URL` outside the repo after the provider gives a public backend HTTPS URL.
6. Wait for a public HTTPS backend URL.

Expected output:

- `PUBLIC_BACKEND_HTTPS_URL=<provider generated URL>`

## Phase 2 - Cloud database

1. Create managed Postgres with PostGIS support.
2. Store the connection string only in the provider secret/config panel.
3. Do not commit the real connection value.
4. Confirm backend can connect without printing credentials.
5. Set `TERRAYIELD_CLOUD_DB_VERIFIED=true` only after runtime connectivity is verified.

Expected output:

- `cloud_db_verified=true` only after runtime confirms connectivity.

## Phase 3 - Frontend

1. Deploy static frontend to a public host.
2. Configure frontend API base URL to the public backend URL.
3. In the loaded frontend config, `landIntelligenceApiBaseUrl` must equal the public backend HTTPS origin.
4. Set `TERRAYIELD_FRONTEND_PUBLIC_URL` outside the repo after the public frontend URL exists.
5. Confirm UI does not call `127.0.0.1`, `localhost`, `0.0.0.0`, Windows paths, or local filesystem paths.
6. Run desktop and mobile browser smoke.

Expected output:

- `PUBLIC_FRONTEND_URL=<provider generated URL>`

## Phase 4 - Hosted smoke

Set public-safe runtime values outside repo and run:

```powershell
$env:TERRAYIELD_PUBLIC_API_URL="https://YOUR_PUBLIC_API_HOST"
$env:TERRAYIELD_FRONTEND_PUBLIC_URL="https://YOUR_PUBLIC_FRONTEND_HOST"
$env:TERRAYIELD_CLOUD_DB_VERIFIED="true"
python terrayield_land_intelligence/scripts/cloud_smoke_check.py
```

Hosted smoke must pass:

- `/`
- `/ops/storage-registry`
- `/ops/consistency-check`
- `/handoff/status`
- `/map/listings?limit=1`
- `/map/sales-history/combined?limit=1`

The smoke script must keep `CLOUD_READY_PENDING_PROVIDER` if cloud DB verification or public frontend verification is missing, even if all endpoints return success.

## Phase 5 - Classification update

Use:

`CLOUD_RUNTIME_READY`

only if all of these are true:

- public backend HTTPS URL is verified,
- cloud DB/PostGIS runtime is verified,
- hosted smoke passes 6/6,
- public frontend URL is verified,
- no secret values were printed or committed.

Use:

`FREE_TIER_BEST_EFFORT_READY`

only if the runtime-ready gates pass and free-tier limits are explicitly accepted.

## Stop rule

Until provider values exist, keep:

`CLOUD_READY_PENDING_PROVIDER`

and:

`WAIT_FOR_USER_PROVIDER_DECISION`

## Safety

- Do not commit real secrets.
- Do not commit `.env` or `.env.local`.
- Do not run migration apply without explicit approval.
- Do not run production deploy without explicit approval.
- Do not perform DB writes or DDL from this checkpoint flow.