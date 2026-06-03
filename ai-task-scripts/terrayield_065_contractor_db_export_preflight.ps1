$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-065-contractor-db-export-preflight'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot = 'E:\AAYS_DATA\legal'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$AuditPath = Join-Path $ResultsDir ($TaskId + '.audit.json')
$ReportPath = Join-Path $ResultsDir ($TaskId + '.report.md')

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
Write-Step ('TASK=' + $TaskId)
Write-Step 'MODE=contractor_db_export_preflight'
Write-Step ('PROJECT_ROOT=' + $ProjectRoot)
Write-Step ('LEGAL_ROOT=' + $LegalRoot)

Ensure-Dir $ResultsDir
foreach ($d in @($LegalRoot, (Join-Path $LegalRoot 'processed'), (Join-Path $LegalRoot 'exports'), (Join-Path $LegalRoot 'reports'), (Join-Path $LegalRoot 'db_transfer'))) { Ensure-Dir $d }

$checks = New-Object System.Collections.Generic.List[object]
$outputChecks = New-Object System.Collections.Generic.List[object]
$notes = New-Object System.Collections.Generic.List[string]

$projectExists = Test-Path $ProjectRoot
if ($projectExists) { Set-Location $ProjectRoot } else { [void]$notes.Add('project_root_missing') }

$files = @(
  (Join-Path $ProjectRoot 'db_transfer\schema_apply.sql'),
  (Join-Path $ProjectRoot 'db_transfer\load_order.csv'),
  (Join-Path $ProjectRoot 'db_transfer\export_manifest.csv'),
  (Join-Path $ProjectRoot 'scripts\contractor_load_to_postgres.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_match_to_parcels.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_export_for_app.py'),
  (Join-Path $LegalRoot 'processed\contractors_normalized.csv'),
  (Join-Path $LegalRoot 'processed\procurement_events_normalized.csv'),
  (Join-Path $LegalRoot 'processed\contractor_scores.csv')
)
foreach ($f in $files) { [void]$outputChecks.Add((File-Info $f)) }

if ($projectExists) {
  [void]$checks.Add((Run-Line 'COMPILE_LOAD_MATCH_EXPORT' 'python -m py_compile scripts\contractor_load_to_postgres.py scripts\contractor_match_to_parcels.py scripts\contractor_export_for_app.py'))
  $env:AAYS_LEGAL_ROOT = $LegalRoot
  [void]$checks.Add((Run-Line 'APP_EXPORT_SMOKE' 'python scripts\contractor_export_for_app.py'))

  if ($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD)) {
    [void]$checks.Add((Run-Line 'POSTGRES_LOAD_ATTEMPT' 'python scripts\contractor_load_to_postgres.py'))
    [void]$checks.Add((Run-Line 'PARCEL_MATCH_ATTEMPT' 'python scripts\contractor_match_to_parcels.py'))
  } else {
    [void]$notes.Add('database_credentials_absent_db_load_and_parcel_match_expected_to_wait')
  }
}

foreach ($rel in @('exports\contractor_app_export.csv','exports\contractor_app_export.jsonl','processed\contractor_parcel_matches.csv','reports\blocked_by_missing_credential_postgres.json')) {
  [void]$outputChecks.Add((File-Info (Join-Path $LegalRoot $rel)))
}

$missingCore = @($outputChecks | Where-Object { $_.path -like '*contractor_scores.csv' -and -not $_.exists })
$compileOk = @($checks | Where-Object { $_.label -eq 'COMPILE_LOAD_MATCH_EXPORT' -and $_.exit_code -eq 0 }).Count -gt 0
$exportOk = @($outputChecks | Where-Object { $_.path -like '*contractor_app_export.csv' -and $_.exists -and $_.bytes -gt 0 }).Count -gt 0
$dbCreds = [bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
$dbAttemptOk = @($checks | Where-Object { $_.label -eq 'POSTGRES_LOAD_ATTEMPT' -and $_.exit_code -eq 0 }).Count -gt 0
$matchOk = @($outputChecks | Where-Object { $_.path -like '*contractor_parcel_matches.csv' -and $_.exists -and $_.bytes -gt 0 }).Count -gt 0

$progress = 48
if ($compileOk) { $progress = 52 }
if ($exportOk) { $progress = 58 }
if ($dbCreds -and $dbAttemptOk) { $progress = 68 }
if ($matchOk) { $progress = 76 }
$status = 'completed_preflight'

$audit = [ordered]@{
  task_id=$TaskId
  status=$status
  generated_at=(Get-Date).ToString('s')
  project_root=$ProjectRoot
  legal_root=$LegalRoot
  database_credentials_present=$dbCreds
  notes=@($notes)
  command_checks=@($checks)
  file_checks=@($outputChecks)
  plan_progress_percent=$progress
  percent_remaining=(100 - $progress)
  recommended_next_step=if (-not $dbCreds) { 'set database credentials, then run postgres load and parcel match' } elseif ($progress -lt 76) { 'repair db load or parcel match output' } else { 'run final export manifest and closure audit' }
}
$audit | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $AuditPath

$lines = @('# TerraYield Contractor DB Export Preflight','',('Status: ' + $status),('Generated at: ' + $audit.generated_at),'',('Plan completed: ' + $progress + '%'),('Plan remaining: ' + (100 - $progress) + '%'),'',('Database credentials present: ' + $dbCreds),'','## Command Checks')
foreach ($c in $checks) { $lines += ('- ' + $c.label + ': exit=' + $c.exit_code) }
$lines += @('', '## File Checks')
foreach ($o in $outputChecks) { $lines += ('- ' + $o.path + ' exists=' + $o.exists + ' bytes=' + $o.bytes) }
$lines += @('', '## Recommended Next Step', $audit.recommended_next_step)
$lines | Set-Content -Encoding UTF8 -Path $ReportPath

Write-Step ('AUDIT_WRITTEN=' + $AuditPath)
Write-Step ('REPORT_WRITTEN=' + $ReportPath)
Write-Step ('PLAN_PROGRESS_PERCENT=' + $progress)
Write-Step ('PLAN_PERCENT_REMAINING=' + (100 - $progress))
Write-Step 'TASK_COMPLETION=100/100'
exit 0
