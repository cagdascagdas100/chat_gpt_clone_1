$ErrorActionPreference = 'Continue'
$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$validator = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\166_security_browser_validator.py'
$outPath = Join-Path $repoRoot 'docs\chatgpt_status\aays1\runner_outputs\147_security_300_browser_validation.json'
if (-not (Test-Path -LiteralPath $validator)) {
  $fallback = [ordered]@{
    task_id = 'aays1-147-security-300-browser-validation-20260711'
    page_key = 'aays1'
    status = 'blocked_300_rows_browser_exception'
    browser_status = 'not_run'
    blockers = @('missing_validator:docs/chatgpt_status/aays1/automation/166_security_browser_validator.py')
    single_runner_only = $true
    parallel_runner = $false
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  $fallback | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $outPath -Encoding UTF8
  exit 2
}
& python $validator $repoRoot
$code = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $outPath)) {
  $fallback = [ordered]@{
    task_id = 'aays1-147-security-300-browser-validation-20260711'
    page_key = 'aays1'
    status = 'blocked_300_rows_browser_exception'
    browser_status = 'not_run'
    blockers = @('browser_validator_output_missing')
    single_runner_only = $true
    parallel_runner = $false
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  $fallback | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $outPath -Encoding UTF8
  exit 2
}
exit $code