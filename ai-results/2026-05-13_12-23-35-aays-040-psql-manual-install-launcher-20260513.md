# AAYS Portable Task Runner Result

## Task
AAYS 040 psql manual install launcher

## Task ID
aays-040-psql-manual-install-launcher-20260513

## Time
2026-05-13 12:23:42

## Working Directory
C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
0

## Runner Mode
no-spawn-foreground-loop

## Output
```text
[2026-05-13T12:23:36] TASK=aays-040-psql-manual-install-launcher-20260513
[2026-05-13T12:23:36] MODE=psql_manual_install_launcher
[2026-05-13T12:23:36] NO_DB_WRITE=true
[2026-05-13T12:23:36] NO_UI_PATCH=true
[2026-05-13T12:23:36] MAY_OPEN_INSTALLER_OR_UAC=true
[2026-05-13T12:23:36] PSQL_BEFORE=
[2026-05-13T12:23:36] WINGET_FOUND=true
[2026-05-13T12:23:36] WINGET_INSTALL_INTERACTIVE_START=PostgreSQL.PostgreSQL

   - 
                                                                                                                        

   - 
                                                                                                                        
No package found matching input criteria.
[2026-05-13T12:23:37] WINGET_INSTALL_INTERACTIVE_EXIT_CODE=-1978335212
[2026-05-13T12:23:42] PSQL_AFTER=
[2026-05-13T12:23:42] PSQL_FOUND=False
[2026-05-13T12:23:42] PLAN_PROGRESS_PERCENT=72
powershell.exe : Set-Content : Akış okunabilir değildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Set-Content : Akış okunabilir değildi.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_040_psql_manual_install_launcher_20260513.ps1:63 char:371
+ ... riptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
+                           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\AAYS_GITHUB_...table-runner.md:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 
[2026-05-13T12:23:42] REPORT_PATH=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-040-psql-manual-install-launcher-20260513.report.md
[2026-05-13T12:23:42] TERRAYIELD_TASK_DONE


```

## Error
```text


```
