$ErrorActionPreference = 'Stop'
$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$pageKey = 'aays1'
$outDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/runner_outputs'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir '102_real_visible_security_site_bridge.json'

$latestRel = 'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'
$testRel = 'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/real_visible_test_20260709.json'
$statusRel = 'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/site_visibility_status.json'
$matrixDir = Join-Path $repoRoot 'england_map_web/data/program_layer_matrix'
$matrixStatusRel = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json'
$matrixStatus = Join-Path $repoRoot $matrixStatusRel
New-Item -ItemType Directory -Force -Path $matrixDir | Out-Null

$latestPath = Join-Path $repoRoot $latestRel
$testPath = Join-Path $repoRoot $testRel
$statusPath = Join-Path $repoRoot $statusRel

$result = [ordered]@{
  task_id = 'aays1-102-real-visible-security-site-bridge-20260709'
  page_key = $pageKey
  status = 'started'
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  checked_at = (Get-Date).ToString('o')
  repo_root = $repoRoot
  inputs = @{}
  outputs = @{}
  blockers = @()
}

foreach ($item in @(@{name='latest_changes'; path=$latestPath}, @{name='real_visible_test'; path=$testPath}, @{name='site_visibility_status'; path=$statusPath})) {
  $exists = Test-Path $item.path
  $result.inputs[$item.name] = @{ path = $item.path; exists = $exists }
  if (-not $exists) { $result.blockers += "missing_$($item.name)" }
}

if ((Test-Path $latestPath) -and (Test-Path $testPath)) {
  $latest = Get-Content -Raw -Encoding UTF8 $latestPath | ConvertFrom-Json
  $test = Get-Content -Raw -Encoding UTF8 $testPath | ConvertFrom-Json
  $visible = [ordered]@{
    page_key = $pageKey
    layer = 'Safety / Security'
    status = 'REAL_DATA_VISIBLE_TEST_BRIDGED_TO_PROGRAM_LAYER_MATRIX'
    message_tr = 'Gercek verified parcel_1 Security/Public Safety testi program_layer_matrix altina kopyalandi. Site bu data klasorunu okuyorsa pozitif veri gorunmelidir; final icin browser smoke gerekir.'
    data_ready = $true
    final_ready = $false
    fake_data = $false
    progress_percent = 99
    remaining_percent = 1
    source_latest_changes = $latestRel
    source_real_visible_test = $testRel
    parcel = $test.parcel
    generated_at = (Get-Date).ToString('o')
  }
  $visible | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $matrixStatus
  $result.outputs['program_layer_matrix_status'] = @{ path = $matrixStatus; rel = $matrixStatusRel; exists = (Test-Path $matrixStatus) }
  $result.status = 'completed_visible_bridge_written_pending_browser_smoke'
} else {
  $result.status = 'blocked_missing_inputs'
}

$result | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
if ($result.blockers.Count -gt 0) { exit 2 }
exit 0
