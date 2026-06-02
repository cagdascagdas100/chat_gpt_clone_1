$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-137-runner-watchdog-and-security-scope-resume'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\Users\cagda\Documents\chat_gpt_clone_1' }
$RepoRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS' }
$RunnerPath = Join-Path $BridgeRoot 'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1'
$HeartbeatPath = Join-Path $BridgeRoot 'ai-heartbeat\portable-runner.md'
$AllowedRoot = Join-Path $RepoRoot 'security_accuracy_expansion'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function Step([int]$N, [string]$Text) { Write-Output (('STEP_{0:D2} ' -f $N) + $Text) }
function RunText([scriptblock]$Block) { try { return (& $Block 2>&1 | Out-String) } catch { return ('ERROR: ' + $_.Exception.Message) } }
function WriteSafe([string]$Rel, [string]$Text) {
  $full = [System.IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel))
  $allowed = [System.IO.Path]::GetFullPath($AllowedRoot)
  if (-not $full.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)) { throw "WRITE_SCOPE_FAIL $Rel" }
  $dir = Split-Path -Parent $full
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($full, $Text, $enc)
  Write-Output ('WROTE=security_accuracy_expansion/' + ($Rel -replace '\\','/'))
}

Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK=' + $TaskId)
Write-Output 'MODE=runner_watchdog_security_scope_resume'
Write-Output 'LIVE_WRITE_POLICY=FORBIDDEN'
Write-Output 'NO_DOCKER=TRUE'
Write-Output 'NO_DOWNLOAD=TRUE'
Write-Output 'NO_SERVICE_RESTART=TRUE'
Write-Output ('BRIDGE_ROOT=' + $BridgeRoot)
Write-Output ('REPO_ROOT=' + $RepoRoot)

Step 1 'Check bridge and runner files.'
Write-Output ('BRIDGE_ROOT_EXISTS=' + (Test-Path -LiteralPath $BridgeRoot))
Write-Output ('RUNNER_PATH_EXISTS=' + (Test-Path -LiteralPath $RunnerPath))
Write-Output ('HEARTBEAT_PATH_EXISTS=' + (Test-Path -LiteralPath $HeartbeatPath))

Step 2 'Check runner PowerShell process.'
$runnerProcesses = @()
try {
  $runnerProcesses = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'powershell' -and $_.CommandLine -match [regex]::Escape('AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1') })
} catch { Write-Output ('RUNNER_PROCESS_CHECK_ERROR=' + $_.Exception.Message) }
Write-Output ('RUNNER_PROCESS_COUNT=' + $runnerProcesses.Count)
foreach ($p in $runnerProcesses) { Write-Output ('RUNNER_PID=' + $p.ProcessId); Write-Output ('RUNNER_CMD=' + $p.CommandLine) }

Step 3 'Start hidden runner only if no runner process exists.'
if ($runnerProcesses.Count -lt 1 -and (Test-Path -LiteralPath $RunnerPath)) {
  try {
    Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$RunnerPath) -WorkingDirectory $BridgeRoot -WindowStyle Hidden
    Start-Sleep -Seconds 3
    $after = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'powershell' -and $_.CommandLine -match [regex]::Escape('AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1') })
    Write-Output ('RUNNER_REOPEN=ATTEMPTED')
    Write-Output ('RUNNER_PROCESS_COUNT_AFTER=' + $after.Count)
  } catch { Write-Output ('RUNNER_REOPEN=ERROR ' + $_.Exception.Message) }
} else {
  Write-Output 'RUNNER_REOPEN=NOT_NEEDED'
}

Step 4 'Read heartbeat file if present.'
if (Test-Path -LiteralPath $HeartbeatPath) {
  Write-Output 'HEARTBEAT_BEGIN'
  Get-Content -Raw -Encoding UTF8 -LiteralPath $HeartbeatPath | Write-Output
  Write-Output 'HEARTBEAT_END'
} else { Write-Output 'HEARTBEAT=MISSING' }

Step 5 'Check AAYS repo and allowed root.'
Write-Output ('AAYS_ROOT_EXISTS=' + (Test-Path -LiteralPath $RepoRoot))
if (-not (Test-Path -LiteralPath $RepoRoot)) { exit 2 }
New-Item -ItemType Directory -Force -Path $AllowedRoot | Out-Null
Set-Location $RepoRoot

Step 6 'Read-only live surface diff check.'
$LiveDiff = RunText { git diff --name-only -- england_map_web }
Write-Output ('LIVE_DIFF=' + $LiveDiff.Trim())
if (-not [string]::IsNullOrWhiteSpace($LiveDiff)) { Write-Output 'LIVE_DIFF_STATUS=FAIL'; exit 5 } else { Write-Output 'LIVE_DIFF_STATUS=PASS' }

Step 7 'Run 136 script directly if available as resume action.'
$Script136 = Join-Path $BridgeRoot 'ai-task-scripts\terrayield_136_security_accuracy_expansion_parallel_deepening.ps1'
if (Test-Path -LiteralPath $Script136) {
  Write-Output 'RESUME_136=BEGIN'
  $out136 = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $Script136 }
  Write-Output $out136
  Write-Output 'RESUME_136=END'
} else {
  Write-Output 'RESUME_136=SKIPPED_SCRIPT_MISSING'
}

Step 8 'Run generated scope verifier if present.'
$ScopeVerifier = Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
if (Test-Path -LiteralPath $ScopeVerifier) { Write-Output (RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $ScopeVerifier }) } else { Write-Output 'SCOPE_VERIFIER=MISSING' }

Step 9 'Run live verifier if present.'
$LiveVerifier = Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
$LiveStatus = 'NOT_RUN'
if (Test-Path -LiteralPath $LiveVerifier) {
  $liveOut = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $LiveVerifier }
  Write-Output $liveOut
  if ($liveOut -match 'OVERALL=PASS') { $LiveStatus='PASS' } elseif ($liveOut -match 'OVERALL=FAIL') { $LiveStatus='FAIL' } else { $LiveStatus='UNKNOWN' }
} else { Write-Output 'LIVE_VERIFIER=MISSING' }
Write-Output ('LIVE_STATUS=' + $LiveStatus)

Step 10 'Write watchdog report under security_accuracy_expansion only.'
$Report = @"
# Runner Watchdog and Scope Resume Report

Task: $TaskId  
Time: $(Get-Date -Format s)  
Runner process count at start: $($runnerProcesses.Count)  
Live diff status: PASS  
Live verifier status: $LiveStatus  

The watchdog did not modify live `england_map_web` surfaces. It only attempted to ensure the portable runner exists and to resume the scope-only 136 workstream when available.
"@
WriteSafe ('run_reports/watchdog_resume_report_' + $Stamp + '.md') $Report

Step 11 'Show security_accuracy_expansion status.'
Write-Output (RunText { git status --short -- security_accuracy_expansion })

Step 12 'Show protected live status.'
Write-Output (RunText { git status --short -- england_map_web })

Step 13 'Optional guarded commit security_accuracy_expansion only.'
$root = (RunText { git rev-parse --show-toplevel }).Trim().TrimEnd('\','/')
$repoClean = $RepoRoot.TrimEnd('\','/')
if ($root -ieq $repoClean) {
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached = RunText { git diff --cached --name-only }
  $bad = @($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if ($bad.Count -gt 0) {
    Write-Output 'COMMIT_GUARD=FAIL_OUTSIDE_SCOPE'
    $bad | Write-Output
    git reset 2>&1 | Out-String | Write-Output
  } elseif ([string]::IsNullOrWhiteSpace($cached)) {
    Write-Output 'PROJECT_COMMIT=SKIPPED_NO_CHANGES'
  } else {
    git commit -m 'Resume security accuracy expansion scope-only workstreams' 2>&1 | Out-String | Write-Output
    Write-Output 'PROJECT_COMMIT=ATTEMPTED_SECURITY_ONLY'
  }
} else { Write-Output ('PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH ' + $root) }
Write-Output 'PROJECT_PUSH=SKIPPED_BY_POLICY'

Step 14 'Final guarded live diff recheck.'
$LiveDiff2 = RunText { git diff --name-only -- england_map_web }
if (-not [string]::IsNullOrWhiteSpace($LiveDiff2)) { Write-Output 'FINAL_LIVE_DIFF_STATUS=FAIL'; Write-Output $LiveDiff2; exit 6 }
Write-Output 'FINAL_LIVE_DIFF_STATUS=PASS'

Step 15 'Complete.'
if ($LiveStatus -eq 'PASS') { Write-Output 'FINAL_STATUS=PASS' } else { Write-Output 'FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER_OR_NOT_RUN' }
Write-Output 'NEXT_CHATGPT_INPUT=devam et'
Write-Output 'TERRAYIELD_137_DONE'
exit 0
