param(
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
)

$ErrorActionPreference = 'Continue'
$StartedAt = (Get-Date).ToString('s')
$ScriptPath = $MyInvocation.MyCommand.Path
$AutomationRoot = Split-Path -Parent $ScriptPath
$PageRoot = Split-Path -Parent $AutomationRoot

function Find-RepoRoot([string]$StartPath){
  $p = (Resolve-Path $StartPath).Path
  for($i=0; $i -lt 8; $i++){
    if(Test-Path (Join-Path $p '.git')){ return $p }
    if(Test-Path (Join-Path $p 'docs')){ if(Test-Path (Join-Path $p 'docs\chatgpt_status')){ return $p } }
    $parent = Split-Path -Parent $p
    if([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $p){ break }
    $p = $parent
  }
  return (Resolve-Path (Join-Path $StartPath '..\..\..')).Path
}

$RepoRoot = Find-RepoRoot $PageRoot
$Reports = Join-Path $PageRoot 'reports'
$Status = Join-Path $PageRoot 'status'
$Heartbeat = Join-Path $PageRoot 'heartbeat'
$RunnerOutput = Join-Path $PageRoot 'runner_output'
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat,$RunnerOutput | Out-Null

function Write-Report([string]$Path,[System.Collections.Generic.List[string]]$Lines){
  $dir = Split-Path -Parent $Path
  if($dir){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Set-Content -Path $Path -Encoding UTF8 -Value $Lines
}
function HasText([string]$Path,[string]$Needle){ if(Test-Path $Path){ return ((Get-Content $Path -Raw -ErrorAction SilentlyContinue) -like "*$Needle*") } return $false }

$contractReport = Join-Path $Reports "$TaskId`_runner_contract_detect.txt"
$tokenReport = Join-Path $Reports "$TaskId`_final_token_verify.txt"
$remoteReport = Join-Path $Reports "$TaskId`_remote_sync_diagnostic.txt"
$dataReport = Join-Path $Reports "$TaskId`_data_coverage_audit.txt"
$lookupReport = Join-Path $Reports "$TaskId`_lookup_coverage_audit.txt"
$uiReport = Join-Path $Reports "$TaskId`_ui_static_contract_audit.txt"
$namingReport = Join-Path $Reports "$TaskId`_naming_debt_audit.txt"
$finalReport = Join-Path $Reports "$TaskId`_final_report.txt"
$finalStatus = Join-Path $Status "$TaskId`_final.status.txt"
$heartbeatFile = Join-Path $Heartbeat "$TaskId.running.heartbeat.txt"

Set-Content -Path $heartbeatFile -Encoding UTF8 -Value @(
  "TASK_ID=$TaskId",
  "PAGE_KEY=$PageKey",
  "STATUS=RUNNING_BY_SINGLE_RUNNER_AUTOMATION",
  "STARTED_AT=$StartedAt",
  "SCRIPT_PATH=$ScriptPath",
  "PAGE_ROOT=$PageRoot",
  "REPO_ROOT=$RepoRoot"
)

# Contract detection. No mutation.
$contract = New-Object System.Collections.Generic.List[string]
$contract.Add("TASK_ID=$TaskId")
$contract.Add("PAGE_KEY=$PageKey")
$contract.Add('REPORT_KIND=runner_contract_detect')
$contract.Add("SCRIPT_PATH=$ScriptPath")
$contract.Add("PAGE_ROOT=$PageRoot")
$contract.Add("REPO_ROOT=$RepoRoot")
@(
  'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1',
  'docs/chatgpt_status/_shared/automation',
  "docs/chatgpt_status/$PageKey/control",
  "docs/chatgpt_status/$PageKey/queue",
  "docs/chatgpt_status/$PageKey/runner_tasks",
  "docs/chatgpt_status/$PageKey/current-task",
  "docs/chatgpt_status/$PageKey/automation",
  "docs/chatgpt_status/$PageKey/reports",
  "docs/chatgpt_status/$PageKey/status",
  "docs/chatgpt_status/$PageKey/heartbeat",
  "docs/chatgpt_status/$PageKey/runner_output"
) | ForEach-Object { $contract.Add("PATH_EXISTS[$_]=$(Test-Path (Join-Path $RepoRoot $_))") }
try {
  Push-Location $RepoRoot
  $contract.Add("GIT_BRANCH=$((git rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim())")
  $contract.Add("GIT_HEAD=$((git rev-parse HEAD 2>&1 | Out-String).Trim())")
  $contract.Add('GIT_STATUS_SHORT_BEGIN')
  $contract.Add((git status --short 2>&1 | Out-String).Trim())
  $contract.Add('GIT_STATUS_SHORT_END')
  Pop-Location
} catch { $contract.Add("GIT_CONTRACT_ERROR=$($_.Exception.Message)"); try{Pop-Location}catch{} }
Write-Report $contractReport $contract

# Job 1: final token verification.
$jobToken = Start-Job -ArgumentList $PageRoot,$tokenReport -ScriptBlock {
  param($PageRoot,$tokenReport)
  $tokens = @('FINAL_STATUS=FINAL_READY_CONFIRMED','PRODUCT_PROGRESS_ESTIMATE=100','PRODUCTION_COMPLETE=true')
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=final_token_verify')
  $files = Get-ChildItem -Path $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\(reports|status)\\' }
  $all = $true
  foreach($t in $tokens){
    $hit = @()
    foreach($f in $files){ try { if((Get-Content $f.FullName -Raw -ErrorAction Stop) -like "*$t*"){ $hit += $f.FullName } } catch {} }
    $lines.Add("TOKEN_FOUND[$t]=$([bool]($hit.Count -gt 0))")
    foreach($h in $hit){ $lines.Add("TOKEN_FILE[$t]=$h") }
    if($hit.Count -eq 0){ $all = $false }
  }
  $lines.Add("FINAL_TOKEN_SET_PRESENT=$all")
  Set-Content -Path $tokenReport -Encoding UTF8 -Value $lines
}

# Job 2: git remote sync diagnostic. Fetch only, no merge, no rebase, no force.
$jobRemote = Start-Job -ArgumentList $RepoRoot,$remoteReport -ScriptBlock {
  param($RepoRoot,$remoteReport)
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=remote_sync_diagnostic')
  try {
    Push-Location $RepoRoot
    $branch = (git rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim()
    $head = (git rev-parse HEAD 2>&1 | Out-String).Trim()
    $lines.Add("LOCAL_BRANCH=$branch")
    $lines.Add("LOCAL_HEAD=$head")
    $lines.Add("REMOTE_ORIGIN=$((git remote get-url origin 2>&1 | Out-String).Trim())")
    $lines.Add('FETCH_OUTPUT_BEGIN')
    $lines.Add((git fetch --prune origin 2>&1 | Out-String).Trim())
    $lines.Add('FETCH_OUTPUT_END')
    $remoteHead = (git rev-parse "origin/$branch" 2>&1 | Out-String).Trim()
    $lines.Add("REMOTE_HEAD_FOR_LOCAL_BRANCH=$remoteHead")
    if($remoteHead -and $remoteHead -notmatch 'fatal'){
      $base = (git merge-base $branch "origin/$branch" 2>&1 | Out-String).Trim()
      $lines.Add("MERGE_BASE=$base")
      $lines.Add("AHEAD_BEHIND_LOCAL_REMOTE=$((git rev-list --left-right --count "$branch...origin/$branch" 2>&1 | Out-String).Trim())")
      if($head -eq $remoteHead){ $lines.Add('REMOTE_SYNC_STATUS=IN_SYNC') }
      elseif($base -eq $remoteHead){ $lines.Add('REMOTE_SYNC_STATUS=LOCAL_AHEAD_FAST_FORWARD_PUSH_POSSIBLE') }
      elseif($base -eq $head){ $lines.Add('REMOTE_SYNC_STATUS=LOCAL_BEHIND_PULL_REQUIRED') }
      else { $lines.Add('REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK') }
    } else { $lines.Add('REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE') }
    Pop-Location
  } catch { $lines.Add("REMOTE_SYNC_ERROR=$($_.Exception.Message)"); try{Pop-Location}catch{} }
  Set-Content -Path $remoteReport -Encoding UTF8 -Value $lines
}

# Job 3: D/F topography data coverage.
$jobData = Start-Job -ArgumentList $dataReport -ScriptBlock {
  param($dataReport)
  $roots = @('D:\AAYS_DATA\topography\england\raw','D:\AAYS_DATA\topography\england\tiles','D:\AAYS_DATA\topography\england\processed','D:\topografik_map\london\terrarium_tiles','F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz')
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=data_coverage_audit')
  foreach($r in $roots){
    $exists = Test-Path $r
    $lines.Add("PATH_EXISTS[$r]=$exists")
    if($exists){
      $item = Get-Item $r -ErrorAction SilentlyContinue
      if($item -and $item.PSIsContainer){ $lines.Add("FILE_COUNT_CAP_2001[$r]=$((Get-ChildItem $r -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 2001 | Measure-Object).Count)") }
      elseif($item){ $lines.Add("FILE_SIZE_BYTES[$r]=$($item.Length)") }
    }
  }
  $england = @($roots[0],$roots[1],$roots[2] | Where-Object { Test-Path $_ }).Count
  $london = ((Test-Path $roots[3]) -and (Test-Path $roots[4]))
  $lines.Add("ENGLAND_WIDE_ROOTS_PRESENT_COUNT=$england")
  $lines.Add("LONDON_ONLY_PROOF_PRESENT=$london")
  if($england -ge 2){ $lines.Add('DATA_COVERAGE_STATUS=ENGLAND_WIDE_EVIDENCE_PRESENT') }
  elseif($london){ $lines.Add('DATA_COVERAGE_STATUS=LONDON_ONLY_EVIDENCE_PRESENT_PRODUCT_WIDE_BLOCKED') }
  else { $lines.Add('DATA_COVERAGE_STATUS=INSUFFICIENT_DATA_EVIDENCE') }
  Set-Content -Path $dataReport -Encoding UTF8 -Value $lines
}

# Job 4: lookup coverage sample.
$jobLookup = Start-Job -ArgumentList $lookupReport -ScriptBlock {
  param($lookupReport)
  $samples = @('29759443')
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=lookup_coverage_audit')
  $ok=0; $noData=0; $err=0
  foreach($pid in $samples){
    try {
      $resp = Invoke-WebRequest -Uri ('http://127.0.0.1:8010/topography/lookup?parcel_id=' + $pid) -UseBasicParsing -TimeoutSec 5
      $statusValue = 'unknown'
      try { $json = $resp.Content | ConvertFrom-Json; $statusValue = [string]$json.status } catch {}
      if($resp.StatusCode -eq 200 -and $statusValue -ne 'no_data'){ $ok++ }
      elseif($resp.StatusCode -eq 200 -and $statusValue -eq 'no_data'){ $noData++ }
      else { $err++ }
      $lines.Add("LOOKUP[$pid]=http_$($resp.StatusCode);status_$statusValue")
    } catch { $err++; $lines.Add("LOOKUP[$pid]=ERROR;$($_.Exception.Message)") }
  }
  $lines.Add("LOOKUP_OK_WITH_DATA=$ok")
  $lines.Add("LOOKUP_NO_DATA=$noData")
  $lines.Add("LOOKUP_ERRORS=$err")
  if($ok -gt 0 -and $err -eq 0){ $lines.Add('LOOKUP_COVERAGE_STATUS=PARTIAL_OR_GOOD_DATA_PRESENT') } else { $lines.Add('LOOKUP_COVERAGE_STATUS=BLOCKED_NO_CONFIRMED_DATA_ROWS') }
  Set-Content -Path $lookupReport -Encoding UTF8 -Value $lines
}

# Job 5: static UI contract.
$jobUi = Start-Job -ArgumentList $RepoRoot,$uiReport -ScriptBlock {
  param($RepoRoot,$uiReport)
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=ui_static_contract_audit')
  $files = @('england_map_web\static\js\app.js','england_map_web\app.js','app.js')
  $tokens = @('normalizeTopographyLookupForPopup','buildTopographyPopupRowsHtml','hight_differance.png','topography')
  $target = $null
  foreach($rel in $files){ $p = Join-Path $RepoRoot $rel; $lines.Add("UI_FILE_EXISTS[$rel]=$(Test-Path $p)"); if((Test-Path $p) -and -not $target){ $target=$p } }
  if($target){ $txt = Get-Content $target -Raw -ErrorAction SilentlyContinue; foreach($t in $tokens){ $lines.Add("UI_TOKEN_FOUND[$t]=$($txt -like "*$t*" )") }; $lines.Add('UI_STATIC_CONTRACT_STATUS=CHECKED') }
  else { $lines.Add('UI_STATIC_CONTRACT_STATUS=BLOCKED_APP_JS_NOT_FOUND') }
  Set-Content -Path $uiReport -Encoding UTF8 -Value $lines
}

# Job 6: pb naming debt.
$jobNaming = Start-Job -ArgumentList $PageRoot,$namingReport -ScriptBlock {
  param($PageRoot,$namingReport)
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=naming_debt_audit')
  $pb = Get-ChildItem -Path $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'pb_*' }
  $lines.Add("PB_NAMED_FILE_COUNT=$($pb.Count)")
  foreach($f in $pb){ $lines.Add("PB_FILE=$($f.FullName)") }
  if($pb.Count -eq 0){ $lines.Add('NAMING_DEBT_STATUS=CLEAN') } else { $lines.Add('NAMING_DEBT_STATUS=DEBT_PRESENT_COMPATIBILITY_RENAME_PLAN_REQUIRED') }
  Set-Content -Path $namingReport -Encoding UTF8 -Value $lines
}

$jobs = @($jobToken,$jobRemote,$jobData,$jobLookup,$jobUi,$jobNaming)
Wait-Job -Job $jobs -Timeout 900 | Out-Null
foreach($j in $jobs){
  if($j.State -eq 'Running'){ Stop-Job $j -Force; Set-Content -Path (Join-Path $RunnerOutput "$TaskId.$($j.Id).timeout.txt") -Encoding UTF8 -Value "JOB_TIMEOUT=$($j.Name)" }
  Receive-Job $j -ErrorAction SilentlyContinue | Out-File -FilePath (Join-Path $RunnerOutput "$TaskId.$($j.Id).stdout.txt") -Encoding UTF8
  Remove-Job $j -Force -ErrorAction SilentlyContinue
}

$blockers = New-Object System.Collections.Generic.List[string]
if(-not (HasText $tokenReport 'FINAL_TOKEN_SET_PRESENT=True')){ $blockers.Add('final_tokens_not_all_verified') }
if(HasText $remoteReport 'REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK'){ $blockers.Add('remote_branch_diverged_non_fast_forward') }
if(HasText $remoteReport 'REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE'){ $blockers.Add('remote_branch_not_found_or_unreadable') }
if(-not (HasText $dataReport 'DATA_COVERAGE_STATUS=ENGLAND_WIDE_EVIDENCE_PRESENT')){ $blockers.Add('england_wide_coverage_not_proven') }
if(-not (HasText $lookupReport 'LOOKUP_COVERAGE_STATUS=PARTIAL_OR_GOOD_DATA_PRESENT')){ $blockers.Add('lookup_data_presence_not_proven') }
if(-not (HasText $uiReport 'UI_STATIC_CONTRACT_STATUS=CHECKED')){ $blockers.Add('ui_static_contract_not_verified') }
if(HasText $namingReport 'NAMING_DEBT_STATUS=DEBT_PRESENT_COMPATIBILITY_RENAME_PLAN_REQUIRED'){ $blockers.Add('pb_naming_debt_present') }
$manualEvidence = Get-ChildItem -Path $Reports -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'manual.*ui.*smoke|ui.*smoke.*manual' }
if($manualEvidence.Count -eq 0){ $blockers.Add('manual_ui_parcel_click_smoke_not_git_visible') }

$progress = 88
if($blockers.Count -le 5){ $progress = 92 }
if($blockers.Count -le 3){ $progress = 96 }
if($blockers.Count -eq 0){ $progress = 100 }

$final = New-Object System.Collections.Generic.List[string]
$final.Add("TASK_ID=$TaskId")
$final.Add("PAGE_KEY=$PageKey")
$final.Add("STARTED_AT=$StartedAt")
$final.Add("FINISHED_AT=$((Get-Date).ToString('s'))")
$final.Add('REPORT_KIND=final_report')
$final.Add('LOCAL_TECHNICAL_COMPLETION_FROM_HANDOFF=100')
$final.Add("PRODUCT_PROGRESS_ESTIMATE=$progress")
$final.Add("BLOCKER_COUNT=$($blockers.Count)")
foreach($b in $blockers){ $final.Add("BLOCKER=$b") }
@($contractReport,$tokenReport,$remoteReport,$dataReport,$lookupReport,$uiReport,$namingReport) | ForEach-Object { $final.Add("EVIDENCE_REPORT=$_") }
Write-Report $finalReport $final

$st = New-Object System.Collections.Generic.List[string]
$st.Add("TASK_ID=$TaskId")
$st.Add("PAGE_KEY=$PageKey")
$st.Add("PRODUCT_PROGRESS_ESTIMATE=$progress")
$st.Add("BLOCKER_COUNT=$($blockers.Count)")
if($blockers.Count -eq 0){
  $st.Add('FINAL_STATUS=FINAL_READY_CONFIRMED')
  $st.Add('PRODUCTION_COMPLETE=true')
  $st.Add('PRODUCT_100_READY=true')
} else {
  $st.Add('FINAL_STATUS=BLOCKED_NEEDS_EVIDENCE')
  $st.Add('PRODUCTION_COMPLETE=false')
  $st.Add('PRODUCT_100_READY=false')
  foreach($b in $blockers){ $st.Add("BLOCKER=$b") }
}
Write-Report $finalStatus $st
Add-Content -Path $heartbeatFile -Encoding UTF8 -Value @("STATUS=FINISHED","FINISHED_AT=$((Get-Date).ToString('s'))","FINAL_REPORT_FILE=$finalReport","FINAL_STATUS_FILE=$finalStatus")

# Safe publish attempt from the existing runner context. This is not a second runner and never force pushes.
try {
  Push-Location $RepoRoot
  git add "docs/chatgpt_status/$PageKey/reports" "docs/chatgpt_status/$PageKey/status" "docs/chatgpt_status/$PageKey/heartbeat" "docs/chatgpt_status/$PageKey/runner_output" 2>&1 | Out-File -FilePath (Join-Path $RunnerOutput "$TaskId.git_add.txt") -Encoding UTF8
  git diff --cached --quiet
  if($LASTEXITCODE -ne 0){
    git commit -m "AAYS Topography: publish single-runner audit outputs" 2>&1 | Out-File -FilePath (Join-Path $RunnerOutput "$TaskId.git_commit.txt") -Encoding UTF8
    git push origin HEAD 2>&1 | Out-File -FilePath (Join-Path $RunnerOutput "$TaskId.git_push.txt") -Encoding UTF8
  }
  Pop-Location
} catch { try{Pop-Location}catch{}; Set-Content -Path (Join-Path $RunnerOutput "$TaskId.git_publish_error.txt") -Encoding UTF8 -Value "GIT_PUBLISH_ERROR=$($_.Exception.Message)" }

exit 0
