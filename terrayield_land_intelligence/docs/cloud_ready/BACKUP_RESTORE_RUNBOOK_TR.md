# Backup / Restore Runbook - TerraYield Oracle Always Free

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Scope

This runbook is a provider-ready planning artifact. It must not execute DB writes, DDL, migration apply, or production deploy during preparation.

## Backup targets

- PostgreSQL/PostGIS logical backup.
- Oracle block volume snapshot.
- Frontend static asset backup through Git.
- Runtime config names only; no secret values in reports.

## Daily logical backup example

Run on the Oracle VM only after production runtime exists:

```bash
mkdir -p backups
STAMP=$(date -u +%Y%m%d_%H%M%S)
docker compose -f docker-compose.cloud.yml exec -T db \
  pg_dump -U terrayield_app -d terrayield -Fc \
  > "backups/terrayield_${STAMP}.dump"
```

## Retention suggestion

- Daily backups: keep 7 days.
- Weekly backups: keep 4 weeks.
- Monthly backups: keep 3 months if disk allows.

## Restore outline

Restore only in a staging/test target first:

```bash
cat backups/terrayield_YYYYMMDD_HHMMSS.dump | \
  docker compose -f docker-compose.cloud.yml exec -T db \
  pg_restore -U terrayield_app -d terrayield --clean --if-exists
```

## Restore smoke checklist

After restore, verify:

```text
/
/handoff/status
/map/listings?limit=1
/map/sales-history/combined?limit=1
```

## PostGIS read-only proof

Run only after runtime exists, without printing secrets:

```bash
docker compose -f docker-compose.cloud.yml exec -T db \
  psql -U terrayield_app -d terrayield -c "select postgis_version();"
```

## Safety

- secret_values_printed=false
- db_write=none during planning
- ddl=none during planning
- migration_apply=none during planning
- prod_deploy=none during planning
