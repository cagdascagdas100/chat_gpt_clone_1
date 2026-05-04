$ErrorActionPreference = "Continue"
$Start = Get-Date
$TaskId = "terrayield-verification-026-comprehensive-parallel-watchdog-recovery"
$Run = Get-Date -Format "yyyyMMdd_HHmmss"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$ReportDir = Join-Path $ProjectRoot ".aays_next_fix\verification_026_comprehensive_parallel_watchdog_recovery_$Run"
$JobsDir = Join-Path $ReportDir "parallel_jobs"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
$StatusFile = Join-Path $ReportDir "status.json"
$ChecksFile = Join-Path $ReportDir "checks.csv"

New-Item -ItemType Directory -Force -Path $ReportDir, $JobsDir | Out-Null

function Log([string]$Text) {
  $elapsed = [int]((Get-Date) - $Start).TotalSeconds
  $line = "[$elapsed s] $Text"
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $DetailFile -Value $line
}
function Check([string]$Name,[string]$Status,[string]$Severity,[string]$Detail) {
  if (-not (Test-Path $ChecksFile)) { "check,status,severity,detail" | Set-Content -Encoding UTF8 $ChecksFile }
  $safe = ($Detail -replace '"','""')
  ('"{0}","{1}","{2}","{3}"' -f $Name,$Status,$Severity,$safe) | Add-Content -Encoding UTF8 $ChecksFile
}
function WriteJson($Path,$Obj) { $Obj | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $Path }

Log "TASK: $TaskId"
Log "PROGRESS: 99%"
Log "MODE: comprehensive parallel watchdog + stuck detection + safe recovery"
Log "SAFETY: NO_DB_WRITE, NO_SQL_EXECUTE, NO_VERIFIED_L4_LOAD, NO_DOCKER_BUILD_RECREATE, NO_EXTERNAL_SCRAPING"

$Critical = 0
$Warnings = 0

foreach ($p in @($BridgeRoot,$ProjectRoot)) {
  if (Test-Path $p) { Check "path_exists_$p" "PASS" "INFO" $p } else { $Critical++; Check "path_exists_$p" "FAIL" "CRITICAL" "Missing path" }
}

$Worker = @'
param([string]$Name,[string]$Kind,[string]$BridgeRoot,[string]$ProjectRoot,[string]$OutDir)
$ErrorActionPreference = "Continue"
$Start = Get-Date
$Out = Join-Path $OutDir ($Name + ".json")
$Log = Join-Path $OutDir ($Name + ".log")
function L($t){ $e=[int]((Get-Date)-$Start).TotalSeconds; "[$e s] $t" | Tee-Object -FilePath $Log -Append | Out-Null }
function Save($o){ $o | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $Out }
$r=[ordered]@{name=$Name;kind=$Kind;status="started";critical=@();warnings=@();data=[ordered]@{};elapsed_seconds=0}
try {
  switch ($Kind) {
    "runner_state" {
      $hb=Join-Path $BridgeRoot "ai-heartbeat\runner-v4.md"
      $wd=Join-Path $BridgeRoot "ai-heartbeat\user-mode-watchdog.md"
      $ct=Join-Path $BridgeRoot "ai-tasks\current-task.json"
      $lt=Join-Path $BridgeRoot "ai-tasks\.last-task-id"
      $r.data.heartbeat_exists=Test-Path $hb
      $r.data.watchdog_exists=Test-Path $wd
      $r.data.current_task_exists=Test-Path $ct
      $r.data.last_task_exists=Test-Path $lt
      if (Test-Path $hb) { $r.data.heartbeat=(Get-Content -Raw $hb) }
      if (Test-Path $wd) { $r.data.watchdog=(Get-Content -Raw $wd) }
      if (Test-Path $ct) { $r.data.current_task=(Get-Content -Raw $ct | ConvertFrom-Json) }
      if (Test-Path $lt) { $r.data.last_task=(Get-Content -Raw $lt).Trim() }
      $r.data.runner_processes=@(Get-Process -Name powershell,pwsh -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,StartTime,Path | Select-Object -First 20)
      if ($r.data.heartbeat -match "Status:\s+running") { $r.warnings += "runner_reports_running_inside_task" }
    }
    "bridge_git_repair" {
      if (-not (Test-Path $BridgeRoot)) { $r.critical += "bridge_missing"; break }
      Push-Location $BridgeRoot
      $r.data.branch=((git rev-parse --abbrev-ref HEAD 2>&1)|Out-String).Trim()
      $r.data.head_before=((git rev-parse --short HEAD 2>&1)|Out-String).Trim()
      $status=((git status --porcelain=v1 2>&1)|Out-String)
      $r.data.status_before=$status.Trim()
      $dirty=@($status -split "`n" | ? { $_.Trim().Length -gt 0 })
      $r.data.dirty_count_before=$dirty.Count
      git status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_status_before.txt")
      git diff --stat | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_diff_stat_before.txt")
      git ls-files --others --exclude-standard | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_untracked_before.txt")
      git config --local pull.rebase false 2>&1 | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_git_config_pull_rebase_false.txt")
      if ($dirty.Count -gt 0) {
        $stash="aays-026-auto-stash-"+(Get-Date -Format "yyyyMMdd_HHmmss")
        $stashOut=((git stash push -u -m $stash 2>&1)|Out-String).Trim()
        $r.data.stash_name=$stash
        $r.data.stash_output=$stashOut
        $r.warnings += "dirty_worktree_stashed"
      }
      $fetch=((git fetch origin main --prune 2>&1)|Out-String).Trim()
      $r.data.fetch_output=$fetch
      $r.data.head_after=((git rev-parse --short HEAD 2>&1)|Out-String).Trim()
      $status2=((git status --porcelain=v1 2>&1)|Out-String)
      $r.data.status_after=$status2.Trim()
      $r.data.dirty_count_after=@($status2 -split "`n" | ? { $_.Trim().Length -gt 0 }).Count
      Pop-Location
    }
    "project_git_snapshot" {
      if (-not (Test-Path $ProjectRoot)) { $r.critical += "project_missing"; break }
      Push-Location $ProjectRoot
      $r.data.branch=((git rev-parse --abbrev-ref HEAD 2>&1)|Out-String).Trim()
      $r.data.head=((git rev-parse --short HEAD 2>&1)|Out-String).Trim()
      $status=((git status --porcelain=v1 2>&1)|Out-String)
      $r.data.status=$status.Trim()
      $r.data.dirty_count=@($status -split "`n" | ? { $_.Trim().Length -gt 0 }).Count
      git status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "project_status.txt")
      git diff --stat | Set-Content -Encoding UTF8 (Join-Path $OutDir "project_diff_stat.txt")
      Pop-Location
    }
    "recent_results_audit" {
      $res=Join-Path $BridgeRoot "ai-results"
      if (-not (Test-Path $res)) { $r.warnings += "no_ai_results_dir"; break }
      $files=Get-ChildItem $res -File -Filter "*.md" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 15
      $r.data.recent=@($files | Select-Object Name,FullName,Length,LastWriteTime)
      $scan=@()
      foreach($f in $files){
        $txt=Get-Content -Raw -ErrorAction SilentlyContinue $f.FullName
        $scan += [ordered]@{ name=$f.Name; exit0=($txt -match "Exit Code\s*\n0|ExitCode=0|RESULT=completed|RESULT=healthy_or_recovered"); critical=($txt -match "CRITICAL_FAILURES=[1-9]|Critical failures:\s*[1-9]"); warnings=($txt -match "WARNINGS=[1-9]|Warnings:\s*[1-9]"); api_ok=($txt -match "API_READY=.*True|API_HEALTH.*True|API_OR_UI_ENDPOINT_OK=True") }
      }
      $r.data.scan=$scan
      $scan | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $OutDir "recent_results_scan.json")
    }
    "endpoint_recover_if_needed" {
      $urls=@("http://127.0.0.1:8000/health","http://127.0.0.1:8000/api/health","http://127.0.0.1:8000/docs","http://127.0.0.1:5173/","http://127.0.0.1:3000/")
      $checks=@()
      foreach($u in $urls){
        try { $sw=[Diagnostics.Stopwatch]::StartNew(); $resp=Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 7; $sw.Stop(); $checks += [ordered]@{url=$u;ok=$true;status=[int]$resp.StatusCode;ms=$sw.ElapsedMilliseconds} }
        catch { $checks += [ordered]@{url=$u;ok=$false;error=$_.Exception.Message} }
      }
      $r.data.initial_checks=$checks
      $ok=@($checks | ? {$_.ok}).Count
      $r.data.initial_ok_count=$ok
      if ($ok -eq 0 -and (Test-Path $ProjectRoot)) {
        Push-Location $ProjectRoot
        $r.warnings += "endpoint_unhealthy_try_api_only_restart"
        $compose = Get-Command docker -ErrorAction SilentlyContinue
        if ($compose) {
          $restartOut=((docker compose up -d api 2>&1)|Out-String).Trim()
          $r.data.api_restart_output=$restartOut
          Start-Sleep -Seconds 20
          $checks2=@()
          foreach($u in $urls){
            try { $sw=[Diagnostics.Stopwatch]::StartNew(); $resp=Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 7; $sw.Stop(); $checks2 += [ordered]@{url=$u;ok=$true;status=[int]$resp.StatusCode;ms=$sw.ElapsedMilliseconds} }
            catch { $checks2 += [ordered]@{url=$u;ok=$false;error=$_.Exception.Message} }
          }
          $r.data.after_restart_checks=$checks2
          if (@($checks2 | ? {$_.ok}).Count -eq 0) { $r.warnings += "endpoint_still_unhealthy_after_api_restart" }
        } else { $r.warnings += "docker_not_available_no_restart" }
        Pop-Location
      }
    }
    "safe_sales_evidence_audit" {
      if (-not (Test-Path $ProjectRoot)) { $r.critical += "project_missing"; break }
      $safeDir=Join-Path $ProjectRoot ".aays_safe_sales"
      New-Item -ItemType Directory -Force -Path $safeDir | Out-Null
      $policy=[ordered]@{
        purpose="Safe sales to parcel evidence pipeline"
        safety_locks=@("NO_DB_WRITE","NO_SQL_EXECUTE","NO_VERIFIED_L4_LOAD","NO_DOCKER_BUILD_RECREATE","NO_EXTERNAL_SCRAPING")
        confidence_levels=@("L0 raw/untrusted","L1 parsed","L2 source-hash verified","L3 cross-source matched","L4 manual reviewed only - load disabled")
        required_fields=@("source_name","source_url_or_path","licence","capture_date","raw_sha256","sale_date","price","area_m2","price_per_m2","address_or_location","parcel_candidate_id","geometry_method","confidence","evidence_files")
        export_rule="Only low-volume evidence manifests and hashes may be exported; raw files remain local/E-drive or approved storage."
      }
      $policyPath=Join-Path $safeDir "verification_policy_026.json"
      $policy | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $policyPath
      $hits=Get-ChildItem -Path $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue | ? { $_.FullName -notmatch "\\.git\\|\\node_modules\\|\\dist\\|\\build\\" -and $_.Name -match "sale|sales|parcel|evidence|registry|verification|backlog" } | Select-Object -First 200 FullName,Length,LastWriteTime
      $r.data.policy_path=$policyPath
      $r.data.hit_count=@($hits).Count
      $r.data.sample=@($hits | Select-Object -First 60)
      $hits | % FullName | Set-Content -Encoding UTF8 (Join-Path $OutDir "safe_sales_evidence_hits.txt")
      if (@($hits).Count -lt 5) { $r.warnings += "safe_sales_scaffold_sparse" }
    }
    "safety_red_flag_scan" {
      if (-not (Test-Path $ProjectRoot)) { $r.critical += "project_missing"; break }
      $files=Get-ChildItem -Path $ProjectRoot -Recurse -File -Include *.ps1,*.py,*.js,*.ts,*.tsx,*.sql,*.json,*.yml,*.yaml,*.md -ErrorAction SilentlyContinue | ? { $_.FullName -notmatch "\\.git\\|\\node_modules\\|\\dist\\|\\build\\" } | Select-Object -First 1500
      $flags=@()
      foreach($f in $files){
        $txt=Get-Content -Raw -ErrorAction SilentlyContinue $f.FullName
        $m=@()
        foreach($pat in @("DROP TABLE","TRUNCATE TABLE","DELETE FROM","INSERT INTO","UPDATE\s+.+\s+SET","VERIFIED_L4_LOAD","docker compose up --build","docker-compose up --build","docker compose build","Invoke-WebRequest.+http","scrapy|selenium|playwright")){
          if($txt -match $pat){ $m += $pat }
        }
        if($m.Count -gt 0){ $flags += [ordered]@{file=$f.FullName;matches=$m} }
      }
      $r.data.scanned=@($files).Count
      $r.data.flag_count=@($flags).Count
      $r.data.flags=@($flags | Select-Object -First 50)
      $flags | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $OutDir "safety_red_flags.json")
      if(@($flags).Count -gt 0){ $r.warnings += "manual_review_red_flags_found" }
    }
  }
  if($r.critical.Count -gt 0){$r.status="failed"}
  elseif($r.warnings.Count -gt 0){$r.status="completed_with_warnings"}
  else{$r.status="completed"}
} catch {
  $r.status="failed"; $r.critical += $_.Exception.Message
} finally {
  $r.elapsed_seconds=[int]((Get-Date)-$Start).TotalSeconds
  Save $r
}
'@

$WorkerPath = Join-Path $ReportDir "worker.ps1"
Set-Content -Encoding UTF8 -Path $WorkerPath -Value $Worker

$items=@(
  @{Name="01_runner_state";Kind="runner_state"},
  @{Name="02_bridge_git_repair";Kind="bridge_git_repair"},
  @{Name="03_project_git_snapshot";Kind="project_git_snapshot"},
  @{Name="04_recent_results_audit";Kind="recent_results_audit"},
  @{Name="05_endpoint_recover_if_needed";Kind="endpoint_recover_if_needed"},
  @{Name="06_safe_sales_evidence_audit";Kind="safe_sales_evidence_audit"},
  @{Name="07_safety_red_flag_scan";Kind="safety_red_flag_scan"}
)

$jobs=@()
foreach($it in $items){
  $jobs += Start-Job -ScriptBlock { param($WorkerPath,$Name,$Kind,$BridgeRoot,$ProjectRoot,$JobsDir) powershell -NoProfile -ExecutionPolicy Bypass -File $WorkerPath -Name $Name -Kind $Kind -BridgeRoot $BridgeRoot -ProjectRoot $ProjectRoot -OutDir $JobsDir } -ArgumentList $WorkerPath,$it.Name,$it.Kind,$BridgeRoot,$ProjectRoot,$JobsDir
}
Log "Started comprehensive parallel jobs: $($jobs.Count)"
$deadline=(Get-Date).AddMinutes(24)
while(@($jobs | ? {$_.State -eq "Running"}).Count -gt 0 -and (Get-Date) -lt $deadline){ Start-Sleep -Seconds 5 }
foreach($j in $jobs){
  if($j.State -eq "Running"){ $Warnings++; Check "job_timeout_$($j.Id)" "WARN" "WARNING" "Stopped timed-out subjob only"; Stop-Job $j -Force | Out-Null }
  Receive-Job $j -ErrorAction SilentlyContinue | Add-Content -Encoding UTF8 $DetailFile
  Remove-Job $j -Force -ErrorAction SilentlyContinue
}

$results=@()
foreach($f in Get-ChildItem $JobsDir -Filter "*.json" -ErrorAction SilentlyContinue){
  try{
    $jr=Get-Content -Raw $f.FullName | ConvertFrom-Json
    $results += $jr
    if($jr.status -eq "failed"){ $Critical++; Check $jr.name "FAIL" "CRITICAL" (($jr.critical|Out-String).Trim()) }
    elseif($jr.status -eq "completed_with_warnings"){ $Warnings++; Check $jr.name "WARN" "WARNING" (($jr.warnings|Out-String).Trim()) }
    else{ Check $jr.name "PASS" "INFO" $jr.status }
  } catch { $Warnings++; Check "parse_$($f.Name)" "WARN" "WARNING" $_.Exception.Message }
}

$endpoint=$results | ? {$_.name -eq "05_endpoint_recover_if_needed"} | Select-Object -First 1
$endpointOk=$false
if($endpoint -and $endpoint.data){
  if($endpoint.data.initial_ok_count -gt 0){$endpointOk=$true}
  if($endpoint.data.after_restart_checks){ if(@($endpoint.data.after_restart_checks | ? {$_.ok}).Count -gt 0){$endpointOk=$true} }
}
$bridge=$results | ? {$_.name -eq "02_bridge_git_repair"} | Select-Object -First 1
$dirtyStashed=$false
if($bridge -and ($bridge.warnings -contains "dirty_worktree_stashed")){ $dirtyStashed=$true }

$Elapsed=[int]((Get-Date)-$Start).TotalSeconds
$Result=if($Critical -eq 0){"completed"}else{"partial_failed"}
$status=[ordered]@{
  task=$TaskId
  result=$Result
  progress=99
  critical_failures=$Critical
  warnings=$Warnings
  endpoint_ok=$endpointOk
  bridge_dirty_stashed=$dirtyStashed
  report_dir=$ReportDir
  summary_file=$SummaryFile
  detail_file=$DetailFile
  checks_file=$ChecksFile
  elapsed_seconds=$Elapsed
  next_wait="20-30 minutes if queued; 5-10 minutes if polling and no new result"
  next_action="devam et"
  safety_locks=@("NO_DB_WRITE","NO_SQL_EXECUTE","NO_VERIFIED_L4_LOAD","NO_DOCKER_BUILD_RECREATE","NO_EXTERNAL_SCRAPING")
}
WriteJson $StatusFile $status

$md=@()
$md += "# $TaskId"
$md += ""
$md += "Result: $Result"
$md += "Progress: 99%"
$md += "Critical failures: $Critical"
$md += "Warnings: $Warnings"
$md += "Endpoint OK: $endpointOk"
$md += "Bridge dirty stashed: $dirtyStashed"
$md += "Elapsed seconds: $Elapsed"
$md += ""
$md += "Safety locks: NO_DB_WRITE, NO_SQL_EXECUTE, NO_VERIFIED_L4_LOAD, NO_DOCKER_BUILD_RECREATE, NO_EXTERNAL_SCRAPING"
$md += ""
$md += "Parallel results:"
foreach($r in $results){ $md += "- $($r.name): $($r.status)" }
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
Write-Output "RESULT=$Result"
Write-Output "CRITICAL_FAILURES=$Critical"
Write-Output "WARNINGS=$Warnings"
Write-Output "ENDPOINT_OK=$endpointOk"
Write-Output "BRIDGE_DIRTY_STASHED=$dirtyStashed"
Write-Output "ELAPSED_SECONDS=$Elapsed"
Write-Output "VERIFICATION_026_COMPREHENSIVE_PARALLEL_WATCHDOG_RECOVERY_DONE"
if($Critical -eq 0){exit 0}else{exit 1}
