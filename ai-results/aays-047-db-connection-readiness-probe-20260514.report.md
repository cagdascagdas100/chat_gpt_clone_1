# AAYS 047 DB Connection Readiness Probe

Generated: 2026-05-14T02:11:53

## Scope
- Read-only readiness probe.
- No DB write. No SQL execution. No secret printing. No UI patch.

## Findings
PSQL_PATH_PRESENT=True
PSQL_VERSION=psql (PostgreSQL) 18.3
CONFIG_SIGNAL_COUNT=562
MODEL_SIGNAL_COUNT=44
ARTIFACT_SIGNAL_COUNT=10

## Env presence only
DATABASE_URL_present=False
POSTGRES_HOST_present=False
POSTGRES_PORT_present=False
POSTGRES_DB_present=False
POSTGRES_USER_present=False
POSTGRES_PASSWORD_present=False

## Missing items
- connection environment variables missing or not visible to runner

DB_CONNECTION_READINESS_SCORE=85/100
PLAN_PROGRESS_PERCENT=94
TASK_COMPLETION=100/100
TERRAYIELD_TASK_DONE
