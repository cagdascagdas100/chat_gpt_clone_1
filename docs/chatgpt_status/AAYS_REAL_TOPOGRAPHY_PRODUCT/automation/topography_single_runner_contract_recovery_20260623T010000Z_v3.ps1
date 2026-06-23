param(
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
)

$ErrorActionPreference = 'Continue'
$ScriptPath = $MyInvocation.MyCommand.Path
$AutomationRoot = Split-Path -Parent $ScriptPath
$PageRoot = Split-Path -Parent $AutomationRoot
$RepoRoot = (Resolve-Path (Join-Path $PageRoot '..\..\..')).Path
$Reports = Join-Path $PageRoot 'reports'
$Status = Join-Path $PageRoot 'status'
$Heartbeat = Join-Path $PageRoot 'heartbeat'
$RunnerOutput = Join-Path $PageRoot 'runner_output'
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat,$RunnerOutput | Out-Null

function W([string]$Path,[string[]]$Lines){ Set-Content -Path $Path -Encoding UTF8 -Value $Lines }
function A([string]$Path,[string[]]$Lines){ Add-Content -Path $Path -Encoding UTF8 -Value $Lines }
function HasText([string]$Path,[string]$Needle){ if(Test-Path $Path){ return ((Get-Content $Path -Raw -ErrorAction SilentlyContinue) -like "*$Needle*") }; return $false }

$hb = Join-Path $Heartbeat ($TaskId + '.heartbeat.txt')
W $hb @(
  "TASK_ID=$TaskId",
  "PAGE_KEY=$PageKey",
  'HEARTBEAT_STATUS=RUNNING_V3_PARALLEL_READONLY_AUDIT',
  "SCRIPT_PATH=$ScriptPath",
  "PAGE_ROOT=$PageRoot",
  "REPO_ROOT=$RepoRoot",
  ('START_UTC=' + (Get-Date).ToUniversalTime().ToString('s') + 'Z')
)

$scriptBlock = {
  param($Kind,$OutFile,$RepoRoot,$PageRoot,$Reports,$Status)
  $ErrorActionPreference = 'Continue'
  function W2([string]$Path,[string[]]$Lines){ Set-Content -Path $Path -Encoding UTF8 -Value $Lines }
  $lines = @("REPORT_KIND=$Kind",('RUN_UTC=' + (Get-Date).ToUniversalTime().ToString('s') + 'Z'))
  switch($Kind){
    'runner_contract_detect' {
      $lines += "REPO_ROOT=$RepoRoot"
      foreach($d in @('control','queue','runner_tasks','current-task','automation','reports','status','heartbeat','runner_output')){ $lines += "PAGE_PATH_EXISTS[$d]=" + (Test-Path (Join-Path $PageRoot $d)) }
      $shared = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'
      $lines += 'SHARED_RUNNER_SCRIPT_EXISTS=' + (Test-Path $shared)
      $candidates = @(
        (Join-Path $PageRoot 'queue\_ACTIVE_TASK.md'),
        (Join-Path $PageRoot 'current-task\ACTIVE_TASK.md'),
        (Join-Path $PageRoot 'runner_tasks\_ACTIVE_TASK.md'),
        (Join-Path $PageRoot 'control\RUNNER_PICKUP_REQUEST.md')
      )
      foreach($c in $candidates){ $lines += "PICKUP_ALIAS_EXISTS[$c]=" + (Test-Path $c) }
    }
    'final_token_verify' {
      $tokens = @('FINAL_STATUS=FINAL_READY_CONFIRMED','PRODUCT_PROGRESS_ESTIMATE=100','PRODUCTION_COMPLETE=true')
      $files = Get-ChildItem $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\(reports|status)\\' }
      $all = $true
      foreach($tok in $tokens){
        $hit = $false
        foreach($f in $files){ try{ if((Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue) -like "*$tok*"){ $hit = $true; $lines += "TOKEN_FILE[$tok]=$($f.FullName)" } } catch{} }
        $lines += "TOKEN_FOUND[$tok]=$hit"
        if(-not $hit){ $all = $false }
      }
      $lines += "FINAL_TOKEN_SET_PRESENT=$all"
    }
    'remote_sync_diagnostic' {
      try{
        Push-Location $RepoRoot
        $branch = (git rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim()
        $head = (git rev-parse HEAD 2>&1 | Out-String).Trim()
        $origin = (git remote get-url origin 2>&1 | Out-String).Trim()
        $fetch = (git fetch --prune origin 2>&1 | Out-String).Trim()
        $remoteRef = 'origin/' + $branch
        $remoteHead = (git rev-parse $remoteRef 2>&1 | Out-String).Trim()
        $lines += "LOCAL_BRANCH=$branch"
        $lines += "LOCAL_HEAD=$head"
        $lines += "ORIGIN_URL=$origin"
        $lines += "FETCH_OUTPUT=$fetch"
        $lines += "REMOTE_REF=$remoteRef"
        $lines += "REMOTE_HEAD_FOR_LOCAL_BRANCH=$remoteHead"
        if($remoteHead -and $remoteHead -notmatch 'fatal'){
          $base = (git merge-base $branch $remoteRef 2>&1 | Out-String).Trim()
          $ab = (git rev-list --left-right --count ($branch + '...' + $remoteRef) 2>&1 | Out-String).Trim()
          $lines += "MERGE_BASE=$base"
          $lines += "AHEAD_BEHIND_LOCAL_REMOTE=$ab"
          if($head -eq $remoteHead){ $lines += 'REMOTE_SYNC_STATUS=IN_SYNC' }
          elseif($base -eq $remoteHead){ $lines += 'REMOTE_SYNC_STATUS=LOCAL_AHEAD_FAST_FORWARD_PUSH_POSSIBLE' }
          elseif($base -eq $head){ $lines += 'REMOTE_SYNC_STATUS=LOCAL_BEHIND_PULL_REQUIRED' }
          else { $lines += 'REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK' }
        } else { $lines += 'REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE' }
        Pop-Location
      } catch { $lines += 'REMOTE_SYNC_ERROR=' + $_.Exception.Message; try{Pop-Location}catch{} }
    }
    'data_coverage_audit' {
      $roots = @(
        'D:\AAYS_DATA\topography\england\raw',
        'D:\AAYS_DATA\topography\england\tiles',
        'D:\AAYS_DATA\topography\england\processed',
        'D:\topografik_map\london\terrarium_tiles',
        'F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz'
      )
      foreach($r in $roots){
        $exists = Test-Path $r
        $lines += "PATH_EXISTS[$r]=$exists"
        if($exists -and (Get-Item $r -ErrorAction SilentlyContinue).PSIsContainer){
          $cnt = (Get-ChildItem $r -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1001).Count
          $lines += "PATH_SAMPLE_FILE_COUNT_UP_TO_1001[$r]=$cnt"
        } elseif($exists) {
          $item = Get-Item $r -ErrorAction SilentlyContinue
          $lines += "FILE_LENGTH_BYTES[$r]=$($item.Length)"
        }
      }
      $england = @($roots[0..2] | Where-Object { Test-Path $_ }).Count
      $london = ((Test-Path $roots[3]) -and (Test-Path $roots[4]))
      $lines += "ENGLAND_WIDE_ROOTS_PRESENT_COUNT=$england"
      $lines += "LONDON_ONLY_PROOF_PRESENT=$london"
      if($england -ge 2){ $lines += 'DATA_COVERAGE_STATUS=ENGLAND_WIDE_EVIDENCE_PRESENT' }
      elseif($london){ $lines += 'DATA_COVERAGE_STATUS=LONDON_ONLY_EVIDENCE_PRESENT_PRODUCT_WIDE_BLOCKED' }
      else { $lines += 'DATA_COVERAGE_STATUS=INSUFFICIENT_DATA_EVIDENCE' }
    }
    'lookup_coverage_audit' {
      $parcelIds = @('29759443')
      $manifest = Join-Path $PageRoot 'reports\topography_lookup_probe_parcels.txt'
      if(Test-Path $manifest){ $parcelIds = Get-Content $manifest -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\d+$' } | Select-Object -First 50 }
      $ok=0; $data=0; $nodata=0; $err=0
      foreach($pid in $parcelIds){
        try{
          $url = 'http://127.0.0.1:8010/topography/lookup?parcel_id=' + $pid
          $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8
          $statusValue='unknown'
          try{ $json = $resp.Content | ConvertFrom-Json; $statusValue = [string]$json.status } catch{}
          $lines += "LOOKUP[$pid]=http_$($resp.StatusCode);status_$statusValue"
          if($resp.StatusCode -eq 200){ $ok++ }
          if($statusValue -eq 'no_data'){ $nodata++ } elseif($resp.StatusCode -eq 200){ $data++ }
        } catch { $err++; $lines += "LOOKUP[$pid]=ERROR;$($_.Exception.Message)" }
      }
      $lines += "LOOKUP_TOTAL=$($parcelIds.Count)"
      $lines += "LOOKUP_HTTP_200=$ok"
      $lines += "LOOKUP_DATA_ROWS=$data"
      $lines += "LOOKUP_NO_DATA_ROWS=$nodata"
      $lines += "LOOKUP_ERRORS=$err"
      if($data -gt 0){ $lines += 'LOOKUP_COVERAGE_STATUS=PARTIAL_OR_GOOD_DATA_PRESENT' } else { $lines += 'LOOKUP_COVERAGE_STATUS=BLOCKED_NO_CONFIRMED_DATA_ROWS' }
    }
    'ui_static_contract_audit' {
      $app = Join-Path $RepoRoot 'england_map_web\static\js\app.js'
      $lines += 'APP_JS_EXISTS=' + (Test-Path $app)
      if(Test-Path $app){
        $txt = Get-Content $app -Raw -ErrorAction SilentlyContinue
        foreach($tok in @('normalizeTopographyLookupForPopup','buildTopographyPopupRowsHtml','hight_differance.png','topography')){ $lines += "UI_TOKEN_FOUND[$tok]=" + ($txt -like "*$tok*") }
        $lines += 'UI_STATIC_CONTRACT_STATUS=CHECKED'
      } else { $lines += 'UI_STATIC_CONTRACT_STATUS=BLOCKED_APP_JS_NOT_FOUND' }
      try{ $page = Invoke-WebRequest -Uri 'http://127.0.0.1:8010/england_map_web/' -UseBasicParsing -TimeoutSec 8; $lines += "APP_HTTP_STATUS=$($page.StatusCode)" } catch { $lines += 'APP_HTTP_STATUS=ERROR;' + $_.Exception.Message }
      $manual = Get-ChildItem $Reports -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'manual.*ui.*smoke|ui.*smoke.*manual|parcel.*click.*smoke' }
      $lines += 'MANUAL_UI_SMOKE_REPORT_COUNT=' + $manual.Count
      if($manual.Count -gt 0){ $lines += 'MANUAL_UI_SMOKE_STATUS=GIT_VISIBLE' } else { $lines += 'MANUAL_UI_SMOKE_STATUS=NOT_GIT_VISIBLE' }
    }
    'naming_debt_audit' {
      $pb = Get-ChildItem $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'pb_*' }
      $lines += 'PB_NAMED_FILE_COUNT=' + $pb.Count
      foreach($f in $pb){ $lines += 'PB_FILE=' + $f.FullName }
      if($pb.Count -eq 0){ $lines += 'NAMING_DEBT_STATUS=CLEAN' } else { $lines += 'NAMING_DEBT_STATUS=DEBT_PRESENT_COMPATIBILITY_RENAME_PLAN_REQUIRED' }
    }
  }
  W2 $OutFile $lines
}

$jobs = @(
  @{Kind='runner_contract_detect'; File=(Join-Path $Reports ($TaskId + '_runner_contract_detect.txt'))},
  @{Kind='final_token_verify'; File=(Join-Path $Reports ($TaskId + '_final_token_verify.txt'))},
  @{Kind='remote_sync_diagnostic'; File=(Join-Path $Reports ($TaskId + '_remote_sync_diagnostic.txt'))},
  @{Kind='data_coverage_audit'; File=(Join-Path $Reports ($TaskId + '_data_coverage_audit.txt'))},
  @{Kind='lookup_coverage_audit'; File=(Join-Path $Reports ($TaskId + '_lookup_coverage_audit.txt'))},
  @{Kind='ui_static_contract_audit'; File=(Join-Path $Reports ($TaskId + '_ui_static_contract_audit.txt'))},
  @{Kind='naming_debt_audit'; File=(Join-Path $Reports ($TaskId + '_naming_debt_audit.txt'))}
)

$running = @()
foreach($j in $jobs){ $running += Start-Job -ScriptBlock $scriptBlock -ArgumentList $j.Kind,$j.File,$RepoRoot,$PageRoot,$Reports,$Status }
Wait-Job -Job $running -Timeout 900 | Out-Null
foreach($job in $running){
  $out = Receive-Job -Job $job -ErrorAction SilentlyContinue | Out-String
  if($out.Trim()){ A (Join-Path $RunnerOutput ($TaskId + '_job_output.txt')) @($out.Trim()) }
  if($job.State -ne 'Completed'){ A (Join-Path $RunnerOutput ($TaskId + '_job_output.txt')) @('JOB_NOT_COMPLETED=' + $job.Id + ';STATE=' + $job.State) }
  Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
}

$finalReport = Join-Path $Reports ($TaskId + '_final_report.txt')
$finalStatus = Join-Path $Status ($TaskId + '_final.status.txt')
$blockers = @()
$tokens = Join-Path $Reports ($TaskId + '_final_token_verify.txt')
$remote = Join-Path $Reports ($TaskId + '_remote_sync_diagnostic.txt')
$data = Join-Path $Reports ($TaskId + '_data_coverage_audit.txt')
$lookup = Join-Path $Reports ($TaskId + '_lookup_coverage_audit.txt')
$ui = Join-Path $Reports ($TaskId + '_ui_static_contract_audit.txt')
$naming = Join-Path $Reports ($TaskId + '_naming_debt_audit.txt')
if(-not (HasText $tokens 'FINAL_TOKEN_SET_PRESENT=True')){ $blockers += 'final_tokens_not_all_verified' }
if(HasText $remote 'REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK'){ $blockers += 'remote_branch_diverged_non_fast_forward' }
if(HasText $remote 'REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE'){ $blockers += 'remote_branch_not_found_or_unreadable' }
if(HasText $remote 'REMOTE_SYNC_ERROR='){ $blockers += 'remote_sync_diagnostic_error' }
if(-not (HasText $data 'DATA_COVERAGE_STATUS=ENGLAND_WIDE_EVIDENCE_PRESENT')){ $blockers += 'england_wide_coverage_not_proven' }
if(-not (HasText $lookup 'LOOKUP_COVERAGE_STATUS=PARTIAL_OR_GOOD_DATA_PRESENT')){ $blockers += 'lookup_data_presence_not_proven' }
if(-not (HasText $ui 'UI_STATIC_CONTRACT_STATUS=CHECKED')){ $blockers += 'ui_static_contract_not_verified' }
if(-not (HasText $ui 'MANUAL_UI_SMOKE_STATUS=GIT_VISIBLE')){ $blockers += 'manual_ui_parcel_click_smoke_not_git_visible' }
if(HasText $naming 'NAMING_DEBT_STATUS=DEBT_PRESENT'){ $blockers += 'pb_naming_debt_present' }

$progress = 90
if($blockers.Count -le 5){ $progress = 92 }
if($blockers.Count -le 3){ $progress = 96 }
if($blockers.Count -eq 0){ $progress = 100 }

$fr = @(
  "TASK_ID=$TaskId",
  "PAGE_KEY=$PageKey",
  'REPORT_KIND=FINAL_AGGREGATED_V3',
  'LOCAL_TECHNICAL_COMPLETION_FROM_HANDOFF=100',
  "PRODUCT_PROGRESS_ESTIMATE=$progress",
  'PRODUCTION_COMPLETE=' + ($(if($blockers.Count -eq 0){'true'}else{'false'})),
  'BLOCKER_COUNT=' + $blockers.Count
)
foreach($b in $blockers){ $fr += 'BLOCKER=' + $b }
$fr += 'EVIDENCE_REPORTS=' + (($jobs | ForEach-Object { $_.File }) -join ';')
W $finalReport $fr

$st = @("TASK_ID=$TaskId","PAGE_KEY=$PageKey","PRODUCT_PROGRESS_ESTIMATE=$progress",'BLOCKER_COUNT=' + $blockers.Count)
if($blockers.Count -eq 0){
  $st += 'FINAL_STATUS=FINAL_READY_CONFIRMED'
  $st += 'PRODUCTION_COMPLETE=true'
  $st += 'PRODUCT_100_READY=true'
} else {
  $st += 'FINAL_STATUS=BLOCKED_NEEDS_EVIDENCE'
  $st += 'PRODUCTION_COMPLETE=false'
  $st += 'PRODUCT_100_READY=false'
  foreach($b in $blockers){ $st += 'BLOCKER=' + $b }
}
W $finalStatus $st
A $hb @('HEARTBEAT_STATUS=FINISHED_V3',('END_UTC=' + (Get-Date).ToUniversalTime().ToString('s') + 'Z'),('FINAL_REPORT=' + $finalReport),('FINAL_STATUS=' + $finalStatus))
exit 0
