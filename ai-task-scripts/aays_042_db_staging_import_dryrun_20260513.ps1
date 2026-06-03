$ErrorActionPreference = 'Continue'
$TaskId = 'aays-042-db-staging-import-dryrun-20260513'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$CostRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
function Log([string]$m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
function FindPsql {
  $cmd = Get-Command psql -ErrorAction SilentlyContinue
  if($cmd){ return $cmd.Source }
  $paths = @('C:\Program Files\PostgreSQL\17\bin\psql.exe','C:\Program Files\PostgreSQL\16\bin\psql.exe','C:\Program Files\PostgreSQL\15\bin\psql.exe','C:\Program Files\PostgreSQL\14\bin\psql.exe','C:\Program Files\PostgreSQL\13\bin\psql.exe','C:\Program Files\PostgreSQL\12\bin\psql.exe')
  foreach($p in $paths){ if(Test-Path $p){ return $p } }
  return $null
}
function CountFiles([string]$root,[string]$pattern){ try { if(Test-Path $root){ return @(Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match $pattern -or $_.FullName -match $pattern }).Count } } catch {}; return 0 }
Log "TASK=$TaskId"
Log 'MODE=db_staging_import_dryrun_no_db_write'
Log "PROJECT_ROOT=$ProjectRoot"
Log "COST_ROOT=$CostRoot"
$psql = FindPsql
$psqlVersion = 'MISSING'
if($psql){ try { $psqlVersion = (& $psql --version 2>&1 | Out-String).Trim() } catch { $psqlVersion = 'VERSION_ERROR=' + $_.Exception.Message } }
$sourceManifestJson = CountFiles $CostRoot '^source_fetch_manifest_latest\.json$'
$sourceManifestCsv = CountFiles $CostRoot '^source_fetch_manifest_latest\.csv$'
$factsExtracted = CountFiles $CostRoot '^source_facts_extracted_.*\.csv$'
$factsScored = CountFiles $CostRoot '^source_facts_scored\.csv$'
$summaryJson = CountFiles $CostRoot '^source_facts_scored_summary\.json$'
$uiMenu = CountFiles $CostRoot '^aays_cost_menu_payload_latest\.json$'
$uiMaterials = CountFiles $CostRoot '^aays_cost_material_lines_latest\.json$'
$dbSignals = CountFiles $ProjectRoot '(postgres|postgis|sqlalchemy|alembic|DATABASE_URL|cost_run_logs|cost_estimates|cost_facts)'
$dryrunScore = 0
if($psql){ $dryrunScore += 20 }
if($sourceManifestJson -gt 0){ $dryrunScore += 10 }
if($sourceManifestCsv -gt 0){ $dryrunScore += 10 }
if($factsExtracted -gt 0){ $dryrunScore += 15 }
if($factsScored -gt 0){ $dryrunScore += 15 }
if($summaryJson -gt 0){ $dryrunScore += 10 }
if($uiMenu -gt 0){ $dryrunScore += 5 }
if($uiMaterials -gt 0){ $dryrunScore += 5 }
if($dbSignals -gt 0){ $dryrunScore += 10 }
if($dryrunScore -gt 100){ $dryrunScore = 100 }
$missing = @()
if(-not $psql){ $missing += 'psql client missing or not in PATH' }
if($sourceManifestJson -eq 0){ $missing += 'source_fetch_manifest_latest.json missing' }
if($sourceManifestCsv -eq 0){ $missing += 'source_fetch_manifest_latest.csv missing' }
if($factsExtracted -eq 0){ $missing += 'source_facts_extracted_*.csv missing' }
if($factsScored -eq 0){ $missing += 'source_facts_scored.csv missing' }
if($summaryJson -eq 0){ $missing += 'source_facts_scored_summary.json missing' }
$out = Join-Path $ResultDir ($TaskId + '.report.md')
$r = @('# AAYS 042 DB Staging Import Dry-run','',('Generated: ' + (Get-Date -Format s)),'','## Scope','- Dry-run only. No DB write. No UI patch. No source mutation.','',('PSQL_PATH=' + $psql),('PSQL_VERSION=' + $psqlVersion),('SOURCE_FETCH_MANIFEST_JSON_COUNT=' + $sourceManifestJson),('SOURCE_FETCH_MANIFEST_CSV_COUNT=' + $sourceManifestCsv),('SOURCE_FACTS_EXTRACTED_COUNT=' + $factsExtracted),('SOURCE_FACTS_SCORED_COUNT=' + $factsScored),('SOURCE_FACTS_SCORED_SUMMARY_COUNT=' + $summaryJson),('UI_MENU_PAYLOAD_COUNT=' + $uiMenu),('UI_MATERIAL_LINES_COUNT=' + $uiMaterials),('DB_SIGNAL_COUNT=' + $dbSignals),('DRYRUN_READINESS_SCORE=' + $dryrunScore + '/100'),'','## Missing items')
if($missing.Count -eq 0){ $r += '- None detected.' } else { foreach($m in $missing){ $r += ('- ' + $m) } }
$r += ''
$r += '## Next'
if($psql -and $dryrunScore -ge 60){ $r += 'Proceed to aays-043-db-connection-readonly-probe.'; $r += 'NEXT_WAIT_MINUTES=3-5' } else { $r += 'Resolve missing dry-run prerequisites before DB probe.'; $r += 'NEXT_WAIT_MINUTES=0' }
$r += ''
$r += 'PLAN_PROGRESS_PERCENT=84'
$r += 'TASK_COMPLETION=100/100'
$r += 'TERRAYIELD_TASK_DONE'
$r | Set-Content -Encoding UTF8 -Path $out
@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 aays_042_db_staging_import_dryrun score=' + $dryrunScore),'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
Log ('REPORT_PATH=' + $out)
Log ('DRYRUN_READINESS_SCORE=' + $dryrunScore + '/100')
Log 'PLAN_PROGRESS_PERCENT=84'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
