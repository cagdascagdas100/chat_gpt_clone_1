# Cost50 Step 006 Schema Migration Draft Audit

Generated: 2026-05-12T02:14:47
Task: cost50-006-schema-migration-draft-audit-20260512

## Scope
- Read-only schema and Alembic readiness audit.
- No database writes and no migration execution.

## Checks
- project_root: True
- models_py: True
- alembic_env: False
- alembic_ini: False
- alembic_versions_dir: True
- app_db_dir: True
- app_main: True

## Pattern Checks
- sqlalchemy_model: True
- cost_domain: True
- alembic_target_metadata: False
- db_url: False
- numeric_money: True

## Alembic Version Samples
- E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\alembic\versions\0008_cost_engine_postgres.py

## Python Compile
- exit: 0
```text

```

## Git Status
```text
git : fatal: not a git repository (or any of the parent directories): .git
At C:\AAYS_GITHUB_BRIDGE_CLEAN\ai-task-scripts\terrayield_cost50_006_schema_migration_draft_audit.ps1:98 char:20
+ try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-Stri ...
+                    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (fatal: not a gi...ectories): .git:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 

```

Readiness score: 69

## Next Recommendation
- Repair schema/Alembic discovery before API/app smoke.

PLAN_PROGRESS_PERCENT=69
TASK_COMPLETION=100/100
TERRAYIELD_TASK_DONE
