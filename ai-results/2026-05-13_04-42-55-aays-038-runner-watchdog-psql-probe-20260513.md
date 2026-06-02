# AAYS Portable Task Runner Result

## Task
AAYS 038 runner watchdog psql probe

## Task ID
aays-038-runner-watchdog-psql-probe-20260513

## Time
2026-05-13 04:42:56

## Working Directory
C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
0

## Runner Mode
no-spawn-foreground-loop

## Output
```text
[2026-05-13T04:42:56] TASK=aays-038-runner-watchdog-psql-probe-20260513
[2026-05-13T04:42:56] MODE=runner_watchdog_psql_probe_readonly
[2026-05-13T04:42:56] NO_DB_WRITE=true
[2026-05-13T04:42:56] NO_UI_PATCH=true
[2026-05-13T04:42:56] PSQL_FOUND=False
[2026-05-13T04:42:56] PSQL_PATH=
[2026-05-13T04:42:56] PLAN_PROGRESS_PERCENT=72
powershell.exe : Set-Content : Akış okunabilir değildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Set-Content : Akış okunabilir değildi.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_038_runner_watchdog_psql_probe_20260513.ps1:30 char:11
+ $report | Set-Content -Encoding UTF8 -Path $reportPath
+           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\AAYS_GITHUB_...60513.report.md:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 
[2026-05-13T04:42:56] REPORT_PATH=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-038-runner-watchdog-psql-probe-20260513.report.md
[2026-05-13T04:42:56] TERRAYIELD_TASK_DONE


```

## Error
```text


```
