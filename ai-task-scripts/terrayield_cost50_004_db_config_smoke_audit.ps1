$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-004-db-config-smoke-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Line([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function Read-Small([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

Line "TASK=$TaskId"
Line 'MODE=cost50_db_config_smoke_audit_readonly'
Line "BRIDGE_ROOT=$BridgeRoot"
Line "PROJECT_ROOT=$ProjectRoot"

$targets = [ordered]@{
  app_main = Join-Path $ProjectRoot 'app\main.py'
  db_models = Join-Path $ProjectRoot 'app\db\models.py'
  alembic_env = Join-Path $ProjectRoot 'alembic\env.py'
  alembic_versions = Join-Path $ProjectRoot 'alembic\versions'
  requirements = Join-Path $ProjectRoot 'requirements.txt'
  pyproject = Join-Path $ProjectRoot 'pyproject.toml'
  env_example = Join-Path $ProjectRoot '.env.example'
}

$checks = [ordered]@{}
Line 'PATH_CHECKS_BEGIN'
foreach ($k in $targets.Keys) {
  $ok = Exists $targets[$k]
  $checks[$k] = $ok
  Line ($k + '=' + $ok + ' path=' + $targets[$k])
}
Line 'PATH_CHECKS_END'

$scanFiles = @(
  $targets.app_main,
  $targets.db_models,
  $targets.alembic_env,
  $targets.requirements,
  $targets.pyproject,
  $targets.env_example
)

$scanText = ''
foreach ($f in $scanFiles) { $scanText += "`n---FILE:$f---`n" + (Read-Small $f) }

$patterns = [ordered]@{
  postgres_token = '(postgresql|postgres|psycopg|asyncpg)'
  database_url_token = 'DATABASE_URL'
  sqlalchemy_token = '(sqlalchemy|SQLAlchemy|create_engine|AsyncSession|sessionmaker)'
  alembic_token = '(alembic|target_metadata|sqlalchemy.url)'
}

Line 'PATTERN_CHECKS_BEGIN'
$patternChecks = [ordered]@{}
foreach ($k in $patterns.Keys) {
  $hit = [bool]($scanText -match $patterns[$k])
  $patternChecks[$k] = $hit
  Line ($k + '=' + $hit)
}
Line 'PATTERN_CHECKS_END'

$score = 0
$total = 0
foreach ($k in $checks.Keys) { $total++; if ($checks[$k]) { $score++ } }
foreach ($k in $patternChecks.Keys) { $total++; if ($patternChecks[$k]) { $score++ } }
$readiness = if ($total -gt 0) { [int](($score / $total) * 100) } else { 0 }

$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = 'git_status_error=' + $_.Exception.Message }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 004 DB Config Smoke Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only DB/config inventory.'
$report += '- No database migration, no source mutation, no external fetch.'
$report += ''
$report += '## Path checks'
foreach ($k in $checks.Keys) { $report += "- ${k}: $($checks[$k])" }
$report += ''
$report += '## Pattern checks'
foreach ($k in $patternChecks.Keys) { $report += "- ${k}: $($patternChecks[$k])" }
$report += ''
$report += "Readiness score: $readiness"
$report += ''
$report += '## Git status'
$report += '```text'
$report += $gitStatus
$report += '```'
$report += ''
$report += '## Next recommendation'
if ($readiness -ge 70) { $report += '- Proceed to Step 005 PostgreSQL cost schema design/migration draft.' } else { $report += '- Repair DB config discovery before schema migration.' }
$report += ''
$report += "PLAN_PROGRESS_PERCENT=8"
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Line ('REPORT_PATH=' + $reportPath)
Line ('READINESS_SCORE=' + $readiness)
Line 'PLAN_PROGRESS_PERCENT=8'
Line 'TASK_COMPLETION=100/100'
Line 'TERRAYIELD_TASK_DONE'
exit 0
