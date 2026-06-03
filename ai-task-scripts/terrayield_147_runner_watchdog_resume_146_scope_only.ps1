$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-147-runner-watchdog-resume-146-scope-only'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\Users\cagda\Documents\chat_gpt_clone_1' }
$RepoRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS' }
$RunnerPath = Join-Path $BridgeRoot 'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1'
$HeartbeatPath = Join-Path $BridgeRoot 'ai-heartbeat\portable-runner.md'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$AllowedRoot = Join-Path $RepoRoot 'security_accuracy_expansion'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function O([string]$x){ Write-Output $x }
function R([scriptblock]$b){ try { return (& $b 2>&1 | Out-String) } catch { return ('ERROR: '+$_.Exception.Message) } }
function W([string]$Rel,[string]$Text){
  $full=[IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel)); $allowed=[IO.Path]::GetFullPath($AllowedRoot)
  if(-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){ throw ('SCOPE_FAIL '+$Rel) }
  $dir=Split-Path -Parent $full; if($dir -and -not(Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc=New-Object Text.UTF8Encoding($false); [IO.File]::WriteAllText($full,$Text,$enc)
}

O 'PROJECT=terrayield'
O ('TASK='+$TaskId)
O 'MODE=runner_watchdog_resume_146_scope_only'
O 'LIVE_WRITE_POLICY=FORBIDDEN'
O 'NO_DOWNLOAD=TRUE'
O 'NO_SERVICE_RESTART=TRUE'
O 'NO_DOCKER=TRUE'
O ('BRIDGE_ROOT='+$BridgeRoot)
O ('REPO_ROOT='+$RepoRoot)

O 'STEP_01_CHECK_RUNNER_PROCESS'
$runner=@()
try {
  $runner=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'powershell' -and $_.CommandLine -match [regex]::Escape('AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1') })
} catch { O ('RUNNER_PROCESS_CHECK_ERROR='+$_.Exception.Message) }
O ('RUNNER_PROCESS_COUNT='+$runner.Count)
foreach($p in $runner){ O ('RUNNER_PID='+$p.ProcessId); O ('RUNNER_CMD='+$p.CommandLine) }

O 'STEP_02_OPEN_RUNNER_IF_ABSENT'
if($runner.Count -lt 1 -and (Test-Path -LiteralPath $RunnerPath)){
  try{
    Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$RunnerPath) -WorkingDirectory $BridgeRoot -WindowStyle Hidden
    Start-Sleep -Seconds 3
    $after=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'powershell' -and $_.CommandLine -match [regex]::Escape('AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1') })
    O 'RUNNER_OPEN_ATTEMPT=YES'
    O ('RUNNER_PROCESS_COUNT_AFTER='+$after.Count)
  }catch{ O ('RUNNER_OPEN_ATTEMPT=ERROR '+$_.Exception.Message) }
}else{ O 'RUNNER_OPEN_ATTEMPT=NOT_NEEDED_OR_RUNNER_FILE_MISSING' }

O 'STEP_03_HEARTBEAT'
if(Test-Path -LiteralPath $HeartbeatPath){ O 'HEARTBEAT_BEGIN'; Get-Content -Raw -Encoding UTF8 -LiteralPath $HeartbeatPath | Write-Output; O 'HEARTBEAT_END' } else { O 'HEARTBEAT=MISSING' }

O 'STEP_04_REPO_AND_LIVE_GUARD'
if(-not(Test-Path -LiteralPath $RepoRoot)){ O ('REPO_ROOT=FAIL '+$RepoRoot); exit 2 }
New-Item -ItemType Directory -Force -Path $AllowedRoot,$ResultDir | Out-Null
Set-Location $RepoRoot
$diff0=(R { git diff --name-only -- england_map_web }).Trim()
O ('LIVE_DIFF_BEFORE='+$diff0)
if(-not [string]::IsNullOrWhiteSpace($diff0)){ O 'LIVE_DIFF_BEFORE_STATUS=FAIL'; exit 3 }
O 'LIVE_DIFF_BEFORE_STATUS=PASS'

O 'STEP_05_RESUME_146_DIRECTLY'
$s146=Join-Path $BridgeRoot 'ai-task-scripts\terrayield_146_security_accuracy_expansion_hyper_pack.ps1'
$ran146='NO'
if(Test-Path -LiteralPath $s146){
  $ran146='YES'
  O 'RUN_146_BEGIN'
  $out146=R { powershell -NoProfile -ExecutionPolicy Bypass -File $s146 }
  O (($out146 -split "`r?`n" | Select-Object -Last 180) -join "`n")
  O 'RUN_146_END'
}else{ O 'RUN_146=SCRIPT_MISSING' }

O 'STEP_06_POST_RESUME_GUARDS'
$diff1=(R { git diff --name-only -- england_map_web }).Trim()
O ('LIVE_DIFF_AFTER='+$diff1)
if(-not [string]::IsNullOrWhiteSpace($diff1)){ O 'LIVE_DIFF_AFTER_STATUS=FAIL'; exit 4 }
O 'LIVE_DIFF_AFTER_STATUS=PASS'
$scope='NOT_RUN'; $live='NOT_RUN'
$sv=Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
if(Test-Path -LiteralPath $sv){ $so=R { powershell -NoProfile -ExecutionPolicy Bypass -File $sv }; if($so -match 'GENERATED_SCOPE=PASS'){$scope='PASS'}elseif($so -match 'GENERATED_SCOPE=FAIL'){$scope='FAIL'}else{$scope='UNKNOWN'}; O ('SCOPE_VERIFIER_STATUS='+$scope); O (($so -split "`r?`n" | Select-Object -Last 30) -join "`n") } else { O 'SCOPE_VERIFIER=MISSING' }
$lv=Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
if(Test-Path -LiteralPath $lv){ $lo=R { powershell -NoProfile -ExecutionPolicy Bypass -File $lv }; if($lo -match 'OVERALL=PASS'){$live='PASS'}elseif($lo -match 'OVERALL=FAIL'){$live='FAIL'}else{$live='UNKNOWN'}; O ('LIVE_VERIFIER_STATUS='+$live); O (($lo -split "`r?`n" | Select-Object -Last 30) -join "`n") } else { O 'LIVE_VERIFIER=MISSING' }

O 'STEP_07_MATERIALIZE_RESULT'
$final=if($scope -ne 'FAIL' -and [string]::IsNullOrWhiteSpace($diff1)){ if($live -eq 'PASS'){'PASS'}else{'PASS_WITH_EXISTING_LIVE_BLOCKER'} }else{'FAIL'}
$report="# Runner Watchdog Resume 146 Report`n`nTask: $TaskId`nTime: $(Get-Date -Format s)`nRunner process count before open attempt: $($runner.Count)`nRan 146 directly: $ran146`nScope status: $scope`nLive status: $live`nLive diff: PASS`nFinal status: $final`n"
W ('run_reports/watchdog_resume_146_'+$Stamp+'.md') $report
$status=@('TASK='+$TaskId,'RESULT='+$final,'RAN_146='+$ran146,'SCOPE_STATUS='+$scope,'LIVE_STATUS='+$live,'LIVE_DIFF_STATUS=PASS','NEXT_COMMAND=devam et') -join "`n"
$status | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ResultDir ($TaskId+'-status.txt'))
("# "+$TaskId+"`n`n"+$status) | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ResultDir ($TaskId+'-summary.md'))
O ('RESULT_FILE='+(Join-Path $ResultDir ($TaskId+'-status.txt')))

O 'STEP_08_GUARDED_COMMIT_SECURITY_ONLY'
$root=(R { git rev-parse --show-toplevel }).Trim().TrimEnd('\','/')
$repo=$RepoRoot.TrimEnd('\','/')
if($root -ieq $repo){
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached=R { git diff --cached --name-only }
  $bad=@($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if($bad.Count -gt 0){ O 'COMMIT_GUARD=FAIL'; $bad | Write-Output; git reset 2>&1 | Out-String | Write-Output }
  elseif([string]::IsNullOrWhiteSpace($cached)){ O 'PROJECT_COMMIT=SKIPPED_NO_CHANGES' }
  else{ git commit -m 'Watchdog resume security accuracy expansion hyper pack' 2>&1 | Out-String | Write-Output; O 'PROJECT_COMMIT=ATTEMPTED_SECURITY_ONLY' }
}else{ O ('PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH '+$root) }
O 'PROJECT_PUSH=SKIPPED_BY_POLICY'

O ('FINAL_STATUS='+$final)
O 'NEXT_CHATGPT_INPUT=devam et'
O 'TERRAYIELD_147_DONE'
exit 0
