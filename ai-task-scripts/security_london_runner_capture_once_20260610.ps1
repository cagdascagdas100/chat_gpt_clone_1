$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Runner = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $BridgeRoot "ai-results\security_london_source_restore_runner_$Stamp.txt"
$Latest = Join-Path $BridgeRoot 'ai-results\security_london_source_restore_runner_latest.txt'
$Expected = @(
  'ai-results\security_london_source_restore_latest.json',
  'ai-results\security_london_source_restore_latest.md',
  'docs\chatgpt_status\security_london_source_restore_status_20260609.md'
)

New-Item -ItemType Directory -Force -Path (Join-Path $BridgeRoot 'ai-results') | Out-Null
Set-Content -Path $Report -Encoding UTF8 -Value "SECURITY_LONDON_RUNNER_CAPTURE_ONCE $Stamp"

function Add-Log($Text) {
  $Text | Tee-Object -FilePath $Report -Append
}

Add-Log "BridgeRoot=$BridgeRoot"
Add-Log "Runner=$Runner"
Add-Log "CurrentDir before cd=$(Get-Location)"

Set-Location $BridgeRoot
Add-Log "CurrentDir after cd=$(Get-Location)"

Add-Log '=== git sync ==='
git fetch origin main 2>&1 | Tee-Object -FilePath $Report -Append
git reset --hard origin/main 2>&1 | Tee-Object -FilePath $Report -Append

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
  Get-Content '.last-task-id' -Raw 2>&1 | Tee-Object -FilePath $Report -Append
  Remove-Item '.last-task-id' -Force
  Add-Log 'CLEARED .last-task-id'
}

Add-Log '=== current-task ==='
if (Test-Path 'ai-tasks\current-task.json') {
  Get-Content 'ai-tasks\current-task.json' -Raw 2>&1 | Tee-Object -FilePath $Report -Append
} else {
  Add-Log 'MISSING ai-tasks\current-task.json'
}

Add-Log '=== run portable queue runner ==='
if (Test-Path $Runner) {
  powershell -ExecutionPolicy Bypass -File $Runner 2>&1 | Tee-Object -FilePath $Report -Append
  Add-Log "RUNNER_EXIT_CODE=$LASTEXITCODE"
} else {
  Add-Log 'RUNNER_MISSING'
}

Add-Log '=== expected outputs ==='
foreach ($p in $Expected) {
  if (Test-Path $p) { Add-Log "EXISTS $p size=$((Get-Item $p).Length)" } else { Add-Log "MISSING $p" }
}

Copy-Item $Report $Latest -Force
Add-Log "LATEST_REPORT=$Latest"

Add-Log '=== git push outputs ==='
git add `
  "ai-results/security_london_source_restore_runner_$Stamp.txt" `
  'ai-results/security_london_source_restore_runner_latest.txt' `
  'ai-results/security_london_source_restore_latest.json' `
  'ai-results/security_london_source_restore_latest.md' `
  'docs/chatgpt_status/security_london_source_restore_status_20260609.md' 2>&1 | Tee-Object -FilePath $Report -Append

git commit -m "Add security London source restore runner output $Stamp" 2>&1 | Tee-Object -FilePath $Report -Append
git push origin main 2>&1 | Tee-Object -FilePath $Report -Append

Add-Log 'DONE security London runner capture once'
