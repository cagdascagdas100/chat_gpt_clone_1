[CmdletBinding()]
param(
  [string]$PortableRoot = 'F:\TerraYield_AAYS_Portable',
  [switch]$Uninstall,
  [switch]$RestoreLegacyTask
)

$ErrorActionPreference='Stop'
$taskName='AAYS Portable Runner Guardian'
$legacyTaskName='AAYS_TerraYield_SingleRunner'
$programRoot=Join-Path $env:ProgramData 'AAYS'
$installedGuardian=Join-Path $programRoot 'portable_runner_guardian.ps1'
$installedConfig=Join-Path $programRoot 'portable_runner_guardian.json'
$statePath=Join-Path $programRoot 'guardian_state.json'
$installResultPath=Join-Path $programRoot 'guardian_install_result.json'
$legacyBackupPath=Join-Path $programRoot 'legacy_single_runner_task.xml'

function Write-Utf8([string]$Path,[string]$Text) {
  $parent=Split-Path -Parent $Path
  if(-not(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null}
  [IO.File]::WriteAllText($Path,$Text,(New-Object Text.UTF8Encoding($false)))
}
function Write-Json([string]$Path,$Value){Write-Utf8 $Path (($Value|ConvertTo-Json -Depth 30)+[Environment]::NewLine)}

if($Uninstall){
  Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {$_.CommandLine-like'*portable_runner_guardian.ps1*'} |
    ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}
  if($RestoreLegacyTask-and(Test-Path -LiteralPath $legacyBackupPath)){
    Register-ScheduledTask -TaskName $legacyTaskName -Xml (Get-Content -LiteralPath $legacyBackupPath -Raw) -Force|Out-Null
  }
  Write-Json $installResultPath ([ordered]@{status='uninstalled';guardian_installed=$false;scheduled_task_installed=$false;legacy_task_restored=[bool]$RestoreLegacyTask;final_ready=$false})
  exit 0
}

$PortableRoot=[IO.Path]::GetFullPath($PortableRoot).TrimEnd('\')
if($PortableRoot.StartsWith('C:\',[StringComparison]::OrdinalIgnoreCase)){throw "C_DRIVE_NOT_CANONICAL: $PortableRoot"}
$repoRoot=Join-Path $PortableRoot 'runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$sourceGuardian=Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\AAYS_PORTABLE_RESUME_GUARDIAN.ps1'
$sourceConfig=Join-Path $repoRoot 'docs\chatgpt_status\_shared\config\AAYS_PORTABLE_RESUME_GUARDIAN.json'
$launcher=Join-Path $PortableRoot 'RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
foreach($required in @($sourceGuardian,$sourceConfig,$launcher,(Join-Path $repoRoot '.git'))){
  if(-not(Test-Path -LiteralPath $required)){throw "INSTALL_REQUIRED_PATH_MISSING: $required"}
}

New-Item -ItemType Directory -Force -Path $programRoot|Out-Null
$config=Get-Content -LiteralPath $sourceConfig -Raw|ConvertFrom-Json
$markerPath=Join-Path $PortableRoot ([string]$config.marker_file)
$marker=$null
if(Test-Path -LiteralPath $markerPath){try{$marker=Get-Content -LiteralPath $markerPath -Raw|ConvertFrom-Json}catch{}}
if(-not$marker-or-not$marker.marker_id){
  $marker=[ordered]@{marker_id=[guid]::NewGuid().ToString('N');created_at=[DateTimeOffset]::UtcNow.ToString('o');portable_product='AAYS_TerraYield';canonical_repo_relative='runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707';final_ready=$false}
  Write-Json $markerPath $marker
}
$driveLetter=[IO.Path]::GetPathRoot($PortableRoot).Substring(0,1)
$volume=Get-Volume -DriveLetter $driveLetter -ErrorAction Stop
$logical=Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='{0}:'" -f $driveLetter) -ErrorAction SilentlyContinue
$config.marker_id=[string]$marker.marker_id
$config.volume_unique_id=[string]$volume.UniqueId
$config.volume_serial=[string]$logical.VolumeSerialNumber
$config.volume_label=[string]$volume.FileSystemLabel
$config.fallback_root=$PortableRoot
Copy-Item -LiteralPath $sourceGuardian -Destination $installedGuardian -Force
Write-Json $installedConfig $config

$tokens=$null;$errors=$null
[Management.Automation.Language.Parser]::ParseFile($installedGuardian,[ref]$tokens,[ref]$errors)|Out-Null
if($errors.Count){throw "GUARDIAN_PARSE_FAILED: $($errors[0].Message)"}

$preflightState=Join-Path $programRoot 'guardian_install_preflight.json'
& powershell -NoProfile -ExecutionPolicy Bypass -File $installedGuardian -ConfigPath $installedConfig -StatePath $preflightState -Once -NoStart -SkipStabilityDelay
if($LASTEXITCODE-ne0-or-not(Test-Path -LiteralPath $preflightState)){throw 'GUARDIAN_PREFLIGHT_FAILED'}
$preflight=Get-Content -LiteralPath $preflightState -Raw|ConvertFrom-Json
if(-not$preflight.portable_disk_present-or-not$preflight.five_pages_registry_verified){throw 'GUARDIAN_PREFLIGHT_CONTRACT_FAILED'}

$legacy=Get-ScheduledTask -TaskName $legacyTaskName -ErrorAction SilentlyContinue
if($legacy){Write-Utf8 $legacyBackupPath (Export-ScheduledTask -TaskName $legacyTaskName)}

$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$sid=$identity.User.Value
$psExe=Join-Path $PSHOME 'powershell.exe'
$actionArgs=('-NoProfile -ExecutionPolicy Bypass -File "{0}" -ConfigPath "{1}" -StatePath "{2}" -Loop' -f $installedGuardian,$installedConfig,$statePath)
$xmlPs=[Security.SecurityElement]::Escape($psExe)
$xmlArgs=[Security.SecurityElement]::Escape($actionArgs)
$xmlSid=[Security.SecurityElement]::Escape($sid)
$startBoundary=(Get-Date).AddMinutes(2).ToString('s')
$subscription=[Security.SecurityElement]::Escape("<QueryList><Query Id='0' Path='System'><Select Path='System'>*[System[Provider[@Name='Microsoft-Windows-Power-Troubleshooter'] and EventID=1]]</Select></Query></QueryList>")
$xml=@"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>AAYS portable runner guardian; health only, one instance.</Description></RegistrationInfo>
  <Triggers>
    <LogonTrigger><Enabled>true</Enabled><UserId>$xmlSid</UserId></LogonTrigger>
    <CalendarTrigger><StartBoundary>$startBoundary</StartBoundary><Enabled>true</Enabled><Repetition><Interval>PT1M</Interval><Duration>P3650D</Duration><StopAtDurationEnd>false</StopAtDurationEnd></Repetition><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger>
    <EventTrigger><Enabled>true</Enabled><Subscription>$subscription</Subscription></EventTrigger>
  </Triggers>
  <Principals><Principal id="Author"><UserId>$xmlSid</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd><RestartOnIdle>false</RestartOnIdle></IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure><Interval>PT1M</Interval><Count>999</Count></RestartOnFailure>
  </Settings>
  <Actions Context="Author"><Exec><Command>$xmlPs</Command><Arguments>$xmlArgs</Arguments><WorkingDirectory>$programRoot</WorkingDirectory></Exec></Actions>
</Task>
"@

try{
  Register-ScheduledTask -TaskName $taskName -Xml $xml -Force|Out-Null
  if($legacy){
    Stop-ScheduledTask -TaskName $legacyTaskName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Unregister-ScheduledTask -TaskName $legacyTaskName -Confirm:$false -ErrorAction Stop
  }
  & powershell -NoProfile -ExecutionPolicy Bypass -File $installedGuardian -ConfigPath $installedConfig -StatePath $statePath -Once -SkipStabilityDelay
  if($LASTEXITCODE-ne0){throw 'GUARDIAN_INITIAL_RUN_FAILED'}
  Start-ScheduledTask -TaskName $taskName
  Start-Sleep -Seconds 4
  $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
  $state=Get-Content -LiteralPath $statePath -Raw|ConvertFrom-Json
  if(-not$state.runner_active){throw "RUNNER_NOT_ACTIVE_AFTER_GUARDIAN_INSTALL: $($state.last_error)"}
  $uninstallCommand=('powershell -NoProfile -ExecutionPolicy Bypass -File "{0}" -Uninstall -RestoreLegacyTask' -f $PSCommandPath)
  $result=[ordered]@{status='installed';installed_at=[DateTimeOffset]::UtcNow.ToString('o');guardian_installed=$true;scheduled_task_installed=$true;task_name=$taskName;task_state=[string]$task.State;portable_root=$state.portable_root;resolved_drive_letter=$state.resolved_drive_letter;volume_unique_id=$config.volume_unique_id;volume_serial=$config.volume_serial;marker_id=$config.marker_id;single_guardian_count=1;single_runner_count=1;legacy_task_removed=$true;rollback_xml=$legacyBackupPath;uninstall_command=$uninstallCommand;five_by_five_plan_applied=$false;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json $installResultPath $result
}catch{
  Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
  if(Test-Path -LiteralPath $legacyBackupPath){
    Register-ScheduledTask -TaskName $legacyTaskName -Xml (Get-Content -LiteralPath $legacyBackupPath -Raw) -Force|Out-Null
    Start-ScheduledTask -TaskName $legacyTaskName -ErrorAction SilentlyContinue
  }
  Write-Json $installResultPath ([ordered]@{status='rollback_restored';error=$_.Exception.Message;guardian_installed=$false;scheduled_task_installed=$false;final_ready=$false})
  throw
}

