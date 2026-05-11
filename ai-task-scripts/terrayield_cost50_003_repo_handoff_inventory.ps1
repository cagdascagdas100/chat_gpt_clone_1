$ErrorActionPreference = 'Continue'

$bridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN' }
$configPath = Join-Path $bridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $configPath) { . $configPath }
$projectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { (Get-Location).Path }
$costDataRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }

Write-Host 'AAYS_COST50_STEP003_REPO_HANDOFF_INVENTORY'
Write-Host ('checked_at=' + (Get-Date -Format 's'))
Write-Host ('bridge_root=' + $bridgeRoot)
Write-Host ('project_root=' + $projectRoot)
Write-Host ('cost_data_root=' + $costDataRoot)
Write-Host ('cwd=' + (Get-Location).Path)

$required = @(
  'app\main.py',
  'app\db\models.py',
  'alembic\env.py',
  'alembic\versions',
  'tools\cost_uk_real_engine',
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_00_README_TR.md',
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_01_MASTER_PLAN_50_STEPS_TR.md',
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_12_COMMAND_RUNBOOK_TR.txt'
)

$missing = @()
Write-Host 'required_path_check_begin'
foreach ($rel in $required) {
  $full = Join-Path $projectRoot $rel
  $ok = Test-Path $full
  Write-Host (($ok ? 'OK   ' : 'MISS ') + $rel)
  if (-not $ok) { $missing += $rel }
}
Write-Host 'required_path_check_end'

$readTargets = @(
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_00_README_TR.md',
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_01_MASTER_PLAN_50_STEPS_TR.md',
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_12_COMMAND_RUNBOOK_TR.txt'
)

Write-Host 'handoff_file_summaries_begin'
foreach ($rel in $readTargets) {
  $full = Join-Path $projectRoot $rel
  if (Test-Path $full) {
    $lines = Get-Content -Encoding UTF8 $full -TotalCount 80 -ErrorAction SilentlyContinue
    Write-Host ('FILE=' + $rel)
    Write-Host ('LINE_COUNT_SAMPLE=' + @($lines).Count)
    Write-Host 'FIRST_LINES_BEGIN'
    $lines | Select-Object -First 20 | ForEach-Object { Write-Host $_ }
    Write-Host 'FIRST_LINES_END'
  } else {
    Write-Host ('FILE_MISSING=' + $rel)
  }
}
Write-Host 'handoff_file_summaries_end'

Write-Host 'git_status_begin'
try { git -C $projectRoot status --short | Write-Host } catch { Write-Host ('git_status_error=' + $_.Exception.Message) }
Write-Host 'git_status_end'

Write-Host 'python_probe_begin'
try { python --version 2>&1 | Write-Host } catch { Write-Host ('python_error=' + $_.Exception.Message) }
Write-Host 'python_probe_end'

Write-Host 'cost_storage_probe_begin'
try {
  New-Item -ItemType Directory -Force -Path $costDataRoot | Out-Null
  Write-Host ('cost_data_root_exists=' + (Test-Path $costDataRoot))
} catch { Write-Host ('cost_storage_error=' + $_.Exception.Message) }
Write-Host 'cost_storage_probe_end'

$resultDir = Join-Path $bridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $resultDir | Out-Null
$summaryPath = Join-Path $resultDir 'cost50-step003-repo-handoff-inventory-latest.json'
$payload = [ordered]@{
  checked_at = (Get-Date -Format 's')
  bridge_root = $bridgeRoot
  project_root = $projectRoot
  cost_data_root = $costDataRoot
  missing_required_paths = $missing
  required_paths_ok = ($missing.Count -eq 0)
}
$payload | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $summaryPath
Write-Host ('summary_json=' + $summaryPath)

if ($missing.Count -gt 0) { exit 2 }
exit 0
