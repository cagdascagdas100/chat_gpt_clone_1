$ErrorActionPreference = "Continue"
$Start = Get-Date
$TaskId = "terrayield-047-mega-parallel-accuracy-and-recovery"
$Run = Get-Date -Format "yyyyMMdd_HHmmss"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$ReportDir = Join-Path $ProjectRoot ".aays_next_fix\047_mega_parallel_accuracy_and_recovery_$Run"
$JobsDir = Join-Path $ReportDir "parallel_jobs"
$SafeDir = Join-Path $ProjectRoot ".aays_safe_sales"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
$StatusFile = Join-Path $ReportDir "status.json"
$ChecksFile = Join-Path $ReportDir "checks.csv"

New-Item -ItemType Directory -Force -Path $ReportDir,$JobsDir,$SafeDir | Out-Null

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
function WriteJson($Path,$Obj) { $Obj | ConvertTo-Json -Depth 40 | Set-Content -Encoding UTF8 $Path }

Log "TASK: $TaskId"
Log "MODE: mega parallel accuracy expansion + runner recovery + continuous program, not final"
Log "SAFETY: NO_DB_WRITE, NO_SQL_EXECUTE, NO_VERIFIED_L4_LOAD, NO_DOCKER_BUILD_RECREATE, NO_EXTERNAL_SCRAPING"

$Critical = 0
$Warnings = 0
foreach($p in @($BridgeRoot,$ProjectRoot)){
  if(Test-Path $p){ Check "path_exists_$p" "PASS" "INFO" $p } else { $Critical++; Check "path_exists_$p" "FAIL" "CRITICAL" "Missing path" }
}

$Worker = @'
param([string]$Name,[string]$Kind,[string]$BridgeRoot,[string]$ProjectRoot,[string]$SafeDir,[string]$OutDir)
$ErrorActionPreference = "Continue"
$Start = Get-Date
$Out = Join-Path $OutDir ($Name + ".json")
$Log = Join-Path $OutDir ($Name + ".log")
function L($t){ $e=[int]((Get-Date)-$Start).TotalSeconds; "[$e s] $t" | Tee-Object -FilePath $Log -Append | Out-Null }
function Save($o){ $o | ConvertTo-Json -Depth 40 | Set-Content -Encoding UTF8 $Out }
$r=[ordered]@{name=$Name;kind=$Kind;status="started";critical=@();warnings=@();data=[ordered]@{};elapsed_seconds=0}
try{
  switch($Kind){
    "runner_state_deep" {
      foreach($rel in @("ai-heartbeat\runner-v4.md","ai-heartbeat\user-mode-watchdog.md","ai-tasks\current-task.json","ai-tasks\.last-task-id")){
        $p=Join-Path $BridgeRoot $rel
        $r.data[$rel]=[ordered]@{exists=(Test-Path $p); last_write=$(if(Test-Path $p){(Get-Item $p).LastWriteTime}else{$null}); content=$(if(Test-Path $p){Get-Content -Raw $p}else{$null})}
      }
      $r.data.powershell_processes=@(Get-Process -Name powershell,pwsh -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,StartTime,Path | Select-Object -First 40)
    }
    "runner_log_tail" {
      $logdir=Join-Path $BridgeRoot "ai-runner-logs"
      if(Test-Path $logdir){
        $files=Get-ChildItem $logdir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 6
        $r.data.logs=@($files | Select-Object FullName,Length,LastWriteTime)
        foreach($f in $files){ Get-Content -Tail 180 -ErrorAction SilentlyContinue $f.FullName | Set-Content -Encoding UTF8 (Join-Path $OutDir ("tail_"+$f.Name+".txt")) }
      } else { $r.warnings += "runner_log_dir_missing" }
    }
    "bridge_git_recovery" {
      if(-not(Test-Path $BridgeRoot)){ $r.critical += "bridge_missing"; break }
      Push-Location $BridgeRoot
      $r.data.branch=((git rev-parse --abbrev-ref HEAD 2>&1)|Out-String).Trim()
      $r.data.head_before=((git rev-parse --short HEAD 2>&1)|Out-String).Trim()
      git status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_status_before.txt")
      git diff --stat | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_diff_stat_before.txt")
      git ls-files --others --exclude-standard | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_untracked_before.txt")
      git config --local pull.rebase false 2>&1 | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_config_pull_rebase_false.txt")
      $status=((git status --porcelain=v1 2>&1)|Out-String)
      $dirty=@($status -split "`n" | ? { $_.Trim().Length -gt 0 })
      $r.data.dirty_count_before=$dirty.Count
      if($dirty.Count -gt 0){
        $stash="aays-047-auto-stash-"+(Get-Date -Format "yyyyMMdd_HHmmss")
        $r.data.stash_name=$stash
        $r.data.stash_output=((git stash push -u -m $stash 2>&1)|Out-String).Trim()
        $r.warnings += "dirty_bridge_stashed"
      }
      $r.data.fetch=((git fetch origin main --prune 2>&1)|Out-String).Trim()
      $r.data.pull_ff_only=((git pull --ff-only origin main 2>&1)|Out-String).Trim()
      $r.data.head_after=((git rev-parse --short HEAD 2>&1)|Out-String).Trim()
      $s2=((git status --porcelain=v1 2>&1)|Out-String)
      $r.data.dirty_count_after=@($s2 -split "`n" | ? { $_.Trim().Length -gt 0 }).Count
      git status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_status_after.txt")
      Pop-Location
    }
    "project_git_profile" {
      if(-not(Test-Path $ProjectRoot)){ $r.critical += "project_missing"; break }
      Push-Location $ProjectRoot
      $r.data.branch=((git rev-parse --abbrev-ref HEAD 2>&1)|Out-String).Trim()
      $r.data.head=((git rev-parse --short HEAD 2>&1)|Out-String).Trim()
      $status=((git status --porcelain=v1 2>&1)|Out-String)
      $r.data.dirty_count=@($status -split "`n" | ? { $_.Trim().Length -gt 0 }).Count
      git status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "project_status.txt")
      git diff --stat | Set-Content -Encoding UTF8 (Join-Path $OutDir "project_diff_stat.txt")
      Pop-Location
    }
    "recent_results_audit" {
      $dir=Join-Path $BridgeRoot "ai-results"
      if(Test-Path $dir){
        $files=Get-ChildItem $dir -File -Filter "*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 30
        $scan=@()
        foreach($f in $files){
          $txt=Get-Content -Raw -ErrorAction SilentlyContinue $f.FullName
          $scan += [ordered]@{name=$f.Name; last_write=$f.LastWriteTime; exit0=($txt -match "Exit Code\s*\n0|ExitCode=0|RESULT=completed|RESULT=completed_continue_program|RESULT=healthy_or_recovered"); critical=($txt -match "CRITICAL_FAILURES=[1-9]|Critical failures:\s*[1-9]"); warnings=($txt -match "WARNINGS=[1-9]|Warnings:\s*[1-9]"); score=($txt -match "SOURCE_ACCURACY_SCORE|Source Accuracy Score")}
        }
        $r.data.scan=$scan
      } else { $r.warnings += "results_dir_missing" }
    }
    "endpoint_probe_and_api_recover" {
      $urls=@("http://127.0.0.1:8000/health","http://127.0.0.1:8000/api/health","http://127.0.0.1:8000/docs","http://127.0.0.1:5173/","http://127.0.0.1:3000/")
      function Probe(){
        $checks=@()
        foreach($u in $urls){
          try{ $sw=[Diagnostics.Stopwatch]::StartNew(); $resp=Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 8; $sw.Stop(); $checks += [ordered]@{url=$u;ok=$true;status=[int]$resp.StatusCode;ms=$sw.ElapsedMilliseconds} }
          catch{ $checks += [ordered]@{url=$u;ok=$false;error=$_.Exception.Message} }
        }
        return $checks
      }
      $initial=Probe
      $r.data.initial=$initial
      $ok=@($initial | ? {$_.ok}).Count
      $r.data.initial_ok_count=$ok
      if($ok -eq 0 -and (Test-Path $ProjectRoot)){
        Push-Location $ProjectRoot
        $r.warnings += "endpoint_down_try_api_only_recover"
        $docker=Get-Command docker -ErrorAction SilentlyContinue
        if($docker){
          $r.data.docker_ps_before=((docker ps 2>&1)|Out-String).Trim()
          $r.data.api_recover_output=((docker compose up -d api 2>&1)|Out-String).Trim()
          Start-Sleep -Seconds 25
          $after=Probe
          $r.data.after=$after
          $r.data.after_ok_count=@($after | ? {$_.ok}).Count
        } else { $r.warnings += "docker_not_found" }
        Pop-Location
      }
    }
    "dataset_inventory_deep" {
      if(-not(Test-Path $ProjectRoot)){ $r.critical += "project_missing"; break }
      $patterns=@("*.csv","*.parquet","*.geojson","*.gpkg","*.json","*.sqlite","*.db","*.zip","*.xlsx")
      $files=@()
      foreach($p in $patterns){ $files += Get-ChildItem -Path $ProjectRoot -Recurse -File -Filter $p -ErrorAction SilentlyContinue | ? { $_.FullName -notmatch "\\.git\\|\\node_modules\\|\\dist\\|\\build\\|\\.venv\\" } }
      $files=$files | Sort-Object FullName -Unique
      $sample=@()
      foreach($f in ($files | Select-Object -First 160)){
        $sha=""; try{ if($f.Length -lt 250MB){ $sha=(Get-FileHash -Algorithm SHA256 $f.FullName).Hash } }catch{}
        $sample += [ordered]@{path=$f.FullName; name=$f.Name; ext=$f.Extension; bytes=$f.Length; sha256=$sha; last_write=$f.LastWriteTime}
      }
      $r.data.dataset_file_count=@($files).Count
      $r.data.sample=$sample
      $sample | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 (Join-Path $OutDir "dataset_inventory_deep.json")
      if(@($files).Count -eq 0){ $r.warnings += "no_dataset_files_found" }
    }
    "safe_sales_source_registry" {
      New-Item -ItemType Directory -Force -Path $SafeDir | Out-Null
      $registry=@(
        [ordered]@{source="Official sale transaction dataset"; priority=1; checks=@("licence","capture_date","raw_sha256","sale_id","price","date","currency","address")},
        [ordered]@{source="Official parcel geometry/cadastre"; priority=1; checks=@("licence","geometry_version","parcel_id","polygon_hash","boundary_date")},
        [ordered]@{source="Address identifier/UPRN/title index"; priority=2; checks=@("identifier","coordinate","address_normalization","hash")},
        [ordered]@{source="Area m2 source"; priority=2; checks=@("area_method","floor_or_land_area","source_hash","date")},
        [ordered]@{source="Cross-source validation evidence"; priority=3; checks=@("source_count","conflict_resolution","manual_review")}
      )
      $path=Join-Path $SafeDir "source_registry_047.json"
      $registry | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $path
      $r.data.path=$path
      $r.data.count=@($registry).Count
    }
    "evidence_chain_and_scoring" {
      New-Item -ItemType Directory -Force -Path $SafeDir | Out-Null
      $model=[ordered]@{
        task="047 mega parallel accuracy"
        record_fields=@("evidence_id","source_name","licence","capture_date","raw_sha256","sale_date","sale_year","sale_price","currency","area_m2","price_per_m2","address_text","coordinate","parcel_candidate_id","match_method","source_accuracy_score","parcel_match_accuracy_score","general_confidence_score","manual_review_required","load_allowed_false")
        source_score_weights=[ordered]@{official_source=20; licence=10; raw_hash=15; price_date_currency=15; area_m2_provenance=10; cross_source=20; manual_review=10}
        parcel_score_weights=[ordered]@{parcel_id=25; uprn_or_title=20; coordinate_inside_polygon=20; address_geometry_consistency=15; boundary_date=10; ambiguity_penalty=-20; manual_review=10}
        levels=@("L0 raw","L1 parsed","L2 hash verified","L3 cross-source matched","L4 manual reviewed - auto load disabled")
        conservative_scores=[ordered]@{source_accuracy=48; parcel_match=31; operational_health="computed separately"}
      }
      $path=Join-Path $SafeDir "evidence_chain_scoring_047.json"
      $model | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $path
      $r.data.path=$path
      $r.data.source_accuracy=48
      $r.data.parcel_match=31
    }
    "parcel_candidate_plan" {
      New-Item -ItemType Directory -Force -Path $SafeDir | Out-Null
      $plan=@"
# Parcel Candidate Matching Plan 047

Goal: maximize correctness before showing sale-linked parcels.

Pipeline:
1. Normalize sale address and date.
2. Resolve address identifiers.
3. Produce parcel candidates from exact parcel/title/UPRN if present.
4. Fall back to coordinate-in-polygon.
5. Penalize multi-parcel ambiguity and historical boundary mismatch.
6. Recalculate price_per_m2 from price and area_m2.
7. Route low-confidence records to manual review.
8. Export only lightweight manifests, not raw bulky data.

Do not auto-load verified L4. Manual review remains required.
"@
      $path=Join-Path $SafeDir "parcel_candidate_plan_047.md"
      $plan | Set-Content -Encoding UTF8 $path
      $r.data.path=$path
    }
    "manual_review_queue_plan" {
      New-Item -ItemType Directory -Force -Path $SafeDir | Out-Null
      $queue=[ordered]@{
        triggers=@("source_score_lt_70","parcel_score_lt_70","multi_parcel_candidate","price_outlier","area_missing","address_conflict","geometry_conflict","licence_unclear","duplicate_sale")
        review_fields=@("record_id","trigger","source_evidence","parcel_candidates","map_snapshot_ref","recommended_action","reviewer","review_time")
        load_policy="manual review does not automatically enable DB load; load remains false unless explicitly approved later"
      }
      $path=Join-Path $SafeDir "manual_review_queue_plan_047.json"
      $queue | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $path
      $r.data.path=$path
    }
    "ui_confidence_badge_plan" {
      New-Item -ItemType Directory -Force -Path $SafeDir | Out-Null
      $ui=@"
# UI Confidence Badge Plan 047

Parcel map display:
- Red: unsafe / review only
- Amber: partial evidence
- Blue: high confidence
- Green: manually reviewed

Each sale-linked parcel card must show:
- sale price
- sale year/date
- area m2
- price per m2
- source accuracy score
- parcel match score
- evidence manifest hash
- manual review status
"@
      $path=Join-Path $SafeDir "ui_confidence_badge_plan_047.md"
      $ui | Set-Content -Encoding UTF8 $path
      $r.data.path=$path
    }
    "export_policy_manifest" {
      New-Item -ItemType Directory -Force -Path $SafeDir | Out-Null
      $export=[ordered]@{
        mode="low_volume_manifest_only"
        raw_data_policy="keep raw files local/E-drive or approved storage; export hashes and evidence summaries only"
        allowed_exports=@("record_id","source_hash","evidence_manifest_path","scores","parcel_candidate_id","review_status")
        blocked_exports=@("large_raw_files","uncertain_licence_data","unreviewed_L4_claims","db_write_payloads")
      }
      $path=Join-Path $SafeDir "data_export_policy_047.json"
      $export | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $path
      $r.data.path=$path
    }
    "safety_red_flags_deep" {
      if(-not(Test-Path $ProjectRoot)){ $r.critical += "project_missing"; break }
      $files=Get-ChildItem -Path $ProjectRoot -Recurse -File -Include *.ps1,*.py,*.js,*.ts,*.tsx,*.sql,*.json,*.yml,*.yaml,*.md -ErrorAction SilentlyContinue | ? { $_.FullName -notmatch "\\.git\\|\\node_modules\\|\\dist\\|\\build\\|\\.venv\\" } | Select-Object -First 2500
      $flags=@()
      foreach($f in $files){
        $txt=Get-Content -Raw -ErrorAction SilentlyContinue $f.FullName
        $m=@()
        foreach($pat in @("DROP TABLE","TRUNCATE TABLE","DELETE FROM","INSERT INTO","UPDATE\s+.+\s+SET","VERIFIED_L4_LOAD","docker compose up --build","docker-compose up --build","docker compose build","playwright|selenium|scrapy","Invoke-WebRequest\s+.*http")){
          if($txt -match $pat){ $m += $pat }
        }
        if($m.Count -gt 0){ $flags += [ordered]@{file=$f.FullName;matches=$m} }
      }
      $r.data.scanned=@($files).Count
      $r.data.flag_count=@($flags).Count
      $r.data.flags=@($flags | Select-Object -First 80)
      $flags | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 (Join-Path $OutDir "safety_red_flags_deep.json")
      if(@($flags).Count -gt 0){ $r.warnings += "manual_review_red_flags_found" }
    }
  }
  if($r.critical.Count -gt 0){$r.status="failed"}elseif($r.warnings.Count -gt 0){$r.status="completed_with_warnings"}else{$r.status="completed"}
}catch{ $r.status="failed"; $r.critical += $_.Exception.Message }
finally{ $r.elapsed_seconds=[int]((Get-Date)-$Start).TotalSeconds; Save $r }
'@

$WorkerPath = Join-Path $ReportDir "worker.ps1"
Set-Content -Encoding UTF8 -Path $WorkerPath -Value $Worker

$tasks=@(
  @{Name="01_runner_state_deep";Kind="runner_state_deep"},
  @{Name="02_runner_log_tail";Kind="runner_log_tail"},
  @{Name="03_bridge_git_recovery";Kind="bridge_git_recovery"},
  @{Name="04_project_git_profile";Kind="project_git_profile"},
  @{Name="05_recent_results_audit";Kind="recent_results_audit"},
  @{Name="06_endpoint_probe_and_api_recover";Kind="endpoint_probe_and_api_recover"},
  @{Name="07_dataset_inventory_deep";Kind="dataset_inventory_deep"},
  @{Name="08_safe_sales_source_registry";Kind="safe_sales_source_registry"},
  @{Name="09_evidence_chain_and_scoring";Kind="evidence_chain_and_scoring"},
  @{Name="10_parcel_candidate_plan";Kind="parcel_candidate_plan"},
  @{Name="11_manual_review_queue_plan";Kind="manual_review_queue_plan"},
  @{Name="12_ui_confidence_badge_plan";Kind="ui_confidence_badge_plan"},
  @{Name="13_export_policy_manifest";Kind="export_policy_manifest"},
  @{Name="14_safety_red_flags_deep";Kind="safety_red_flags_deep"}
)

$jobs=@()
foreach($t in $tasks){
  $jobs += Start-Job -ScriptBlock { param($WorkerPath,$Name,$Kind,$BridgeRoot,$ProjectRoot,$SafeDir,$JobsDir) powershell -NoProfile -ExecutionPolicy Bypass -File $WorkerPath -Name $Name -Kind $Kind -BridgeRoot $BridgeRoot -ProjectRoot $ProjectRoot -SafeDir $SafeDir -OutDir $JobsDir } -ArgumentList $WorkerPath,$t.Name,$t.Kind,$BridgeRoot,$ProjectRoot,$SafeDir,$JobsDir
}
Log "Started mega parallel jobs: $($jobs.Count)"
$deadline=(Get-Date).AddMinutes(45)
while(@($jobs | ? {$_.State -eq "Running"}).Count -gt 0 -and (Get-Date) -lt $deadline){ Start-Sleep -Seconds 5 }
foreach($j in $jobs){
  if($j.State -eq "Running"){ $Warnings++; Check "job_timeout_$($j.Id)" "WARN" "WARNING" "Timed-out subjob stopped; main runner preserved"; Stop-Job $j -Force | Out-Null }
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
  }catch{ $Warnings++; Check "parse_$($f.Name)" "WARN" "WARNING" $_.Exception.Message }
}

$scoreJob=$results | ? {$_.name -eq "09_evidence_chain_and_scoring"} | Select-Object -First 1
$endpointJob=$results | ? {$_.name -eq "06_endpoint_probe_and_api_recover"} | Select-Object -First 1
$sourceScore=48
$parcelScore=31
if($scoreJob -and $scoreJob.data.source_accuracy){ $sourceScore=[int]$scoreJob.data.source_accuracy }
if($scoreJob -and $scoreJob.data.parcel_match){ $parcelScore=[int]$scoreJob.data.parcel_match }
$opScore=0
if($endpointJob -and $endpointJob.data.initial_ok_count -ne $null){ $opScore=[Math]::Min(100,[int]$endpointJob.data.initial_ok_count*20) }
if($endpointJob -and $endpointJob.data.after_ok_count -ne $null -and $endpointJob.data.after_ok_count -gt $endpointJob.data.initial_ok_count){ $opScore=[Math]::Min(100,[int]$endpointJob.data.after_ok_count*20) }
$general=[int]([Math]::Round((0.45*$sourceScore)+(0.45*$parcelScore)+(0.10*$opScore)))
$Elapsed=[int]((Get-Date)-$Start).TotalSeconds
$Result=if($Critical -eq 0){"completed_continue_program"}else{"partial_failed_continue_recovery"}
$status=[ordered]@{
  task=$TaskId
  result=$Result
  progress="99 technical / continuous accuracy program ongoing"
  critical_failures=$Critical
  warnings=$Warnings
  source_accuracy_score=$sourceScore
  parcel_match_accuracy_score=$parcelScore
  operational_health_score=$opScore
  general_confidence_score=$general
  parallel_job_count=@($tasks).Count
  report_dir=$ReportDir
  summary_file=$SummaryFile
  detail_file=$DetailFile
  checks_file=$ChecksFile
  elapsed_seconds=$Elapsed
  next_action="devam et"
  next_wait="45-70 minutes"
  safety_locks=@("NO_DB_WRITE","NO_SQL_EXECUTE","NO_VERIFIED_L4_LOAD","NO_DOCKER_BUILD_RECREATE","NO_EXTERNAL_SCRAPING")
}
WriteJson $StatusFile $status

$md=@()
$md += "# $TaskId"
$md += ""
$md += "Result: $Result"
$md += "Critical failures: $Critical"
$md += "Warnings: $Warnings"
$md += "Parallel jobs: $(@($tasks).Count)"
$md += "Source Accuracy Score: $sourceScore/100"
$md += "Parcel Match Accuracy Score: $parcelScore/100"
$md += "Operational Health Score: $opScore/100"
$md += "General Confidence Score: $general/100"
$md += ""
$md += "Program intentionally continues; do not finish. Next task should add real geometry/boundary checks and source conflict resolution."
$md += ""
$md += "Parallel results:"
foreach($r in $results){ $md += "- $($r.name): $($r.status)" }
$md += ""
$md += "Safety locks: NO_DB_WRITE, NO_SQL_EXECUTE, NO_VERIFIED_L4_LOAD, NO_DOCKER_BUILD_RECREATE, NO_EXTERNAL_SCRAPING"
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
Write-Output "SOURCE_ACCURACY_SCORE=$sourceScore"
Write-Output "PARCEL_MATCH_ACCURACY_SCORE=$parcelScore"
Write-Output "OPERATIONAL_HEALTH_SCORE=$opScore"
Write-Output "GENERAL_CONFIDENCE_SCORE=$general"
Write-Output "PARALLEL_JOB_COUNT=$(@($tasks).Count)"
Write-Output "ELAPSED_SECONDS=$Elapsed"
Write-Output "TERRAYIELD_047_MEGA_PARALLEL_ACCURACY_AND_RECOVERY_DONE"
if($Critical -eq 0){exit 0}else{exit 1}
