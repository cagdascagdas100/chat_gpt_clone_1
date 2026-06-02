$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-061-pytest-temp-repair'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$TempRoot = 'C:\AAYS1_GITHUB_BRIDGE\pytest_tmp'
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null
$env:TEMP = $TempRoot
$env:TMP = $TempRoot
$errors = @()
$pytestOutput = ''
$pytestExitCode = 999
try {
  Push-Location $Backend
  $pytestOutput = (& python -m pytest future_growth\tests\test_source_catalog_loader.py -q --basetemp $TempRoot 2>&1 | Out-String)
  $pytestExitCode = $LASTEXITCODE
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  $errors += $_.Exception.Message
}
$status = if (($errors.Count -eq 0) -and ($pytestExitCode -eq 0)) { 'completed' } else { 'failed' }
$audit = [ordered]@{
  task_id = $TaskId
  status = $status
  generated_at = (Get-Date).ToString('s')
  pytest_exit_code = $pytestExitCode
  pytest_output = $pytestOutput
  temp_root = $TempRoot
  errors = $errors
  next_action = 'If completed, runner result channel is healthy with controlled pytest temp. If failed, inspect pytest_output.'
}
$audit | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $ResultsDir ($TaskId + '.audit.json')) -Encoding UTF8
if ($status -eq 'completed') { Write-Host 'PYTEST_TEMP_REPAIR_COMPLETE'; exit 0 }
Write-Host 'PYTEST_TEMP_REPAIR_FAILED'; exit 1
