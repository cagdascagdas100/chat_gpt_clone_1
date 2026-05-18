$ErrorActionPreference = "Stop"
$env:GIT_PAGER = "cat"
$env:PAGER = "cat"
Set-Location "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
param(
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence",
  [string]$ExpectedBranch = "security-accuracy-expansion-20260508",
  [string]$ExpectedHead = "b7cdaf34",
  [string]$ApiBase = "http://127.0.0.1:8010"
)

$ErrorActionPreference = "Stop"
$reportDir = Join-Path $RepoRoot "docs\chatgpt_handoff\db_readiness_probe_20260515"
$step12 = Join-Path $reportDir "STEP12_ULTRA_SCOPE_EXECUTION_REPORT.txt"
if(-not (Test-Path $reportDir)){ New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }

$rows = New-Object "System.Collections.Generic.List[string]"
function Row([string]$k,[string]$v){ $script:rows.Add("$k=$v") }

Push-Location $RepoRoot
try {
  Row "timestamp_utc" ([DateTime]::UtcNow.ToString("o"))
  $branch = (git branch --show-current).Trim()
  $head = (git rev-parse --short=8 HEAD).Trim()
  & git merge-base --is-ancestor $ExpectedHead HEAD 1>$null 2>$null
  $headOk = ($LASTEXITCODE -eq 0)
  Row "branch_expected" $ExpectedBranch
  Row "branch_current" $branch
  Row "head_short" $head
  Row "head_at_or_above_expected" ($headOk.ToString().ToLowerInvariant())

  $step10 = Join-Path $reportDir "STEP10_CONTROLLED_GO_LIVE_GATE_REPORT.txt"
  $step11 = Join-Path $reportDir "STEP11_WIDE_SCOPE_PLATFORM_REPORT.txt"
  Row "step10_exists" ((Test-Path $step10).ToString().ToLowerInvariant())
  Row "step11_exists" ((Test-Path $step11).ToString().ToLowerInvariant())

  if(Test-Path $step10){
    $s10 = Get-Content -LiteralPath $step10 -Raw
    foreach($k in @('final_classification','pytest_status','api_smoke_ok_count','api_smoke_total','db_write','ddl','migration_apply','prod_deploy','secret_values_printed')){
      $m = [regex]::Match($s10, "(?m)^" + [regex]::Escape($k) + "=(.+)$")
      if($m.Success){ Row ("step10_"+$k) ($m.Groups[1].Value.Trim()) }
    }
  }
  if(Test-Path $step11){
    $s11 = Get-Content -LiteralPath $step11 -Raw
    foreach($k in @('final_classification','pytest_status','api_smoke_ok_count','api_smoke_total','container_running','db_write','ddl','migration_apply','prod_deploy','secret_values_printed')){
      $m = [regex]::Match($s11, "(?m)^" + [regex]::Escape($k) + "=(.+)$")
      if($m.Success){ Row ("step11_"+$k) ($m.Groups[1].Value.Trim()) }
    }
  }

  $eps = @('/health','/cost/integration/status','/handoff/status','/handoff/final-lock','/handoff/accuracy','/ops/storage-registry','/ops/consistency-check')
  $ok = 0
  $dur = @()
  foreach($ep in $eps){
    try {
      $sw=[System.Diagnostics.Stopwatch]::StartNew()
      $r=Invoke-WebRequest -Uri ($ApiBase+$ep) -Method GET -TimeoutSec 8 -UseBasicParsing
      $sw.Stop()
      $dur += [int]$sw.ElapsedMilliseconds
      if($r.StatusCode -ge 200 -and $r.StatusCode -lt 300){ $ok++ }
    } catch {
      $dur += 8000
    }
  }
  $sorted = $dur | Sort-Object
  $p95index = [Math]::Ceiling($sorted.Count*0.95)-1
  if($p95index -lt 0){$p95index=0}
  if($p95index -ge $sorted.Count){$p95index=$sorted.Count-1}
  $p95 = if($sorted.Count -gt 0){ [int]$sorted[$p95index] } else { -1 }

  Row "api_smoke_ok_count" ([string]$ok)
  Row "api_smoke_total" ([string]$eps.Count)
  Row "api_smoke_p95_ms" ([string]$p95)

  $pytestAvailable = $null -ne (Get-Command pytest -ErrorAction SilentlyContinue)
  $pytestStatus = 'not_available'
  $pytestSummary = 'not_run'
  if($pytestAvailable){
    $out = & pytest .\tests\test_source_confidence_rules.py .\tests\test_source_confidence_integration.py .\tests\test_scoring.py .\tests\test_source_manifest_status.py .\tests\test_sale_land_verification_route.py .\tests\test_parcel_matcher_source_confidence.py -q 2>&1
    $code = $LASTEXITCODE
    if($out){ $pytestSummary = (($out | Select-Object -Last 1) -as [string]).Trim() }
    if($code -eq 0){ $pytestStatus = 'passed' } else { $pytestStatus = 'failed' }
  }
  Row "pytest_available" ($pytestAvailable.ToString().ToLowerInvariant())
  Row "pytest_status" $pytestStatus
  Row "pytest_summary" $pytestSummary

  $final = 'CANLIYA_HAZIR_DEGIL'
  if($branch -eq $ExpectedBranch -and $headOk -and $ok -eq 7 -and $pytestStatus -eq 'passed'){
    $final = 'ULTRA_SCOPE_READY_FOR_CHATGPT_IMPLEMENTATION'
  }
  Row "final_classification" $final
  Row "db_write" "none"
  Row "ddl" "none"
  Row "migration_apply" "none"
  Row "prod_deploy" "none"
  Row "secret_values_printed" "false"

  $rows | Set-Content -LiteralPath $step12 -Encoding UTF8
  Write-Host "STEP12_REPORT=$step12"
  Write-Host "FINAL_CLASSIFICATION=$final"
}
finally {
  Pop-Location
}

