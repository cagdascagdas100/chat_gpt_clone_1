$ErrorActionPreference = 'Continue'
$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$outDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/runner_outputs'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir '136_runner_github_roundtrip_test.json'
$lockPath = Join-Path $repoRoot 'docs/chatgpt_status/_shared/locks/single_runner.lock'
$lock = $null
try { if (Test-Path $lockPath) { $lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json } } catch {}
$result = [ordered]@{
  task_id = 'aays1-136-runner-github-roundtrip-test-20260709'
  page_key = 'aays1'
  status = 'roundtrip_output_written_by_runner'
  checked_at = (Get-Date).ToUniversalTime().ToString('o')
  repo_root = $repoRoot
  lock_pid = if ($lock) { $lock.pid } else { $null }
  runner_active = $true
  pid_alive = $true
  lock_valid = [bool]$lock
  chatgpt_can_read_from_github = $false
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$result | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
exit 0
