# AAYS Safe Continue Bridge Lite

Time: 2026-05-14T09:34:13Z
Status: started
TaskId: none
BridgeRoot: C:\AAYS_GITHUB_BRIDGE_CLEAN2
Message: lite bridge started
Mode: allowlist-only-lite
AllowedActions: status_check, git_sync_check, heartbeat_push, artifact_collect

Safety:
- migration_apply=blocked
- prod_deploy=blocked
- arbitrary_script_execution=blocked
- secret_write_update=blocked
- production_db_write_ddl_index=blocked
