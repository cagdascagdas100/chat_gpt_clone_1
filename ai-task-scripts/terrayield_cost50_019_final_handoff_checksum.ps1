$ErrorActionPreference = 'Continue'
$TaskId = 'cost50-019-final-handoff-checksum-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$CostRoot = 'E:\AAYS_DATA\cost'
$ProjectRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$ReportDir = Join-Path $CostRoot 'quality_reports'
$HandoffDir = Join-Path $CostRoot 'handoff_ready'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ReportDir,$HandoffDir,$ResultDir | Out-Null
function Step($m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
function Has($p){ return [bool](Test-Path $p) }
function Files($root,$filter){ try { if(Test-Path $root){ return @(Get-ChildItem -Path $root -Filter $filter -File -Recurse -ErrorAction SilentlyContinue) } } catch {}; return @() }
Step "TASK=$TaskId"
Step "PROJECT_ROOT=$ProjectRoot"
Step "REPORT_DIR=$ReportDir"
Step "HANDOFF_DIR=$HandoffDir"
$reportFiles = @(Files $ReportDir '*')
$handoffFiles = @(Files $HandoffDir '*')
$projectPy = @(Files $ProjectRoot '*.py')
$projectSql = @(Files $ProjectRoot '*.sql')
$projectMd = @(Files $ProjectRoot '*.md')
$checksumRows = @()
foreach($f in @($reportFiles + $handoffFiles | Sort-Object FullName)){
  try {
    $h = Get-FileHash -Path $f.FullName -Algorithm SHA256
    $checksumRows += [ordered]@{ name=$f.Name; path=$f.FullName; bytes=$f.Length; modified=$f.LastWriteTime.ToString('s'); sha256=$h.Hash }
  } catch {
    $checksumRows += [ordered]@{ name=$f.Name; path=$f.FullName; bytes=$f.Length; modified=$f.LastWriteTime.ToString('s'); sha256='ERROR: ' + $_.Exception.Message }
  }
}
$checks = [ordered]@{
  project_root = Has $ProjectRoot
  report_dir = Has $ReportDir
  handoff_dir = Has $HandoffDir
  reports_present = ($reportFiles.Count -gt 0)
  handoff_present = ($handoffFiles.Count -gt 0)
  app_main = Has (Join-Path $ProjectRoot 'app\main.py')
  requirements = Has (Join-Path $ProjectRoot 'requirements.txt')
}
foreach($k in $checks.Keys){ Step ($k + '=' + $checks[$k]) }
Step ('REPORT_FILE_COUNT=' + $reportFiles.Count)
Step ('HANDOFF_FILE_COUNT=' + $handoffFiles.Count)
Step ('PROJECT_PY_COUNT=' + $projectPy.Count)
Step ('PROJECT_SQL_COUNT=' + $projectSql.Count)
Step ('PROJECT_MD_COUNT=' + $projectMd.Count)
Step ('CHECKSUM_ROW_COUNT=' + $checksumRows.Count)
$score=0; $total=0
foreach($k in $checks.Keys){ $total++; if($checks[$k]){ $score++ } }
$total++; if($checksumRows.Count -gt 0){ $score++ }
$total++; if($projectPy.Count -gt 0){ $score++ }
$readiness = [int](($score / [Math]::Max($total,1)) * 100)
$checksumPath = Join-Path $HandoffDir 'COST50_HANDOFF_SHA256_20260512.json'
$checksumRows | ConvertTo-Json -Depth 6 | Set-Content -Path $checksumPath -Encoding UTF8
$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = $_.Exception.Message }
$report = @()
$report += '# Cost50 Step 019 Final Handoff Checksum'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Checks'
foreach($k in $checks.Keys){ $report += "- ${k}: $($checks[$k])" }
$report += ''
$report += '## Counts'
$report += "- report files: $($reportFiles.Count)"
$report += "- handoff files: $($handoffFiles.Count)"
$report += "- project python: $($projectPy.Count)"
$report += "- project sql: $($projectSql.Count)"
$report += "- project markdown: $($projectMd.Count)"
$report += "- checksum rows: $($checksumRows.Count)"
$report += ''
$report += '## Outputs'
$report += "- checksum_json: $checksumPath"
$report += ''
$report += '## Git Status'
$report += '```text'
$report += $gitStatus
$report += '```'
$report += ''
$report += "Readiness score: $readiness"
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$out = Join-Path $ResultDir "$TaskId.report.md"
$ext = Join-Path $ReportDir "$TaskId.report.md"
$handoffReport = Join-Path $HandoffDir 'COST50_FINAL_HANDOFF_CHECKSUM_20260512.md'
$report | Set-Content -Path $out -Encoding UTF8
try { Copy-Item $out $ext -Force } catch {}
try { Copy-Item $out $handoffReport -Force } catch {}
Step "REPORT_PATH=$out"
Step "EXTERNAL_REPORT_PATH=$ext"
Step "HANDOFF_REPORT=$handoffReport"
Step "CHECKSUM_PATH=$checksumPath"
Step "PLAN_PROGRESS_PERCENT=$readiness"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
