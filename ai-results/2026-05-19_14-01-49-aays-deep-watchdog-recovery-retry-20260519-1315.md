# AAYS Portable Task Runner Result

## Task
AAYS deep watchdog recovery retry

## Task ID
aays-deep-watchdog-recovery-retry-20260519-1315

## Time
2026-05-19 14:03:21

## Working Directory
C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
1

## Runner Mode
no-spawn-foreground-loop

## Output
```text
powershell.exe : The term 'W' is not recognized as the name of a cmdlet, function, script file, or operable program. Ch
eck the spelling 
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (The term 'W' is...k the spelling :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
of the name, or if a path was included, verify that the path is correct and try again.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_deep_watchdog_orchestrator.ps1:69 char:6
+      Receive-Job $j | Out-Null
+      ~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (W:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
    + PSComputerName        : localhost
 


```

## Error
```text


```
