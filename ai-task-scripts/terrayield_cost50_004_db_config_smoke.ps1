$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-004-db-config-smoke-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot = 'E:\AAYS_DATA\cost'
$HandoffRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229'
$ProjectRoot = Join-Path $HandoffRoot 'terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ReportDir = Join-Path $CostRoot 'quality_reports'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function Find-First([string]$Root, [string]$Filter) { try { if (Test-Path $Root) { return @(Get-ChildItem -Path $Root -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5 | ForEach-Object { $_.FullName }) } } catch {}; return @() }

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=cost50_db_config_smoke'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "COST_ROOT=$CostRoot"
Step "HANDOFF_ROOT=$HandoffRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$checks = [ordered]@{}
$checks.project_root = Exists $ProjectRoot
$checks.app_main = Exists (Join-Path $ProjectRoot 'app\main.py')
$checks.db_dir = Exists (Join-Path $ProjectRoot 'app\db')
$checks.db_models = Exists (Join-Path $ProjectRoot 'app\db\models.py')
$checks.alembic_ini = Exists (Join-Path $ProjectRoot 'alembic.ini')
$checks.alembic_versions = Exists (Join-Path $ProjectRoot 'alembic\versions')
$checks.requirements = Exists (Join-Path $ProjectRoot 'requirements.txt')
$checks.env_example = (Exists (Join-Path $ProjectRoot '.env.example')) -or (Exists (Join-Path $ProjectRoot 'env.example'))
$checks.cost_engine = Exists (Join-Path $ProjectRoot 'tools\cost_uk_real_engine')

Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$envRefs = @()
if (Test-Path $ProjectRoot) {
  try {
    $envRefs = @(Select-String -Path (Join-Path $ProjectRoot '*') -Pattern 'DATABASE_URL|POSTGRES|SQLALCHEMY|PGHOST|PGUSER' -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 20 | ForEach-Object { $_.Path + ':' + $_.LineNumber + ':' + $_.Line.Trim() })
  } catch {}
}

$pythonVersion = ''
try { $pythonVersion = python --version 2>&1 | Out-String } catch { $pythonVersion = 'PYTHON_CHECK_ERROR=' + $_.Exception.Message }
Step ('PYTHON_VERSION=' + $pythonVersion.Trim())

$pyCompileExit = $null
$pyCompileOutput = ''
if (Exists (Join-Path $ProjectRoot 'app\main.py')) {
  try {
    Push-Location $ProjectRoot
    $pyCompileOutput = python -m py_compile (Join-Path $ProjectRoot 'app\main.py') 2>&1 | Out-String
    $pyCompileExit = $LASTEXITCODE
    Pop-Location
  } catch {
    try { Pop-Location } catch {}
    $pyCompileExit = 999
    $pyCompileOutput = $_.Exception.Message
  }
} else {
  $pyCompileExit = 998
  $pyCompileOutput = 'app/main.py missing'
}
Step ('PY_COMPILE_APP_MAIN_EXIT=' + $pyCompileExit)

$score = 0
foreach ($k in $checks.Keys) { if ($checks[$k]) { $score++ } }
$readiness = [int](($score / $checks.Count) * 100)
if ($pyCompileExit -eq 0) { $readiness = [Math]::Min(100, $readiness + 5) }

$alembicVersions = Find-First (Join-Path $ProjectRoot 'alembic\versions') '*.py'
$sqlFiles = Find-First $ProjectRoot '*.sql'

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$Report = @()
$Report += '# Cost50 Step 004 DB Config Smoke'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Python Compile'
$Report += "- app/main.py py_compile exit: $pyCompileExit"
$Report += '```text'
$Report += $pyCompileOutput
$Report += '```'
$Report += ''
$Report += '## Alembic Version Samples'
if ($alembicVersions.Count -eq 0) { $Report += '- none' } else { $alembicVersions | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## SQL File Samples'
if ($sqlFiles.Count -eq 0) { $Report += '- none' } else { $sqlFiles | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += '## DB Config References'
if ($envRefs.Count -eq 0) { $Report += '- none found in shallow scan' } else { $envRefs | ForEach-Object { $Report += '- ' + $_ } }
$Report += ''
$Report += "Readiness score: $readiness"
$Report += ''
$Report += '## Next Recommendation'
if ($readiness -ge 75) { $Report += '- Proceed to Step 005 route/import smoke audit.' } else { $Report += '- Repair missing DB/config sentinels before route/import smoke.' }
$Report += ''
$Report += "PLAN_PROGRESS_PERCENT=$readiness"
$Report += 'TASK_COMPLETION=100/100'
$Report += 'TERRAYIELD_TASK_DONE'

$Report | Set-Content -Path $ReportPath -Encoding UTF8
try { Copy-Item -Path $ReportPath -Destination $ExternalReportPath -Force } catch {}

Step ('REPORT_PATH=' + $ReportPath)
Step ('EXTERNAL_REPORT_PATH=' + $ExternalReportPath)
Step ('PLAN_PROGRESS_PERCENT=' + $readiness)
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
