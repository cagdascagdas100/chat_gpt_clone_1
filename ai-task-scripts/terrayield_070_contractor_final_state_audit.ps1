$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-070-contractor-final-state-audit'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot = 'E:\AAYS_DATA\legal'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$HandoffDir = Join-Path $BridgeRoot 'ai-handoff'
$ReportPath = Join-Path $HandoffDir 'aays1-contractor-final-status.md'
$JsonPath = Join-Path $HandoffDir 'aays1-contractor-final-status.json'

function Write-Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function Ensure-Dir([string]$Path) { if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function FileInfo([string]$Path) {
  if (Test-Path $Path) {
    $i = Get-Item $Path
    return [ordered]@{ path=$Path; exists=$true; bytes=$i.Length; modified=$i.LastWriteTime.ToString('s') }
  }
  return [ordered]@{ path=$Path; exists=$false; bytes=0; modified=$null }
}
function CountRows([string]$Path) {
  try {
    if (Test-Path $Path) {
      $lineCount = 0
      $reader = [System.IO.File]::OpenText($Path)
      try { while ($null -ne $reader.ReadLine()) { $lineCount++ } } finally { $reader.Close() }
      if ($lineCount -gt 0) { return ($lineCount - 1) }
    }
  } catch {}
  return 0
}

Write-Step 'PROJECT=terrayield'
Write-Step ('TASK=' + $TaskId)
Write-Step 'MODE=contractor_final_state_audit'
Write-Step ('BRIDGE_ROOT=' + $BridgeRoot)
Write-Step ('PROJECT_ROOT=' + $ProjectRoot)
Write-Step ('LEGAL_ROOT=' + $LegalRoot)

Ensure-Dir $ResultsDir
Ensure-Dir $HandoffDir
Ensure-Dir $LegalRoot

$dbCreds = [bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
$corePaths = @(
  (Join-Path $ProjectRoot 'scripts\contractor_collect_companies_house.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_collect_procurement_ocds.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_normalize_and_score.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_load_to_postgres.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_match_to_parcels.py'),
  (Join-Path $ProjectRoot 'scripts\contractor_export_for_app.py'),
  (Join-Path $ProjectRoot 'scripts\requirements_contractor.txt'),
  (Join-Path $ProjectRoot 'scripts\README_CONTRACTOR_PIPELINE.md'),
  (Join-Path $ProjectRoot 'db_transfer\schema_apply.sql'),
  (Join-Path $ProjectRoot 'db_transfer\load_order.csv'),
  (Join-Path $ProjectRoot 'db_transfer\export_manifest.csv'),
  (Join-Path $ProjectRoot 'db_transfer\runbook_windows_linux.txt'),
  (Join-Path $LegalRoot 'raw\companies_house\company_profiles.jsonl'),
  (Join-Path $LegalRoot 'raw\procurement\contracts_finder_ocds.jsonl'),
  (Join-Path $LegalRoot 'raw\procurement\find_tender_ocds.jsonl'),
  (Join-Path $LegalRoot 'processed\contractors_normalized.csv'),
  (Join-Path $LegalRoot 'processed\procurement_events_normalized.csv'),
  (Join-Path $LegalRoot 'processed\contractor_scores.csv'),
  (Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv'),
  (Join-Path $LegalRoot 'exports\contractor_app_export.csv'),
  (Join-Path $LegalRoot 'exports\contractor_app_export.jsonl')
)
$fileInfo = @()
foreach ($p in $corePaths) { $fileInfo += (FileInfo $p) }

$scriptFiles = @($fileInfo | Where-Object { $_.path -like '*\scripts\contractor_*' -and $_.exists })
$dbTransferFiles = @($fileInfo | Where-Object { $_.path -like '*\db_transfer\*' -and $_.exists })
$rawProcFiles = @($fileInfo | Where-Object { ($_.path -like '*contracts_finder_ocds.jsonl' -or $_.path -like '*find_tender_ocds.jsonl') -and $_.exists -and $_.bytes -gt 0 })
$chRaw = @($fileInfo | Where-Object { $_.path -like '*company_profiles.jsonl' -and $_.exists -and $_.bytes -gt 0 })
$scoreRows = CountRows (Join-Path $LegalRoot 'processed\contractor_scores.csv')
$appRows = CountRows (Join-Path $LegalRoot 'exports\contractor_app_export.csv')
$matchRows = CountRows (Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv')

$compileExit = $null
$compilePreview = ''
if (Test-Path $ProjectRoot) {
  try {
    Push-Location $ProjectRoot
    $compileOutput = python -m py_compile scripts\contractor_collect_companies_house.py scripts\contractor_collect_procurement_ocds.py scripts\contractor_normalize_and_score.py scripts\contractor_load_to_postgres.py scripts\contractor_match_to_parcels.py scripts\contractor_export_for_app.py 2>&1
    $compileExit = $LASTEXITCODE
    $compilePreview = ($compileOutput | Out-String)
    Pop-Location
  } catch { try { Pop-Location } catch {}; $compileExit = 999; $compilePreview = $_.Exception.Message }
}

$progress = 25
if ($scriptFiles.Count -ge 6) { $progress = 32 }
if ($compileExit -eq 0) { $progress = 38 }
if ($rawProcFiles.Count -ge 1) { $progress = 48 }
if ($scoreRows -gt 0) { $progress = 58 }
if ($appRows -gt 0) { $progress = 64 }
if ($dbTransferFiles.Count -ge 4) { $progress = [Math]::Max($progress, 68) }
if ($dbCreds) { $progress = [Math]::Max($progress, 70) }
if ($matchRows -gt 0) { $progress = [Math]::Max($progress, 78) }

$next = if (-not $dbCreds) { 'DB credentials are not visible to this runner. Set DATABASE_URL or PGHOST/PGDATABASE/PGUSER/PGPASSWORD, then run DB load and parcel match.' } elseif ($matchRows -lt 1) { 'DB credentials are present; run DB load, parcel match, and final app export.' } else { 'Run final closure package verification and app handoff.' }

$status = [ordered]@{
  task_id=$TaskId
  status='completed'
  generated_at=(Get-Date).ToString('s')
  bridge_root=$BridgeRoot
  project_root=$ProjectRoot
  legal_root=$LegalRoot
  database_credentials_present=$dbCreds
  script_files_present=$scriptFiles.Count
  db_transfer_files_present=$dbTransferFiles.Count
  procurement_raw_files_present=$rawProcFiles.Count
  companies_house_raw_present=($chRaw.Count -gt 0)
  compile_exit_code=$compileExit
  contractor_score_rows=$scoreRows
  app_export_rows=$appRows
  parcel_match_rows=$matchRows
  plan_progress_percent=$progress
  plan_percent_remaining=(100 - $progress)
  next_action=$next
  file_checks=$fileInfo
}
$status | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $JsonPath

$lines = @(
  '# AAYS1 TerraYield Contractor Final State',
  '',
  ('Generated at: ' + $status.generated_at),
  ('Status: ' + $status.status),
  ('Plan completed: ' + $progress + '%'),
  ('Plan remaining: ' + (100 - $progress) + '%'),
  '',
  '## Key Counters',
  ('- Script files present: ' + $scriptFiles.Count),
  ('- DB transfer files present: ' + $dbTransferFiles.Count),
  ('- Procurement raw files present: ' + $rawProcFiles.Count),
  ('- Companies House raw present: ' + ($chRaw.Count -gt 0)),
  ('- Compile exit code: ' + $compileExit),
  ('- Contractor score rows: ' + $scoreRows),
  ('- App export rows: ' + $appRows),
  ('- Parcel match rows: ' + $matchRows),
  ('- DB credentials present: ' + $dbCreds),
  '',
  '## Next Action',
  $next,
  '',
  '## File Checks'
)
foreach ($f in $fileInfo) { $lines += ('- ' + $f.path + ' exists=' + $f.exists + ' bytes=' + $f.bytes) }
$lines | Set-Content -Encoding UTF8 -Path $ReportPath

Write-Step ('HANDOFF_REPORT_WRITTEN=' + $ReportPath)
Write-Step ('HANDOFF_JSON_WRITTEN=' + $JsonPath)
Write-Step ('PLAN_PROGRESS_PERCENT=' + $progress)
Write-Step ('PLAN_PERCENT_REMAINING=' + (100 - $progress))
Write-Step ('NEXT_ACTION=' + $next)

try {
  Push-Location $BridgeRoot
  git add ai-handoff ai-results 2>&1 | Out-String | Write-Output
  git commit -m ('chore(ai): contractor final state audit ' + $TaskId) 2>&1 | Out-String | Write-Output
  git push origin main 2>&1 | Out-String | Write-Output
  Pop-Location
} catch { try { Pop-Location } catch {}; Write-Step ('GIT_PUSH_WARNING=' + $_.Exception.Message) }
exit 0
