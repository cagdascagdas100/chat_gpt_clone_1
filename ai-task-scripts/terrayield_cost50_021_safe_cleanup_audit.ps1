$ErrorActionPreference = 'Continue'
$TaskId = 'cost50-021-safe-cleanup-audit-20260512'
$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$CostRoot = 'E:\AAYS_DATA\cost'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$QualityDir = Join-Path $CostRoot 'quality_reports'
New-Item -ItemType Directory -Force -Path $ResultDir,$QualityDir | Out-Null
function DirStats($Label, $Path) {
  if (!(Test-Path $Path)) {
    return [pscustomobject]@{ label=$Label; path=$Path; exists=$false; files=0; bytes=0; mb=0; candidates=0 }
  }
  $items = Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue
  $bytes = ($items | Measure-Object -Property Length -Sum).Sum
  if ($null -eq $bytes) { $bytes = 0 }
  $old = $items | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-2) }
  return [pscustomobject]@{ label=$Label; path=$Path; exists=$true; files=@($items).Count; bytes=[int64]$bytes; mb=[math]::Round(($bytes/1MB),2); candidates=@($old).Count }
}
Write-Output "[$(Get-Date -Format s)] TASK=$TaskId"
Write-Output "[$(Get-Date -Format s)] MODE=safe_cleanup_audit_no_delete"
Write-Output "[$(Get-Date -Format s)] BridgeRoot=$BridgeRoot"
Write-Output "[$(Get-Date -Format s)] ProjectRoot=$ProjectRoot"
$targets = @(
  @{label='bridge_ai_results'; path=(Join-Path $BridgeRoot 'ai-results')},
  @{label='bridge_runner_logs'; path=(Join-Path $BridgeRoot 'ai-runner-logs')},
  @{label='bridge_ai_tmp'; path=(Join-Path $BridgeRoot 'ai-tmp')},
  @{label='bridge_heartbeat'; path=(Join-Path $BridgeRoot 'ai-heartbeat')},
  @{label='project_tmp'; path=(Join-Path $ProjectRoot 'tmp')},
  @{label='project_test_tmp'; path=(Join-Path $ProjectRoot '.test_tmp')},
  @{label='project_pytest_tmp'; path=(Join-Path $ProjectRoot '.pytest_tmp')},
  @{label='cost_quality_reports'; path=$QualityDir}
)
$stats = foreach ($t in $targets) { DirStats $t.label $t.path }
$large = $stats | Sort-Object bytes -Descending | Select-Object -First 8
$totalBytes = ($stats | Measure-Object -Property bytes -Sum).Sum
if ($null -eq $totalBytes) { $totalBytes = 0 }
$oldCandidates = ($stats | Measure-Object -Property candidates -Sum).Sum
if ($null -eq $oldCandidates) { $oldCandidates = 0 }
$report = @()
$report += '# Cost50 Step 021 Safe Cleanup Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Policy'
$report += '- No files deleted.'
$report += '- No DB files touched.'
$report += '- No source manifests touched.'
$report += '- This is inventory only, intended to reduce future UI/page freezes by identifying archive candidates.'
$report += ''
$report += '## Summary'
$report += "- total scanned MB: $([math]::Round(($totalBytes/1MB),2))"
$report += "- old candidate files (>2 days): $oldCandidates"
$report += ''
$report += '## Directory stats'
foreach ($s in $stats) { $report += "- $($s.label): exists=$($s.exists), files=$($s.files), MB=$($s.mb), old_candidates=$($s.candidates), path=$($s.path)" }
$report += ''
$report += '## Largest areas'
foreach ($s in $large) { $report += "- $($s.label): MB=$($s.mb), files=$($s.files)" }
$report += ''
$report += '## Recommended next safe cleanup'
$report += '- Archive old ai-results markdown files older than 2 days, keeping latest 30 result files.'
$report += '- Archive old ai-runner-logs older than 2 days, keeping current runner log.'
$report += '- Clear ai-tmp only after runner is idle.'
$report += '- Do not delete quality_reports, manifests, DB files, source CSV/JSON outputs, or handoff zips.'
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=100'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$reportPath = Join-Path $ResultDir "$TaskId.report.md"
$externalReportPath = Join-Path $QualityDir "$TaskId.report.md"
$reportText = $report -join "`r`n"
[IO.File]::WriteAllText($reportPath, $reportText, [Text.UTF8Encoding]::new($true))
[IO.File]::WriteAllText($externalReportPath, $reportText, [Text.UTF8Encoding]::new($true))
Write-Output "[$(Get-Date -Format s)] REPORT_PATH=$reportPath"
Write-Output "[$(Get-Date -Format s)] EXTERNAL_REPORT_PATH=$externalReportPath"
Write-Output "[$(Get-Date -Format s)] TOTAL_SCANNED_MB=$([math]::Round(($totalBytes/1MB),2))"
Write-Output "[$(Get-Date -Format s)] OLD_CANDIDATE_FILES=$oldCandidates"
Write-Output "[$(Get-Date -Format s)] PLAN_PROGRESS_PERCENT=100"
Write-Output "[$(Get-Date -Format s)] TASK_COMPLETION=100/100"
Write-Output "[$(Get-Date -Format s)] TERRAYIELD_TASK_DONE"
