$ErrorActionPreference = "Continue"

$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$Branch = "security-accuracy-expansion-20260508"
$BaseUrl = "http://127.0.0.1:8010"
$OutDir = Join-Path $Repo "docs\chatgpt_handoff\cloud_ready_20260517"
$Report = Join-Path $OutDir "014_LOCAL_API_SMOKE_PERF_REPORT.txt"
$Raw = Join-Path $OutDir "014_LOCAL_API_SMOKE_PERF_RAW.txt"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Set-Location $Repo

$B = New-Object System.Collections.Generic.List[string]
function Add-Blocker($x){ if(-not $B.Contains($x)){ $B.Add($x) } }
function Percentile95([double[]]$values){
  if($values.Count -eq 0){ return $null }
  $sorted = $values | Sort-Object
  $idx = [Math]::Ceiling(0.95 * $sorted.Count) - 1
  if($idx -lt 0){ $idx = 0 }
  if($idx -ge $sorted.Count){ $idx = $sorted.Count - 1 }
  return [Math]::Round($sorted[$idx] * 1000, 2)
}
function CurlTime($url){
  $out = & curl.exe -s -o NUL -w "%{http_code} %{time_total}" $url
  $parts = $out.Trim().Split(" ")
  return @{ code=$parts[0]; sec=[double]$parts[1]; raw=$out }
}

$head = (git rev-parse --short=12 HEAD).Trim()
$smokeEndpoints = @(
  "/",
  "/ops/storage-registry",
  "/ops/consistency-check",
  "/handoff/status",
  "/map/listings?limit=1",
  "/map/sales-history/combined?limit=1"
)
$perfEndpoints = @(
  @{ name="handoff_status"; path="/handoff/status"; gate=600 },
  @{ name="map_listings_200"; path="/map/listings?limit=200"; gate=1500 },
  @{ name="sales_history_combined_200"; path="/map/sales-history/combined?limit=200"; gate=1800 }
)

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("timestamp_utc=$([DateTime]::UtcNow.ToString('o'))")
$lines.Add("task=014_LOCAL_API_SMOKE_PERF")
$lines.Add("base_url=$BaseUrl")
$lines.Add("head=$head")

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

$perfStatus = "passed"
foreach($p in $perfEndpoints){
  $url = $BaseUrl + $p.path
  $samples = New-Object System.Collections.Generic.List[double]
  for($i=0; $i -lt 5; $i++){ try { [void](CurlTime $url) } catch {} }
  for($i=0; $i -lt 30; $i++){
    try {
      $r = CurlTime $url
      if($r.code -ge 200 -and $r.code -lt 500){ $samples.Add($r.sec) } else { Add-Blocker "perf_http_$($p.name)_$($r.code)" }
    } catch { Add-Blocker "perf_exception_$($p.name)" }
  }
  $p95 = Percentile95 $samples.ToArray()
  if($null -eq $p95){
    $perfStatus = "failed"
    Add-Blocker "perf_no_samples_$($p.name)"
    $lines.Add("perf:$($p.name) p95_ms=not_available gate_ms=$($p.gate) samples=0 status=failed")
  } elseif($p95 -le $p.gate){
    $lines.Add("perf:$($p.name) p95_ms=$p95 gate_ms=$($p.gate) samples=$($samples.Count) status=passed")
  } else {
    $perfStatus = "failed"
    Add-Blocker "perf_gate_failed_$($p.name)"
    $lines.Add("perf:$($p.name) p95_ms=$p95 gate_ms=$($p.gate) samples=$($samples.Count) status=failed")
  }
}
$lines | Set-Content -LiteralPath $Raw -Encoding UTF8

$blockerText = if($B.Count -eq 0){"none"}else{($B -join ";")}
@(
"timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
"task=014_LOCAL_API_SMOKE_PERF",
"report_type=actual_direct_or_runner_output",
"checked_branch=$Branch",
"head=$head",
"api_smoke_status=$apiSmokeStatus",
"smoke_ok_count=$smokeOk",
"smoke_total=$($smokeEndpoints.Count)",
"perf_status=$perfStatus",
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

git add "docs/chatgpt_handoff/cloud_ready_20260517/014_LOCAL_API_SMOKE_PERF_REPORT.txt" "docs/chatgpt_handoff/cloud_ready_20260517/014_LOCAL_API_SMOKE_PERF_RAW.txt" | Out-Null
if(git diff --cached --name-only){ git commit -m "Publish 014 local API smoke perf report" | Out-Null; if($LASTEXITCODE -eq 0){ git push origin $Branch | Out-Null } }
Get-Content $Report
