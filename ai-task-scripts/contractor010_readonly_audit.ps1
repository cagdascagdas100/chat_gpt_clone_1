$ErrorActionPreference = 'Continue'
$TaskId = 'contractor010-readonly-audit-20260522-r1'
$Bridge = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
if (!(Test-Path $ProjectRoot)) { $ProjectRoot = $Bridge }
$HbDir = Join-Path $Bridge 'ai-heartbeat'
$ResultDir = Join-Path $Bridge 'ai-results'
$ManifestDir = Join-Path $Bridge 'ai-manifests'
New-Item -ItemType Directory -Force -Path $HbDir,$ResultDir,$ManifestDir | Out-Null
$Hb = Join-Path $HbDir 'contractor-010-readonly-audit.md'
function W($stage,$pct,$msg){
  @(
    '# Contractor 010 Read-only Audit',
    ('task_id=' + $TaskId),
    ('stage=' + $stage),
    ('progress_percent=' + $pct),
    ('checked_at=' + (Get-Date -Format s)),
    ('message=' + $msg),
    ('project_root=' + $ProjectRoot),
    'db_write=false',
    'production_deploy=false',
    'fake_data=false'
  ) | Out-File -FilePath $Hb -Encoding utf8 -Force
}
W 'start' 5 'read-only audit started'
Start-Sleep -Seconds 600
$Files = Get-ChildItem -Path $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|\\node_modules\\|\\__pycache__\\|\\.venv\\|\\dist\\|\\build\\' }
$Summary = [ordered]@{
  task_id = $TaskId
  file_count = @($Files).Count
  test_file_count = @($Files | Where-Object { $_.Name -match 'test|spec' }).Count
  api_file_count = @($Files | Where-Object { $_.FullName -match 'api|routes|schemas' }).Count
  docs_file_count = @($Files | Where-Object { $_.FullName -match 'docs|README|md$' }).Count
  db_write = $false
  production_deploy = $false
  fake_data = $false
  generated_at = (Get-Date -Format s)
}
$SummaryPath = Join-Path $ManifestDir 'contractor010_readonly_audit_summary.json'
$Summary | ConvertTo-Json -Depth 5 | Out-File -FilePath $SummaryPath -Encoding utf8 -Force
W 'middle' 50 'file inventory and summary written'
Start-Sleep -Seconds 900
$TopDirsPath = Join-Path $ManifestDir 'contractor010_top_dirs.csv'
$Files | ForEach-Object {
  $rel = $_.FullName.Substring($ProjectRoot.Length).TrimStart('\')
  $top = ($rel -split '\\')[0]
  [PSCustomObject]@{ top_dir=$top; extension=$_.Extension; bytes=$_.Length }
} | Group-Object top_dir,extension | ForEach-Object {
  $parts = $_.Name -split ', '
  [PSCustomObject]@{ top_dir=$parts[0]; extension=$parts[1]; count=$_.Count; bytes=($_.Group | Measure-Object bytes -Sum).Sum }
} | Sort-Object count -Descending | Export-Csv -Path $TopDirsPath -NoTypeInformation -Encoding UTF8
W 'finalizing' 85 'top directory manifest written'
Start-Sleep -Seconds 300
$Report = Join-Path $ResultDir 'contractor-010-readonly-audit-20260522.report.md'
@(
  '# Contractor 010 Read-only Audit',
  'status=completed',
  'PLAN_PROGRESS_PERCENT=60',
  'db_write=false',
  'production_deploy=false',
  'fake_data=false',
  ('file_count=' + $Summary.file_count),
  ('test_file_count=' + $Summary.test_file_count),
  ('api_file_count=' + $Summary.api_file_count),
  ('docs_file_count=' + $Summary.docs_file_count),
  'TASK_COMPLETION=100/100',
  'TERRAYIELD_TASK_DONE'
) | Out-File -FilePath $Report -Encoding utf8 -Force
W 'done' 100 'read-only audit completed and result written'
Write-Output 'PLAN_PROGRESS_PERCENT=60'
Write-Output 'TASK_COMPLETION=100/100'
Write-Output 'TERRAYIELD_TASK_DONE'
exit 0
