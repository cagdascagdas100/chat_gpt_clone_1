param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [int]$Port = 8012
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne 'gas_emissions_1') { throw 'WRONG_SLOT_CONTEXT' }
$env:AAYS_SLOT_ID = 'gas_emissions_1'

$baseRelative = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/RUN_GAS_EMISSIONS_1_SINGLE_PASS_RECOVERY_20260722_V2.ps1'
$basePath = Join-Path $RepoRoot $baseRelative
$requiredBaseSha = 'fcf2312f8847467eef05f364f51c5c3d53948f08'
if (-not (Test-Path -LiteralPath $basePath -PathType Leaf)) { throw 'PINNED_V2_ORCHESTRATOR_NOT_FOUND' }
$actualBaseSha = (Get-FileHash -LiteralPath $basePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualBaseSha -ne $requiredBaseSha) { throw ('PINNED_V2_ORCHESTRATOR_SHA_MISMATCH:' + $actualBaseSha) }

$text = Get-Content -LiteralPath $basePath -Raw
$replacements = [ordered]@{
  'HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V15.py' = 'HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V16.py'
  'CLASSIFY_PRTR_PI_TARGET_RECORDS_20260722_V3.py' = 'CLASSIFY_PRTR_PI_TARGET_RECORDS_20260722_V4.py'
  'VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V13.py' = 'VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V14.py'
  'V15_ADDS_S_NORTON_AND_BD_WATER_IDENTITIES_WITH_HMLR_TITLE_SEARCH_DISABLED' = 'V16_ADDS_H_SIVYER_AND_DB_CARGO_IDENTITIES_WITH_HMLR_TITLE_SEARCH_DISABLED'
  'V3_USES_EXACT_PARSER_V15_ALIAS_SET_WITH_BASE_QUALITY_GATES' = 'V4_USES_EXACT_PARSER_V16_ALIAS_SET_WITH_BASE_QUALITY_GATES'
  'V13_INCLUDES_V12_SURRENDER_HISTORY_AND_ADDS_HAZARDOUS_STORAGE_COOLING_WATER_FLOW_EXCLUSIONS' = 'V14_INCLUDES_V13_AND_ADDS_TRANSFER_STATION_EWC_CAPACITY_AND_BOUNDARY_EXCLUSIONS'
}
foreach ($entry in $replacements.GetEnumerator()) {
  if (-not $text.Contains($entry.Key)) { throw ('EXPECTED_PINNED_TEXT_NOT_FOUND:' + $entry.Key) }
  $text = $text.Replace($entry.Key, $entry.Value)
}

$tempPath = Join-Path ([IO.Path]::GetTempPath()) ('gas_emissions_1_recovery_v16_' + [Guid]::NewGuid().ToString('N') + '.ps1')
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
