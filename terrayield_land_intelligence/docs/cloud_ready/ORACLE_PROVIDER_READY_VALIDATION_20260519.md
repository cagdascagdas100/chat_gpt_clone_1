# Oracle Provider Ready Validation - 2026-05-19

## Classification

`CLOUD_READY_PENDING_PROVIDER`

## Validation result

`PROVIDER_READY_ARTIFACTS_VALIDATED`

## Checked artifacts

| Artifact | Result |
|---|---|
| `docker-compose.cloud.yml` | present; includes PostGIS, API, and Caddy services |
| `deploy/Caddyfile` | present; routes `api-terrayield.edalmo.com` to API and `terrayield.edalmo.com` to frontend |
| `deploy/oracle/bootstrap_readonly_checks.sh` | present |
| `deploy/oracle/vm_env_template.example` | present; placeholder-only |
| `deploy/oracle/ORACLE_VM_STEPS_TR.md` | present |
| `deploy/oracle/ORACLE_VM_START_CHECKLIST_TR.md` | present |
| `deploy/oracle/HOSTED_SMOKE_COMMANDS_TR.md` | present |
| `england_map_web/config/regions.public.json` | present; uses `https://api-terrayield.edalmo.com` |
| `docs/cloud_ready/ORACLE_ALWAYS_FREE_DEPLOY_TR.md` | present |
| `docs/cloud_ready/EDALMO_DNS_SSL_PLAN_TR.md` | present |
| `docs/cloud_ready/BACKUP_RESTORE_RUNBOOK_TR.md` | present |
| `docs/cloud_ready/CANONICAL_EVIDENCE_MAP_20260519.md` | present |
| `scripts/cloud_smoke_check.py` | hardened; only HTTP 2xx/3xx count as success |

## Did not repeat

- 012A
- 012B
- 014
- 016

## Still blocked by provider runtime

- Oracle account/login or signup
- Oracle VM public IP
- edalmo.com DNS records
- VM-local secret env values
- public backend HTTPS URL
- cloud DB/PostGIS runtime proof
- public frontend URL
- hosted smoke 6/6
- hosted p95/performance proof

## Safety

- secret_values_printed=false
- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none

## Next single action

`WAIT_FOR_USER_PROVIDER_LOGIN_AND_DNS_APPLY`
