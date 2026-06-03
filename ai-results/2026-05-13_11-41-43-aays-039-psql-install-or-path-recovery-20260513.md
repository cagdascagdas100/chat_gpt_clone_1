# AAYS Portable Task Runner Result

## Task
AAYS 039 psql install or PATH recovery

## Task ID
aays-039-psql-install-or-path-recovery-20260513

## Time
2026-05-13 11:41:51

## Working Directory
C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
0

## Runner Mode
no-spawn-foreground-loop

## Output
```text
[2026-05-13T11:41:43] TASK=aays-039-psql-install-or-path-recovery-20260513
[2026-05-13T11:41:43] MODE=psql_install_or_path_recovery
[2026-05-13T11:41:43] NO_DB_WRITE=true
[2026-05-13T11:41:43] NO_UI_PATCH=true
[2026-05-13T11:41:43] MAY_TRIGGER_INSTALLER_OR_UAC=true
[2026-05-13T11:41:43] PSQL_BEFORE=
[2026-05-13T11:41:43] WINGET_FOUND=true
[2026-05-13T11:41:43] WINGET_INSTALL_START=PostgreSQL.PostgreSQL

   - 
                                                                                                                        

   - 
   \ 
   | 
                                                                                                                        
No package found matching input criteria.
[2026-05-13T11:41:45] WINGET_INSTALL_EXIT_CODE=-1978335212
[2026-05-13T11:41:50] PSQL_AFTER=
[2026-05-13T11:41:50] PLAN_PROGRESS_PERCENT=72
[2026-05-13T11:41:50] NEXT_TASK=manual-postgresql-client-install
[2026-05-13T11:41:50] NEXT_WAIT_MINUTES=0
powershell.exe : Set-Content : Akış okunabilir değildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Set-Content : Akış okunabilir değildi.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_039_psql_install_or_path_recovery_20260513.ps1:65 char:371
+ ... riptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
+                           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\AAYS_GITHUB_...table-runner.md:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 
[2026-05-13T11:41:51] REPORT_PATH=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-039-psql-install-or-path-recovery-20260513.report.md
[2026-05-13T11:41:51] TERRAYIELD_TASK_DONE


```

## Error
```text


```
