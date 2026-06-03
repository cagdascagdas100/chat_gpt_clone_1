$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-003b-inventory-audit-cleanroot-20260512'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
if ($env:AAYS_BRIDGE_ROOT) { $BridgeRoot = $env:AAYS_BRIDGE_ROOT }
$CostRoot = 'E:\AAYS_DATA\cost'
$HandoffRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229'
$ProjectRoot = Join-Path $HandoffRoot 'terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ReportDir = Join-Path $CostRoot 'quality_reports'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Exists([string]$Path) { return [bool](Test-Path $Path) }
function Count-Files([string]$Path, [string]$Filter='*') {
  try {
    if (Test-Path $Path) {
      return @(Get-ChildItem -Path $Path -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue).Count
    }
  } catch {}
  return 0
}

New-Item -ItemType Directory -Force -Path $ResultDir,$ReportDir,$HeartbeatDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=cost50_inventory_audit_cleanroot_retry'
Step "BRIDGE_ROOT=$BridgeRoot"
Step "COST_ROOT=$CostRoot"
Step "HANDOFF_ROOT=$HandoffRoot"
Step "PROJECT_ROOT=$ProjectRoot"

$checks = [ordered]@{}
$checks.cost_root = Exists $CostRoot
$checks.handoff_root = Exists $HandoffRoot
$checks.project_root = Exists $ProjectRoot
$checks.app_main = Exists (Join-Path $ProjectRoot 'app\main.py')
$checks.db_models = Exists (Join-Path $ProjectRoot 'app\db\models.py')
$checks.alembic_versions = Exists (Join-Path $ProjectRoot 'alembic\versions')
$checks.cost_engine = Exists (Join-Path $ProjectRoot 'tools\cost_uk_real_engine')
$checks.master_plan = Exists (Join-Path $ProjectRoot 'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_01_MASTER_PLAN_50_STEPS_TR.md')

Step 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Step ($k + '=' + $checks[$k]) }
Step 'CHECKS_END'

$pyCount = Count-Files $ProjectRoot '*.py'
$sqlCount = Count-Files $ProjectRoot '*.sql'
$mdCount = Count-Files $ProjectRoot '*.md'
$alembicCount = Count-Files (Join-Path $ProjectRoot 'alembic\versions') '*.py'

Step "PY_FILE_COUNT=$pyCount"
Step "SQL_FILE_COUNT=$sqlCount"
Step "MD_FILE_COUNT=$mdCount"
Step "ALEMBIC_VERSION_COUNT=$alembicCount"

$score = 0
foreach ($k in $checks.Keys) { if ($checks[$k]) { $score++ } }
$readiness = 0
if ($checks.Count -gt 0) { $readiness = [int](($score / $checks.Count) * 100) }

$gitStatus = ''
$gitHead = ''
try {
  if (Test-Path $ProjectRoot) {
    Push-Location $ProjectRoot
    $gitStatus = git status --short 2>&1 | Out-String
    $gitHead = git rev-parse HEAD 2>&1 | Out-String
    Pop-Location
  }
} catch {
  try { Pop-Location } catch {}
  $gitStatus = 'GIT_STATUS_ERROR=' + $_.Exception.Message
}

$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ExternalReportPath = Join-Path $ReportDir "$TaskId.report.md"
$JsonPath = Join-Path $ResultDir "$TaskId.result.json"

$Report = @()
$Report += '# Cost50 Step 003B Inventory Audit Cleanroot Retry'
$Report += ''
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Task: $TaskId"
$Report += ''
$Report += '## Paths'
$Report += "- BridgeRoot: $BridgeRoot"
$Report += "- CostRoot: $CostRoot"
$Report += "- HandoffRoot: $HandoffRoot"
$Report += "- ProjectRoot: $ProjectRoot"
$Report += ''
$Report += '## Checks'
foreach ($k in $checks.Keys) { $Report += "- ${k}: $($checks[$k])" }
$Report += ''
$Report += '## Counts'
$Report += "- Python files: $pyCount"
$Report += "- SQL files: $sqlCount"
$Report += "- Markdown files: $mdCount"
$Report += "- Alembic versions: $alembicCount"
$Report += ''
$Report += "Readiness score: $readiness"
$Report += ''
$Report += '## Git'
$Report += "Head: $($gitHead.Trim())"
$Report += '```text'
$Report += $gitStatus
$Report += '```'
$Report += ''
if ($readiness -ge 80) { $Report += 'NEXT_RECOMMENDATION=Proceed to Step 004 DB/config smoke audit.' } else { $Report += 'NEXT_RECOMMENDATION=Repair missing Cost50 sentinel files before DB smoke.' }
$Report += "PLAN_PROGRESS_PERCENT=$readiness"
$Report += 'TASK_COMPLETION=100/100'
$Report += 'TERRAYIELD_TASK_DONE'

$Report | Set-Content -Path $ReportPath -Encoding UTF8
try { Copy-Item -Path $ReportPath -Destination $ExternalReportPath -Force } catch {}

$result = [ordered]@{
  task_id = $TaskId
  status = 'completed'
  bridge_root = $BridgeRoot
  project_root = $ProjectRoot
  readiness = $readiness
  checks = $checks
  py_file_count = $pyCount
  sql_file_count = $sqlCount
  md_file_count = $mdCount
  alembic_version_count = $alembicCount
  report_path = $ReportPath
  external_report_path = $ExternalReportPath
  generated_at = (Get-Date -Format s)
}
$result | ConvertTo-Json -Depth 8 | Set-Content -Path $JsonPath -Encoding UTF8

@(
  '# AAYS Portable Task Runner Fixed',
  '',
  "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
  'Status: completed',
  "TaskId: $TaskId",
  "BridgeRoot: $BridgeRoot",
  "ProjectRoot: $ProjectRoot",
  "Message: cost50 inventory audit cleanroot retry completed",
  "PLAN_PROGRESS_PERCENT=$readiness"
) | Set-Content -Path $HeartbeatPath -Encoding UTF8

Step ('REPORT_PATH=' + $ReportPath)
Step ('JSON_RESULT_PATH=' + $JsonPath)
Step ('EXTERNAL_REPORT_PATH=' + $ExternalReportPath)
Step ('PLAN_PROGRESS_PERCENT=' + $readiness)
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
