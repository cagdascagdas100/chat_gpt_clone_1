$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$recoveryId = 'aays1-162-security-103-runtime-recovery-20260713'
$startedAt = (Get-Date).ToUniversalTime().ToString('o')

$script103Rel = 'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1'
$script146Rel = 'docs/chatgpt_status/aays1/automation/146_security_strict_multiwork_orchestrator.ps1'
$out103Rel = 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
$out146Rel = 'docs/chatgpt_status/aays1/runner_outputs/146_security_strict_multiwork_orchestrator.json'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/162_security_103_runtime_recovery_orchestrator.json'

$script103Path = Join-Path $repoRoot ($script103Rel -replace '/', '\')
$script146Path = Join-Path $repoRoot ($script146Rel -replace '/', '\')
$out103Path = Join-Path $repoRoot ($out103Rel -replace '/', '\')
$out146Path = Join-Path $repoRoot ($out146Rel -replace '/', '\')
$outputPath = Join-Path $repoRoot ($outputRel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPath) | Out-Null

$sitePaths = @(
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson',
  'england_map_web/data/security_public_safety/security_evidence_manifest.json',
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json',
  'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json',
  'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'
)

$result = [ordered]@{
  task_id = $taskId
  recovery_id = $recoveryId
  status = 'started'
  started_at = $startedAt
  completed_at = $null
  repo_root = $repoRoot
  canonical_storage = 'F_PORTABLE_ROOT'
  single_runner_only = $true
  parallel_runner = $false
  parser_error_count = $null
  parser_errors = @()
  expansion_exit_code = $null
  expansion_output_tail = $null
  expansion_output_exists = $false
  expansion_status = $null
  source_feature_count = $null
  selected_count = $null
  added_count = $null
  score_4_count = $null
  manual_review_count = $null
  csv_geojson_count_parity = $null
  strict_orchestrator_exit_code = $null
  strict_orchestrator_output_tail = $null
  strict_orchestrator_status = $null
  site_data_restored_after_blocker = $false
  blockers = @()
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
}

function Save-Result {
  $result | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $outputPath -Encoding UTF8
}

function Tail-Text([object[]]$Lines, [int]$MaxChars = 16000) {
  $text = (($Lines | Out-String).Trim())
  if ($text.Length -gt $MaxChars) { return $text.Substring($text.Length - $MaxChars) }
  return $text
}

function Read-JsonSafe([string]$Path) {
  try {
    if (Test-Path -LiteralPath $Path) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json }
  } catch {}
  return $null
}

function Restore-Baseline {
  try {
    Push-Location $repoRoot
    & git fetch origin codex/aays-single-runner-v5-20260706 2>&1 | Out-Null
    & git restore --source 'origin/codex/aays-single-runner-v5-20260706' -- @sitePaths 2>&1 | Out-Null
    $result.site_data_restored_after_blocker = ($LASTEXITCODE -eq 0)
    if (-not $result.site_data_restored_after_blocker) { $result.blockers += 'site_data_restore_failed' }
  } catch {
    $result.blockers += ('site_data_restore_exception:' + $_.Exception.Message)
  } finally {
    try { Pop-Location } catch {}
  }
}

try {
  if (-not (Test-Path -LiteralPath $script103Path)) { throw "missing_script:$script103Rel" }
  if (-not (Test-Path -LiteralPath $script146Path)) { throw "missing_script:$script146Rel" }

  $tokens = $null
  $parseErrors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($script103Path, [ref]$tokens, [ref]$parseErrors)
  $result.parser_error_count = @($parseErrors).Count
  $result.parser_errors = @($parseErrors | ForEach-Object { [string]$_.Message })
  if ($result.parser_error_count -ne 0) {
    throw ('103_parser_validation_failed:' + ($result.parser_errors -join ' | '))
  }

  Save-Result
  $oldPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = 'Continue'
    $expansionOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script103Path 2>&1
    $result.expansion_exit_code = $LASTEXITCODE
    $result.expansion_output_tail = Tail-Text $expansionOutput
  } finally {
    $ErrorActionPreference = $oldPreference
  }

  $out103 = Read-JsonSafe $out103Path
  $result.expansion_output_exists = ($null -ne $out103)
  if ($null -ne $out103) {
    $result.expansion_status = [string]$out103.status
    $result.source_feature_count = $out103.source_feature_count
    $result.selected_count = $out103.selected_count
    $result.added_count = $out103.added_count
    $result.score_4_count = $out103.score_4_count
    $result.manual_review_count = $out103.manual_review_count
    $result.csv_geojson_count_parity = $out103.csv_geojson_count_parity
    if ($out103.blockers) { $result.blockers += @($out103.blockers | ForEach-Object { '103:' + [string]$_ }) }
  } else {
    $result.blockers += '103_output_missing_or_invalid'
  }

  $expansionPass = (
    $result.expansion_exit_code -eq 0 -and
    $null -ne $out103 -and
    [int]$out103.selected_count -eq 300 -and
    [int]$out103.added_count -eq 150 -and
    [int]$out103.score_4_count -eq 300 -and
    [int]$out103.manual_review_count -eq 0 -and
    $out103.csv_geojson_count_parity -eq $true
  )

  if (-not $expansionPass) {
    $result.status = 'blocked_after_diagnostic_103_run'
    if (-not ($result.blockers -contains '103_strict_expansion_gate_not_passed')) { $result.blockers += '103_strict_expansion_gate_not_passed' }
    Restore-Baseline
  } else {
    Save-Result
    $oldPreference = $ErrorActionPreference
    try {
      $ErrorActionPreference = 'Continue'
      $strictOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script146Path 2>&1
      $result.strict_orchestrator_exit_code = $LASTEXITCODE
      $result.strict_orchestrator_output_tail = Tail-Text $strictOutput
    } finally {
      $ErrorActionPreference = $oldPreference
    }

    $out146 = Read-JsonSafe $out146Path
    if ($null -ne $out146) {
      $result.strict_orchestrator_status = [string]$out146.status
      if ($out146.blockers) { $result.blockers += @($out146.blockers | ForEach-Object { '146:' + [string]$_ }) }
    } else {
      $result.blockers += '146_output_missing_or_invalid'
    }

    if ($result.strict_orchestrator_exit_code -eq 0 -and $null -ne $out146 -and $out146.site_data_published -eq $true -and $out146.remote_readback_status -eq 'passed') {
      $result.status = 'completed_103_diagnostic_and_strict_chain'
    } else {
      $result.status = '103_passed_strict_chain_blocked'
      $result.blockers += ('146_exit_' + [string]$result.strict_orchestrator_exit_code)
      if ($null -eq $out146 -or $out146.site_data_published -ne $true) { Restore-Baseline }
    }
  }
}
catch {
  $result.status = 'blocked_runtime_recovery'
  $result.blockers += $_.Exception.Message
  Restore-Baseline
}
finally {
  $result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  Save-Result
}

Write-Host "OUTPUT=$outputPath"
if ($result.blockers.Count -gt 0) { exit 2 }
exit 0
