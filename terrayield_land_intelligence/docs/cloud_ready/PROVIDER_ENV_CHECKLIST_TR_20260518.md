# Provider Environment Checklist - 2026-05-18

## Purpose

This checklist lists configuration names for provider dashboards. It does not contain real secret values.

## Backend service config

Required or recommended names:

- `APP_HOST`
- `APP_PORT`
- `ALLOWED_ORIGINS`
- `AAYS_DEPLOYMENT_MODE`
- `DATABASE_URL`
- `TERRAYIELD_PUBLIC_API_URL`

## Expected non-secret example values

- `APP_HOST=0.0.0.0`
- `APP_PORT=8010`
- `AAYS_DEPLOYMENT_MODE=cloud`

## Values that must be provided outside repo

- `DATABASE_URL`
- any token/API key
- any JWT/signing secret
- provider-generated public URL values

## Frontend config

The frontend must receive only public-safe values:

- public backend API base URL
- public feature flags
- public map/UI settings

The map frontend reads its land intelligence API base from the loaded config key:

- `landIntelligenceApiBaseUrl`

For public frontend hosting this value must point to the public backend HTTPS API origin. It must not remain `same-origin`, `localhost`, `127.0.0.1`, `0.0.0.0`, a Windows path, or a private tunnel URL unless explicitly accepted for a temporary test.

The public smoke gate must verify that browser-visible API calls use the hosted backend URL, not the local PC.

Never expose:

- database connection values
- private API keys
- backend signing secrets

## Verification checklist

- No real secret values committed.
- `.env` not committed.
- `.env.local` not committed.
- Backend public URL exists before hosted smoke.
- Cloud DB is configured in provider dashboard.
- Frontend config `landIntelligenceApiBaseUrl` points to the hosted backend URL.
- Frontend browser check confirms no API request goes to `127.0.0.1`, `localhost`, or local filesystem paths.
- Hosted smoke passes before classification update.

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`