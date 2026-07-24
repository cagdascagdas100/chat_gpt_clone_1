$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$taskId = 'aays1-137-next-batch-source-fetch-20260710'
$recoveryId = 'aays1-168-security-browser-cli-profile-regex-recovery-20260713'
$validatorRel = 'docs/chatgpt_status/aays1/automation/166_security_browser_validator.py'
$script167Rel = 'docs/chatgpt_status/aays1/automation/167_security_strict_chain_status_reconciliation.ps1'
$outRel = 'docs/chatgpt_status/aays1/runner_outputs/168_security_browser_cli_profile_regex_recovery.json'
$validatorPath = Join-Path $repoRoot ($validatorRel -replace '/', '\')
$script167Path = Join-Path $repoRoot ($script167Rel -replace '/', '\')
$outPath = Join-Path $repoRoot ($outRel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outPath) | Out-Null

$result = [ordered]@{
  task_id = $taskId
  recovery_id = $recoveryId
  page_key = 'aays1'
  status = 'started'
  started_at = (Get-Date).ToUniversalTime().ToString('o')
  completed_at = $null
  repo_root = $repoRoot
  canonical_storage = 'F_PORTABLE_ROOT'
  single_runner_only = $true
  parallel_runner = $false
  execution_mode = 'single_runner_sequential_multiwork'
  requested_subtask_count = 15
  validator_patch_count = 0
  cli_isolated_profile_patch = $false
  tolerant_probe_regex_patch = $false
  cli_profile_cleanup_patch = $false
  validator_compile_exit_code = $null
  child_167_exit_code = $null
  child_167_status = $null
  candidate_source_features = $null
  selected_verified_rows = $null
  added_rows = $null
  score_4_count = $null
  manual_review_count = $null
  official_latest_month = $null
  unique_lsoa_count = $null
  lsoa_http_200_count = $null
  browser_status = $null
  browser_engine = $null
  latest_filter_rows = $null
  console_error_count = $null
  site_data_published = $false
  git_push_status = $null
  remote_readback_status = $null
  completed_gate_count = 0
  total_gate_count = 4
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
  $result | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $outPath -Encoding UTF8
}

function Read-Json([string]$rel) {
  $path = Join-Path $repoRoot ($rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

try {
  if (-not (Test-Path -LiteralPath $validatorPath)) { throw "missing_validator:$validatorRel" }
  if (-not (Test-Path -LiteralPath $script167Path)) { throw "missing_167_script:$script167Rel" }

  $source = Get-Content -LiteralPath $validatorPath -Raw -Encoding UTF8
  $changed = $false

  $oldStart = @'
                try:
                    process = subprocess.run(
'@
  $newStart = @'
                cli_profile = tempfile.mkdtemp(prefix=f"aays_{engine}_")
                try:
                    process = subprocess.run(
'@
  if ($source.Contains($oldStart) -and -not $source.Contains('cli_profile = tempfile.mkdtemp(prefix=f"aays_{engine}_")')) {
    $source = $source.Replace($oldStart,$newStart)
    $result.validator_patch_count++
    $result.cli_isolated_profile_patch = $true
    $changed = $true
  } elseif ($source.Contains('cli_profile = tempfile.mkdtemp(prefix=f"aays_{engine}_")')) {
    $result.cli_isolated_profile_patch = $true
  }

  $oldArgs = @'
                            "--no-default-browser-check",
                            "--virtual-time-budget=22000",
'@
  $newArgs = @'
                            "--no-default-browser-check",
                            "--user-data-dir=" + cli_profile,
                            "--virtual-time-budget=22000",
'@
  if ($source.Contains($oldArgs) -and -not $source.Contains('"--user-data-dir=" + cli_profile')) {
    $source = $source.Replace($oldArgs,$newArgs)
    $result.validator_patch_count++
    $result.cli_isolated_profile_patch = $true
    $changed = $true
  }

  $oldRegex = @'
                    match = re.search(r'<pre id="proof">([^<]*)</pre>', process.stdout, re.S)
'@
  $newRegex = @'
                    match = re.search(r"""<pre[^>]*\bid\s*=\s*['"]proof['"][^>]*>(.*?)</pre>""", process.stdout, re.S | re.I)
'@
  if ($source.Contains($oldRegex)) {
    $source = $source.Replace($oldRegex,$newRegex)
    $result.validator_patch_count++
    $result.tolerant_probe_regex_patch = $true
    $changed = $true
  } elseif ($source.Contains('<pre[^>]*\bid\s*=\s*')) {
    $result.tolerant_probe_regex_patch = $true
  }

  $oldCleanup = @'
                except Exception as exc:
                    proof["diagnostics"].append(
                        f"{engine}: {type(exc).__name__}: {exc!r}"
                    )

        if proof["status"] != "pass":
'@
  $newCleanup = @'
                except Exception as exc:
                    proof["diagnostics"].append(
                        f"{engine}: {type(exc).__name__}: {exc!r}"
                    )
                finally:
                    shutil.rmtree(cli_profile, ignore_errors=True)

        if proof["status"] != "pass":
'@
  if ($source.Contains($oldCleanup) -and -not $source.Contains('shutil.rmtree(cli_profile, ignore_errors=True)')) {
    $source = $source.Replace($oldCleanup,$newCleanup)
    $result.validator_patch_count++
    $result.cli_profile_cleanup_patch = $true
    $changed = $true
  } elseif ($source.Contains('shutil.rmtree(cli_profile, ignore_errors=True)')) {
    $result.cli_profile_cleanup_patch = $true
  }

  if ($changed) {
    [System.IO.File]::WriteAllText($validatorPath,$source,[System.Text.UTF8Encoding]::new($false))
  }

  & python -m py_compile $validatorPath
  $result.validator_compile_exit_code = $LASTEXITCODE
  if ($result.validator_compile_exit_code -ne 0) { throw "validator_python_compile_exit_$($result.validator_compile_exit_code)" }
  if (-not $result.cli_isolated_profile_patch) { throw 'cli_isolated_profile_patch_not_confirmed' }
  if (-not $result.tolerant_probe_regex_patch) { throw 'tolerant_probe_regex_patch_not_confirmed' }
  if (-not $result.cli_profile_cleanup_patch) { throw 'cli_profile_cleanup_patch_not_confirmed' }

  Save-Result
  $childOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script167Path 2>&1
  $result.child_167_exit_code = $LASTEXITCODE

  $out167 = Read-Json 'docs/chatgpt_status/aays1/runner_outputs/167_security_strict_chain_status_reconciliation.json'
  if ($null -eq $out167) { throw 'missing_167_output_after_execution' }

  $result.child_167_status = [string]$out167.status
  $result.candidate_source_features = $out167.candidate_source_features
  $result.selected_verified_rows = $out167.selected_verified_rows
  $result.added_rows = $out167.added_rows
  $result.score_4_count = $out167.score_4_count
  $result.manual_review_count = $out167.manual_review_count
  $result.official_latest_month = $out167.official_latest_month
  $result.unique_lsoa_count = $out167.unique_lsoa_count
  $result.lsoa_http_200_count = $out167.lsoa_http_200_count
  $result.browser_status = $out167.browser_status
  $result.browser_engine = $out167.browser_engine
  $result.latest_filter_rows = $out167.latest_filter_rows
  $result.console_error_count = $out167.console_error_count
  $result.site_data_published = [bool]$out167.site_data_published
  $result.git_push_status = $out167.git_push_status
  $result.remote_readback_status = $out167.remote_readback_status
  $result.completed_gate_count = [int]$out167.completed_gate_count
  $result.total_gate_count = [int]$out167.total_gate_count
  if ($out167.blockers) { $result.blockers += @($out167.blockers | ForEach-Object { "167:$_" }) }

  if ($result.completed_gate_count -eq 4 -and $result.site_data_published -and $result.remote_readback_status -eq 'passed') {
    $result.status = 'completed_browser_cli_hardening_strict_chain_remote_readback_pass_final_false'
    $result.blockers = @()
  } else {
    $result.status = 'blocked_browser_cli_hardening_strict_chain'
    if ($result.child_167_exit_code -ne 0) { $result.blockers += "child_167_exit_$($result.child_167_exit_code)" }
  }
} catch {
  $result.status = 'blocked_browser_cli_profile_regex_recovery'
  $result.blockers += $_.Exception.Message
} finally {
  $result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  $result.blockers = @($result.blockers | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Select-Object -Unique)
  $result.final_ready = $false
  $result.product_final_ready = $false
  Save-Result
}

Write-Host "OUTPUT=$outPath"
if ($result.completed_gate_count -ne $result.total_gate_count -or $result.blockers.Count -gt 0) { exit 2 }
exit 0
