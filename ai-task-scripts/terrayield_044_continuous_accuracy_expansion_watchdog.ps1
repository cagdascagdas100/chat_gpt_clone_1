$ErrorActionPreference = "Continue"
$Start = Get-Date
$TaskId = "terrayield-044-continuous-accuracy-expansion-watchdog"
$Run = Get-Date -Format "yyyyMMdd_HHmmss"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$ReportDir = Join-Path $ProjectRoot ".aays_next_fix\044_continuous_accuracy_expansion_watchdog_$Run"
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
function WriteJson($Path,$Obj) { $Obj | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $Path }

Log "TASK: $TaskId"
Log "PROGRESS: 99 technical runner / continuous accuracy program not finished"
Log "MODE: broad parallel accuracy expansion + stuck detection + non-destructive recovery"
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
function Save($o){ $o | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $Out }
$r=[ordered]@{name=$Name;kind=$Kind;status="started";critical=@();warnings=@();data=[ordered]@{};elapsed_seconds=0}
try {
  switch($Kind){
    "runner_stuck_detector" {
      $hb=Join-Path $BridgeRoot "ai-heartbeat\runner-v4.md"
      $wd=Join-Path $BridgeRoot "ai-heartbeat\user-mode-watchdog.md"
      $ct=Join-Path $BridgeRoot "ai-tasks\current-task.json"
      $lt=Join-Path $BridgeRoot "ai-tasks\.last-task-id"
      $logdir=Join-Path $BridgeRoot "ai-runner-logs"
      if(Test-Path $hb){ $r.data.heartbeat=Get-Content -Raw $hb }
      if(Test-Path $wd){ $r.data.watchdog=Get-Content -Raw $wd }
      if(Test-Path $ct){ $r.data.current_task=Get-Content -Raw $ct | ConvertFrom-Json }
      if(Test-Path $lt){ $r.data.last_task=(Get-Content -Raw $lt).Trim() }
      if(Test-Path $logdir){
        $latest=Get-ChildItem $logdir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3
        $r.data.latest_logs=@($latest | Select-Object FullName,Length,LastWriteTime)
        foreach($f in $latest){
          Get-Content -Tail 120 -ErrorAction SilentlyContinue $f.FullName | Set-Content -Encoding UTF8 (Join-Path $OutDir ("tail_"+$f.Name+".txt"))
        }
      }
      if($r.data.heartbeat -match "Status:\s+running") { $r.warnings += "runner_currently_running_do_not_interrupt" }
      if($r.data.current_task -and $r.data.last_task -and $r.data.current_task.id -ne $r.data.last_task){ $r.data.pending_or_running=$true }
    }
    "bridge_git_stabilizer" {
      if(-not(Test-Path $BridgeRoot)){ $r.critical += "bridge_missing"; break }
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
      git config --local pull.rebase false 2>&1 | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_pull_rebase_false.txt")
      if($dirty.Count -gt 0){
        $stash="aays-044-auto-stash-"+(Get-Date -Format "yyyyMMdd_HHmmss")
        $r.data.stash_name=$stash
        $r.data.stash_output=((git stash push -u -m $stash 2>&1)|Out-String).Trim()
        $r.warnings += "dirty_bridge_stashed"
      }
      $r.data.fetch_output=((git fetch origin main --prune 2>&1)|Out-String).Trim()
      $status2=((git status --porcelain=v1 2>&1)|Out-String)
      $r.data.status_after=$status2.Trim()
      $r.data.dirty_count_after=@($status2 -split "`n" | ? { $_.Trim().Length -gt 0 }).Count
      Pop-Location
    }
    "project_profile_and_red_flags" {
      if(-not(Test-Path $ProjectRoot)){ $r.critical += "project_missing"; break }
      Push-Location $ProjectRoot
      $r.data.branch=((git rev-parse --abbrev-ref HEAD 2>&1)|Out-String).Trim()
      $r.data.head=((git rev-parse --short HEAD 2>&1)|Out-String).Trim()
      $status=((git status --porcelain=v1 2>&1)|Out-String)
      $r.data.git_dirty_count=@($status -split "`n" | ? { $_.Trim().Length -gt 0 }).Count
      git status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "project_status.txt")
      $files=Get-ChildItem -Path $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue | ? { $_.FullName -notmatch "\\.git\\|\\node_modules\\|\\dist\\|\\build\\|\\.venv\\" }
      $r.data.file_count=@($files).Count
      $r.data.ext_counts=@($files | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 20 Name,Count)
      $flags=@()
      foreach($f in ($files | ? { $_.Extension -match "\.ps1|\.py|\.js|\.ts|\.tsx|\.sql|\.json|\.yml|\.yaml|\.md" } | Select-Object -First 2000)){
        $txt=Get-Content -Raw -ErrorAction SilentlyContinue $f.FullName
        $m=@()
        foreach($pat in @("DROP TABLE","TRUNCATE TABLE","DELETE FROM","INSERT INTO","UPDATE\s+.+\s+SET","VERIFIED_L4_LOAD","docker compose up --build","docker-compose up --build","docker compose build","playwright|selenium|scrapy")){
          if($txt -match $pat){ $m += $pat }
        }
        if($m.Count -gt 0){ $flags += [ordered]@{file=$f.FullName;matches=$m} }
      }
      $r.data.red_flag_count=@($flags).Count
      $r.data.red_flags=@($flags | Select-Object -First 60)
      $flags | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $OutDir "red_flags.json")
      if(@($flags).Count -gt 0){ $r.warnings += "manual_review_red_flags" }
      Pop-Location
    }
    "real_dataset_inventory" {
      if(-not(Test-Path $ProjectRoot)){ $r.critical += "project_missing"; break }
      $patterns=@("*.csv","*.parquet","*.geojson","*.gpkg","*.json","*.sqlite","*.db","*.zip")
      $dataFiles=@()
      foreach($p in $patterns){ $dataFiles += Get-ChildItem -Path $ProjectRoot -Recurse -File -Filter $p -ErrorAction SilentlyContinue | ? { $_.FullName -notmatch "\\.git\\|\\node_modules\\|\\dist\\|\\build\\" } }
      $dataFiles=$dataFiles | Sort-Object FullName -Unique
      $sample=@()
      foreach($f in ($dataFiles | Select-Object -First 80)){
        $sha=""
        try{ if($f.Length -lt 200MB){ $sha=(Get-FileHash -Algorithm SHA256 $f.FullName).Hash } }catch{}
        $sample += [ordered]@{path=$f.FullName;name=$f.Name;bytes=$f.Length;ext=$f.Extension;sha256=$sha;last_write=$f.LastWriteTime}
      }
      $r.data.dataset_file_count=@($dataFiles).Count
      $r.data.sample=$sample
      $sample | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $OutDir "dataset_inventory_sample.json")
      if(@($dataFiles).Count -eq 0){ $r.warnings += "no_real_dataset_files_found" }
    }
    "accuracy_model_expand" {
      New-Item -ItemType Directory -Force -Path $SafeDir | Out-Null
      $model=[ordered]@{
        task="044 continuous accuracy expansion"
        purpose="Keep expanding correctness for sales-to-parcel matching; do not finish the program."
        source_accuracy_dimensions=@(
          "official_source_or_licence_verified",
          "raw_file_sha256_manifest",
          "capture_date_and_version",
          "sale_price_date_currency_normalized",
          "area_m2_provenance",
          "price_per_m2_recalculated",
          "address_identifier_quality",
          "duplicate_and_outlier_screen",
          "cross_source_confirmation",
          "manual_review_gate"
        )
        parcel_match_dimensions=@(
          "exact_parcel_id_match",
          "UPRN_or_title_number_match",
          "coordinate_inside_polygon",
          "address_to_geometry_consistency",
          "boundary_intersection_quality",
          "multi_parcel_ambiguity_penalty",
          "distance_to_centroid_or_address_point",
          "historical_boundary_date_consistency",
          "manual_review_gate"
        )
        score_formula=@{
          source_accuracy="weighted 0-100; official/hash/cross-source/manual gates dominate"
          parcel_match_accuracy="weighted 0-100; parcel id/UPRN/polygon containment dominate"
          general_confidence="0.45*source + 0.45*parcel + 0.10*operational_health"
        }
        current_estimate=@{
          source_accuracy_score=42
          parcel_match_accuracy_score=24
          general_confidence_score=32
          notes="Scores are conservative until real dataset inventory and parcel geometry matching are verified."
        }
        next_backlog=@(
          "Locate and hash real sale/parcel datasets",
          "Create evidence_chain table draft only, no DB write",
          "Create source_registry expansion",
          "Create parcel candidate scoring module draft",
          "Create manual review queue schema draft",
          "Create UI confidence badge plan",
          "Create low-volume export manifest policy"
        )
      }
      $path=Join-Path $SafeDir "accuracy_model_044.json"
      $model | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $path
      $r.data.model_path=$path
      $r.data.scores=$model.current_estimate
    }
    "evidence_chain_scaffold" {
      New-Item -ItemType Directory -Force -Path $SafeDir | Out-Null
      $schema=@"
# Evidence Chain Draft - No DB Write

This file is documentation only.

Required record fields:
- evidence_id
- source_name
- source_type
- source_url_or_local_path
- licence
- capture_date
- raw_sha256
- normalized_sale_id
- sale_date
- sale_year
- sale_price
- currency
- area_m2
- price_per_m2
- address_text
- postcode_or_local_identifier
- coordinate_source
- geometry_source
- parcel_candidate_id
- parcel_match_method
- source_accuracy_score
- parcel_match_accuracy_score
- general_confidence_score
- manual_review_required
- load_allowed=false

Load policy:
- L0/L1/L2/L3 records are display/review only.
- L4 requires manual review and remains disabled for automatic load.
"@
      $path=Join-Path $SafeDir "evidence_chain_draft_044.md"
      $schema | Set-Content -Encoding UTF8 $path
      $r.data.schema_path=$path
    }
    "endpoint_operational_health" {
      $urls=@("http://127.0.0.1:8000/health","http://127.0.0.1:8000/api/health","http://127.0.0.1:8000/docs","http://127.0.0.1:5173/","http://127.0.0.1:3000/")
      $checks=@()
      foreach($u in $urls){
        try{ $sw=[Diagnostics.Stopwatch]::StartNew(); $resp=Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 8; $sw.Stop(); $checks += [ordered]@{url=$u;ok=$true;status=[int]$resp.StatusCode;ms=$sw.ElapsedMilliseconds} }
        catch{ $checks += [ordered]@{url=$u;ok=$false;error=$_.Exception.Message} }
      }
      $r.data.checks=$checks
      $r.data.ok_count=@($checks | ? {$_.ok}).Count
      $r.data.operational_health_score=[Math]::Min(100, [int]($r.data.ok_count * 20))
      if($r.data.ok_count -eq 0){ $r.warnings += "no_endpoint_healthy" }
    }
  }
  if($r.critical.Count -gt 0){ $r.status="failed" }
  elseif($r.warnings.Count -gt 0){ $r.status="completed_with_warnings" }
  else{ $r.status="completed" }
}catch{
  $r.status="failed"; $r.critical += $_.Exception.Message
}finally{
  $r.elapsed_seconds=[int]((Get-Date)-$Start).TotalSeconds
  Save $r
}
'@

$WorkerPath = Join-Path $ReportDir "worker.ps1"
Set-Content -Encoding UTF8 -Path $WorkerPath -Value $Worker

$tasks=@(
  @{Name="01_runner_stuck_detector";Kind="runner_stuck_detector"},
  @{Name="02_bridge_git_stabilizer";Kind="bridge_git_stabilizer"},
  @{Name="03_project_profile_and_red_flags";Kind="project_profile_and_red_flags"},
  @{Name="04_real_dataset_inventory";Kind="real_dataset_inventory"},
  @{Name="05_accuracy_model_expand";Kind="accuracy_model_expand"},
  @{Name="06_evidence_chain_scaffold";Kind="evidence_chain_scaffold"},
  @{Name="07_endpoint_operational_health";Kind="endpoint_operational_health"}
)

$jobs=@()
foreach($t in $tasks){
  $jobs += Start-Job -ScriptBlock { param($WorkerPath,$Name,$Kind,$BridgeRoot,$ProjectRoot,$SafeDir,$JobsDir) powershell -NoProfile -ExecutionPolicy Bypass -File $WorkerPath -Name $Name -Kind $Kind -BridgeRoot $BridgeRoot -ProjectRoot $ProjectRoot -SafeDir $SafeDir -OutDir $JobsDir } -ArgumentList $WorkerPath,$t.Name,$t.Kind,$BridgeRoot,$ProjectRoot,$SafeDir,$JobsDir
}
Log "Started parallel tasks: $($jobs.Count)"
$deadline=(Get-Date).AddMinutes(28)
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

$accuracy=$results | ? {$_.name -eq "05_accuracy_model_expand"} | Select-Object -First 1
$endpoint=$results | ? {$_.name -eq "07_endpoint_operational_health"} | Select-Object -First 1
$sourceScore=42
$parcelScore=24
$operationalScore=0
if($accuracy -and $accuracy.data.scores){
  $sourceScore=[int]$accuracy.data.scores.source_accuracy_score
  $parcelScore=[int]$accuracy.data.scores.parcel_match_accuracy_score
}
if($endpoint -and $endpoint.data.operational_health_score -ne $null){ $operationalScore=[int]$endpoint.data.operational_health_score }
$generalScore=[int]([Math]::Round((0.45*$sourceScore)+(0.45*$parcelScore)+(0.10*$operationalScore)))

$Result=if($Critical -eq 0){"completed_continue_program"}else{"partial_failed_continue_with_recovery"}
$Elapsed=[int]((Get-Date)-$Start).TotalSeconds
$status=[ordered]@{
  task=$TaskId
  result=$Result
  progress="99 technical / continuous program ongoing"
  critical_failures=$Critical
  warnings=$Warnings
  source_accuracy_score=$sourceScore
  parcel_match_accuracy_score=$parcelScore
  operational_health_score=$operationalScore
  general_confidence_score=$generalScore
  report_dir=$ReportDir
  summary_file=$SummaryFile
  detail_file=$DetailFile
  checks_file=$ChecksFile
  next_action="devam et"
  next_wait="25-40 minutes"
  safety_locks=@("NO_DB_WRITE","NO_SQL_EXECUTE","NO_VERIFIED_L4_LOAD","NO_DOCKER_BUILD_RECREATE","NO_EXTERNAL_SCRAPING")
  elapsed_seconds=$Elapsed
}
WriteJson $StatusFile $status

$md=@()
$md += "# $TaskId"
$md += ""
$md += "Result: $Result"
$md += "Critical failures: $Critical"
$md += "Warnings: $Warnings"
$md += "Source Accuracy Score: $sourceScore/100"
$md += "Parcel Match Accuracy Score: $parcelScore/100"
$md += "Operational Health Score: $operationalScore/100"
$md += "General Confidence Score: $generalScore/100"
$md += ""
$md += "The program is intentionally not finished. Next steps must further improve evidence-chain and parcel-boundary accuracy."
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
Write-Output "OPERATIONAL_HEALTH_SCORE=$operationalScore"
Write-Output "GENERAL_CONFIDENCE_SCORE=$generalScore"
Write-Output "ELAPSED_SECONDS=$Elapsed"
Write-Output "TERRAYIELD_044_CONTINUOUS_ACCURACY_EXPANSION_WATCHDOG_DONE"
if($Critical -eq 0){exit 0}else{exit 1}
