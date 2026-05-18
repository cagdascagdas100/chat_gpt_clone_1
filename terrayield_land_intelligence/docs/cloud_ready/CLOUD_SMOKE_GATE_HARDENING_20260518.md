# Cloud Smoke Gate Hardening - 2026-05-18

## Purpose

Prevent hosted smoke output from upgrading TerraYield to `CLOUD_RUNTIME_READY` unless all runtime proof gates are satisfied.

## Current confirmed state

- Local static validation is already passed.
- Local targeted pytest is already passed.
- Local API smoke is already passed 6/6.
- Local performance is already passed.
- Public backend runtime is not verified yet.
- Cloud database runtime is not verified yet.
- Public frontend runtime is not verified yet.
- Hosted smoke and hosted performance are not verified yet.

## Required hard gate

The hosted smoke result must keep `CLOUD_READY_PENDING_PROVIDER` until all of these are true:

1. Public backend HTTPS URL is verified.
2. Cloud database/PostGIS runtime is verified without exposing connection values.
3. Hosted smoke returns 6/6 from the public URL.
4. Public frontend URL is verified.
5. Hosted p95 performance is recorded.

## Do not repeat

Do not rerun 012A, 012B, or 014 local checks unless new local evidence is explicitly needed.

## Next action

Harden `scripts/cloud_smoke_check.py` so its classification cannot say `CLOUD_RUNTIME_READY` from endpoint success alone.