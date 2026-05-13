# AAYS Portable Task Runner Result

## Task
AAYS 047 DB connection readiness probe

## Task ID
aays-047-db-connection-readiness-probe-20260514

## Time
2026-05-14 02:11:53

## Working Directory
C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
0

## Runner Mode
no-spawn-foreground-loop

## Output
```text
[2026-05-14T02:11:42] TASK=aays-047-db-connection-readiness-probe-20260514
[2026-05-14T02:11:42] MODE=db_connection_readiness_probe_readonly
[2026-05-14T02:11:42] SAFETY=NO_DB_WRITE;NO_SQL_EXECUTE;NO_SECRET_PRINT;NO_UI_PATCH
[2026-05-14T02:11:42] BRIDGE_ROOT=C:\AAYS_GITHUB_BRIDGE_CLEAN2
[2026-05-14T02:11:42] PROJECT_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
[2026-05-14T02:11:42] COST_ROOT=E:\AAYS_DATA\cost
powershell.exe : Set-Content : İşlem, başka bir işlem tarafından kullanıldığından 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-resu
lts\aays-047-db-c
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Set-Content : İ...s\aays-047-db-c:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
onnection-readiness-probe-20260514.report.md' dosyasına erişemiyor.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_047_db_connection_readiness_probe_20260514.ps1:61 char:6
+ $r | Set-Content -Encoding UTF8 -Path $out
+      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : WriteError: (C:\AAYS_GITHUB_...60514.report.md:String) [Set-Content], IOException
    + FullyQualifiedErrorId : GetContentWriterIOError,Microsoft.PowerShell.Commands.SetContentCommand
 
[2026-05-14T02:11:53] REPORT_PATH=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-047-db-connection-readiness-probe-20260514.report.md
[2026-05-14T02:11:53] STATUS_PATH=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-047-db-connection-readiness-probe-20260514.status.json
[2026-05-14T02:11:53] DB_CONNECTION_READINESS_SCORE=85/100
[2026-05-14T02:11:53] PLAN_PROGRESS_PERCENT=94
[2026-05-14T02:11:53] TASK_COMPLETION=100/100
[2026-05-14T02:11:53] TERRAYIELD_TASK_DONE


```

## Error
```text


```
