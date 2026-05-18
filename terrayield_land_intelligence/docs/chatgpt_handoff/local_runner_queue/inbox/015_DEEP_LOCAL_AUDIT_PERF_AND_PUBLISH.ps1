$ErrorActionPreference = "Continue"

$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$Branch = "security-accuracy-expansion-20260508"
$BaseUrl = "http://127.0.0.1:8010"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
$Report = Join-Path $OutDir "015_DEEP_LOCAL_AUDIT_PERF_REPORT.txt"
$Raw = Join-Path $OutDir "015_DEEP_LOCAL_AUDIT_PERF_RAW.txt"
$PytestRaw = Join-Path $OutDir "015_PYTEST_FULL_RAW.txt"
$StaticRaw = Join-Path $OutDir "015_STATIC_VALIDATE_RAW.txt"
$WatchdogRaw = Join-Path $OutDir "015_WATCHDOG_VALIDATE_RAW.txt"
$PathScanRaw = Join-Path $OutDir "015_LOCAL_PATH_SCAN_RAW.txt"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Set-Location $Repo

$B = New-Object System.Collections.Generic.List[string]
function Add-Blocker($x){ if(-not $B.Contains($x)){ $B.Add($x) } }
function Percentile([double[]]$values, [double]$p){
  if($values.Count -eq 0){ return $null }
  $sorted = $values | Sort-Object
  $idx = [Math]::Ceiling($p * $sorted.Count) - 1
  if($idx -lt 0){ $idx = 0 }
  if($idx -ge $sorted.Count){ $idx = $sorted.Count - 1 }
  return [Math]::Round($sorted[$idx] * 1000, 2)
}
function CurlTime($url){
  $out = & curl.exe -s -o NUL -w "%{http_code} %{time_total}" $url
  $parts = $out.Trim().Split(" ")
  return @{ code=$parts[0]; sec=[double]$parts[1]; raw=$out }
}

$started = Get-Date
$head = (git rev-parse --short=12 HEAD).Trim()
$branchNow = (git branch --show-current).Trim()
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("timestamp_utc=$([DateTime]::UtcNow.ToString('o'))")
$lines.Add("task=015_DEEP_LOCAL_AUDIT_PERF")
$lines.Add("repo=$Repo")
$lines.Add("branch=$branchNow")
$lines.Add("head=$head")
$lines.Add("base_url=$BaseUrl")

# 1) Static cloud readiness validation
$staticStatus = "not_run"
$staticExit = "not_run"
if(Test-Path "scripts\validate_cloud_readiness_static.py"){
  python "scripts\validate_cloud_readiness_static.py" *> $StaticRaw
  $staticExit = $LASTEXITCODE
  $staticStatus = if($staticExit -eq 0){"passed"}else{"failed"}
  if($staticExit -ne 0){ Add-Blocker "static_validation_failed" }
}else{
  "missing scripts\validate_cloud_readiness_static.py" | Set-Content -LiteralPath $StaticRaw -Encoding UTF8
  $staticStatus = "failed"
  $staticExit = 999
  Add-Blocker "static_validator_missing"
}
$lines.Add("static_validation_status=$staticStatus exit=$staticExit raw=$StaticRaw")

# 2) Watchdog readiness validation
$watchdogStatus = "not_run"
$watchdogExit = "not_run"
if(Test-Path "scripts\validate_watchdog_readiness.py"){
  python "scripts\validate_watchdog_readiness.py" *> $WatchdogRaw
  $watchdogExit = $LASTEXITCODE
  $watchdogStatus = if($watchdogExit -eq 0){"passed"}else{"failed"}
  if($watchdogExit -ne 0){ Add-Blocker "watchdog_validation_failed" }
}else{
  "missing scripts\validate_watchdog_readiness.py" | Set-Content -LiteralPath $WatchdogRaw -Encoding UTF8
  $watchdogStatus = "failed"
  $watchdogExit = 999
  Add-Blocker "watchdog_validator_missing"
}
$lines.Add("watchdog_validation_status=$watchdogStatus exit=$watchdogExit raw=$WatchdogRaw")

# 3) Full pytest attempt for broader confidence
$pytestStatus = "not_run"
$pytestExit = "not_run"
if(Test-Path "tests"){
  python -m pytest -q *> $PytestRaw
  $pytestExit = $LASTEXITCODE
  $pytestStatus = if($pytestExit -eq 0){"passed"}else{"failed"}
  if($pytestExit -ne 0){ Add-Blocker "full_pytest_failed" }
}else{
  "tests_dir_missing" | Set-Content -LiteralPath $PytestRaw -Encoding UTF8
  $pytestStatus = "failed"
  $pytestExit = 999
  Add-Blocker "tests_dir_missing"
}
$lines.Add("full_pytest_status=$pytestStatus exit=$pytestExit raw=$PytestRaw")

# 4) Local path / local-only dependency scan. This is evidence-only and can produce findings without failing the run.
$scanPatterns = @("C:\\Users", "E:\\AAYS_DATA", "127.0.0.1", "localhost")
$scanFindings = 0
Remove-Item -LiteralPath $PathScanRaw -ErrorAction SilentlyContinue
foreach($pat in $scanPatterns){
  "### pattern=$pat" | Add-Content -LiteralPath $PathScanRaw -Encoding UTF8
  $res = git grep -n -- "$pat" 2>$null
  if($LASTEXITCODE -eq 0 -and $res){
    $scanFindings += ($res | Measure-Object).Count
    $res | Select-Object -First 200 | Add-Content -LiteralPath $PathScanRaw -Encoding UTF8
  } else {
    "no_match" | Add-Content -LiteralPath $PathScanRaw -Encoding UTF8
  }
}
$lines.Add("local_path_scan_findings=$scanFindings raw=$PathScanRaw")

# 5) Local API smoke 6/6
$smokeEndpoints = @(
  "/",
  "/ops/storage-registry",
  "/ops/consistency-check",
  "/handoff/status",
  "/map/listings?limit=1",
  "/map/sales-history/combined?limit=1"
)
$smokeOk = 0
foreach($ep in $smokeEndpoints){
  $url = $BaseUrl + $ep
  try {
    $r = CurlTime $url
    $ok = ($r.code -ge 200 -and $r.code -lt 500)
    if($ok){ $smokeOk++ } else { Add-Blocker "smoke_failed_$ep" }
    $lines.Add("smoke:$ep code=$($r.code) ms=$([Math]::Round($r.sec*1000,2)) ok=$ok")
  } catch {
    Add-Blocker "smoke_exception_$ep"
    $lines.Add("smoke:$ep exception=$($_.Exception.Message)")
  }
}
$apiSmokeStatus = if($smokeOk -eq $smokeEndpoints.Count){"passed"}else{"failed"}

# 6) Heavier perf: warmup 20, sample 100 each. Effective 10-15 min depending on local service speed.
$perfEndpoints = @(
  @{ name="handoff_status"; path="/handoff/status"; gate=600 },
  @{ name="map_listings_200"; path="/map/listings?limit=200"; gate=1500 },
  @{ name="sales_history_combined_200"; path="/map/sales-history/combined?limit=200"; gate=1800 }
)
$perfStatus = "passed"
foreach($pinfo in $perfEndpoints){
  $url = $BaseUrl + $pinfo.path
  $samples = New-Object System.Collections.Generic.List[double]
  for($i=0; $i -lt 20; $i++){ try { [void](CurlTime $url) } catch {} }
  for($i=0; $i -lt 100; $i++){
    try {
      $r = CurlTime $url
      if($r.code -ge 200 -and $r.code -lt 500){ $samples.Add($r.sec) } else { Add-Blocker "perf_http_$($pinfo.name)_$($r.code)" }
    } catch { Add-Blocker "perf_exception_$($pinfo.name)" }
  }
  $p50 = Percentile $samples.ToArray() 0.50
  $p95 = Percentile $samples.ToArray() 0.95
  $p99 = Percentile $samples.ToArray() 0.99
  if($null -eq $p95){
    $perfStatus = "failed"
    Add-Blocker "perf_no_samples_$($pinfo.name)"
    $lines.Add("perf:$($pinfo.name) p50_ms=not_available p95_ms=not_available p99_ms=not_available gate_ms=$($pinfo.gate) samples=0 status=failed")
  } elseif($p95 -le $pinfo.gate){
    $lines.Add("perf:$($pinfo.name) p50_ms=$p50 p95_ms=$p95 p99_ms=$p99 gate_ms=$($pinfo.gate) samples=$($samples.Count) status=passed")
  } else {
    $perfStatus = "failed"
    Add-Blocker "perf_gate_failed_$($pinfo.name)"
    $lines.Add("perf:$($pinfo.name) p50_ms=$p50 p95_ms=$p95 p99_ms=$p99 gate_ms=$($pinfo.gate) samples=$($samples.Count) status=failed")
  }
}
$ended = Get-Date
$durationSec = [Math]::Round(($ended - $started).TotalSeconds, 2)
$lines.Add("duration_seconds=$durationSec")
$lines | Set-Content -LiteralPath $Raw -Encoding UTF8

$blockerText = if($B.Count -eq 0){"none"}else{($B -join ";")}
@(
"timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
"task=015_DEEP_LOCAL_AUDIT_PERF",
"report_type=actual_deep_direct_or_runner_output",
"checked_branch=$Branch",
"actual_branch=$branchNow",
"head=$head",
"static_validation_status=$staticStatus",
"watchdog_validation_status=$watchdogStatus",
"full_pytest_status=$pytestStatus",
"local_path_scan_findings=$scanFindings",
"api_smoke_status=$apiSmokeStatus",
"smoke_ok_count=$smokeOk",
"smoke_total=$($smokeEndpoints.Count)",
"deep_perf_status=$perfStatus",
"duration_seconds=$durationSec",
"raw_output=$Raw",
"public_url_verified=false",
"cloud_db_verified=false",
"classification_recommendation=CLOUD_READY_PENDING_PROVIDER",
"next_single_action=WAIT_FOR_USER_PROVIDER_DECISION",
"blockers=$blockerText",
"secret_values_printed=false",
"db_write=none",
"ddl=none",
"migration_apply=none",
"prod_deploy=none"
) | Set-Content -LiteralPath $Report -Encoding UTF8

git add "docs/chatgpt_handoff/cloud_ready_20260517/015_DEEP_LOCAL_AUDIT_PERF_REPORT.txt" "docs/chatgpt_handoff/cloud_ready_20260517/015_DEEP_LOCAL_AUDIT_PERF_RAW.txt" "docs/chatgpt_handoff/cloud_ready_20260517/015_PYTEST_FULL_RAW.txt" "docs/chatgpt_handoff/cloud_ready_20260517/015_STATIC_VALIDATE_RAW.txt" "docs/chatgpt_handoff/cloud_ready_20260517/015_WATCHDOG_VALIDATE_RAW.txt" "docs/chatgpt_handoff/cloud_ready_20260517/015_LOCAL_PATH_SCAN_RAW.txt" | Out-Null
if(git diff --cached --name-only){ git commit -m "Publish 015 deep local audit and performance report" | Out-Null; if($LASTEXITCODE -eq 0){ git push origin $Branch | Out-Null } }
Get-Content $Report
