# Long Batch Public Runtime Precheck - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Result

Repository-side public runtime preparation was checked using GitHub-visible files.

## Checked files

- `terrayield_land_intelligence/Dockerfile.cloud`
- `terrayield_land_intelligence/render.example.yaml`
- `terrayield_land_intelligence/.env.cloud.example`
- `terrayield_land_intelligence/scripts/cloud_smoke_check.py`
- `terrayield_land_intelligence/docs/chatgpt_handoff/cloud_ready_20260517/014_LOCAL_API_SMOKE_PERF_REPORT.txt`
- `terrayield_land_intelligence/docs/cloud_ready/CURRENT_STATUS_MACHINE_20260518.json`

## Findings

- Docker cloud runtime scaffold is present.
- Dockerfile uses Python 3.11 slim, installs geospatial/database dependencies and starts uvicorn.
- Render example is present and declares Docker runtime.
- Render example leaves `DATABASE_URL` as provider-side/non-synced value.
- Cloud env example is a template and does not include real secret values.
- Hosted smoke script requires `TERRAYIELD_PUBLIC_API_URL` and blocks if missing.
- Local API smoke/performance evidence has passed for the local checkpoint.

## Still not proven

- Public backend HTTPS URL.
- Cloud DB/PostGIS connection.
- Hosted smoke 6/6 against public URL.
- Public frontend runtime.
- Hosted p95 performance.

## Decision

Keep classification as `CLOUD_READY_PENDING_PROVIDER`.

## Next single action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Safety

- secret_values_printed=false
- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
