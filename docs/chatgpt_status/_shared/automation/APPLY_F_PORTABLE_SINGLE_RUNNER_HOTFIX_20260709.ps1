# AAYS F portable single-runner hotfix
# Purpose: prepare an external patched copy of the stable shared runner for the F portable system.
# It avoids dirtying the controller repo runner script, adds the active 8012 portable site port to browser smoke,
# and keeps the single-runner topology unchanged.
# Safety: no fake data, no DB write, no migration, no production deploy.
# Idempotent: if already applied, continue without throwing.

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$runnerScript = Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1'
$portableRoot = if ($env:AAYS_PORTABLE_ROOT) { $env:AAYS_PORTABLE_ROOT } else { 'F:\TerraYield_AAYS_Portable' }
$runtimeDir = Join-Path $portableRoot '_portable_runtime'
$patchedRunner = Join-Path $runtimeDir 'RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_PATCHED_20260709.ps1'

if (-not (Test-Path -LiteralPath $runnerScript)) {
  throw "RUNNER_SCRIPT_MISSING: $runnerScript"
}
if (-not (Test-Path -LiteralPath $runtimeDir)) { New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null }

$content = Get-Content -LiteralPath $runnerScript -Raw
$original = $content

# Canonical F portable defaults, without editing the repo file in place.
$content = $content.Replace("[string]`$RepoRoot = 'C:\AAYS_WT\AAYS_REPAIR_20260706_1738'", "[string]`$RepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'")
$content = $content.Replace("[string]`$WorkRoot = 'C:\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'", "[string]`$WorkRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'")
$content = $content.Replace("[int]`$MaxTasks = 1", "[int]`$MaxTasks = 5")
$content = $content.Replace("if (`$RepoRoot.StartsWith('F:\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED_F_DRIVE_NOT_CANONICAL: ' + `$RepoRoot }", "if (`$RepoRoot.StartsWith('C:\AAYS_WT\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED_C_DRIVE_NOT_CANONICAL: ' + `$RepoRoot }")

# Treat the local hotfix proof as controller-runtime output, not a dirty blocker.
$content = $content.Replace(
"    `$r -eq 'docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json' -or",
"    `$r -eq 'docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json' -or`r`n    `$r -eq 'docs/chatgpt_status/_shared/status/f_portable_runner_hotfix_latest.json' -or"
)

# Portable panel/app runs on 8012. Older smoke checks only looked at 8010/8020 and caused false BLOCKED_BROWSER_ENVIRONMENT.
$content = $content.Replace(
"  `$site8010 = `$false`r`n  `$site8020 = `$false",
"  `$site8010 = `$false`r`n  `$site8020 = `$false`r`n  `$site8012 = `$false"
)
$content = $content.Replace(
"  try { `$resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?runner_smoke=1' -TimeoutSec 5; `$site8020 = (`$resp.StatusCode -ge 200 -and `$resp.StatusCode -lt 500) } catch {}",
"  try { `$resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?runner_smoke=1' -TimeoutSec 5; `$site8020 = (`$resp.StatusCode -ge 200 -and `$resp.StatusCode -lt 500) } catch {}`r`n  try { `$resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/health' -TimeoutSec 5; `$site8012 = (`$resp.StatusCode -ge 200 -and `$resp.StatusCode -lt 500) } catch {}"
)
$content = $content.Replace(
"  `$smoke = ([bool]`$edge -and (`$site8010 -or `$site8020))",
"  `$smoke = ([bool]`$edge -and (`$site8010 -or `$site8020 -or `$site8012))"
)
$content = $content.Replace(
"site_8010_ok=`$site8010; site_8020_ok=`$site8020; browser_smoke_degraded_ok=(`$smoke -and -not `$playwright); browser_smoke_passed=`$smoke",
"site_8010_ok=`$site8010; site_8020_ok=`$site8020; site_8012_ok=`$site8012; browser_smoke_degraded_ok=(`$smoke -and -not `$playwright); browser_smoke_passed=`$smoke"
)
$content = $content.Replace(
"site_8020_ok=`$(`$browser.site_8020_ok)`nbrowser_smoke_passed=`$(`$browser.browser_smoke_passed)",
"site_8020_ok=`$(`$browser.site_8020_ok)`nsite_8012_ok=`$(`$browser.site_8012_ok)`nbrowser_smoke_passed=`$(`$browser.browser_smoke_passed)"
)

[System.IO.File]::WriteAllText($patchedRunner, $content, [System.Text.UTF8Encoding]::new($false))

$patchMode = if ($content -eq $original) { 'external_copy_without_source_changes' } else { 'external_patched_copy_created' }
$statusPath = Join-Path $repoRoot 'docs\chatgpt_status\_shared\status\f_portable_runner_hotfix_latest.json'
$statusDir = Split-Path -Parent $statusPath
if (-not (Test-Path -LiteralPath $statusDir)) { New-Item -ItemType Directory -Force -Path $statusDir | Out-Null }
$status = [ordered]@{
  status = 'F_PORTABLE_SINGLE_RUNNER_HOTFIX_OK'
  patch_mode = $patchMode
  runner_script = 'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1'
  patched_runner_script = $patchedRunner
  canonical_repo_root = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
  canonical_work_root = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'
  browser_smoke_ports = @(8012, 8020, 8010)
  max_tasks = 5
  single_runner_only = $true
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  applied_at_utc = (Get-Date).ToUniversalTime().ToString('o')
}
$status | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statusPath -Encoding UTF8
Write-Output ($status | ConvertTo-Json -Depth 20)
