$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$recoveryId = 'aays1-161-security-137-parser-recovery-20260713'
$startedAt = (Get-Date).ToUniversalTime().ToString('o')

$script103Rel = 'docs/chatgpt_status/aays1/automation/103_security_accuracy_count_expansion.ps1'
$script146Rel = 'docs/chatgpt_status/aays1/automation/146_security_strict_multiwork_orchestrator.ps1'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/161_security_137_parser_recovery_orchestrator.json'
$script103Path = Join-Path $repoRoot ($script103Rel -replace '/', '\')
$script146Path = Join-Path $repoRoot ($script146Rel -replace '/', '\')
$outputPath = Join-Path $repoRoot ($outputRel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPath) | Out-Null

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
  repaired_script = $script103Rel
  parser_fix_applied = $false
  parser_error_count = $null
  parser_errors = @()
  child_orchestrator = $script146Rel
  child_exit_code = $null
  child_output_tail = $null
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
  $result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $outputPath -Encoding UTF8
}

try {
  if (-not (Test-Path -LiteralPath $script103Path)) { throw "missing_script:$script103Rel" }
  if (-not (Test-Path -LiteralPath $script146Path)) { throw "missing_script:$script146Rel" }

  $source = Get-Content -LiteralPath $script103Path -Raw -Encoding UTF8
  $bad = 'throw "baseline_count_not_$baselineExpected:$($baselineRows.Count)"'
  $good = 'throw "baseline_count_not_${baselineExpected}:$($baselineRows.Count)"'

  if ($source.Contains($bad)) {
    $source = $source.Replace($bad, $good)
    [System.IO.File]::WriteAllText($script103Path, $source, [System.Text.UTF8Encoding]::new($false))
    $result.parser_fix_applied = $true
  } elseif ($source.Contains($good)) {
    $result.parser_fix_applied = $false
  } else {
    throw 'expected_103_parser_signature_not_found'
  }

  $tokens = $null
  $parseErrors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($script103Path, [ref]$tokens, [ref]$parseErrors)
  $result.parser_error_count = @($parseErrors).Count
  $result.parser_errors = @($parseErrors | ForEach-Object { [string]$_.Message })
  if ($result.parser_error_count -ne 0) { throw ('103_parser_validation_failed:' + ($result.parser_errors -join ' | ')) }

  Save-Result
  $childOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script146Path 2>&1
  $childCode = $LASTEXITCODE
  $result.child_exit_code = $childCode
  $childText = ($childOutput | Out-String).Trim()
  if ($childText.Length -gt 12000) { $childText = $childText.Substring($childText.Length - 12000) }
  $result.child_output_tail = $childText

  if ($childCode -ne 0) {
    $result.status = 'parser_fixed_child_orchestrator_blocked'
    $result.blockers += "child_orchestrator_exit_$childCode"
  } else {
    $result.status = 'parser_fixed_child_orchestrator_completed'
  }
}
catch {
  $result.status = 'blocked_parser_recovery'
  $result.blockers += $_.Exception.Message
}
finally {
  $result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  Save-Result
}

Write-Host "OUTPUT=$outputPath"
if ($result.blockers.Count -gt 0 -or $result.child_exit_code -notin @(0,$null)) { exit 2 }
exit 0
