# AAYS Direct Autopilot Result

TaskId: aays-081-sleepwait-wrapper-min-20260514-2330
Script: aays_080_sleepwait_wrapper_min_20260514.ps1
ExitCode: 
Time: 2026-05-14T23:33:17

## STDOUT
```text
```

## STDERR
```text
R : Cannot locate the history for command line Generated: 2026-05-14T23:33:16.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_080_sleepwait_wrapper_min_20260514.ps1:11 char:1
+ R ('Generated: ' + (Get-Date -Format s))
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (Generated: 2026-05-14T23:33:17:String) [Invoke-History], ArgumentExcept 
   ion
    + FullyQualifiedErrorId : InvokeHistoryNoHistoryForCommandline,Microsoft.PowerShell.Commands.InvokeHistoryCommand
 
R : Cannot locate the history for command line SLEEPWAIT_PATCHED=true.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_080_sleepwait_wrapper_min_20260514.ps1:28 char:3
+   R 'SLEEPWAIT_PATCHED=true'
+   ~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (SLEEPWAIT_PATCHED=true:String) [Invoke-History], ArgumentException
    + FullyQualifiedErrorId : InvokeHistoryNoHistoryForCommandline,Microsoft.PowerShell.Commands.InvokeHistoryCommand
 
R : Cannot locate the history for command line patched: C:\Users\cagda\AppData\Local\Temp\aays080_20260514_233316.ps1.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_080_sleepwait_wrapper_min_20260514.ps1:32 char:1
+ R ('patched: ' + $Patched)
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (patched: C:\Use...0514_233316.ps1:String) [Invoke-History], ArgumentExc 
   eption
    + FullyQualifiedErrorId : InvokeHistoryNoHistoryForCommandline,Microsoft.PowerShell.Commands.InvokeHistoryCommand
 
& : ��lem, ba�ka bir i�lem taraf�ndan kullan�ld���ndan 'C:\Users\cagda\AppData\Local\Temp\aays080_20260514_233316.ps1' 
dosyas�na eri�emiyor.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_080_sleepwait_wrapper_min_20260514.ps1:33 char:3
+ & $Patched
+   ~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
R : Cannot locate the history for command line CHILD_EXIT_CODE=.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_080_sleepwait_wrapper_min_20260514.ps1:35 char:1
+ R ('CHILD_EXIT_CODE=' + $code)
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (CHILD_EXIT_CODE=:String) [Invoke-History], ArgumentException
    + FullyQualifiedErrorId : InvokeHistoryNoHistoryForCommandline,Microsoft.PowerShell.Commands.InvokeHistoryCommand
 
R : Cannot locate the history for command line AAYS_080_SLEEPWAIT_WRAPPER_MIN_DONE=false.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_080_sleepwait_wrapper_min_20260514.ps1:36 char:72
+ ... N_DONE=true' } else { R 'AAYS_080_SLEEPWAIT_WRAPPER_MIN_DONE=false' }
+                           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (AAYS_080_SLEEPW..._MIN_DONE=false:String) [Invoke-History], ArgumentExc 
   eption
    + FullyQualifiedErrorId : InvokeHistoryNoHistoryForCommandline,Microsoft.PowerShell.Commands.InvokeHistoryCommand
 

```
