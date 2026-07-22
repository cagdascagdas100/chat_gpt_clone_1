param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [int]$Port = 8012
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne 'gas_emissions_1') { throw 'WRONG_SLOT_CONTEXT' }
$env:AAYS_SLOT_ID = 'gas_emissions_1'
if (-not $env:AAYS_TASK_ID) { $env:AAYS_TASK_ID = 'gas_emissions_1_single_pass_recovery_20260722_01' }

$reportRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_single_pass_recovery_latest.json'
$statusRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_single_pass_recovery_latest.json'
$webRel = 'england_map_web/data/aays_21_slots/gas_emissions_1/single_pass_recovery_latest.json'

function UtcNow { [DateTime]::UtcNow.ToString('o') }

function Get-GitBlobSha([string]$Path) {
  $bytes = [IO.File]::ReadAllBytes($Path)
  $header = [Text.Encoding]::ASCII.GetBytes(('blob ' + $bytes.Length + [char]0))
  $stream = New-Object IO.MemoryStream
  try {
    $stream.Write($header, 0, $header.Length)
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Position = 0
    $sha1 = [Security.Cryptography.SHA1]::Create()
    try {
      $hash = $sha1.ComputeHash($stream)
      return (-join ($hash | ForEach-Object { $_.ToString('x2') }))
    }
    finally { $sha1.Dispose() }
  }
  finally { $stream.Dispose() }
}

function Write-CarrierFailure([string]$Reason, [object[]]$Checks) {
  $payload = [ordered]@{
    schema_version = 4
    architecture_version = 3
    workstream_id = 'AAYS_21_SLOT_SAFE_PARALLEL_V1'
    slot_id = 'gas_emissions_1'
    task_id = $env:AAYS_TASK_ID
    generated_at = UtcNow
    status = 'BLOCKED_CARRIER_PRECHECK_RECORDED'
    orchestration_completed = $false
    runner_execution_observed = $true
    carrier_version = 5
    carrier_precheck_passed = $false
    blocker = $Reason
    git_blob_checks = $Checks
    measured_facility_emission_rows_claimed_by_orchestrator = 0
    measured_parcel_emission_rows_claimed_by_orchestrator = 0
    verified_parcel_bindings_claimed_by_orchestrator = 0
    actual_business_data_rows_written_by_orchestrator = 0
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  foreach ($relative in @($reportRel,$statusRel,$webRel)) {
    $path = Join-Path $RepoRoot $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
    $payload | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $path -Encoding UTF8
  }
  $payload | ConvertTo-Json -Depth 12
}

$requiredFiles = [ordered]@{
  'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/RUN_GAS_EMISSIONS_1_SINGLE_PASS_RECOVERY_20260722_V2.ps1' = 'fcf2312f8847467eef05f364f51c5c3d53948f08'
  'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/VERIFY_100_ROWS_BROWSER_DUMP_DOM_20260722.ps1' = '782a33612e5e81f2402a66d61d1073c12dbc6e30'
  'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/EXTRACT_HMLR_INSPIRE_PROXIMITY_20260722_V2.py' = '12ef61ecd32c11527d5c4e7171ca30de3049d496'
  'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V17.py' = '08a30bf3507d8777e2992da11350d7228574af60'
  'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/CLASSIFY_PRTR_PI_TARGET_RECORDS_20260722_V5.py' = 'caca618745689df20ee6b5285a2167c0fa9875b8'
  'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V15.py' = 'd59d8ecc8d2ca6c847f00da04cf16d160e51b610'
}

$checks = @()
try {
  foreach ($entry in $requiredFiles.GetEnumerator()) {
    $absolute = Join-Path $RepoRoot $entry.Key
    if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) {
      $checks += [pscustomobject]@{ path=$entry.Key; expected_git_blob_sha=$entry.Value; actual_git_blob_sha=$null; passed=$false; blocker='FILE_NOT_FOUND' }
      throw ('PINNED_FILE_NOT_FOUND:' + $entry.Key)
    }
    $actual = Get-GitBlobSha $absolute
    $passed = ($actual -eq $entry.Value)
    $checks += [pscustomobject]@{ path=$entry.Key; expected_git_blob_sha=$entry.Value; actual_git_blob_sha=$actual; passed=$passed; blocker=$(if ($passed) {$null} else {'GIT_BLOB_SHA_MISMATCH'}) }
    if (-not $passed) { throw ('PINNED_GIT_BLOB_SHA_MISMATCH:' + $entry.Key + ':' + $actual) }
  }

  $baseRelative = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/RUN_GAS_EMISSIONS_1_SINGLE_PASS_RECOVERY_20260722_V2.ps1'
  $basePath = Join-Path $RepoRoot $baseRelative
  $text = Get-Content -LiteralPath $basePath -Raw
  $replacements = [ordered]@{
    'HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V15.py' = 'HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V17.py'
    'CLASSIFY_PRTR_PI_TARGET_RECORDS_20260722_V3.py' = 'CLASSIFY_PRTR_PI_TARGET_RECORDS_20260722_V5.py'
    'VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V13.py' = 'VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V15.py'
    'V15_ADDS_S_NORTON_AND_BD_WATER_IDENTITIES_WITH_HMLR_TITLE_SEARCH_DISABLED' = 'V17_ADDS_RIVERSIDE_VEOLIA_SHARPSMART_AND_ITM_IDENTITIES_WITH_HMLR_TITLE_SEARCH_DISABLED'
    'V3_USES_EXACT_PARSER_V15_ALIAS_SET_WITH_BASE_QUALITY_GATES' = 'V5_USES_EXACT_PARSER_V17_ALIAS_SET_WITH_BASE_QUALITY_GATES'
    'V13_INCLUDES_V12_SURRENDER_HISTORY_AND_ADDS_HAZARDOUS_STORAGE_COOLING_WATER_FLOW_EXCLUSIONS' = 'V15_INCLUDES_V14_AND_ADDS_PARTIAL_SURRENDER_SUPPORT_SITE_CAPACITY_DOCUMENT_AND_NAME_CHANGE_EXCLUSIONS'
  }
  foreach ($entry in $replacements.GetEnumerator()) {
    if (-not $text.Contains($entry.Key)) { throw ('EXPECTED_PINNED_TEXT_NOT_FOUND:' + $entry.Key) }
    $text = $text.Replace($entry.Key, $entry.Value)
  }

  $tempPath = Join-Path ([IO.Path]::GetTempPath()) ('gas_emissions_1_recovery_v17_' + [Guid]::NewGuid().ToString('N') + '.ps1')
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [IO.File]::WriteAllText($tempPath, $text, $utf8)
  $powershell = Get-Command powershell.exe -ErrorAction SilentlyContinue
  if (-not $powershell) { $powershell = Get-Command powershell -ErrorAction SilentlyContinue }
  if (-not $powershell) { throw 'POWERSHELL_CHILD_RUNTIME_NOT_FOUND' }

  try {
    & $powershell.Source -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $tempPath -RepoRoot $RepoRoot -Port $Port
    $code = $LASTEXITCODE
  }
  finally {
    Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
  }
  exit $code
}
catch {
  Write-CarrierFailure $_.Exception.Message $checks
  exit 2
}
