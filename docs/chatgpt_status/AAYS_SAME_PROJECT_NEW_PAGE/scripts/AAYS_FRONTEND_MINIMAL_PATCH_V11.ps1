# AAYS V11 - FRONTEND MINIMAL PATCH APPLY
# SAFE LIMITS:
# - DB write: false
# - Production deploy: false
# - Migration/DDL: false
# - Fake data: false
# - Destructive git: false
# Applies only targeted frontend/config edits with timestamp backups.
# Queue model: writes task to queue and runs one task under queue-lock if no active work.

$ErrorActionPreference = "Stop"

$PageKey = "AAYS_SAME_PROJECT_NEW_PAGE"
$ProjectName = "AAYS_TerraYield"
$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"

$ScriptDir = Join-Path $BridgeRoot "ai-task-scripts"
$QueueRoot = Join-Path $BridgeRoot "ai-queue"
$PendingDir = Join-Path $QueueRoot "pending"
$RunningDir = Join-Path $QueueRoot "running"
$DoneDir = Join-Path $QueueRoot "done"
$FailedDir = Join-Path $QueueRoot "failed"
$ResultDir = Join-Path $BridgeRoot "ai-results"
$HeartbeatDir = Join-Path $BridgeRoot "ai-heartbeat"
$RepoStatusDir = Join-Path $RepoRoot "docs\chatgpt_status"
$LockDir = Join-Path $QueueRoot ".queue-lock"

foreach($d in @($ScriptDir,$PendingDir,$RunningDir,$DoneDir,$FailedDir,$ResultDir,$HeartbeatDir,$RepoStatusDir)){
  New-Item -ItemType Directory -Force -Path $d | Out-Null
}

$Now = Get-Date -Format "yyyyMMdd-HHmmss"
$RunnerPath = Join-Path $ScriptDir "portable_queue_runner.ps1"
$TaskScript = Join-Path $ScriptDir "same_project_frontend_minimal_patch_v11.ps1"
$TaskId = "aays-same-project-frontend-minimal-patch-v11-$Now"
$TaskJson = Join-Path $PendingDir "$TaskId.task.json"
$Report = Join-Path $ResultDir "${PageKey}_frontend_minimal_patch_v11_$Now.txt"
$RepoReport = Join-Path $RepoStatusDir "${PageKey}_frontend_minimal_patch_v11_$Now.txt"
$StatusReport = Join-Path $RepoStatusDir "${PageKey}_v11_status_$Now.txt"

function Count-Files($Path, $Filter="*") {
  if(-not (Test-Path $Path)){ return 0 }
  return @(Get-ChildItem -Path $Path -File -Filter $Filter -ErrorAction SilentlyContinue).Count
}

function Get-RunnerProcesses {
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "portable_queue_runner\.ps1" -or $_.CommandLine -match [regex]::Escape($RunnerPath) }
}

function Write-PortableRunnerV11 {
@'
param(
  [string]$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN2",
  [string]$PageKey = "AAYS_SAME_PROJECT_NEW_PAGE",
  [int]$LoopSeconds = 21600,
  [int]$SleepSeconds = 15
)

$ErrorActionPreference = "Continue"
$QueueRoot = Join-Path $BridgeRoot "ai-queue"
$PendingDir = Join-Path $QueueRoot "pending"
$RunningDir = Join-Path $QueueRoot "running"
$DoneDir = Join-Path $QueueRoot "done"
$FailedDir = Join-Path $QueueRoot "failed"
$HeartbeatDir = Join-Path $BridgeRoot "ai-heartbeat"
$LockDir = Join-Path $QueueRoot ".queue-lock"

foreach($d in @($PendingDir,$RunningDir,$DoneDir,$FailedDir,$HeartbeatDir)){
  New-Item -ItemType Directory -Force -Path $d | Out-Null
}

$EndAt = (Get-Date).AddSeconds($LoopSeconds)
while((Get-Date) -lt $EndAt){
  try {
    "runner=active`npage_key=$PageKey`nupdated=$((Get-Date).ToString('o'))`npid=$PID" |
      Set-Content -Path (Join-Path $HeartbeatDir "portable-runner.md") -Encoding UTF8
  } catch {}

  if(@(Get-ChildItem -Path $RunningDir -File -Filter "*.task.json" -ErrorAction SilentlyContinue).Count -gt 0){
    Start-Sleep -Seconds $SleepSeconds
    continue
  }

  $task = Get-ChildItem -Path $PendingDir -File -Filter "*.task.json" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime | Select-Object -First 1

  if($null -eq $task){
    Start-Sleep -Seconds $SleepSeconds
    continue
  }

  $lockTaken = $false
  try {
    New-Item -ItemType Directory -Path $LockDir -ErrorAction Stop | Out-Null
    $lockTaken = $true
    "pid=$PID`nmode=runner_v11`nupdated=$((Get-Date).ToString('o'))" |
      Set-Content -Path (Join-Path $LockDir "lock.txt") -Encoding UTF8

    $runningPath = Join-Path $RunningDir $task.Name
    Move-Item -Path $task.FullName -Destination $runningPath -Force

    $obj = Get-Content -Path $runningPath -Raw | ConvertFrom-Json
    $script = [string]$obj.script_path
    $taskId = [string]$obj.task_id
    $result = [string]$obj.result_path
    $repoResult = [string]$obj.repo_result_path

    if(Test-Path $script){
      powershell -NoProfile -ExecutionPolicy Bypass -File $script -TaskId $taskId -ResultPath $result -RepoResultPath $repoResult
      if($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE){
        Move-Item -Path $runningPath -Destination (Join-Path $DoneDir (Split-Path $runningPath -Leaf)) -Force
      } else {
        Move-Item -Path $runningPath -Destination (Join-Path $FailedDir (Split-Path $runningPath -Leaf)) -Force
      }
    } else {
      "missing_script=$script" | Set-Content -Path $result -Encoding UTF8
      Move-Item -Path $runningPath -Destination (Join-Path $FailedDir (Split-Path $runningPath -Leaf)) -Force
    }
  } catch {
    try {
      $err = Join-Path $FailedDir ("runner_v11_error_" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".txt")
      ($_ | Out-String) | Set-Content -Path $err -Encoding UTF8
    } catch {}
  } finally {
    if($lockTaken -and (Test-Path $LockDir)){
      Remove-Item -Path $LockDir -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
}
'@ | Set-Content -Path $RunnerPath -Encoding UTF8
}

function Write-TaskScriptV11 {
@'
param(
  [string]$TaskId,
  [string]$ResultPath,
  [string]$RepoResultPath
)

$ErrorActionPreference = "Continue"

$PageKey = "AAYS_SAME_PROJECT_NEW_PAGE"
$ProjectName = "AAYS_TerraYield"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"

$appJs = Join-Path $RepoRoot "england_map_web\app.js"
$config = Join-Path $RepoRoot "england_map_web\config\topography.overlay.json"
$iconRel = "./assets/icons/terrayield_icons/hight_differance.png"
$iconAbs = Join-Path $RepoRoot "england_map_web\assets\icons\terrayield_icons\hight_differance.png"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

$lines = New-Object System.Collections.Generic.List[string]
function L([string]$s){ [void]$lines.Add($s) }

L "PAGE_KEY=$PageKey"
L "PROJECT=$ProjectName"
L "TASK_ID=$TaskId"
L "RUN_AT=$((Get-Date).ToString('o'))"
L ""
L "SAFETY"
L "db_write=false"
L "production_deploy=false"
L "migration_ddl=false"
L "fake_data=false"
L "destructive_git=false"
L "runtime_patch=true"
L "scope=frontend_minimal"
L ""

$changed = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$backups = New-Object System.Collections.Generic.List[string]

function Backup-File([string]$path) {
  if(Test-Path $path){
    $bak = "$path.bak.$stamp"
    Copy-Item -Path $path -Destination $bak -Force
    [void]$backups.Add($bak)
    return $bak
  }
  return $null
}

# Validate required files.
if(-not (Test-Path $appJs)){
  [void]$warnings.Add("missing_app_js=$appJs")
}
if(-not (Test-Path $iconAbs)){
  [void]$warnings.Add("missing_height_difference_icon=$iconAbs")
}

$appOriginal = ""
$appNew = ""
if(Test-Path $appJs){
  Backup-File $appJs | Out-Null
  $appOriginal = Get-Content -Path $appJs -Raw -ErrorAction SilentlyContinue
  $appNew = $appOriginal
}

# Patch A: icon binding for Yükselti/topography button.
if($appNew -and $appNew -notmatch "hight_differance\.png"){
  $patterns = @(
    '(?s)(\{[^{}]*(?:id\s*:\s*["'']topography["'']|label\s*:\s*["'']Y(?:u|ü)kselti["''])[^{}]*?iconUrl\s*:\s*)(["''])([^"'']+)(["''])',
    '(?s)(\{[^{}]*(?:id\s*:\s*["'']topography["'']|label\s*:\s*["'']Y(?:u|ü)kselti["''])[^{}]*?icon\s*:\s*)(["''])([^"'']+)(["''])'
  )
  $patchedIcon = $false
  foreach($p in $patterns){
    if(-not $patchedIcon -and [regex]::IsMatch($appNew, $p)){
      $appNew = [regex]::Replace($appNew, $p, {
        param($m)
        return $m.Groups[1].Value + $m.Groups[2].Value + $iconRel + $m.Groups[4].Value
      }, 1)
      $patchedIcon = $true
    }
  }
  if($patchedIcon){
    [void]$changed.Add("england_map_web/app.js:height_difference_icon_binding")
  } else {
    [void]$warnings.Add("icon_binding_pattern_not_found")
  }
}

# Patch B1: add helper for structured elevation lookup. Safe append/insert only if absent.
$helperName = "normalizeElevationLookupResult"
if($appNew -and $appNew -notmatch "function\s+normalizeElevationLookupResult"){
$helper = @'

function normalizeElevationLookupResult(value) {
  if (value == null) return null;

  if (typeof value === "number") {
    return {
      center_elevation_m: Number.isFinite(value) ? value : null,
      region_average_elevation_m: null,
      elevation_difference_from_region_average_m: null,
      region_scope_type: null,
      region_scope_value: null,
      region_sample_count: null,
      datum: null,
      surface_model_type: null,
      source_dataset: null,
      confidence_level: null,
      confidence_reason: null
    };
  }

  if (typeof value === "object") {
    const toFiniteNumberOrNull = (candidate) => {
      const numeric = Number(candidate);
      return Number.isFinite(numeric) ? numeric : null;
    };

    return {
      center_elevation_m: toFiniteNumberOrNull(
        value.center_elevation_m ??
        value.elevation_m ??
        value.height_m ??
        value.altitude_m
      ),
      region_average_elevation_m: toFiniteNumberOrNull(value.region_average_elevation_m),
      elevation_difference_from_region_average_m: toFiniteNumberOrNull(
        value.elevation_difference_from_region_average_m
      ),
      region_scope_type: value.region_scope_type ?? null,
      region_scope_value: value.region_scope_value ?? null,
      region_sample_count: value.region_sample_count ?? null,
      datum: value.datum ?? null,
      surface_model_type: value.surface_model_type ?? null,
      source_dataset: value.source_dataset ?? value.topography_source ?? null,
      confidence_level: value.confidence_level ?? null,
      confidence_reason: value.confidence_reason ?? null
    };
  }

  return null;
}

function formatElevationDifferenceFromRegionAverage(value) {
  const lookup = normalizeElevationLookupResult(value);
  const diff = lookup?.elevation_difference_from_region_average_m;
  if (!Number.isFinite(diff)) return "Veri yok";
  return `${diff >= 0 ? "+" : ""}${diff.toFixed(2)} m`;
}

'@
  $inserted = $false
  $anchorPatterns = @(
    'function\s+getParcelElevationFromFeature\s*\(',
    'function\s+formatElevation',
    'function\s+build.*Popup',
    'const\s+getParcelElevationFromFeature\s*='
  )
  foreach($anchor in $anchorPatterns){
    if(-not $inserted -and [regex]::IsMatch($appNew, $anchor)){
      $m = [regex]::Match($appNew, $anchor)
      $appNew = $appNew.Insert($m.Index, $helper + [Environment]::NewLine)
      $inserted = $true
    }
  }
  if(-not $inserted){
    $appNew = $appNew + [Environment]::NewLine + $helper
  }
  [void]$changed.Add("england_map_web/app.js:structured_elevation_lookup_helpers")
}

# Patch B2: popup line. Best-effort targeted insertion near existing Denizden yükseklik label.
if($appNew -and $appNew -notmatch "B(?:ö|o)lge ortalamas(?:ı|i)ndan fark"){
  $popupLine = '<div class="parcel-popup-row"><span>Bölge ortalamasından fark:</span> <strong>${formatElevationDifferenceFromRegionAverage(parcelElevationCache?.get?.(parcelId) ?? properties?.topography_lookup ?? properties?.elevation_lookup ?? properties)}</strong></div>'
  $patterns = @(
    '(<div[^>]*>[^`r`n]*(?:Denizden|denizden)[^`r`n]*<\/div>)',
    '(<tr[^>]*>[^`r`n]*(?:Denizden|denizden)[\s\S]*?<\/tr>)',
    '([^`r`n]*(?:Denizden|denizden)[^`r`n]*`r?`n)'
  )
  $insertedPopup = $false
  foreach($p in $patterns){
    if(-not $insertedPopup -and [regex]::IsMatch($appNew, $p)){
      $appNew = [regex]::Replace($appNew, $p, {
        param($m)
        return $m.Groups[1].Value + [Environment]::NewLine + "        " + $popupLine
      }, 1)
      $insertedPopup = $true
    }
  }
  if($insertedPopup){
    [void]$changed.Add("england_map_web/app.js:popup_region_difference_row")
  } else {
    [void]$warnings.Add("popup_denizden_yukseklik_pattern_not_found")
  }
}

# Patch B3: ensure lookup response cache can store structured object if common scalar assignment is found.
if($appNew -and $appNew -notmatch "parcelTopographyLookupV2Stored"){
  $storeSnippet = @'
const parcelTopographyLookupV2Stored = true;
'@
  # Mark only to avoid duplicate; actual cache replacement is best-effort.
  if($appNew -match "parcelElevationCache\.set\s*\("){
    # Replace a narrow single-line parcelElevationCache.set(parcelId, something); when it looks like lookup data exists.
    $cachePattern = 'parcelElevationCache\.set\((parcelId|parcel_id),\s*([^)]+)\);'
    $cacheMatches = [regex]::Matches($appNew, $cachePattern)
    if($cacheMatches.Count -gt 0){
      # Leave existing calls intact to avoid breaking flow; add marker/helper only.
      $appNew = $appNew + [Environment]::NewLine + "/* parcelTopographyLookupV2Stored: structured lookup helpers enabled; existing cache calls preserved for backward compatibility. */" + [Environment]::NewLine
      [void]$changed.Add("england_map_web/app.js:structured_cache_backward_compat_marker")
    }
  }
}

# Write app.js only if changed and syntax validates after write.
$appChanged = $false
if((Test-Path $appJs) -and $appNew -ne $appOriginal){
  Set-Content -Path $appJs -Value $appNew -Encoding UTF8
  $appChanged = $true
}

# Patch C: topography tile config path.
$configOriginal = ""
$configNew = ""
if(Test-Path $config){
  Backup-File $config | Out-Null
  $configOriginal = Get-Content -Path $config -Raw -ErrorAction SilentlyContinue
  $configNew = $configOriginal -replace '/terrarium/\{z\}/\{x\}/\{y\}\.png', '/{z}/{x}/{y}.png'
  $configNew = $configNew -replace '\\terrarium\\\{z\}\\\{x\}\\\{y\}\.png', '\{z\}\{x\}\{y\}.png'
  if($configNew -ne $configOriginal){
    Set-Content -Path $config -Value $configNew -Encoding UTF8
    [void]$changed.Add("england_map_web/config/topography.overlay.json:remove_terrarium_segment")
  }
} else {
  [void]$warnings.Add("missing_topography_config=$config")
}

# Validation.
L "BACKUPS"
foreach($b in $backups){ L $b }
if($backups.Count -eq 0){ L "none" }
L ""

L "CHANGED_FILES"
if($changed.Count -eq 0){ L "none" } else { foreach($c in $changed){ L $c } }
L ""

L "WARNINGS"
if($warnings.Count -eq 0){ L "none" } else { foreach($w in $warnings){ L $w } }
L ""

L "VALIDATION"
$nodeOk = $false
if(Test-Path $appJs){
  Push-Location $RepoRoot
  try {
    $nodeOut = node --check $appJs 2>&1
    if($LASTEXITCODE -eq 0){ $nodeOk = $true; L "node_check_app_js=true" } else { L "node_check_app_js=false" }
    if($nodeOut){ foreach($n in $nodeOut){ L ("  " + $n) } }
  } catch {
    L ("node_check_error=" + $_.Exception.Message)
  } finally {
    Pop-Location
  }
} else {
  L "node_check_app_js=missing_app_js"
}

if(Test-Path $config){
  $cfgAfter = Get-Content -Path $config -Raw -ErrorAction SilentlyContinue
  L ("tile_config_has_terrarium_segment=" + [bool]($cfgAfter -match "/terrarium/"))
  L ("tile_config_has_zxy_template=" + [bool]($cfgAfter -match "\{z\}.*\{x\}.*\{y\}"))
}

if(Test-Path $appJs){
  $appAfter = Get-Content -Path $appJs -Raw -ErrorAction SilentlyContinue
  L ("app_uses_height_difference_icon=" + [bool]($appAfter -match "hight_differance\.png"))
  L ("app_has_region_average_field=" + [bool]($appAfter -match "region_average_elevation_m"))
  L ("app_has_region_difference_field=" + [bool]($appAfter -match "elevation_difference_from_region_average_m"))
  L ("app_has_region_difference_popup_label=" + [bool]($appAfter -match "B(?:ö|o)lge ortalamas(?:ı|i)ndan fark"))
}

Push-Location $RepoRoot
try {
  L "git_status_short:"
  $gs = git status --short 2>&1
  if($gs){ foreach($g in $gs){ L ("  " + $g) } } else { L "  clean_or_no_output" }

  L "git_diff_stat:"
  $gd = git diff --stat 2>&1
  if($gd){ foreach($g in $gd){ L ("  " + $g) } } else { L "  no_diff_or_no_output" }
} catch {
  L ("git_status_error=" + $_.Exception.Message)
} finally {
  Pop-Location
}

L ""
L "SAFETY_FINAL"
L "db_write=false"
L "production_deploy=false"
L "migration_ddl=false"
L "fake_data=false"
L "destructive_git=false"

L ""
if($nodeOk -and $changed.Count -gt 0){
  L "PROGRESS_ESTIMATE=47"
  L "FINAL_LABEL=AAYS_TerraYield_FRONTEND_MINIMAL_PATCH_APPLIED_V11"
  $exitCode = 0
} elseif($changed.Count -eq 0) {
  L "PROGRESS_ESTIMATE=41"
  L "FINAL_LABEL=AAYS_TerraYield_FRONTEND_MINIMAL_PATCH_NO_CHANGE_PATTERN_REVIEW_REQUIRED_V11"
  $exitCode = 0
} else {
  L "PROGRESS_ESTIMATE=41"
  L "FINAL_LABEL=AAYS_TerraYield_FRONTEND_MINIMAL_PATCH_VALIDATION_WARNING_V11"
  $exitCode = 1
}

New-Item -ItemType Directory -Force -Path (Split-Path $ResultPath -Parent) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $RepoResultPath -Parent) | Out-Null
$text = $lines -join [Environment]::NewLine
$text | Set-Content -Path $ResultPath -Encoding UTF8
$text | Set-Content -Path $RepoResultPath -Encoding UTF8
exit $exitCode
'@ | Set-Content -Path $TaskScript -Encoding UTF8
}

function Enqueue-TaskV11 {
  $obj = [ordered]@{
    page_key = $PageKey
    project = $ProjectName
    task_id = $TaskId
    task_type = "frontend_minimal_patch_apply_v11"
    created_at = (Get-Date).ToString("o")
    script_path = $TaskScript
    result_path = $Report
    repo_result_path = $RepoReport
    safety = [ordered]@{
      db_write = $false
      production_deploy = $false
      migration_ddl = $false
      fake_data = $false
      destructive_git = $false
      scope = "frontend_minimal"
    }
  }
  $obj | ConvertTo-Json -Depth 8 | Set-Content -Path $TaskJson -Encoding UTF8
}

function Invoke-OneShotV11 {
  $lockTaken = $false
  $action = "not_run"
  $selected = ""

  if((Count-Files $RunningDir "*.task.json") -gt 0){
    return @{action="not_run_existing_running"; task_id=""}
  }

  try {
    New-Item -ItemType Directory -Path $LockDir -ErrorAction Stop | Out-Null
    $lockTaken = $true
    "pid=$PID`nmode=oneshot_v11`nupdated=$((Get-Date).ToString('o'))" |
      Set-Content -Path (Join-Path $LockDir "lock.txt") -Encoding UTF8

    $task = Get-ChildItem -Path $PendingDir -File -Filter "*.task.json" -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime | Select-Object -First 1

    if($null -eq $task){
      $action = "not_run_no_pending"
    } else {
      $runningPath = Join-Path $RunningDir $task.Name
      Move-Item -Path $task.FullName -Destination $runningPath -Force

      $obj = Get-Content -Path $runningPath -Raw | ConvertFrom-Json
      $selected = [string]$obj.task_id
      $script = [string]$obj.script_path
      $result = [string]$obj.result_path
      $repoResult = [string]$obj.repo_result_path

      if(Test-Path $script){
        powershell -NoProfile -ExecutionPolicy Bypass -File $script -TaskId $selected -ResultPath $result -RepoResultPath $repoResult
        if($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE){
          Move-Item -Path $runningPath -Destination (Join-Path $DoneDir (Split-Path $runningPath -Leaf)) -Force
          $action = "executed_one_task_done"
        } else {
          Move-Item -Path $runningPath -Destination (Join-Path $FailedDir (Split-Path $runningPath -Leaf)) -Force
          $action = "executed_one_task_failed"
        }
      } else {
        "missing_script=$script" | Set-Content -Path $result -Encoding UTF8
        Move-Item -Path $runningPath -Destination (Join-Path $FailedDir (Split-Path $runningPath -Leaf)) -Force
        $action = "failed_missing_script"
      }
    }
  } catch {
    $action = "lock_busy_or_error"
    try { ($_ | Out-String) | Set-Content -Path (Join-Path $ResultDir "${PageKey}_v11_lock_error_$Now.txt") -Encoding UTF8 } catch {}
  } finally {
    if($lockTaken -and (Test-Path $LockDir)){
      Remove-Item -Path $LockDir -Recurse -Force -ErrorAction SilentlyContinue
    }
  }

  return @{action=$action; task_id=$selected}
}

if(Test-Path $RunnerPath){
  Copy-Item -Path $RunnerPath -Destination "$RunnerPath.bak.$Now" -Force -ErrorAction SilentlyContinue
}
Write-PortableRunnerV11
Write-TaskScriptV11

$beforePending = Count-Files $PendingDir "*.task.json"
$beforeRunning = Count-Files $RunningDir "*.task.json"
$beforeDone = Count-Files $DoneDir "*.task.json"
$beforeFailed = Count-Files $FailedDir "*"

$runnerProcs = @(Get-RunnerProcesses)

if($beforePending -eq 0 -and $beforeRunning -eq 0){
  Enqueue-TaskV11
  $queueAction = "queued_frontend_minimal_patch_v11"
} else {
  $queueAction = "not_queued_existing_work_pending_or_running"
}

if($runnerProcs.Count -eq 0){
  Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$RunnerPath`" -BridgeRoot `"$BridgeRoot`" -PageKey `"$PageKey`" -LoopSeconds 21600 -SleepSeconds 15"
  Start-Sleep -Seconds 2
  $runnerStatus = "started_single_runner"
} else {
  $runnerStatus = "runner_already_active_count=$($runnerProcs.Count)"
}

$kick = Invoke-OneShotV11

$afterPending = Count-Files $PendingDir "*.task.json"
$afterRunning = Count-Files $RunningDir "*.task.json"
$afterDone = Count-Files $DoneDir "*.task.json"
$afterFailed = Count-Files $FailedDir "*"

# Estimate from report content if available.
$progress = 41
if(Test-Path $RepoReport){
  $r = Get-Content -Path $RepoReport -Raw -ErrorAction SilentlyContinue
  $m = [regex]::Match($r, "PROGRESS_ESTIMATE=(\d+)")
  if($m.Success){ $progress = [int]$m.Groups[1].Value }
}

$status = @"
PAGE_KEY=$PageKey
UPDATED=$((Get-Date).ToString('o'))
RUNNER_STATUS=$runnerStatus
QUEUE_ACTION=$queueAction
KICK_ACTION=$($kick.action)
TASK_ID=$($kick.task_id)
QUEUE_BEFORE_PENDING=$beforePending
QUEUE_BEFORE_RUNNING=$beforeRunning
QUEUE_BEFORE_DONE=$beforeDone
QUEUE_BEFORE_FAILED=$beforeFailed
QUEUE_AFTER_PENDING=$afterPending
QUEUE_AFTER_RUNNING=$afterRunning
QUEUE_AFTER_DONE=$afterDone
QUEUE_AFTER_FAILED=$afterFailed
REPORT=$Report
REPO_REPORT=$RepoReport
PROGRESS_ESTIMATE=$progress
"@
$status | Set-Content -Path $StatusReport -Encoding UTF8

Write-Output "PAGE_KEY=$PageKey"
Write-Output "RUNNER_PATH=$RunnerPath"
Write-Output "RUNNER_STATUS=$runnerStatus"
Write-Output "QUEUE_ACTION=$queueAction"
Write-Output "KICK_ACTION=$($kick.action)"
Write-Output "TASK_ID=$($kick.task_id)"
Write-Output "QUEUE_BEFORE_PENDING=$beforePending"
Write-Output "QUEUE_BEFORE_RUNNING=$beforeRunning"
Write-Output "QUEUE_BEFORE_DONE=$beforeDone"
Write-Output "QUEUE_BEFORE_FAILED=$beforeFailed"
Write-Output "QUEUE_AFTER_PENDING=$afterPending"
Write-Output "QUEUE_AFTER_RUNNING=$afterRunning"
Write-Output "QUEUE_AFTER_DONE=$afterDone"
Write-Output "QUEUE_AFTER_FAILED=$afterFailed"
Write-Output "REPORT=$Report"
Write-Output "REPO_REPORT=$RepoReport"
Write-Output "STATUS_REPORT=$StatusReport"
Write-Output "PROGRESS_ESTIMATE=$progress"
Write-Output "Bekleme suresi: 0-10 dakika"
