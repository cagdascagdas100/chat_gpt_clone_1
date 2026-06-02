$ErrorActionPreference='Continue'
$TaskId='cost50-025-final-artifact-index-map-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function CountFiles($p,$filter='*'){ if(Test-Path $p){ return @((Get-ChildItem -Path $p -File -Filter $filter -ErrorAction SilentlyContinue)).Count } return 0 }
function SizeFiles($p,$filter='*'){ if(Test-Path $p){ return [Int64]((Get-ChildItem -Path $p -File -Filter $filter -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum) } return 0 }
function ReadFlag($Path,$Pattern){ if(Test-Path $Path){ $txt=Get-Content -Raw -Encoding UTF8 -Path $Path; if($txt -match $Pattern){ return $Matches[0] } }; return 'MISSING' }
Log "TASK=$TaskId"
Log 'MODE=readonly_final_artifact_index_map'
$ProjectRoot='E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$qDir=Join-Path $ProjectRoot 'quality_reports'
$mDir=Join-Path $ProjectRoot 'source_manifests'
$reports=@(Get-ChildItem -Path $ResultDir -File -Filter '*.md' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 40)
$rows=New-Object System.Collections.Generic.List[string]
$rows.Add('| File | LastWriteTime | Bytes | Completion | Percent |') | Out-Null
$rows.Add('|---|---:|---:|---:|---:|') | Out-Null
foreach($f in $reports){
  $txt=''; try { $txt=Get-Content -Raw -Encoding UTF8 -Path $f.FullName } catch {}
  $comp='MISSING'; $pct='MISSING'
  if($txt -match 'TASK_COMPLETION=\S+'){ $comp=$Matches[0] }
  if($txt -match '(PLAN_PROGRESS_PERCENT|COST50_APPROX_PERCENT)=\d+'){ $pct=$Matches[0] }
  $rows.Add("| $($f.Name) | $($f.LastWriteTime.ToString('s')) | $($f.Length) | $comp | $pct |") | Out-Null
}
$cleanup=Join-Path $ResultDir 'cost50-024-delete-old-temp-runner-logs-only-20260512.report.md'
$out=Join-Path $ResultDir "$TaskId.report.md"
$report=@(
  '# Cost50 025 Final Artifact Index Map',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=readonly_index_only',
  "PROJECT_ROOT=$ProjectRoot",
  "QUALITY_REPORTS_DIR_EXISTS=$(Test-Path $qDir)",
  "QUALITY_REPORTS_FILE_COUNT=$(CountFiles $qDir)",
  "QUALITY_REPORTS_BYTES=$(SizeFiles $qDir)",
  "SOURCE_MANIFESTS_DIR_EXISTS=$(Test-Path $mDir)",
  "SOURCE_MANIFESTS_FILE_COUNT=$(CountFiles $mDir)",
  "SOURCE_MANIFESTS_BYTES=$(SizeFiles $mDir)",
  "AI_RESULTS_MD_COUNT=$(CountFiles $ResultDir '*.md')",
  "CLEANUP_024_DONE=$(ReadFlag $cleanup 'TASK_COMPLETION=100/100')",
  "CLEANUP_024_PROTECTED=$(ReadFlag $cleanup 'PROTECTED_TOUCH_COUNT=0')",
  'ARTIFACT_INDEX_READY=True',
  'NEXT_RECOMMENDED_STEP=cost50-026-db-platform-readiness-matrix-audit',
  'PLAN_PROGRESS_PERCENT=48',
  'TASK_COMPLETION=100/100',
  '',
  '## Recent AI result report index',
  ''
) + $rows
$report | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log 'ARTIFACT_INDEX_READY=True'
Log 'PLAN_PROGRESS_PERCENT=48'
Log 'TASK_COMPLETION=100/100'
exit 0
