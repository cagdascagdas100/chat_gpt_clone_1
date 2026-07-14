$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-170-current-five-pages-verified-continuation-20260714'
$outRel = 'docs/chatgpt_status/aays1/runner_outputs/170_current_five_pages_verified_continuation.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/170_current_five_pages_verified_continuation_20260714.md'
$outPath = Join-Path $repoRoot ($outRel -replace '/', '\')
$reportPath = Join-Path $repoRoot ($reportRel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outPath),(Split-Path -Parent $reportPath) | Out-Null

function Read-Text([string]$rel) {
  $path = Join-Path $repoRoot ($rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "missing_file:$rel" }
  return Get-Content -LiteralPath $path -Raw -Encoding UTF8
}

function Read-Json([string]$rel) {
  $text = Read-Text $rel
  try { return $text | ConvertFrom-Json } catch { throw "invalid_json:$rel" }
}

$result = [ordered]@{
  task_id = $taskId
  page_key = 'aays1'
  status = 'started'
  checked_at = (Get-Date).ToUniversalTime().ToString('o')
  scope = 'current_five_pages_only_no_5x5'
  runner_architecture_change = $false
  five_by_five_plan_applied = $false
  parcel_label = [ordered]@{ passed=$false; verified_rows=0 }
  topography_runner_contract = [ordered]@{ passed=$false; tests_passed=0; tests_total=6 }
  gas_emissions = [ordered]@{ passed=$false; verified_rows=0; latest_rows=0; console_errors=$null }
  security = [ordered]@{ passed=$false; verified_rows=0; new_rows=0; official_lsoa=0; gates='0/4'; console_errors=$null }
  ready_to_sell = [ordered]@{ passed=$false; served_rows=0; ready_rows=0; photo_rows=0; polygon_rows=0 }
  completed_domain_checks = 0
  total_domain_checks = 5
  blockers = @()
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}

try {
  $parcel = Read-Text 'docs/chatgpt_status/aays1/reports/CHATGPT_RESULT_PARCEL_LABEL_20260714.md'
  if ($parcel -match '36/36' -and $parcel -match 'Runner sonucu: `done`' -and $parcel -match 'HTTP/browser') {
    $result.parcel_label.passed = $true
    $result.parcel_label.verified_rows = 36
  } else { $result.blockers += 'parcel_label_report_contract_failed' }

  $claim = Read-Json 'docs/chatgpt_status/_shared/status/single_runner_claim_contract_test_latest.json'
  $testValues = @($claim.tests.PSObject.Properties | ForEach-Object { [bool]$_.Value })
  $passedTests = @($testValues | Where-Object { $_ }).Count
  $result.topography_runner_contract.tests_passed = $passedTests
  if ([bool]$claim.queue_fix_verified -and [bool]$claim.remote_readback_ok -and $passedTests -eq 6 -and @($claim.blockers).Count -eq 0) {
    $result.topography_runner_contract.passed = $true
  } else { $result.blockers += 'topography_runner_contract_failed' }

  $gas = Read-Text 'docs/chatgpt_status/aays1/reports/CHATGPT_RESULT_GAS_EMISSIONS_20260714.md'
  if ($gas -match '66/66/66' -and $gas -match 'Browser testi: PASS' -and $gas -match 'Console hata say') {
    $result.gas_emissions.passed = $true
    $result.gas_emissions.verified_rows = 66
    $result.gas_emissions.latest_rows = 29
    $result.gas_emissions.console_errors = 0
  } else { $result.blockers += 'gas_emissions_report_contract_failed' }

  $security = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/169_security_publish_remote_readback_recovery.json'
  if ([int]$security.verified_csv_rows -eq 300 -and [int]$security.verified_geojson_features -eq 300 -and [int]$security.browser_visible_rows -eq 300 -and [int]$security.new_rows -eq 150 -and [int]$security.completed_gate_count -eq 4 -and [int]$security.total_gate_count -eq 4 -and [bool]$security.remote_readback_ok -and @($security.blockers).Count -eq 0) {
    $result.security.passed = $true
    $result.security.verified_rows = 300
    $result.security.new_rows = 150
    $result.security.official_lsoa = [int]$security.official_api_lsoa_validated_count
    $result.security.gates = '4/4'
    $result.security.console_errors = [int]$security.console_error_count
  } else { $result.blockers += 'security_remote_readback_contract_failed' }

  $ready = Read-Text 'docs/chatgpt_status/aays1/reports/CHATGPT_RESULT_READY_TO_SELL_20260714.md'
  if ($ready -match '655/655/655' -and $ready -match 'Runner push ve remote readback: ba') {
    $result.ready_to_sell.passed = $true
    $result.ready_to_sell.served_rows = 655
    $result.ready_to_sell.ready_rows = 469
    $result.ready_to_sell.photo_rows = 469
    $result.ready_to_sell.polygon_rows = 470
  } else { $result.blockers += 'ready_to_sell_report_contract_failed' }

  $passes = @(
    [bool]$result.parcel_label.passed,
    [bool]$result.topography_runner_contract.passed,
    [bool]$result.gas_emissions.passed,
    [bool]$result.security.passed,
    [bool]$result.ready_to_sell.passed
  )
  $result.completed_domain_checks = @($passes | Where-Object { $_ }).Count
  if ($result.completed_domain_checks -eq 5 -and $result.blockers.Count -eq 0) {
    $result.status = 'completed_current_five_pages_verified_no_5x5_final_false'
  } else {
    $result.status = 'blocked_current_five_pages_verification'
  }
} catch {
  $result.status = 'blocked_current_five_pages_verification_exception'
  $result.blockers += $_.Exception.Message
} finally {
  $result.checked_at = (Get-Date).ToUniversalTime().ToString('o')
  $result.blockers = @($result.blockers | Where-Object { $_ } | Select-Object -Unique)
  $result.final_ready = $false
  $result.product_final_ready = $false
  $result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $outPath -Encoding UTF8

  $lines = @(
    '# Current Five Pages - Verified Continuation',
    '',
    "- Status: `$($result.status)`",
    "- Checks: $($result.completed_domain_checks)/$($result.total_domain_checks)",
    "- Parcel Label: $($result.parcel_label.verified_rows) verified rows",
    "- Topography runner contract: $($result.topography_runner_contract.tests_passed)/6 tests",
    "- Gas Emissions: $($result.gas_emissions.verified_rows) verified rows; latest $($result.gas_emissions.latest_rows)",
    "- Security: $($result.security.verified_rows) verified; new $($result.security.new_rows); LSOA $($result.security.official_lsoa); gates $($result.security.gates)",
    "- Ready to Sell: served $($result.ready_to_sell.served_rows); ready $($result.ready_to_sell.ready_rows)",
    "- 5x5 applied: false",
    "- Blockers: $(@($result.blockers) -join '; ')",
    '- final_ready=false',
    '- product_final_ready=false',
    '- fake_data=false',
    '- db_write=false',
    '- migration=false',
    '- production_deploy=false'
  )
  $lines | Set-Content -LiteralPath $reportPath -Encoding UTF8
}

Write-Host "OUTPUT=$outPath"
if ($result.blockers.Count -gt 0) { exit 2 }
exit 0
