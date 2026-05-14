# AAYS 053 Auto Clean Cluster DB Dry-run
Generated: 2026-05-14T15:51:53
mode: auto_clean_isolated_cluster_trust_local_only_pgctl_timeout_guard
pg_host: 127.0.0.1
pg_port: 5434
cluster_dir: E:\AAYS_DATA\postgresql18_aays_auto_cluster_20260514_155152
log_file: E:\AAYS_DATA\postgresql18_aays_logs\postgresql-aays-auto-20260514_155152.log
no_secret_required: true

## 01 initdb trust locale C
COMMAND: C:\Program Files\PostgreSQL\18\bin\initdb.exe -D E:\AAYS_DATA\postgresql18_aays_auto_cluster_20260514_155152 -U postgres --encoding=UTF8 --locale=C --auth=trust
