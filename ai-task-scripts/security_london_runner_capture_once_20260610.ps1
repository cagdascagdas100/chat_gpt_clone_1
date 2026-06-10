$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Runner = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportRel = "ai-results/security_london_source_restore_runner_$Stamp.txt"
$LatestRel = 'ai-results/security_london_source_restore_runner_latest.txt'
$Report = Join-Path $BridgeRoot ($ReportRel -replace '/', '\')
$Latest = Join-Path $BridgeRoot ($LatestRel -replace '/', '\')
$TaskRel = 'ai-tasks/current-task.json'
$ExpectedRel = @(
  'ai-results/security_london_source_restore_latest.json',
  'ai-results/security_london_source_restore_latest.md',
  'docs/chatgpt_status/security_london_source_restore_status_20260609.md'
)

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
New-Item -ItemType Directory -Force -Path (Join-Path $BridgeRoot 'ai-results') | Out-Null

function Clean-Text([object]$Value) {
  if ($null -eq $Value) { return '' }
  $s = [string]$Value
  $s = $s -replace "[\x00-\x08\x0B\x0C\x0E-\x1F]", '?'
  return $s
}

function Add-Log([object]$Value) {
  $line = Clean-Text $Value
  [System.IO.File]::AppendAllText($Report, $line + [Environment]::NewLine, $Utf8NoBom)
  Write-Host $line
}

function Run-Logged([string]$Label, [scriptblock]$Block) {
  Add-Log "=== $Label ==="
  try {
    & $Block 2>&1 | ForEach-Object { Add-Log $_ }
    Add-Log "$Label EXIT=$LASTEXITCODE"
  } catch {
    Add-Log "$Label EXCEPTION=$($_.Exception.Message)"
  }
}

function Add-ExistingRel([string[]]$Items) {
  foreach ($rel in ($Items | Select-Object -Unique)) {
    $local = Join-Path $BridgeRoot ($rel -replace '/', '\')
    if (Test-Path $local) {
      Run-Logged "git add $rel" { git add $rel }
      Add-Log "GIT_ADD_EXISTING $rel"
    } else {
      Add-Log "SKIP_MISSING $rel"
    }
  }
}

[System.IO.File]::WriteAllText($Report, "SECURITY_LONDON_RUNNER_CAPTURE_ONCE_FALLBACK_UTF8 $Stamp" + [Environment]::NewLine, $Utf8NoBom)
Add-Log "BridgeRoot=$BridgeRoot"
Add-Log "Runner=$Runner"
Add-Log "CurrentDir before cd=$(Get-Location)"

if (-not (Test-Path $BridgeRoot)) {
  Add-Log "BRIDGE_ROOT_MISSING=$BridgeRoot"
  Copy-Item $Report $Latest -Force
  exit 2
}

Set-Location $BridgeRoot
Add-Log "CurrentDir after cd=$(Get-Location)"

Run-Logged 'git sync' { git fetch origin main; git reset --hard origin/main }

Add-Log '=== local runner contract files ==='
@(
  '.last-task-id',
  'ai-tasks\current-task.json',
  'ai-task-scripts\portable_queue_runner.ps1',
  'ai-task-scripts\security_asayis_london_source_restore_20260609.ps1'
) | ForEach-Object {
  if (Test-Path $_) { Add-Log "EXISTS $_ size=$((Get-Item $_).Length)" } else { Add-Log "MISSING $_" }
}

if (Test-Path '.last-task-id') {
  Add-Log '=== clear .last-task-id ==='
  Get-Content '.last-task-id' -Raw 2>&1 | ForEach-Object { Add-Log $_ }
  Remove-Item '.last-task-id' -Force
  Add-Log 'CLEARED .last-task-id'
}

Add-Log '=== current-task ==='
$TaskObj = $null
if (Test-Path 'ai-tasks\current-task.json') {
  $TaskRaw = Get-Content 'ai-tasks\current-task.json' -Raw
  Add-Log $TaskRaw
  try { $TaskObj = $TaskRaw | ConvertFrom-Json } catch { Add-Log "TASK_JSON_PARSE_ERROR=$($_.Exception.Message)" }
} else {
  Add-Log 'MISSING ai-tasks\current-task.json'
}

Add-Log '=== run portable queue runner ==='
$RunnerExit = $null
if (Test-Path $Runner) {
  powershell -ExecutionPolicy Bypass -File $Runner 2>&1 | ForEach-Object { Add-Log $_ }
  $RunnerExit = $LASTEXITCODE
  Add-Log "RUNNER_EXIT_CODE=$RunnerExit"
} else {
  Add-Log 'RUNNER_MISSING'
}

$NeedFallback = $false
foreach ($p in $ExpectedRel) {
  $local = Join-Path $BridgeRoot ($p -replace '/', '\')
  if (-not (Test-Path $local)) { $NeedFallback = $true }
}

if ($NeedFallback -and $TaskObj -ne $null) {
  Add-Log '=== fallback direct current-task script execution ==='
  $WorkDir = [string]$TaskObj.working_directory
  $ScriptPath = [string]$TaskObj.script_path
  if ([string]::IsNullOrWhiteSpace($WorkDir)) { $WorkDir = $BridgeRoot }
  if ([string]::IsNullOrWhiteSpace($ScriptPath)) { Add-Log 'FALLBACK_NO_SCRIPT_PATH' }
  else {
    $ResolvedScript = $ScriptPath
    if (-not [System.IO.Path]::IsPathRooted($ResolvedScript)) {
      $ResolvedScript = Join-Path $BridgeRoot ($ResolvedScript -replace '/', '\')
    }
    Add-Log "FALLBACK_WORKDIR=$WorkDir"
    Add-Log "FALLBACK_SCRIPT=$ResolvedScript"
    if (Test-Path $ResolvedScript) {
      Push-Location $WorkDir
      powershell -NoProfile -ExecutionPolicy Bypass -File $ResolvedScript 2>&1 | ForEach-Object { Add-Log $_ }
      $FallbackExit = $LASTEXITCODE
      Pop-Location
      Add-Log "FALLBACK_EXIT_CODE=$FallbackExit"
    } else {
      Add-Log "FALLBACK_SCRIPT_MISSING=$ResolvedScript"
    }
  }
} else {
  Add-Log "FALLBACK_SKIPPED NeedFallback=$NeedFallback TaskObjPresent=$($TaskObj -ne $null)"
}

Add-Log '=== expected outputs ==='
$ExistingRel = @($ReportRel, $LatestRel)
foreach ($p in $ExpectedRel) {
  $local = Join-Path $BridgeRoot ($p -replace '/', '\')
  if (Test-Path $local) {
    Add-Log "EXISTS $p size=$((Get-Item $local).Length)"
    $ExistingRel += $p
  } else {
    Add-Log "MISSING $p"
  }
}

Copy-Item $Report $Latest -Force
Add-Log "LATEST_REPORT=$Latest"
Add-Log '=== git push existing outputs only ==='
Add-ExistingRel $ExistingRel
Copy-Item $Report $Latest -Force
Run-Logged "git add latest report" { git add $LatestRel }
Run-Logged "git commit" { git commit -m "Add security London source restore runner output $Stamp" }
Run-Logged "git push" { git push origin main }
Copy-Item $Report $Latest -Force
Add-Log 'DONE security London runner capture once fallback utf8'
