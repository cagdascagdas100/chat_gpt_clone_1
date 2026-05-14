# AAYS 053 Auto Clean Cluster DB Dry-run
Generated: 2026-05-14T13:48:51
mode: auto_clean_isolated_cluster_trust_local_only
pg_host: 127.0.0.1
pg_port: 5437
cluster_dir: E:\AAYS_DATA\postgresql18_aays_auto_cluster_20260514_134847
log_file: E:\AAYS_DATA\postgresql18_aays_logs\postgresql-aays-auto-20260514_134847.log
no_secret_required: true

## 01 initdb trust locale C
COMMAND: C:\Program Files\PostgreSQL\18\bin\initdb.exe -D E:\AAYS_DATA\postgresql18_aays_auto_cluster_20260514_134847 -U postgres --encoding=UTF8 --locale=C --auth=trust
