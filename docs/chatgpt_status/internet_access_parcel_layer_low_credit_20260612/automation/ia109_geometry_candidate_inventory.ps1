$ErrorActionPreference = 'Continue'
$pageKey='internet_access_parcel_layer_low_credit_20260612'
$taskId='internet-access-109-geometry-candidate-inventory'
$repoRoot=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$statusRoot=Join-Path $repoRoot 'docs\chatgpt_status'
$pageRoot=Join-Path $statusRoot $pageKey
$statusDir=Join-Path $pageRoot 'status'
$reportsDir=Join-Path $statusRoot 'reports'
$pageReportsDir=Join-Path $pageRoot 'reports'
New-Item -ItemType Directory -Force -Path $statusDir,$reportsDir,$pageReportsDir | Out-Null
$heavyRoot='F:\AAYS_WORK\internet_access_final_20260616'
if(-not(Test-Path 'F:\')){$heavyRoot='D:\AAYS_WORK\internet_access_final_20260616'}
New-Item -ItemType Directory -Force -Path (Join-Path $heavyRoot 'diagnostics') | Out-Null
$roots=@((Join-Path $repoRoot 'england_map_web\data'),'F:\AAYS_WORK','F:\chatgpt\AAYS_WORK','D:\AAYS_WORK','D:\chatgpt\AAYS_WORK') | Where-Object { Test-Path $_ }
$candidates=@()
foreach($r in $roots){
  Get-ChildItem -Path $r -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq '.geojson' -and ($_.Name -match 'parcel|polygon|title|uprn|geometry') } | ForEach-Object {
    $sample=''
    try { $sample=(Get-Content -Path $_.FullName -Encoding UTF8 -TotalCount 80 -ErrorAction SilentlyContinue) -join ' ' } catch {}
    $hasPolygon=($sample -match 'Polygon|MultiPolygon')
    $hasNull=($sample -match '"geometry"\s*:\s*null')
    $candidates += [ordered]@{ path=$_.FullName; length=$_.Length; has_polygon_token=$hasPolygon; has_null_geometry_token=$hasNull; last_write_utc=$_.LastWriteTimeUtc.ToString('o') }
  }
}
$result=[ordered]@{
  task_id=$taskId
  page_key=$pageKey
  status='GEOMETRY_CANDIDATE_INVENTORY_DONE'
  completion_percent=72
  final_ready=$false
  manual_stdout_required=$false
  candidate_count=$candidates.Count
  candidates=$candidates | Select-Object -First 200
  generated_at_utc=(Get-Date).ToUniversalTime().ToString('o')
}
$result | ConvertTo-Json -Depth 8 | Out-File (Join-Path $reportsDir 'internet-access-109-geometry-candidate-inventory.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 8 | Out-File (Join-Path $pageReportsDir 'internet-access-109-geometry-candidate-inventory.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 8 | Out-File (Join-Path $heavyRoot 'diagnostics\internet_access_geometry_candidate_inventory.json') -Encoding UTF8
"task_id=$taskId`nstatus=GEOMETRY_CANDIDATE_INVENTORY_DONE`ncompletion_percent=72`nfinal_ready=false" | Out-File (Join-Path $statusDir 'ia109_geometry_candidate_inventory.txt') -Encoding UTF8
