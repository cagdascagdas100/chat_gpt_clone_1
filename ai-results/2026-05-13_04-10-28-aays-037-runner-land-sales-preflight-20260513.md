# AAYS Portable Task Runner Result

## Task
AAYS 037 runner and land sales preflight

## Task ID
aays-037-runner-land-sales-preflight-20260513

## Time
2026-05-13 04:10:32

## Working Directory
C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
0

## Runner Mode
no-spawn-foreground-loop

## Output
```text
[2026-05-13T04:10:29] TASK=aays-037-runner-land-sales-preflight-20260513
[2026-05-13T04:10:29] MODE=read_only_preflight
[2026-05-13T04:10:29] NO_LIVE_DB_WRITE=true
[2026-05-13T04:10:29] NO_UI_PATCH=true
[2026-05-13T04:10:29] NO_DESTRUCTIVE_OPERATION=true
[2026-05-13T04:10:29] BRIDGE_ROOT=C:\AAYS_GITHUB_BRIDGE_CLEAN2
[2026-05-13T04:10:29] LAND_FINAL_OUT=E:\AAYS_DATA\land_sales\final_outputs
[2026-05-13T04:10:29] SECTION=required_files
[2026-05-13T04:10:32] MISSING_REQUIRED_FILE_COUNT=0
[2026-05-13T04:10:32] SECTION=validation_report
[2026-05-13T04:10:32] INPUT_ZIP_SHA256_VERIFIED=True
[2026-05-13T04:10:32] CSV_ROWS=120
[2026-05-13T04:10:32] JSONL_ROWS=120
[2026-05-13T04:10:32] LONDON_ROWS=100
[2026-05-13T04:10:32] NON_LONDON_ROWS=20
[2026-05-13T04:10:32] VERIFIED_POLYGON_NON_EMPTY=0
[2026-05-13T04:10:32] SANITIZED_PUBLIC_ONLY_URL_FINDINGS=0
[2026-05-13T04:10:32] SECTION=db_ready_csv
[2026-05-13T04:10:32] DB_READY_CSV_ROWS=120
[2026-05-13T04:10:32] SECTION=psql_detection
[2026-05-13T04:10:32] PSQL_FOUND=false
[2026-05-13T04:10:32] PSQL_INSTALL_NEEDED=true
[2026-05-13T04:10:32] SECTION=progress
[2026-05-13T04:10:32] PLAN_PROGRESS_PERCENT=72
[2026-05-13T04:10:32] PACKAGE_EXPORT_PROGRESS=100
[2026-05-13T04:10:32] VALIDATION_PROGRESS=100
[2026-05-13T04:10:32] RUNNER_CONTINUITY_PROGRESS=60
[2026-05-13T04:10:32] DB_STAGING_IMPORT_READINESS=25
[2026-05-13T04:10:32] NEXT_WAIT_MINUTES=3-5
[2026-05-13T04:10:32] NEXT_USER_ACTION=devam et
[2026-05-13T04:10:32] AAYS_037_PREFLIGHT_DONE=true
powershell.exe : Set-Content : İşlem, başka bir işlem tarafından kullanıldığından 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-hear
tbeat\portable-ru
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Set-Content : İ...eat\portable-ru:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
nner.md' dosyasına erişemiyor.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_037_runner_land_sales_preflight_20260513.ps1:209 char:5
+ ) | Set-Content -Encoding UTF8 $HeartbeatPath
+     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : WriteError: (C:\AAYS_GITHUB_...table-runner.md:String) [Set-Content], IOException
    + FullyQualifiedErrorId : GetContentWriterIOError,Microsoft.PowerShell.Commands.SetContentCommand
 
[2026-05-13T04:10:32] REPORT_PATH=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-037-runner-land-sales-preflight-20260513.report.md
[2026-05-13T04:10:32] TERRAYIELD_TASK_DONE


```

## Error
```text


```
