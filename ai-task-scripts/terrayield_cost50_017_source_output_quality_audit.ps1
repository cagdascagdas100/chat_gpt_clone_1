$ErrorActionPreference = 'Continue'
$TaskId = 'cost50-017-source-output-quality-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$CostRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function CountFiles($Root,$Pattern) { try { if (Test-Path $Root) { return @(Get-ChildItem -Path $Root -Filter $Pattern -File -Recurse -ErrorAction SilentlyContinue).Count } } catch {}; return 0 }
Log "TASK=$TaskId"
Log 'MODE=source_output_quality_audit_readonly'
$roots = @($CostRoot,$ProjectRoot) | Where-Object { Test-Path $_ }
$patterns = [ordered]@{
  source_fetch_manifest_json='source_fetch_manifest_latest.json'
  source_fetch_manifest_csv='source_fetch_manifest_latest.csv'
  source_facts_extracted='source_facts_extracted_*.csv'
  source_facts_scored='source_facts_scored.csv'
  source_facts_scored_summary='source_facts_scored_summary.json'
}
$hits=[ordered]@{}
foreach($k in $patterns.Keys){$count=0;foreach($r in $roots){$count+=CountFiles $r $patterns[$k]};$hits[$k]=($count -gt 0);Log ($k+'='+$hits[$k]+' count='+$count)}
$csv = $null
foreach($r in $roots){try{$csv=Get-ChildItem -Path $r -Filter 'source_facts_extracted_*.csv' -File -Recurse -ErrorAction SilentlyContinue|Select-Object -First 1;if($csv){break}}catch{}}
$header=''
if($csv){$header=Get-Content -Path $csv.FullName -TotalCount 1 -Encoding UTF8 -ErrorAction SilentlyContinue}
$cols=@('source_id','source_url','metric_name','metric_value','metric_unit','evidence_text','reliability','correctness','confidence')
$colHits=[ordered]@{}
foreach($c in $cols){$colHits[$c]=[bool]($header -match [regex]::Escape($c));Log ('column_'+$c+'='+$colHits[$c])}
$total=$hits.Count+$colHits.Count;$ok=0;foreach($k in $hits.Keys){if($hits[$k]){$ok++}};foreach($k in $colHits.Keys){if($colHits[$k]){$ok++}}
$score=if($total -gt 0){[int](($ok/$total)*100)}else{0}
$reportPath=Join-Path $ResultDir ($TaskId+'.report.md')
$report=@('# Cost50 Step 017 Source Output Quality Audit','',"Generated: $(Get-Date -Format s)",'','## Artifact hits')
foreach($k in $hits.Keys){$report += "- ${k}: $($hits[$k])"}
$report += '','## Required CSV column hits'
foreach($k in $colHits.Keys){$report += "- ${k}: $($colHits[$k])"}
$report += '',"Source output quality score: $score",'','PLAN_PROGRESS_PERCENT=34','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE'
$report|Set-Content -Encoding UTF8 -Path $reportPath
Log ('REPORT_PATH='+$reportPath)
Log ('SOURCE_OUTPUT_QUALITY_SCORE='+$score)
Log 'PLAN_PROGRESS_PERCENT=34'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
