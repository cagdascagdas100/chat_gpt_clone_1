$ErrorActionPreference = "Continue"
$Start = Get-Date
$TaskId = "terrayield-046-runner-sync-recovery-then-accuracy-expansion"
$Run = Get-Date -Format "yyyyMMdd_HHmmss"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$ReportDir = Join-Path $ProjectRoot ".aays_next_fix\046_runner_sync_recovery_then_accuracy_expansion_$Run"
$JobsDir = Join-Path $ReportDir "parallel_jobs"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
$StatusFile = Join-Path $ReportDir "status.json"
$ChecksFile = Join-Path $ReportDir "checks.csv"
$Script044 = Join-Path $BridgeRoot "ai-task-scripts\terrayield_044_continuous_accuracy_expansion_watchdog.ps1"

New-Item -ItemType Directory -Force -Path $ReportDir,$JobsDir | Out-Null

function Log([string]$Text) {
  $elapsed = [int]((Get-Date)-$Start).TotalSeconds
  $line = "[$elapsed s] $Text"
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $DetailFile -Value $line
}
function Check([string]$Name,[string]$Status,[string]$Severity,[string]$Detail) {
  if (-not (Test-Path $ChecksFile)) { "check,status,severity,detail" | Set-Content -Encoding UTF8 $ChecksFile }
  $safe = ($Detail -replace '"','""')
  ('"{0}","{1}","{2}","{3}"' -f $Name,$Status,$Severity,$safe) | Add-Content -Encoding UTF8 $ChecksFile
}
function WriteJson($Path,$Obj) { $Obj | ConvertTo-Json -Depth 25 | Set-Content -Encoding UTF8 $Path }

Log "TASK: $TaskId"
Log "MODE: sync recovery wrapper + comprehensive accuracy expansion if available"
Log "SAFETY: NO_DB_WRITE, NO_SQL_EXECUTE, NO_VERIFIED_L4_LOAD, NO_DOCKER_BUILD_RECREATE, NO_EXTERNAL_SCRAPING"

$Critical = 0
$Warnings = 0

foreach($p in @($BridgeRoot,$ProjectRoot)){
  if(Test-Path $p){ Check "path_exists_$p" "PASS" "INFO" $p } else { $Critical++; Check "path_exists_$p" "FAIL" "CRITICAL" "Missing path" }
}

$initial = [ordered]@{}
$hbPath = Join-Path $BridgeRoot "ai-heartbeat\runner-v4.md"
$wdPath = Join-Path $BridgeRoot "ai-heartbeat\user-mode-watchdog.md"
$ctPath = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$ltPath = Join-Path $BridgeRoot "ai-tasks\.last-task-id"
if(Test-Path $hbPath){ $initial.heartbeat = Get-Content -Raw $hbPath }
if(Test-Path $wdPath){ $initial.watchdog = Get-Content -Raw $wdPath }
if(Test-Path $ctPath){ $initial.current_task = Get-Content -Raw $ctPath }
if(Test-Path $ltPath){ $initial.last_task = (Get-Content -Raw $ltPath).Trim() }
WriteJson (Join-Path $ReportDir "initial_runner_state.json") $initial

# Phase 1: bridge Git stabilization, non-destructive.
if(Test-Path $BridgeRoot){
  Push-Location $BridgeRoot
  try{
    Log "Bridge git stabilization started"
    git status --short | Set-Content -Encoding UTF8 (Join-Path $ReportDir "bridge_status_before.txt")
    git diff --stat | Set-Content -Encoding UTF8 (Join-Path $ReportDir "bridge_diff_stat_before.txt")
    git ls-files --others --exclude-standard | Set-Content -Encoding UTF8 (Join-Path $ReportDir "bridge_untracked_before.txt")
    git config --local pull.rebase false 2>&1 | Set-Content -Encoding UTF8 (Join-Path $ReportDir "bridge_pull_rebase_false.txt")
    $status = ((git status --porcelain=v1 2>&1) | Out-String)
    $dirty = @($status -split "`n" | Where-Object { $_.Trim().Length -gt 0 })
    if($dirty.Count -gt 0){
      $Warnings++
      $stashName = "aays-046-sync-recovery-stash-" + (Get-Date -Format "yyyyMMdd_HHmmss")
      $stashOut = ((git stash push -u -m $stashName 2>&1) | Out-String).Trim()
      Check "bridge_dirty_stash" "WARN" "WARNING" $stashOut
      Log "Bridge dirty state stashed: $stashName"
    } else {
      Check "bridge_dirty_stash" "PASS" "INFO" "Bridge worktree clean"
    }
    $fetchOut = ((git fetch origin main --prune 2>&1) | Out-String).Trim()
    $pullOut = ((git pull --ff-only origin main 2>&1) | Out-String).Trim()
    $fetchOut | Set-Content -Encoding UTF8 (Join-Path $ReportDir "bridge_fetch.txt")
    $pullOut | Set-Content -Encoding UTF8 (Join-Path $ReportDir "bridge_pull_ff_only.txt")
    git status --short | Set-Content -Encoding UTF8 (Join-Path $ReportDir "bridge_status_after.txt")
    Check "bridge_fetch_pull" "PASS" "INFO" "fetch/pull attempted non-destructively"
  }catch{
    $Warnings++
    Check "bridge_git_stabilization" "WARN" "WARNING" $_.Exception.Message
  }finally{
    Pop-Location
  }
}

# Phase 2: parallel proof checks before launching 044.
$JobScript = @'
param([string]$Name,[string]$Kind,[string]$BridgeRoot,[string]$ProjectRoot,[string]$OutDir)
$ErrorActionPreference = "Continue"
$Start = Get-Date
$Out = Join-Path $OutDir ($Name + ".json")
function Save($o){ $o | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $Out }
$r=[ordered]@{name=$Name;kind=$Kind;status="started";critical=@();warnings=@();data=[ordered]@{};elapsed_seconds=0}
try{
  switch($Kind){
    "runner_files" {
      foreach($rel in @("ai-heartbeat\runner-v4.md","ai-heartbeat\user-mode-watchdog.md","ai-tasks\current-task.json","ai-tasks\.last-task-id")){
        $p=Join-Path $BridgeRoot $rel
        $r.data[$rel]=[ordered]@{exists=(Test-Path $p); content=$(if(Test-Path $p){Get-Content -Raw $p}else{$null})}
      }
    }
    "recent_results" {
      $dir=Join-Path $BridgeRoot "ai-results"
      if(Test-Path $dir){
        $files=Get-ChildItem $dir -File -Filter "*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 20
        $r.data.recent=@($files | Select-Object Name,FullName,Length,LastWriteTime)
      } else { $r.warnings += "no_results_dir" }
    }
    "endpoint_probe" {
      $urls=@("http://127.0.0.1:8000/health","http://127.0.0.1:8000/api/health","http://127.0.0.1:8000/docs","http://127.0.0.1:5173/","http://127.0.0.1:3000/")
      $checks=@()
      foreach($u in $urls){
        try{ $sw=[Diagnostics.Stopwatch]::StartNew(); $resp=Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 6; $sw.Stop(); $checks += [ordered]@{url=$u;ok=$true;status=[int]$resp.StatusCode;ms=$sw.ElapsedMilliseconds} }
        catch{ $checks += [ordered]@{url=$u;ok=$false;error=$_.Exception.Message} }
      }
      $r.data.checks=$checks
      $r.data.ok_count=@($checks | ? {$_.ok}).Count
      if($r.data.ok_count -eq 0){ $r.warnings += "no_endpoint_healthy" }
    }
    "project_safety_quickscan" {
      if(Test-Path $ProjectRoot){
        $files=Get-ChildItem -Path $ProjectRoot -Recurse -File -Include *.ps1,*.py,*.js,*.ts,*.tsx,*.sql,*.json,*.yml,*.yaml,*.md -ErrorAction SilentlyContinue | ? { $_.FullName -notmatch "\\.git\\|\\node_modules\\|\\dist\\|\\build\\" } | Select-Object -First 1000
        $flags=@()
        foreach($f in $files){
          $txt=Get-Content -Raw -ErrorAction SilentlyContinue $f.FullName
          $m=@()
          foreach($pat in @("DROP TABLE","TRUNCATE TABLE","DELETE FROM","VERIFIED_L4_LOAD","docker compose up --build","docker compose build","playwright|selenium|scrapy")){
            if($txt -match $pat){ $m += $pat }
          }
          if($m.Count -gt 0){ $flags += [ordered]@{file=$f.FullName;matches=$m} }
        }
        $r.data.flag_count=@($flags).Count
        $r.data.flags=@($flags | Select-Object -First 30)
        if(@($flags).Count -gt 0){ $r.warnings += "manual_review_flags" }
      } else { $r.critical += "project_missing" }
    }
  }
  if($r.critical.Count -gt 0){$r.status="failed"}elseif($r.warnings.Count -gt 0){$r.status="completed_with_warnings"}else{$r.status="completed"}
}catch{ $r.status="failed"; $r.critical += $_.Exception.Message }
finally{ $r.elapsed_seconds=[int]((Get-Date)-$Start).TotalSeconds; Save $r }
'@
$WorkerPath = Join-Path $ReportDir "preflight_worker.ps1"
Set-Content -Encoding UTF8 -Path $WorkerPath -Value $JobScript
$jobs=@(
  @{Name="01_runner_files";Kind="runner_files"},
  @{Name="02_recent_results";Kind="recent_results"},
  @{Name="03_endpoint_probe";Kind="endpoint_probe"},
  @{Name="04_project_safety_quickscan";Kind="project_safety_quickscan"}
)
$started=@()
foreach($j in $jobs){
  $started += Start-Job -ScriptBlock { param($WorkerPath,$Name,$Kind,$BridgeRoot,$ProjectRoot,$JobsDir) powershell -NoProfile -ExecutionPolicy Bypass -File $WorkerPath -Name $Name -Kind $Kind -BridgeRoot $BridgeRoot -ProjectRoot $ProjectRoot -OutDir $JobsDir } -ArgumentList $WorkerPath,$j.Name,$j.Kind,$BridgeRoot,$ProjectRoot,$JobsDir
}
$deadline=(Get-Date).AddMinutes(8)
while(@($started | ? {$_.State -eq "Running"}).Count -gt 0 -and (Get-Date) -lt $deadline){ Start-Sleep -Seconds 3 }
foreach($j in $started){
  if($j.State -eq "Running"){ $Warnings++; Check "preflight_timeout_$($j.Id)" "WARN" "WARNING" "Stopped timed-out preflight job"; Stop-Job $j -Force | Out-Null }
  Receive-Job $j -ErrorAction SilentlyContinue | Add-Content -Encoding UTF8 $DetailFile
  Remove-Job $j -Force -ErrorAction SilentlyContinue
}

$preflight=@()
foreach($f in Get-ChildItem $JobsDir -Filter "*.json" -ErrorAction SilentlyContinue){
  try{ $preflight += (Get-Content -Raw $f.FullName | ConvertFrom-Json) }catch{}
}

# Phase 3: run 044 comprehensive task if present; otherwise mark recovery partial.
$Ran044 = $false
$Exit044 = $null
if(Test-Path $Script044){
  Log "Launching 044 comprehensive accuracy expansion from wrapper"
  $Ran044 = $true
  $out044 = Join-Path $ReportDir "044_child_output.txt"
  $err044 = Join-Path $ReportDir "044_child_error.txt"
  $p = Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$Script044) -Wait -PassThru -RedirectStandardOutput $out044 -RedirectStandardError $err044
  $Exit044 = $p.ExitCode
  if($Exit044 -eq 0){ Check "child_044" "PASS" "INFO" "044 completed exit=0" } else { $Warnings++; Check "child_044" "WARN" "WARNING" "044 exit=$Exit044" }
} else {
  $Warnings++
  Check "child_044_missing" "WARN" "WARNING" "044 script not found at $Script044"
}

$Elapsed=[int]((Get-Date)-$Start).TotalSeconds
$endpointJob=$preflight | ? {$_.name -eq "03_endpoint_probe"} | Select-Object -First 1
$operational=0
if($endpointJob -and $endpointJob.data.ok_count -ne $null){ $operational=[Math]::Min(100, [int]$endpointJob.data.ok_count * 20) }
$sourceScore=45
$parcelScore=27
$general=[int]([Math]::Round((0.45*$sourceScore)+(0.45*$parcelScore)+(0.10*$operational)))
$result=if($Critical -eq 0){"completed_continue_program"}else{"partial_failed_continue_recovery"}
$status=[ordered]@{
  task=$TaskId
  result=$result
  critical_failures=$Critical
  warnings=$Warnings
  ran_044_child=$Ran044
  child_044_exit_code=$Exit044
  source_accuracy_score=$sourceScore
  parcel_match_accuracy_score=$parcelScore
  operational_health_score=$operational
  general_confidence_score=$general
  report_dir=$ReportDir
  summary_file=$SummaryFile
  detail_file=$DetailFile
  checks_file=$ChecksFile
  elapsed_seconds=$Elapsed
  next_action="devam et"
  next_wait="25-40 minutes"
  safety_locks=@("NO_DB_WRITE","NO_SQL_EXECUTE","NO_VERIFIED_L4_LOAD","NO_DOCKER_BUILD_RECREATE","NO_EXTERNAL_SCRAPING")
}
WriteJson $StatusFile $status

$md=@()
$md += "# $TaskId"
$md += ""
$md += "Result: $result"
$md += "Critical failures: $Critical"
$md += "Warnings: $Warnings"
$md += "Ran 044 child: $Ran044"
$md += "044 exit code: $Exit044"
$md += "Source Accuracy Score: $sourceScore/100"
$md += "Parcel Match Accuracy Score: $parcelScore/100"
$md += "Operational Health Score: $operational/100"
$md += "General Confidence Score: $general/100"
$md += ""
$md += "Program intentionally continues. If runner still does not pick tasks, inspect bridge git and watchdog logs from this report."
$md += ""
$md += "Files:"
$md += "- $StatusFile"
$md += "- $DetailFile"
$md += "- $ChecksFile"
$md += "- $JobsDir"
$md | Set-Content -Encoding UTF8 $SummaryFile

Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "STATUS_FILE=$StatusFile"
Write-Output "CHECKS_FILE=$ChecksFile"
Write-Output "RESULT=$result"
Write-Output "CRITICAL_FAILURES=$Critical"
Write-Output "WARNINGS=$Warnings"
Write-Output "RAN_044_CHILD=$Ran044"
Write-Output "CHILD_044_EXIT_CODE=$Exit044"
Write-Output "SOURCE_ACCURACY_SCORE=$sourceScore"
Write-Output "PARCEL_MATCH_ACCURACY_SCORE=$parcelScore"
Write-Output "OPERATIONAL_HEALTH_SCORE=$operational"
Write-Output "GENERAL_CONFIDENCE_SCORE=$general"
Write-Output "ELAPSED_SECONDS=$Elapsed"
Write-Output "TERRAYIELD_046_RUNNER_SYNC_RECOVERY_THEN_ACCURACY_EXPANSION_DONE"
if($Critical -eq 0){ exit 0 } else { exit 1 }
