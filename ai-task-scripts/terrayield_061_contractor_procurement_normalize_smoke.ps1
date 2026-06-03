$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-061-contractor-procurement-normalize-smoke'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot = 'E:\AAYS_DATA\legal'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$ReportPath = Join-Path $ResultsDir ($TaskId + '.report.md')
$AuditPath = Join-Path $ResultsDir ($TaskId + '.audit.json')

function Write-Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Ensure-Dir([string]$Path) { if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Invoke-CmdLine([string]$Label, [string]$CommandLine) {
  Write-Step ($Label + '_BEGIN')
  Write-Step ('COMMAND=' + $CommandLine)
  $out = cmd.exe /c $CommandLine 2>&1
  $code = $LASTEXITCODE
  $text = ($out | Out-String)
  Write-Output $text
  Write-Step ($Label + '_EXIT=' + $code)
  return [ordered]@{ label=$Label; command=$CommandLine; exit_code=$code; output=$text }
}

Write-Step 'PROJECT=terrayield'
Write-Step 'DISPLAY_PROJECT=TerraYield'
Write-Step 'CHATGPT_PAGE_PROJECT=aays1'
Write-Step ('TASK=' + $TaskId)
Write-Step 'MODE=contractor_procurement_normalize_smoke'
Write-Step ('PROJECT_ROOT=' + $ProjectRoot)
Write-Step ('LEGAL_ROOT=' + $LegalRoot)

Ensure-Dir $ResultsDir
Ensure-Dir $LegalRoot
foreach ($d in @('raw','processed','reports','exports','db_transfer','raw\procurement','raw\companies_house')) { Ensure-Dir (Join-Path $LegalRoot $d) }

$checks = New-Object System.Collections.Generic.List[object]
$errors = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path $ProjectRoot)) {
  [void]$errors.Add('project_root_missing')
} else {
  Set-Location $ProjectRoot
}

$required = @(
  'scripts\contractor_collect_companies_house.py',
  'scripts\contractor_collect_procurement_ocds.py',
  'scripts\contractor_normalize_and_score.py',
  'scripts\contractor_load_to_postgres.py',
  'scripts\contractor_match_to_parcels.py',
  'scripts\contractor_export_for_app.py',
  'scripts\requirements_contractor.txt'
)
$missing = @()
foreach ($rel in $required) {
  if (Test-Path (Join-Path $ProjectRoot $rel)) { Write-Step ('FOUND=' + $rel) } else { Write-Step ('MISSING=' + $rel); $missing += $rel }
}
if ($missing.Count -gt 0) { foreach ($m in $missing) { [void]$errors.Add('missing_file:' + $m) } }

if ($errors.Count -eq 0) {
  [void]$checks.Add((Invoke-CmdLine 'PY_COMPILE' 'python -m py_compile scripts\contractor_collect_procurement_ocds.py scripts\contractor_normalize_and_score.py scripts\contractor_export_for_app.py'))
}

if ($errors.Count -eq 0) {
  $env:AAYS_LEGAL_ROOT = $LegalRoot
  $cmd1 = 'python scripts\contractor_collect_procurement_ocds.py --demo-limit 10 --storage-root "' + $LegalRoot + '"'
  $r1 = Invoke-CmdLine 'PROCUREMENT_COLLECT_PRIMARY' $cmd1
  [void]$checks.Add($r1)
  if ($r1.exit_code -ne 0) {
    $cmd1b = 'python scripts\contractor_collect_procurement_ocds.py --demo-limit 10'
    $r1b = Invoke-CmdLine 'PROCUREMENT_COLLECT_FALLBACK' $cmd1b
    [void]$checks.Add($r1b)
  }

  $cmd2 = 'python scripts\contractor_normalize_and_score.py --storage-root "' + $LegalRoot + '"'
  $r2 = Invoke-CmdLine 'NORMALIZE_SCORE_PRIMARY' $cmd2
  [void]$checks.Add($r2)
  if ($r2.exit_code -ne 0) {
    $cmd2b = 'python scripts\contractor_normalize_and_score.py'
    $r2b = Invoke-CmdLine 'NORMALIZE_SCORE_FALLBACK' $cmd2b
    [void]$checks.Add($r2b)
  }

  $cmd3 = 'python scripts\contractor_export_for_app.py --storage-root "' + $LegalRoot + '"'
  $r3 = Invoke-CmdLine 'EXPORT_APP_PRIMARY' $cmd3
  [void]$checks.Add($r3)
  if ($r3.exit_code -ne 0) {
    $cmd3b = 'python scripts\contractor_export_for_app.py'
    $r3b = Invoke-CmdLine 'EXPORT_APP_FALLBACK' $cmd3b
    [void]$checks.Add($r3b)
  }
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
$outputStatus = @()
foreach ($rel in $expectedOutputs) {
  $full = Join-Path $LegalRoot $rel
  $exists = Test-Path $full
  $len = if ($exists) { (Get-Item $full).Length } else { 0 }
  Write-Step ('OUTPUT_CHECK=' + $rel + ' exists=' + $exists + ' bytes=' + $len)
  $outputStatus += [ordered]@{ path=$full; exists=$exists; bytes=$len }
}

$hardFailures = @($checks | Where-Object { $_.exit_code -ne 0 -and $_.label -notlike '*PRIMARY' })
$status = if (($errors.Count -eq 0) -and ($hardFailures.Count -eq 0)) { 'completed' } else { 'failed' }
$progress = if ($status -eq 'completed') { 38 } else { 27 }

$audit = [ordered]@{
  task_id=$TaskId
  status=$status
  generated_at=(Get-Date).ToString('s')
  project_root=$ProjectRoot
  legal_root=$LegalRoot
  checks=@($checks)
  errors=@($errors)
  outputs=@($outputStatus)
  policy=[ordered]@{
    official_structured_sources_only=$true
    scraping_allowed=$false
    fake_data_allowed=$false
    missing_evidence_must_remain_null=$true
    provenance_required=$true
  }
  plan_progress_percent=$progress
  percent_remaining=(100 - $progress)
}
$audit | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $AuditPath

$lines = @(
  '# TerraYield Contractor Procurement + Normalize Smoke',
  '',
  ('Status: ' + $status),
  ('Generated at: ' + $audit.generated_at),
  ('Legal root: ' + $LegalRoot),
  '',
  '## Checks',
  ''
)
foreach ($c in $checks) { $lines += ('- ' + $c.label + ': exit=' + $c.exit_code) }
$lines += @('', '## Output Files', '')
foreach ($o in $outputStatus) { $lines += ('- ' + $o.path + ' exists=' + $o.exists + ' bytes=' + $o.bytes) }
$lines += @('', '## Plan Progress', '', ('- Completed: ' + $progress + '%'), ('- Remaining: ' + (100 - $progress) + '%'))
$lines | Set-Content -Encoding UTF8 -Path $ReportPath

Write-Step ('REPORT_WRITTEN=' + $ReportPath)
Write-Step ('AUDIT_WRITTEN=' + $AuditPath)
Write-Step ('PLAN_PROGRESS_PERCENT=' + $progress)
Write-Step ('PLAN_PERCENT_REMAINING=' + (100 - $progress))
if ($status -eq 'completed') { Write-Step 'TASK_COMPLETION=100/100'; exit 0 }
Write-Step 'TASK_COMPLETION=failed'
exit 1
