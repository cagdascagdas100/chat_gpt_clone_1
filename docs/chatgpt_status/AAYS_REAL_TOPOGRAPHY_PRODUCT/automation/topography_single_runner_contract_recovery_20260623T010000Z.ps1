param(
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
)

$ErrorActionPreference = 'Continue'
$StartedAt = (Get-Date).ToString('s')
$ScriptPath = $MyInvocation.MyCommand.Path
$AutomationRoot = Split-Path -Parent $ScriptPath
$PageRoot = Split-Path -Parent $AutomationRoot
$RepoRoot = (Resolve-Path (Join-Path $PageRoot '..\..')).Path
$Reports = Join-Path $PageRoot 'reports'
$Status = Join-Path $PageRoot 'status'
$Heartbeat = Join-Path $PageRoot 'heartbeat'
$RunnerOutput = Join-Path $PageRoot 'runner_output'
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat,$RunnerOutput | Out-Null

function Write-TextFile([string]$Path,[string[]]$Lines){
  $dir = Split-Path -Parent $Path
  if($dir){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Set-Content -Path $Path -Encoding UTF8 -Value $Lines
}

function Add-Line([string]$Path,[string]$Line){
  Add-Content -Path $Path -Encoding UTF8 -Value $Line
}

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

Write-TextFile $heartbeatFile @(
  "TASK_ID=$TaskId",
  "PAGE_KEY=$PageKey",
  "STATUS=RUNNING_BY_SINGLE_RUNNER_AUTOMATION",
  "STARTED_AT=$StartedAt",
  "SCRIPT_PATH=$ScriptPath",
  "PAGE_ROOT=$PageRoot",
  "REPO_ROOT=$RepoRoot"
)

# 1. Runner contract detection - no mutation.
$runnerCandidates = @(
  'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1',
  'docs/chatgpt_status/_shared/automation',
  "docs/chatgpt_status/$PageKey/queue",
  "docs/chatgpt_status/$PageKey/runner_tasks",
  "docs/chatgpt_status/$PageKey/current-task",
  "docs/chatgpt_status/$PageKey/control",
  "docs/chatgpt_status/$PageKey/status",
  "docs/chatgpt_status/$PageKey/reports",
  "docs/chatgpt_status/$PageKey/heartbeat",
  "docs/chatgpt_status/$PageKey/runner_output"
)
$contractLines = New-Object System.Collections.Generic.List[string]
$contractLines.Add("TASK_ID=$TaskId")
$contractLines.Add("PAGE_KEY=$PageKey")
$contractLines.Add("REPORT_KIND=runner_contract_detect")
$contractLines.Add("SCRIPT_PATH=$ScriptPath")
$contractLines.Add("PAGE_ROOT=$PageRoot")
$contractLines.Add("REPO_ROOT=$RepoRoot")
foreach($rel in $runnerCandidates){
  $p = Join-Path $RepoRoot $rel
  $exists = Test-Path $p
  $contractLines.Add("PATH_EXISTS[$rel]=$exists")
}
try {
  Push-Location $RepoRoot
  $contractLines.Add("GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>&1)")
  $contractLines.Add("GIT_HEAD=$(git rev-parse HEAD 2>&1)")
  $contractLines.Add("GIT_STATUS_SHORT_BEGIN")
  $contractLines.Add((git status --short 2>&1 | Out-String).Trim())
  $contractLines.Add("GIT_STATUS_SHORT_END")
  Pop-Location
} catch {
  $contractLines.Add("GIT_CONTRACT_ERROR=$($_.Exception.Message)")
  try { Pop-Location } catch {}
}
Write-TextFile $contractReport $contractLines

# Independent read-only jobs. Each writes a unique report. No DB, deploy, migration, seed, or force push.
$jobs = @()

$jobs += Start-Job -Name 'final_token_verify' -ArgumentList $PageRoot,$Reports,$tokenReport -ScriptBlock {
  param($PageRoot,$Reports,$tokenReport)
  $tokens = @('FINAL_STATUS=FINAL_READY_CONFIRMED','PRODUCT_PROGRESS_ESTIMATE=100','PRODUCTION_COMPLETE=true')
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=final_token_verify')
  $files = Get-ChildItem -Path $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\(reports|status)\\' }
  $hits = @{}
  foreach($t in $tokens){ $hits[$t] = @() }
  foreach($f in $files){
    try {
      $txt = Get-Content -Path $f.FullName -Raw -ErrorAction Stop
      foreach($t in $tokens){ if($txt -like "*$t*"){ $hits[$t] += $f.FullName } }
    } catch {}
  }
  foreach($t in $tokens){ $lines.Add("TOKEN_FOUND[$t]=$([bool]($hits[$t].Count -gt 0))") ; foreach($h in $hits[$t]){ $lines.Add("TOKEN_FILE[$t]=$h") } }
  $all = $true
  foreach($t in $tokens){ if($hits[$t].Count -eq 0){ $all = $false } }
  $lines.Add("FINAL_TOKEN_SET_PRESENT=$all")
  Set-Content -Path $tokenReport -Encoding UTF8 -Value $lines
}

$jobs += Start-Job -Name 'remote_sync_diagnostic' -ArgumentList $RepoRoot,$remoteReport -ScriptBlock {
  param($RepoRoot,$remoteReport)
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=remote_sync_diagnostic')
  try {
    Push-Location $RepoRoot
    $lines.Add("PWD=$PWD")
    $branch = (git rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim()
    $head = (git rev-parse HEAD 2>&1 | Out-String).Trim()
    $lines.Add("LOCAL_BRANCH=$branch")
    $lines.Add("LOCAL_HEAD=$head")
    $lines.Add("REMOTE_ORIGIN=$(git remote get-url origin 2>&1)")
    $lines.Add('FETCH_OUTPUT_BEGIN')
    $lines.Add((git fetch --prune origin 2>&1 | Out-String).Trim())
    $lines.Add('FETCH_OUTPUT_END')
    $remoteHead = (git rev-parse "origin/$branch" 2>&1 | Out-String).Trim()
    $lines.Add("REMOTE_HEAD_FOR_LOCAL_BRANCH=$remoteHead")
    if($remoteHead -and $remoteHead -notmatch 'fatal'){
      $aheadBehind = (git rev-list --left-right --count "$branch...origin/$branch" 2>&1 | Out-String).Trim()
      $lines.Add("AHEAD_BEHIND_LOCAL_REMOTE=$aheadBehind")
      $mergeBase = (git merge-base $branch "origin/$branch" 2>&1 | Out-String).Trim()
      $lines.Add("MERGE_BASE=$mergeBase")
      if($head -eq $remoteHead){ $lines.Add('REMOTE_SYNC_STATUS=IN_SYNC') }
      elseif($mergeBase -eq $remoteHead){ $lines.Add('REMOTE_SYNC_STATUS=LOCAL_AHEAD_FAST_FORWARD_PUSH_POSSIBLE') }
      elseif($mergeBase -eq $head){ $lines.Add('REMOTE_SYNC_STATUS=LOCAL_BEHIND_PULL_REQUIRED') }
      else { $lines.Add('REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK') }
    } else {
      $lines.Add('REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE')
    }
    Pop-Location
  } catch {
    $lines.Add("REMOTE_SYNC_ERROR=$($_.Exception.Message)")
    try { Pop-Location } catch {}
  }
  Set-Content -Path $remoteReport -Encoding UTF8 -Value $lines
}

$jobs += Start-Job -Name 'data_coverage_audit' -ArgumentList $dataReport -ScriptBlock {
  param($dataReport)
  $roots = @(
    'D:\AAYS_DATA\topography\england\raw',
    'D:\AAYS_DATA\topography\england\tiles',
    'D:\AAYS_DATA\topography\england\processed',
    'D:\topografik_map\london\terrarium_tiles',
    'F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz'
  )
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=data_coverage_audit')
  foreach($r in $roots){
    $exists = Test-Path $r
    $lines.Add("PATH_EXISTS[$r]=$exists")
    if($exists){
      try {
        $item = Get-Item $r -ErrorAction Stop
        $lines.Add("PATH_TYPE[$r]=$($item.PSIsContainer)")
        if($item.PSIsContainer){
          $count = (Get-ChildItem -Path $r -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 2001 | Measure-Object).Count
          $lines.Add("FILE_COUNT_CAP_2001[$r]=$count")
        } else {
          $lines.Add("FILE_SIZE_BYTES[$r]=$($item.Length)")
          $lines.Add("LAST_WRITE[$r]=$($item.LastWriteTime.ToString('s'))")
        }
      } catch { $lines.Add("PATH_AUDIT_ERROR[$r]=$($_.Exception.Message)") }
    }
  }
  $englandProof = ($roots[0..2] | Where-Object { Test-Path $_ }).Count
  $londonProof = ((Test-Path 'D:\topografik_map\london\terrarium_tiles') -and (Test-Path 'F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz'))
  $lines.Add("ENGLAND_WIDE_ROOTS_PRESENT_COUNT=$englandProof")
  $lines.Add("LONDON_ONLY_PROOF_PRESENT=$londonProof")
  if($englandProof -ge 2){ $lines.Add('DATA_COVERAGE_STATUS=ENGLAND_WIDE_EVIDENCE_PRESENT') }
  elseif($londonProof){ $lines.Add('DATA_COVERAGE_STATUS=LONDON_ONLY_EVIDENCE_PRESENT_PRODUCT_WIDE_BLOCKED') }
  else { $lines.Add('DATA_COVERAGE_STATUS=INSUFFICIENT_DATA_EVIDENCE') }
  Set-Content -Path $dataReport -Encoding UTF8 -Value $lines
}

$jobs += Start-Job -Name 'lookup_coverage_audit' -ArgumentList $lookupReport -ScriptBlock {
  param($lookupReport)
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=lookup_coverage_audit')
  $base = 'http://127.0.0.1:8010/topography/lookup?parcel_id='
  $samples = New-Object System.Collections.Generic.List[string]
  $samples.Add('29759443')
  $source = 'F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz'
  if(Test-Path $source){
    try {
      $fs = [System.IO.File]::OpenRead($source)
      $gz = New-Object System.IO.Compression.GzipStream($fs,[System.IO.Compression.CompressionMode]::Decompress)
      $sr = New-Object System.IO.StreamReader($gz)
      $header = $sr.ReadLine()
      $lines.Add("SOURCE_HEADER=$header")
      $idx = 0
      if($header){
        $cols = $header.Split(',')
        for($i=0; $i -lt $cols.Length; $i++){ if($cols[$i] -match 'parcel'){ $idx = $i; break } }
      }
      while(-not $sr.EndOfStream -and $samples.Count -lt 51){
        $row = $sr.ReadLine()
        if($row){
          $parts = $row.Split(',')
          if($parts.Length -gt $idx){
            $pid = ($parts[$idx] -replace '"','').Trim()
            if($pid -match '^[0-9A-Za-z_-]+$' -and -not $samples.Contains($pid)){ $samples.Add($pid) }
          }
        }
      }
      $sr.Close(); $gz.Close(); $fs.Close()
    } catch { $lines.Add("SOURCE_SAMPLE_READ_ERROR=$($_.Exception.Message)") }
  } else {
    $lines.Add('SOURCE_SAMPLE_FILE_EXISTS=false')
  }
  $ok=0; $noData=0; $errors=0; $total=0
  foreach($pid in $samples){
    $total++
    try {
      $resp = Invoke-WebRequest -Uri ($base + [uri]::EscapeDataString($pid)) -UseBasicParsing -TimeoutSec 5
      $body = $resp.Content
      $statusValue = 'unknown'
      try { $json = $body | ConvertFrom-Json; $statusValue = [string]$json.status } catch {}
      if($resp.StatusCode -eq 200 -and $statusValue -ne 'no_data'){ $ok++ }
      elseif($resp.StatusCode -eq 200 -and $statusValue -eq 'no_data'){ $noData++ }
      else { $errors++ }
      $lines.Add("LOOKUP[$pid]=http_$($resp.StatusCode);status_$statusValue")
    } catch {
      $errors++
      $lines.Add("LOOKUP[$pid]=ERROR;$($_.Exception.Message)")
    }
  }
  $lines.Add("LOOKUP_TOTAL=$total")
  $lines.Add("LOOKUP_OK_WITH_DATA=$ok")
  $lines.Add("LOOKUP_NO_DATA=$noData")
  $lines.Add("LOOKUP_ERRORS=$errors")
  if($total -gt 0){ $lines.Add("LOOKUP_DATA_RATE=$([math]::Round(($ok / $total),4))") }
  if($ok -gt 0 -and $errors -eq 0){ $lines.Add('LOOKUP_COVERAGE_STATUS=PARTIAL_OR_GOOD_DATA_PRESENT') } else { $lines.Add('LOOKUP_COVERAGE_STATUS=BLOCKED_NO_CONFIRMED_DATA_ROWS') }
  Set-Content -Path $lookupReport -Encoding UTF8 -Value $lines
}

$jobs += Start-Job -Name 'ui_static_contract_audit' -ArgumentList $RepoRoot,$uiReport -ScriptBlock {
  param($RepoRoot,$uiReport)
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=ui_static_contract_audit')
  $candidates = @(
    'england_map_web\static\js\app.js',
    'england_map_web\app.js',
    'app.js'
  )
  $tokens = @('normalizeTopographyLookupForPopup','buildTopographyPopupRowsHtml','hight_differance.png','topography')
  $foundFile = $null
  foreach($rel in $candidates){
    $p = Join-Path $RepoRoot $rel
    $exists = Test-Path $p
    $lines.Add("UI_FILE_EXISTS[$rel]=$exists")
    if($exists -and -not $foundFile){ $foundFile = $p }
  }
  if($foundFile){
    $txt = Get-Content -Path $foundFile -Raw -ErrorAction SilentlyContinue
    foreach($t in $tokens){ $lines.Add("UI_TOKEN_FOUND[$t]=$($txt -like "*$t*" )") }
    $lines.Add('UI_STATIC_CONTRACT_STATUS=CHECKED')
  } else {
    $lines.Add('UI_STATIC_CONTRACT_STATUS=BLOCKED_APP_JS_NOT_FOUND')
  }
  Set-Content -Path $uiReport -Encoding UTF8 -Value $lines
}

$jobs += Start-Job -Name 'naming_debt_audit' -ArgumentList $PageRoot,$namingReport -ScriptBlock {
  param($PageRoot,$namingReport)
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('REPORT_KIND=naming_debt_audit')
  $pb = Get-ChildItem -Path $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'pb_*' }
  $lines.Add("PB_NAMED_FILE_COUNT=$($pb.Count)")
  foreach($f in $pb){ $lines.Add("PB_FILE=$($f.FullName)") }
  if($pb.Count -eq 0){ $lines.Add('NAMING_DEBT_STATUS=CLEAN') } else { $lines.Add('NAMING_DEBT_STATUS=DEBT_PRESENT_COMPATIBILITY_RENAME_PLAN_REQUIRED') }
  Set-Content -Path $namingReport -Encoding UTF8 -Value $lines
}

Wait-Job -Job $jobs -Timeout 900 | Out-Null
foreach($j in $jobs){
  if($j.State -eq 'Running'){
    Stop-Job $j -Force
    $p = Join-Path $RunnerOutput "$TaskId`_$($j.Name)_timeout.txt"
    Set-Content -Path $p -Encoding UTF8 -Value "JOB_TIMEOUT=$($j.Name)"
  }
  Receive-Job $j -ErrorAction SilentlyContinue | Out-File -FilePath (Join-Path $RunnerOutput "$TaskId`_$($j.Name)_stdout.txt") -Encoding UTF8
  Remove-Job $j -Force -ErrorAction SilentlyContinue
}

# Aggregate decision.
$blockers = New-Object System.Collections.Generic.List[string]
function FileHas([string]$Path,[string]$Needle){ if(Test-Path $Path){ return ((Get-Content $Path -Raw -ErrorAction SilentlyContinue) -like "*$Needle*") } return $false }

if(-not (FileHas $tokenReport 'FINAL_TOKEN_SET_PRESENT=True')){ $blockers.Add('final_tokens_not_all_verified') }
if(FileHas $remoteReport 'REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK'){ $blockers.Add('remote_branch_diverged_non_fast_forward') }
if(FileHas $remoteReport 'REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE'){ $blockers.Add('remote_branch_not_found_or_unreadable') }
if(-not (FileHas $dataReport 'DATA_COVERAGE_STATUS=ENGLAND_WIDE_EVIDENCE_PRESENT')){ $blockers.Add('england_wide_coverage_not_proven') }
if(-not (FileHas $lookupReport 'LOOKUP_COVERAGE_STATUS=PARTIAL_OR_GOOD_DATA_PRESENT')){ $blockers.Add('lookup_data_presence_not_proven') }
if(-not (FileHas $uiReport 'UI_STATIC_CONTRACT_STATUS=CHECKED')){ $blockers.Add('ui_static_contract_not_verified') }
if(FileHas $namingReport 'NAMING_DEBT_STATUS=DEBT_PRESENT_COMPATIBILITY_RENAME_PLAN_REQUIRED'){ $blockers.Add('pb_naming_debt_present') }

$manualEvidence = Get-ChildItem -Path $Reports -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'manual.*ui.*smoke|ui.*smoke.*manual' }
if($manualEvidence.Count -eq 0){ $blockers.Add('manual_ui_parcel_click_smoke_not_git_visible') }

$progress = 88
if($blockers.Count -le 5){ $progress = 92 }
if($blockers.Count -le 3){ $progress = 96 }
if($blockers.Count -eq 0){ $progress = 100 }

$finalLines = New-Object System.Collections.Generic.List[string]
$finalLines.Add("TASK_ID=$TaskId")
$finalLines.Add("PAGE_KEY=$PageKey")
$finalLines.Add("STARTED_AT=$StartedAt")
$finalLines.Add("FINISHED_AT=$((Get-Date).ToString('s'))")
$finalLines.Add("REPORT_KIND=final_report")
$finalLines.Add("LOCAL_TECHNICAL_COMPLETION_FROM_HANDOFF=100")
$finalLines.Add("PRODUCT_PROGRESS_ESTIMATE=$progress")
$finalLines.Add("BLOCKER_COUNT=$($blockers.Count)")
foreach($b in $blockers){ $finalLines.Add("BLOCKER=$b") }
$finalLines.Add("EVIDENCE_REPORT=$contractReport")
$finalLines.Add("EVIDENCE_REPORT=$tokenReport")
$finalLines.Add("EVIDENCE_REPORT=$remoteReport")
$finalLines.Add("EVIDENCE_REPORT=$dataReport")
$finalLines.Add("EVIDENCE_REPORT=$lookupReport")
$finalLines.Add("EVIDENCE_REPORT=$uiReport")
$finalLines.Add("EVIDENCE_REPORT=$namingReport")
Write-TextFile $finalReport $finalLines

$statusLines = New-Object System.Collections.Generic.List[string]
$statusLines.Add("TASK_ID=$TaskId")
$statusLines.Add("PAGE_KEY=$PageKey")
$statusLines.Add("PRODUCT_PROGRESS_ESTIMATE=$progress")
$statusLines.Add("BLOCKER_COUNT=$($blockers.Count)")
if($blockers.Count -eq 0){
  $statusLines.Add('FINAL_STATUS=FINAL_READY_CONFIRMED')
  $statusLines.Add('PRODUCTION_COMPLETE=true')
  $statusLines.Add('PRODUCT_100_READY=true')
} else {
  $statusLines.Add('FINAL_STATUS=BLOCKED_NEEDS_EVIDENCE')
  $statusLines.Add('PRODUCTION_COMPLETE=false')
  $statusLines.Add('PRODUCT_100_READY=false')
  foreach($b in $blockers){ $statusLines.Add("BLOCKER=$b") }
}
Write-TextFile $finalStatus $statusLines

Add-Line $heartbeatFile "STATUS=FINISHED"
Add-Line $heartbeatFile "FINISHED_AT=$((Get-Date).ToString('s'))"
Add-Line $heartbeatFile "FINAL_STATUS_FILE=$finalStatus"
Add-Line $heartbeatFile "FINAL_REPORT_FILE=$finalReport"

# Optional safe git publish if this script is executed inside the local worktree and credentials are available.
# No force push. If push fails, write the failure to runner_output and leave local evidence intact.
try {
  Push-Location $RepoRoot
  git add "docs/chatgpt_status/$PageKey/reports" "docs/chatgpt_status/$PageKey/status" "docs/chatgpt_status/$PageKey/heartbeat" "docs/chatgpt_status/$PageKey/runner_output" 2>&1 | Out-File -FilePath (Join-Path $RunnerOutput "$TaskId`_git_add.txt") -Encoding UTF8
  $diffQuiet = git diff --cached --quiet; $hasChanges = ($LASTEXITCODE -ne 0)
  if($hasChanges){
    git commit -m "AAYS Topography: publish contract recovery audit outputs" 2>&1 | Out-File -FilePath (Join-Path $RunnerOutput "$TaskId`_git_commit.txt") -Encoding UTF8
    git push origin HEAD 2>&1 | Out-File -FilePath (Join-Path $RunnerOutput "$TaskId`_git_push.txt") -Encoding UTF8
  }
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  Set-Content -Path (Join-Path $RunnerOutput "$TaskId`_git_publish_error.txt") -Encoding UTF8 -Value "GIT_PUBLISH_ERROR=$($_.Exception.Message)"
}

exit 0
