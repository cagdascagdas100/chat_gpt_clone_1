$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-063-contractor-smoke-diagnostic'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot = 'E:\AAYS_DATA\legal'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$ReportPath = Join-Path $ResultsDir ($TaskId + '.report.md')
$AuditPath = Join-Path $ResultsDir ($TaskId + '.audit.json')

function Write-Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Ensure-Dir([string]$Path) { if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Run-Line([string]$Label, [string]$CommandLine) {
  Write-Step ($Label + '_BEGIN')
  Write-Step ('COMMAND=' + $CommandLine)
  $out = cmd.exe /c $CommandLine 2>&1
  $code = $LASTEXITCODE
  $text = ($out | Out-String)
  Write-Output $text
  Write-Step ($Label + '_EXIT=' + $code)
  return [ordered]@{ label=$Label; command=$CommandLine; exit_code=$code; output=$text }
}
function File-Info([string]$Path) {
  if (Test-Path $Path) {
    $item = Get-Item $Path
    return [ordered]@{ path=$Path; exists=$true; bytes=$item.Length; modified=$item.LastWriteTime.ToString('s') }
  }
  return [ordered]@{ path=$Path; exists=$false; bytes=0; modified=$null }
}

Write-Step 'PROJECT=terrayield'
Write-Step 'TASK=terrayield-063-contractor-smoke-diagnostic'
Write-Step 'MODE=contractor_smoke_diagnostic_non_blocking'
Write-Step ('PROJECT_ROOT=' + $ProjectRoot)
Write-Step ('LEGAL_ROOT=' + $LegalRoot)

Ensure-Dir $ResultsDir
Ensure-Dir $LegalRoot
foreach ($d in @('raw','processed','reports','exports','db_transfer','raw\procurement','raw\companies_house')) { Ensure-Dir (Join-Path $LegalRoot $d) }

$checks = New-Object System.Collections.Generic.List[object]
$scriptChecks = New-Object System.Collections.Generic.List[object]
$outputChecks = New-Object System.Collections.Generic.List[object]
$notes = New-Object System.Collections.Generic.List[string]

$projectExists = Test-Path $ProjectRoot
if ($projectExists) { Set-Location $ProjectRoot } else { [void]$notes.Add('project_root_missing') }

$required = @(
  'scripts\contractor_collect_companies_house.py',
  'scripts\contractor_collect_procurement_ocds.py',
  'scripts\contractor_normalize_and_score.py',
  'scripts\contractor_load_to_postgres.py',
  'scripts\contractor_match_to_parcels.py',
  'scripts\contractor_export_for_app.py',
  'scripts\requirements_contractor.txt',
  'scripts\README_CONTRACTOR_PIPELINE.md'
)
foreach ($rel in $required) {
  $full = Join-Path $ProjectRoot $rel
  [void]$scriptChecks.Add((File-Info $full))
}

if ($projectExists) {
  [void]$checks.Add((Run-Line 'PYTHON_VERSION' 'python --version'))
  [void]$checks.Add((Run-Line 'SCRIPT_COMPILE_ALL' 'python -m py_compile scripts\contractor_collect_companies_house.py scripts\contractor_collect_procurement_ocds.py scripts\contractor_normalize_and_score.py scripts\contractor_load_to_postgres.py scripts\contractor_match_to_parcels.py scripts\contractor_export_for_app.py'))

  $procHelp = Run-Line 'PROCUREMENT_HELP' 'python scripts\contractor_collect_procurement_ocds.py --help'
  [void]$checks.Add($procHelp)
  $normHelp = Run-Line 'NORMALIZE_HELP' 'python scripts\contractor_normalize_and_score.py --help'
  [void]$checks.Add($normHelp)
  $exportHelp = Run-Line 'EXPORT_HELP' 'python scripts\contractor_export_for_app.py --help'
  [void]$checks.Add($exportHelp)

  $env:AAYS_LEGAL_ROOT = $LegalRoot
  $smoke = Run-Line 'PROCUREMENT_DEMO_SMOKE' 'python scripts\contractor_collect_procurement_ocds.py --demo-limit 10'
  [void]$checks.Add($smoke)
  $norm = Run-Line 'NORMALIZE_SCORE_SMOKE' 'python scripts\contractor_normalize_and_score.py'
  [void]$checks.Add($norm)
}

$expectedOutputs = @(
  'raw\procurement\contracts_finder_ocds.jsonl',
  'raw\procurement\find_tender_ocds.jsonl',
  'processed\contractors_normalized.csv',
  'processed\procurement_events_normalized.csv',
  'processed\contractor_scores.csv',
  'exports\contractor_app_export.csv',
  'exports\contractor_app_export.jsonl'
)
foreach ($rel in $expectedOutputs) {
  [void]$outputChecks.Add((File-Info (Join-Path $LegalRoot $rel)))
}

$missingScripts = @($scriptChecks | Where-Object { -not $_.exists })
$compile = @($checks | Where-Object { $_.label -eq 'SCRIPT_COMPILE_ALL' } | Select-Object -First 1)
$procSmoke = @($checks | Where-Object { $_.label -eq 'PROCUREMENT_DEMO_SMOKE' } | Select-Object -First 1)
$normSmoke = @($checks | Where-Object { $_.label -eq 'NORMALIZE_SCORE_SMOKE' } | Select-Object -First 1)
$progress = 25
if ($missingScripts.Count -eq 0) { $progress = 32 }
if ($compile -and $compile.exit_code -eq 0) { $progress = 36 }
if ($procSmoke -and $procSmoke.exit_code -eq 0) { $progress = 42 }
if ($normSmoke -and $normSmoke.exit_code -eq 0) { $progress = 48 }

$status = 'completed_diagnostic'
$audit = [ordered]@{
  task_id=$TaskId
  status=$status
  generated_at=(Get-Date).ToString('s')
  project_root=$ProjectRoot
  legal_root=$LegalRoot
  notes=@($notes)
  script_checks=@($scriptChecks)
  command_checks=@($checks)
  output_checks=@($outputChecks)
  plan_progress_percent=$progress
  percent_remaining=(100 - $progress)
  recommended_next_step=if ($progress -ge 48) { 'queue app export and database transfer smoke' } elseif ($progress -ge 36) { 'repair procurement or normalize runtime arguments' } else { 'restore or reinstall contractor pipeline files' }
}
$audit | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $AuditPath

$lines = @('# TerraYield Contractor Smoke Diagnostic','',('Status: ' + $status),('Generated at: ' + $audit.generated_at),'',('Plan completed: ' + $progress + '%'),('Plan remaining: ' + (100 - $progress) + '%'),'', '## Script Files')
foreach ($s in $scriptChecks) { $lines += ('- ' + $s.path + ' exists=' + $s.exists + ' bytes=' + $s.bytes) }
$lines += @('', '## Command Checks')
foreach ($c in $checks) { $lines += ('- ' + $c.label + ': exit=' + $c.exit_code) }
$lines += @('', '## Output Files')
foreach ($o in $outputChecks) { $lines += ('- ' + $o.path + ' exists=' + $o.exists + ' bytes=' + $o.bytes) }
$lines += @('', '## Recommended Next Step', $audit.recommended_next_step)
$lines | Set-Content -Encoding UTF8 -Path $ReportPath

Write-Step ('AUDIT_WRITTEN=' + $AuditPath)
Write-Step ('REPORT_WRITTEN=' + $ReportPath)
Write-Step ('PLAN_PROGRESS_PERCENT=' + $progress)
Write-Step ('PLAN_PERCENT_REMAINING=' + (100 - $progress))
Write-Step 'TASK_COMPLETION=diagnostic_completed'
exit 0
