$ErrorActionPreference = "Continue"
$Start = Get-Date
$TaskId = "terrayield-verification-024-parallel-stability-sales-audit"
$Run = Get-Date -Format "yyyyMMdd_HHmmss"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$ReportRoot = Join-Path $ProjectRoot ".aays_next_fix"
$ReportDir = Join-Path $ReportRoot "verification_024_parallel_stability_sales_audit_$Run"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
$StatusFile = Join-Path $ReportDir "status.json"
$ChecksFile = Join-Path $ReportDir "checks.csv"
$JobsDir = Join-Path $ReportDir "parallel_jobs"

New-Item -ItemType Directory -Force -Path $ReportDir, $JobsDir | Out-Null

function Log([string]$Text) {
    $elapsed = [int]((Get-Date) - $Start).TotalSeconds
    $line = "[$elapsed s] $Text"
    Write-Output $line
    Add-Content -Encoding UTF8 -Path $DetailFile -Value $line
}

function Add-Check([string]$Name, [string]$Status, [string]$Severity, [string]$Detail) {
    if (-not (Test-Path $ChecksFile)) {
        "check,status,severity,detail" | Set-Content -Encoding UTF8 $ChecksFile
    }
    $safe = ($Detail -replace '"','""')
    ('"{0}","{1}","{2}","{3}"' -f $Name,$Status,$Severity,$safe) | Add-Content -Encoding UTF8 $ChecksFile
}

function Write-Json($Path, $Obj) {
    $Obj | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $Path
}

Log "TASK: $TaskId"
Log "PROGRESS: 99%"
Log "MODE: parallel stability + safe sales evidence audit + non-destructive recovery"
Log "SAFETY: NO_DB_WRITE, NO_VERIFIED_L4_LOAD, NO_SQL_EXECUTE, NO_DOCKER_BUILD_RECREATE, NO_EXTERNAL_SCRAPING"

$Critical = 0
$Warnings = 0

if (-not (Test-Path $BridgeRoot)) { $Critical++; Add-Check "bridge_root_exists" "FAIL" "CRITICAL" "Missing $BridgeRoot" } else { Add-Check "bridge_root_exists" "PASS" "INFO" $BridgeRoot }
if (-not (Test-Path $ProjectRoot)) { $Critical++; Add-Check "project_root_exists" "FAIL" "CRITICAL" "Missing $ProjectRoot" } else { Add-Check "project_root_exists" "PASS" "INFO" $ProjectRoot }

$jobScript = @'
param(
  [string]$Name,
  [string]$Kind,
  [string]$BridgeRoot,
  [string]$ProjectRoot,
  [string]$OutDir
)
$ErrorActionPreference = "Continue"
$Start = Get-Date
$Out = Join-Path $OutDir ($Name + ".json")
$Log = Join-Path $OutDir ($Name + ".log")
function J($obj){ $obj | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $Out }
function L($t){ $e=[int]((Get-Date)-$Start).TotalSeconds; "[$e s] $t" | Tee-Object -FilePath $Log -Append | Out-Null }
$result = [ordered]@{ name=$Name; kind=$Kind; status="started"; warnings=@(); critical=@(); data=[ordered]@{}; elapsed_seconds=0 }
try {
  switch ($Kind) {
    "bridge_git_safe_recovery" {
      if (-not (Test-Path $BridgeRoot)) { $result.critical += "bridge_missing"; break }
      Push-Location $BridgeRoot
      $result.data.pwd = (Get-Location).Path
      $result.data.branch = ((git rev-parse --abbrev-ref HEAD 2>&1) | Out-String).Trim()
      $status = ((git status --porcelain=v1 2>&1) | Out-String)
      $result.data.status_before = $status.Trim()
      $dirtyLines = @($status -split "`n" | Where-Object { $_.Trim().Length -gt 0 })
      $result.data.dirty_count_before = $dirtyLines.Count
      git status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_git_status_before.txt")
      git diff --stat | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_git_diff_stat_before.txt")
      git ls-files --others --exclude-standard | Set-Content -Encoding UTF8 (Join-Path $OutDir "bridge_git_untracked_before.txt")
      if ($dirtyLines.Count -gt 0) {
        $stashName = "aays-auto-stash-before-$Name-" + (Get-Date -Format "yyyyMMdd_HHmmss")
        $stashOutput = ((git stash push -u -m $stashName 2>&1) | Out-String).Trim()
        $result.data.stash_name = $stashName
        $result.data.stash_output = $stashOutput
        $result.warnings += "bridge_dirty_stashed"
      }
      $fetch = ((git fetch origin main --prune 2>&1) | Out-String).Trim()
      $result.data.fetch_output = $fetch
      $status2 = ((git status --porcelain=v1 2>&1) | Out-String)
      $result.data.status_after = $status2.Trim()
      $result.data.dirty_count_after = @($status2 -split "`n" | Where-Object { $_.Trim().Length -gt 0 }).Count
      Pop-Location
    }
    "project_git_snapshot" {
      if (-not (Test-Path $ProjectRoot)) { $result.critical += "project_missing"; break }
      Push-Location $ProjectRoot
      $result.data.pwd = (Get-Location).Path
      $result.data.branch = ((git rev-parse --abbrev-ref HEAD 2>&1) | Out-String).Trim()
      $result.data.head = ((git rev-parse --short HEAD 2>&1) | Out-String).Trim()
      $status = ((git status --porcelain=v1 2>&1) | Out-String)
      $result.data.status_short = $status.Trim()
      $result.data.dirty_count = @($status -split "`n" | Where-Object { $_.Trim().Length -gt 0 }).Count
      git status --short | Set-Content -Encoding UTF8 (Join-Path $OutDir "project_git_status.txt")
      git diff --stat | Set-Content -Encoding UTF8 (Join-Path $OutDir "project_git_diff_stat.txt")
      Pop-Location
    }
    "verification_scaffold_audit" {
      if (-not (Test-Path $ProjectRoot)) { $result.critical += "project_missing"; break }
      $patterns = @("*sale*", "*sales*", "*parcel*", "*evidence*", "*verification*", "*source*registry*", "*backlog*")
      $hits = @()
      foreach ($p in $patterns) {
        $hits += Get-ChildItem -Path $ProjectRoot -Recurse -File -Filter $p -ErrorAction SilentlyContinue | Select-Object -First 80 FullName, Length, LastWriteTime
      }
      $hits = $hits | Sort-Object FullName -Unique
      $result.data.hit_count = @($hits).Count
      $result.data.sample = @($hits | Select-Object -First 40)
      $hits | ForEach-Object { $_.FullName } | Set-Content -Encoding UTF8 (Join-Path $OutDir "verification_scaffold_hits.txt")
      if (@($hits).Count -lt 3) { $result.warnings += "low_scaffold_hits" }
    }
    "safety_lock_audit" {
      if (-not (Test-Path $ProjectRoot)) { $result.critical += "project_missing"; break }
      $files = Get-ChildItem -Path $ProjectRoot -Recurse -File -Include *.ps1,*.py,*.js,*.ts,*.tsx,*.json,*.md,*.yml,*.yaml -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "\\node_modules\\|\\.git\\|\\dist\\|\\build\\" } | Select-Object -First 1000
      $danger = @()
      foreach ($f in $files) {
        $txt = Get-Content -Raw -ErrorAction SilentlyContinue $f.FullName
        if ($txt -match "VERIFIED_L4_LOAD|DROP TABLE|TRUNCATE TABLE|docker compose build|docker-compose build|docker compose up --build|INSERT INTO|UPDATE .+ SET") {
          $danger += [ordered]@{ file=$f.FullName; matches=($Matches.Values -join ",") }
        }
      }
      $result.data.scanned_files = @($files).Count
      $result.data.danger_count = @($danger).Count
      $result.data.danger_sample = @($danger | Select-Object -First 25)
      $danger | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $OutDir "safety_danger_matches.json")
      if (@($danger).Count -gt 0) { $result.warnings += "manual_review_safety_matches" }
    }
    "endpoint_health" {
      $urls = @(
        "http://127.0.0.1:8000/health",
        "http://127.0.0.1:8000/api/health",
        "http://127.0.0.1:8000/docs",
        "http://127.0.0.1:5173/",
        "http://127.0.0.1:3000/"
      )
      $checks = @()
      foreach ($u in $urls) {
        try {
          $sw=[Diagnostics.Stopwatch]::StartNew()
          $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 8
          $sw.Stop()
          $checks += [ordered]@{ url=$u; ok=$true; status=[int]$r.StatusCode; ms=$sw.ElapsedMilliseconds }
        } catch {
          $checks += [ordered]@{ url=$u; ok=$false; error=$_.Exception.Message }
        }
      }
      $result.data.checks = $checks
      $result.data.ok_count = @($checks | Where-Object { $_.ok }).Count
      if ($result.data.ok_count -eq 0) { $result.warnings += "no_endpoint_healthy" }
    }
    "source_registry_seed" {
      if (-not (Test-Path $ProjectRoot)) { $result.critical += "project_missing"; break }
      $dir = Join-Path $ProjectRoot ".aays_safe_sales"
      New-Item -ItemType Directory -Force -Path $dir | Out-Null
      $registryPath = Join-Path $dir "source_registry_seed.json"
      $registry = @(
        [ordered]@{ source_name="HM Land Registry Price Paid Data"; source_type="OFFICIAL_GOV"; required_checks=@("licence","download_date","transaction_id","hash","address_postcode") ; verified_load_allowed=$false },
        [ordered]@{ source_name="HM Land Registry INSPIRE Index Polygons"; source_type="OFFICIAL_GOV_GEOMETRY_INDICATIVE"; required_checks=@("licence","download_date","geometry_hash","title_or_inspire_id") ; verified_load_allowed=$false },
        [ordered]@{ source_name="OS Open UPRN"; source_type="OFFICIAL_GEOSPATIAL_IDENTIFIER"; required_checks=@("licence","uprn","coordinate","hash") ; verified_load_allowed=$false },
        [ordered]@{ source_name="EPC Open Data"; source_type="OFFICIAL_GOV_ATTRIBUTE_HELPER"; required_checks=@("licence","uprn_or_address","floor_area_source","hash") ; verified_load_allowed=$false }
      )
      $registry | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $registryPath
      $result.data.registry_path = $registryPath
      $result.data.registry_count = @($registry).Count
    }
  }
  if ($result.critical.Count -gt 0) { $result.status="failed" }
  elseif ($result.warnings.Count -gt 0) { $result.status="completed_with_warnings" }
  else { $result.status="completed" }
} catch {
  $result.status="failed"
  $result.critical += $_.Exception.Message
} finally {
  $result.elapsed_seconds = [int]((Get-Date)-$Start).TotalSeconds
  J $result
}
'@

$WorkerPath = Join-Path $ReportDir "worker.ps1"
Set-Content -Encoding UTF8 -Path $WorkerPath -Value $jobScript

$jobs = @(
    @{Name="01_bridge_git_safe_recovery"; Kind="bridge_git_safe_recovery"},
    @{Name="02_project_git_snapshot"; Kind="project_git_snapshot"},
    @{Name="03_verification_scaffold_audit"; Kind="verification_scaffold_audit"},
    @{Name="04_safety_lock_audit"; Kind="safety_lock_audit"},
    @{Name="05_endpoint_health"; Kind="endpoint_health"},
    @{Name="06_source_registry_seed"; Kind="source_registry_seed"}
)

$started = @()
foreach ($j in $jobs) {
    $started += Start-Job -ScriptBlock {
        param($WorkerPath,$Name,$Kind,$BridgeRoot,$ProjectRoot,$JobsDir)
        powershell -NoProfile -ExecutionPolicy Bypass -File $WorkerPath -Name $Name -Kind $Kind -BridgeRoot $BridgeRoot -ProjectRoot $ProjectRoot -OutDir $JobsDir
    } -ArgumentList $WorkerPath,$j.Name,$j.Kind,$BridgeRoot,$ProjectRoot,$JobsDir
}

Log "Started parallel jobs: $($started.Count)"
$deadline = (Get-Date).AddMinutes(18)
while (@($started | Where-Object { $_.State -eq "Running" }).Count -gt 0 -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
}

foreach ($job in $started) {
    if ($job.State -eq "Running") {
        $Warnings++
        Add-Check "parallel_job_timeout_$($job.Id)" "WARN" "WARNING" "Job exceeded deadline; stopping child job only."
        Stop-Job $job -Force | Out-Null
    }
    Receive-Job $job -ErrorAction SilentlyContinue | Add-Content -Encoding UTF8 -Path $DetailFile
    Remove-Job $job -Force -ErrorAction SilentlyContinue
}

$jobResults = @()
foreach ($f in Get-ChildItem -Path $JobsDir -Filter "*.json" -ErrorAction SilentlyContinue) {
    try {
        $jr = Get-Content -Raw $f.FullName | ConvertFrom-Json
        $jobResults += $jr
        if ($jr.status -eq "failed") {
            $Critical++
            Add-Check $jr.name "FAIL" "CRITICAL" (($jr.critical | Out-String).Trim())
        } elseif ($jr.status -eq "completed_with_warnings") {
            $Warnings++
            Add-Check $jr.name "WARN" "WARNING" (($jr.warnings | Out-String).Trim())
        } else {
            Add-Check $jr.name "PASS" "INFO" $jr.status
        }
    } catch {
        $Warnings++
        Add-Check "parse_$($f.Name)" "WARN" "WARNING" $_.Exception.Message
    }
}

$endpoint = $jobResults | Where-Object { $_.name -eq "05_endpoint_health" } | Select-Object -First 1
$apiOk = $false
if ($endpoint -and $endpoint.data -and $endpoint.data.ok_count -gt 0) { $apiOk = $true }

$bridge = $jobResults | Where-Object { $_.name -eq "01_bridge_git_safe_recovery" } | Select-Object -First 1
$bridgeStashed = $false
if ($bridge -and $bridge.warnings -contains "bridge_dirty_stashed") { $bridgeStashed = $true }

$Elapsed = [int]((Get-Date) - $Start).TotalSeconds
$resultText = if ($Critical -eq 0) { "completed" } else { "partial_failed" }

$status = [ordered]@{
    task = $TaskId
    result = $resultText
    progress = 99
    critical_failures = $Critical
    warnings = $Warnings
    api_or_ui_endpoint_ok = $apiOk
    bridge_dirty_stashed = $bridgeStashed
    report_dir = $ReportDir
    summary_file = $SummaryFile
    detail_file = $DetailFile
    checks_file = $ChecksFile
    safety = [ordered]@{
        no_db_write = $true
        no_verified_l4_load = $true
        no_sql_execute = $true
        no_docker_build_recreate = $true
        no_external_scraping = $true
    }
    elapsed_seconds = $Elapsed
    next_recommended_action = "If critical_failures=0, continue to AAYS Safe Sales source evidence registry expansion; if warnings include bridge_dirty_stashed, inspect stash before destructive cleanup."
}
Write-Json $StatusFile $status

$summary = @()
$summary += "# $TaskId"
$summary += ""
$summary += "Result: $resultText"
$summary += "Progress: 99%"
$summary += "Critical failures: $Critical"
$summary += "Warnings: $Warnings"
$summary += "API/UI endpoint ok: $apiOk"
$summary += "Bridge dirty stashed: $bridgeStashed"
$summary += "Mode: parallel stability + safe sales evidence audit"
$summary += ""
$summary += "Safety locks: NO_DB_WRITE, NO_VERIFIED_L4_LOAD, NO_SQL_EXECUTE, NO_DOCKER_BUILD_RECREATE, NO_EXTERNAL_SCRAPING"
$summary += ""
$summary += "Parallel jobs:"
foreach ($jr in $jobResults) { $summary += "- $($jr.name): $($jr.status)" }
$summary += ""
$summary += "Files:"
$summary += "- Status: $StatusFile"
$summary += "- Detail: $DetailFile"
$summary += "- Checks: $ChecksFile"
$summary += "- Jobs: $JobsDir"
$summary | Set-Content -Encoding UTF8 -Path $SummaryFile

Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "STATUS_FILE=$StatusFile"
Write-Output "CHECKS_FILE=$ChecksFile"
Write-Output "RESULT=$resultText"
Write-Output "CRITICAL_FAILURES=$Critical"
Write-Output "WARNINGS=$Warnings"
Write-Output "API_OR_UI_ENDPOINT_OK=$apiOk"
Write-Output "BRIDGE_DIRTY_STASHED=$bridgeStashed"
Write-Output "ELAPSED_SECONDS=$Elapsed"
Write-Output "VERIFICATION_024_PARALLEL_STABILITY_SALES_AUDIT_DONE"

if ($Critical -eq 0) { exit 0 } else { exit 1 }
