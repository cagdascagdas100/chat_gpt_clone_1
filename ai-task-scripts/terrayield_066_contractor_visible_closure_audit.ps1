$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-066-contractor-visible-closure-audit'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot = 'E:\AAYS_DATA\legal'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$ReportPath = Join-Path $ResultsDir ($TaskId + '.report.md')
$AuditPath = Join-Path $ResultsDir ($TaskId + '.audit.json')
function Write-Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Ensure-Dir([string]$Path) { if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function FileInfo([string]$Path) { if (Test-Path $Path) { $i = Get-Item $Path; return [ordered]@{path=$Path;exists=$true;bytes=$i.Length;modified=$i.LastWriteTime.ToString('s')} } return [ordered]@{path=$Path;exists=$false;bytes=0;modified=$null} }
function CsvCount([string]$Path) { try { if (Test-Path $Path) { $lines = [System.IO.File]::ReadAllLines($Path); if ($lines.Length -gt 0) { return [Math]::Max(0,$lines.Length-1) } } } catch {} return 0 }
function RunLine([string]$Label,[string]$CommandLine) { Write-Step ($Label + '_BEGIN'); Write-Step ('COMMAND=' + $CommandLine); $out = cmd.exe /c $CommandLine 2>&1; $code=$LASTEXITCODE; $text=($out|Out-String); Write-Output $text; Write-Step ($Label + '_EXIT=' + $code); return [ordered]@{label=$Label;command=$CommandLine;exit_code=$code;output_preview=($text.Substring(0,[Math]::Min(4000,$text.Length)))} }

Write-Step 'PROJECT=terrayield'
Write-Step ('TASK=' + $TaskId)
Write-Step 'MODE=visible_closure_audit'
Write-Step ('PROJECT_ROOT=' + $ProjectRoot)
Write-Step ('LEGAL_ROOT=' + $LegalRoot)
Ensure-Dir $ResultsDir
foreach ($d in @($LegalRoot,(Join-Path $LegalRoot 'raw'),(Join-Path $LegalRoot 'processed'),(Join-Path $LegalRoot 'exports'),(Join-Path $LegalRoot 'reports'),(Join-Path $LegalRoot 'db_transfer'))) { Ensure-Dir $d }

$checks = New-Object System.Collections.Generic.List[object]
$files = New-Object System.Collections.Generic.List[object]
$notes = New-Object System.Collections.Generic.List[string]
$dbCreds = [bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))

if (Test-Path $ProjectRoot) { Set-Location $ProjectRoot; [void]$checks.Add((RunLine 'GIT_STATUS_PROJECT' 'git status --short --untracked-files=all')) } else { [void]$notes.Add('project_root_missing') }

$paths = @(
  (Join-Path $ProjectRoot 'scripts\contractor_collect_companies_house.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_collect_procurement_ocds.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_normalize_and_score.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_load_to_postgres.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_match_to_parcels.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_export_for_app.py'),
  (Join-Path $ProjectRoot 'scripts\requirements_contractor.txt'),
  (Join-Path $ProjectRoot 'db_transfer\schema_apply.sql'),
  (Join-Path $ProjectRoot 'db_transfer\load_order.csv'),
  (Join-Path $ProjectRoot 'db_transfer\export_manifest.csv'),
  (Join-Path $ProjectRoot 'db_transfer\runbook_windows_linux.txt'),
  (Join-Path $LegalRoot 'raw\procurement\contracts_finder_ocds.jsonl'),
  (Join-Path $LegalRoot 'raw\procurement\find_tender_ocds.jsonl'),
  (Join-Path $LegalRoot 'raw\companies_house\company_profiles.jsonl'),
  (Join-Path $LegalRoot 'processed\contractors_normalized.csv'),
  (Join-Path $LegalRoot 'processed\procurement_events_normalized.csv'),
  (Join-Path $LegalRoot 'processed\contractor_scores.csv'),
  (Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv'),
  (Join-Path $LegalRoot 'exports\contractor_app_export.csv'),
  (Join-Path $LegalRoot 'exports\contractor_app_export.jsonl')
)
foreach ($p in $paths) { [void]$files.Add((FileInfo $p)) }

if (Test-Path $ProjectRoot) {
  [void]$checks.Add((RunLine 'PY_COMPILE_CRITICAL' 'python -m py_compile scripts\contractor_collect_companies_house.py scripts\contractor_collect_procurement_ocds.py scripts\contractor_normalize_and_score.py scripts\contractor_load_to_postgres.py scripts\contractor_match_to_parcels.py scripts\contractor_export_for_app.py'))
}

$scorePath = Join-Path $LegalRoot 'processed\contractor_scores.csv'
$appCsv = Join-Path $LegalRoot 'exports\contractor_app_export.csv'
$matchCsv = Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv'
$scoreRows = CsvCount $scorePath
$appRows = CsvCount $appCsv
$matchRows = CsvCount $matchCsv
$scriptCount = @($files | Where-Object { $_.path -like '*\scripts\contractor_*' -and $_.exists }).Count
$dbTransferCount = @($files | Where-Object { $_.path -like '*\db_transfer\*' -and $_.exists }).Count
$compileOk = @($checks | Where-Object { $_.label -eq 'PY_COMPILE_CRITICAL' -and $_.exit_code -eq 0 }).Count -gt 0
$rawProcurementOk = @($files | Where-Object { ($_.path -like '*contracts_finder_ocds.jsonl' -or $_.path -like '*find_tender_ocds.jsonl') -and $_.exists -and $_.bytes -gt 0 }).Count -gt 0
$appOk = (Test-Path $appCsv) -and ((Get-Item $appCsv).Length -gt 0)
$matchesOk = (Test-Path $matchCsv) -and ((Get-Item $matchCsv).Length -gt 0)

$progress = 25
if ($scriptCount -ge 6) { $progress = 32 }
if ($compileOk) { $progress = 38 }
if ($rawProcurementOk) { $progress = 48 }
if ($scoreRows -gt 0) { $progress = 58 }
if ($appOk -and $appRows -gt 0) { $progress = 64 }
if ($dbTransferCount -ge 4) { $progress = [Math]::Max($progress,68) }
if ($dbCreds) { $progress = [Math]::Max($progress,70) } else { [void]$notes.Add('database_credentials_absent_db_load_and_parcel_match_not_proven') }
if ($matchesOk -and $matchRows -gt 0) { $progress = 78 }

$status = 'completed_visible_audit'
$audit = [ordered]@{
  task_id=$TaskId
  status=$status
  generated_at=(Get-Date).ToString('s')
  project_root=$ProjectRoot
  legal_root=$LegalRoot
  database_credentials_present=$dbCreds
  script_count=$scriptCount
  db_transfer_count=$dbTransferCount
  contractor_score_rows=$scoreRows
  app_export_rows=$appRows
  parcel_match_rows=$matchRows
  notes=@($notes)
  checks=@($checks)
  files=@($files)
  plan_progress_percent=$progress
  percent_remaining=(100-$progress)
  recommended_next_step=if (-not $dbCreds) { 'Provide DB credentials in the running environment, then queue DB load and parcel match.' } elseif (-not $matchesOk) { 'Run DB load and parcel match repair.' } else { 'Run final manifest closure and app handoff.' }
}
$audit | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $AuditPath
$lines = @('# TerraYield Contractor Visible Closure Audit','',('Status: ' + $status),('Generated at: ' + $audit.generated_at),('Plan completed: ' + $progress + '%'),('Plan remaining: ' + (100-$progress) + '%'),('Database credentials present: ' + $dbCreds),('Contractor score rows: ' + $scoreRows),('App export rows: ' + $appRows),('Parcel match rows: ' + $matchRows),'','## Notes')
foreach ($n in $notes) { $lines += ('- ' + $n) }
$lines += @('','## Checks')
foreach ($c in $checks) { $lines += ('- ' + $c.label + ': exit=' + $c.exit_code) }
$lines += @('','## Files')
foreach ($f in $files) { $lines += ('- ' + $f.path + ' exists=' + $f.exists + ' bytes=' + $f.bytes) }
$lines += @('','## Recommended Next Step',$audit.recommended_next_step)
$lines | Set-Content -Encoding UTF8 -Path $ReportPath

Write-Step ('AUDIT_WRITTEN=' + $AuditPath)
Write-Step ('REPORT_WRITTEN=' + $ReportPath)
Write-Step ('PLAN_PROGRESS_PERCENT=' + $progress)
Write-Step ('PLAN_PERCENT_REMAINING=' + (100-$progress))
Write-Step 'TASK_COMPLETION=100/100'

try {
  Set-Location $BridgeRoot
  git add ai-results 2>&1 | Out-String | Write-Output
  git commit -m ('chore(ai): visible audit ' + $TaskId) 2>&1 | Out-String | Write-Output
  git push origin main 2>&1 | Out-String | Write-Output
} catch { Write-Step ('GIT_PUSH_VISIBLE_AUDIT_WARNING=' + $_.Exception.Message) }
exit 0
