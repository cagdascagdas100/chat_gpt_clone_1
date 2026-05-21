# AAYS Portable Task Runner Result

## Task
Contractor 007 long England parcel-group and source scaffold pipeline WAKE3

## Task ID
contractor-007-long-parcel-group-pipeline-20260521-wake3

## Time
2026-05-21 21:48:55

## Working Directory
C:/AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
0

## Runner Mode
no-spawn-foreground-loop

## Output
```text
powershell.exe : Join-Path : Cannot find drive. A drive with the name 'E' does not exist.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Join-Path : Can...does not exist.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:5 char:14
+ $ExportDir = Join-Path $ContractorRoot 'exports'
+              ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (E:String) [Join-Path], DriveNotFoundException
    + FullyQualifiedErrorId : DriveNotFound,Microsoft.PowerShell.Commands.JoinPathCommand
 
Join-Path : Cannot find drive. A drive with the name 'E' does not exist.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:6 char:16
+ $ManifestDir = Join-Path $ContractorRoot 'manifests'
+                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (E:String) [Join-Path], DriveNotFoundException
    + FullyQualifiedErrorId : DriveNotFound,Microsoft.PowerShell.Commands.JoinPathCommand
 
Join-Path : Cannot find drive. A drive with the name 'E' does not exist.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:7 char:15
+ $CuratedDir = Join-Path $ContractorRoot 'curated'
+               ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (E:String) [Join-Path], DriveNotFoundException
    + FullyQualifiedErrorId : DriveNotFound,Microsoft.PowerShell.Commands.JoinPathCommand
 
Join-Path : Cannot find drive. A drive with the name 'E' does not exist.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:8 char:11
+ $RawDir = Join-Path $ContractorRoot 'raw'
+           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (E:String) [Join-Path], DriveNotFoundException
    + FullyQualifiedErrorId : DriveNotFound,Microsoft.PowerShell.Commands.JoinPathCommand
 
Join-Path : Cannot find drive. A drive with the name 'E' does not exist.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:9 char:15
+ $StagingDir = Join-Path $ContractorRoot 'staging'
+               ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (E:String) [Join-Path], DriveNotFoundException
    + FullyQualifiedErrorId : DriveNotFound,Microsoft.PowerShell.Commands.JoinPathCommand
 
New-Item : Cannot bind argument to parameter 'Path' because it is null.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:13 char:43
+ ... Force -Path $ExportDir,$ManifestDir,$CuratedDir,$RawDir,$StagingDir,$ ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [New-Item], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationErrorNullNotAllowed,Microsoft.PowerShell.Commands.NewItemComm 
   and
 
[2026-05-21T21:32:45] TASK=contractor-007-long-parcel-group-pipeline-20260521
[2026-05-21T21:32:45] MODE=read_only_no_fake_contractors_long_cycle
Add-Content : Akış okunabilir değildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:14 char:80
+ ... ite-Output $line; Add-Content -Encoding UTF8 -Path $Hb -Value $line }
+                       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\AAYS_GITHUB_...ong-pipeline.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Set-Content : Akış okunabilir değildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:15 char:40
+ ... $pct,$msg){ Set-Content -Encoding UTF8 -Path $Hb -Value @('# Contract ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\AAYS_GITHUB_...ong-pipeline.md:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 
Join-Path : Cannot bind argument to parameter 'Path' because it is null.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:25 char:22
+ $groupsCsv=Join-Path $ExportDir 'england_parcel_groups_200.csv'; $gro ...
+                      ~~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [Join-Path], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationErrorNullNotAllowed,Microsoft.PowerShell.Commands.JoinPathCom 
   mand
 
Join-Path : Cannot bind argument to parameter 'Path' because it is null.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:25 char:88
+ ... land_parcel_groups_200.csv'; $groupsJson=Join-Path $ExportDir 'englan ...
+                                                        ~~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [Join-Path], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationErrorNullNotAllowed,Microsoft.PowerShell.Commands.JoinPathCom 
   mand
 
Export-Csv : Cannot validate argument on parameter 'Path'. The argument is null or empty. Provide an argument that is n
ot null or empty, and then try the command again.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:26 char:62
+ ... roups | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $groupsCsv
+                                                                ~~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [Export-Csv], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationError,Microsoft.PowerShell.Commands.ExportCsvCommand
 
Set-Content : Cannot bind argument to parameter 'Path' because it is null.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:27 char:70
+ ... onvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $groupsJson
+                                                               ~~~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [Set-Content], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationErrorNullNotAllowed,Microsoft.PowerShell.Commands.SetContentC 
   ommand
 
Join-Path : Cannot bind argument to parameter 'Path' because it is null.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:31 char:21
+ $template=Join-Path $ExportDir 'contractor_rows_template.csv'; ($cont ...
+                     ~~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [Join-Path], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationErrorNullNotAllowed,Microsoft.PowerShell.Commands.JoinPathCom 
   mand
 
Set-Content : Cannot bind argument to parameter 'Path' because it is null.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:31 char:127
+ ... ontractorCols -join ',') | Set-Content -Encoding UTF8 -Path $template
+                                                                 ~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [Set-Content], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationErrorNullNotAllowed,Microsoft.PowerShell.Commands.SetContentC 
   ommand
 
Join-Path : Cannot bind argument to parameter 'Path' because it is null.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:33 char:26
+ $matchTemplate=Join-Path $ExportDir 'contractor_group_match_template. ...
+                          ~~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [Join-Path], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationErrorNullNotAllowed,Microsoft.PowerShell.Commands.JoinPathCom 
   mand
 
Set-Content : Cannot bind argument to parameter 'Path' because it is null.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:33 char:134
+ ... atchCols -join ',') | Set-Content -Encoding UTF8 -Path $matchTemplate
+                                                            ~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidData: (:) [Set-Content], ParameterBindingValidationException
    + FullyQualifiedErrorId : ParameterArgumentValidationErrorNullNotAllowed,Microsoft.PowerShell.Commands.SetContentC 
   ommand
 
Set-Content : Akış okunabilir değildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:15 char:40
+ ... $pct,$msg){ Set-Content -Encoding UTF8 -Path $Hb -Value @('# Contract ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\AAYS_GITHUB_...ong-pipeline.md:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 
Set-Content : Akış okunabilir değildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_contractor_007_long_parcel_group_pipeline.ps1:15 char:40
+ ... $pct,$msg){ Set-Content -Encoding UTF8 -Path $Hb -Value @('# Contract ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\AAYS_GITHUB_...ong-pipeline.md:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 


```

## Error
```text


```
