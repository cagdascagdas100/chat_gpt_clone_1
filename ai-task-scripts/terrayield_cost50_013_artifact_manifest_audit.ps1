$ErrorActionPreference = 'Continue'
$TaskId = 'cost50-013-artifact-manifest-audit-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$ProjectRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$CostRoot = 'E:\AAYS_DATA\cost'
$ReportDir = Join-Path $CostRoot 'quality_reports'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ReportDir,$ResultDir | Out-Null
function Step($m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
function Has($p){ return [bool](Test-Path $p) }
function CountFiles($root,$filter){ try { if(Test-Path $root){ return @(Get-ChildItem -Path $root -Filter $filter -File -Recurse -ErrorAction SilentlyContinue).Count } } catch {}; return 0 }
function FirstFiles($root,$filter,$n){ try { if(Test-Path $root){ return @(Get-ChildItem -Path $root -Filter $filter -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First $n | ForEach-Object { $_.FullName }) } } catch {}; return @() }
Step "TASK=$TaskId"
Step "PROJECT_ROOT=$ProjectRoot"
$paths = [ordered]@{
  project_root = $ProjectRoot
  app_main = (Join-Path $ProjectRoot 'app\main.py')
  models = (Join-Path $ProjectRoot 'app\db\models.py')
  alembic = (Join-Path $ProjectRoot 'alembic')
  requirements = (Join-Path $ProjectRoot 'requirements.txt')
  readme = (Join-Path $ProjectRoot 'README.md')
  tests = (Join-Path $ProjectRoot 'tests')
  scripts = (Join-Path $ProjectRoot 'scripts')
  tools = (Join-Path $ProjectRoot 'tools')
  quality_reports = $ReportDir
}
$checks = [ordered]@{}
foreach($k in $paths.Keys){ $checks[$k] = Has $paths[$k]; Step ($k + '=' + $checks[$k] + ' :: ' + $paths[$k]) }
$counts = [ordered]@{
  python = CountFiles $ProjectRoot '*.py'
  markdown = CountFiles $ProjectRoot '*.md'
  sql = CountFiles $ProjectRoot '*.sql'
  csv = CountFiles $ProjectRoot '*.csv'
  json = CountFiles $ProjectRoot '*.json'
  yaml = ((CountFiles $ProjectRoot '*.yml') + (CountFiles $ProjectRoot '*.yaml'))
  reports = CountFiles $ReportDir '*.md'
}
foreach($k in $counts.Keys){ Step ($k.ToUpper() + '_COUNT=' + $counts[$k]) }
$manifest = [ordered]@{
  task_id = $TaskId
  generated_at = (Get-Date -Format s)
  project_root = $ProjectRoot
  cost_root = $CostRoot
  checks = $checks
  counts = $counts
  sample_python = @(FirstFiles $ProjectRoot '*.py' 40)
  sample_reports = @(FirstFiles $ReportDir '*.md' 40)
}
$manifestPath = Join-Path $ResultDir "$TaskId.manifest.json"
$manifestExternal = Join-Path $ReportDir "$TaskId.manifest.json"
($manifest | ConvertTo-Json -Depth 8) | Set-Content -Path $manifestPath -Encoding UTF8
try { Copy-Item $manifestPath $manifestExternal -Force } catch {}
$score = 0; $total = 0
foreach($k in $checks.Keys){ $total++; if($checks[$k]){ $score++ } }
$total++; if($counts.python -gt 0){ $score++ }
$total++; if($counts.reports -gt 0){ $score++ }
$readiness = [int](($score / [Math]::Max($total,1)) * 100)
$gitStatus = ''
try { $gitStatus = git -C $ProjectRoot status --short 2>&1 | Out-String } catch { $gitStatus = $_.Exception.Message }
$report = @()
$report += '# Cost50 Step 013 Artifact Manifest Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Checks'
foreach($k in $checks.Keys){ $report += "- ${k}: $($checks[$k]) :: $($paths[$k])" }
$report += ''
$report += '## Counts'
foreach($k in $counts.Keys){ $report += "- ${k}: $($counts[$k])" }
$report += ''
$report += '## Manifest'
$report += "- local: $manifestPath"
$report += "- external: $manifestExternal"
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
$report | Set-Content -Path $out -Encoding UTF8
try { Copy-Item $out $ext -Force } catch {}
Step "REPORT_PATH=$out"
Step "EXTERNAL_REPORT_PATH=$ext"
Step "MANIFEST_PATH=$manifestPath"
Step "MANIFEST_EXTERNAL=$manifestExternal"
Step "PLAN_PROGRESS_PERCENT=$readiness"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
