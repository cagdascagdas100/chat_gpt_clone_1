# Docker psql DB dry-run

Generated: 2026-05-13T14:08:28

mode: docker_psql_db_dryrun
pg_host: host.docker.internal
pg_port: 5432
pg_database: postgres
pg_user: postgres
exit_code: 2
plan_progress_percent: 80

## Output
```text
Password for user postgres: 
psql: error: connection to server at "host.docker.internal" (192.168.65.254), port 5432 failed: fe_sendauth: no password supplied
```
