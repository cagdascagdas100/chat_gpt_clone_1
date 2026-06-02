# AAYS Portable Task Runner Result

## Task
PARCELSALES 002 source inventory

## Task ID
parcelsales-002-source-inventory-20260518

## Time
2026-05-18 12:59:08

## Working Directory
C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
1

## Runner Mode
no-spawn-foreground-loop

## Output
```text
powershell.exe : Set-Content : Akış okunabilir değildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Set-Content : Akış okunabilir değildi.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\parcelsales_002_source_inventory_20260518.ps1:21 char:10
+ $Lines | Set-Content -LiteralPath (Join-Path $OutDir "source_inventor ...
+          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\AAYS_GITHUB_...ntory_report.md:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 


```

## Error
```text


```
