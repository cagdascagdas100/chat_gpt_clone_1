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
- Hosted smoke passes before classification update.

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`
