# AAYS Autopilot Runner V6 Result

## Task
AAYS 053 auto clean cluster DB dry-run force run

## Task ID
aays-053-auto-clean-cluster-db-dryrun-20260514-force-0419

## Time
2026-05-14 12:28:14

## Working Directory
C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Timeout Seconds
1800

## Exit Code
1

## Output
``text
01 initdb trust locale C

``

## Error
``text
initdb.exe : initdb: hata: hibir veri dizini belirtilmedi
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_053_auto_clean_cluster_db_dryrun_20260514.ps1:14 char:10
+   $out = & $exe @args 2>&1
+          ~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (initdb: hata: h...ni belirtilmedi:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 

``
