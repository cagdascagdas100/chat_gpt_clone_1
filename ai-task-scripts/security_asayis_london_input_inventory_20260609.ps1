$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$TaskId = 'security-asayis-london-input-inventory-20260609'
$StartedAt = (Get-Date).ToString('o')
$RepoRoot = (Get-Location).Path
$RepoOutDir = Join-Path $RepoRoot 'ai-results'
$RepoStatusDir = Join-Path $RepoRoot 'docs\chatgpt_status'
$FWorkRoot = 'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609'
$FDataDir = Join-Path $FWorkRoot 'data'
New-Item -ItemType Directory -Force -Path $RepoOutDir, $RepoStatusDir, $FDataDir | Out-Null

$SearchRoots = @(
  (Join-Path $RepoRoot 'england_map_web\data'),
  (Join-Path $RepoRoot 'data'),
  (Join-Path $RepoRoot 'ai-results'),
  'F:\chatgpt\AAYS_WORK',
  'F:\sold_buildings',
  'F:\chatgpt'
) | Select-Object -Unique

$WantedNames = @(
  'parcel_security_scores_rechecked_0_120m_spatial.geojson',
  'parcel_security_scores_polygons.geojson',
  'parcel_security_scores.geojson',
  'security_scores.geojson',
  'security_asayis.geojson'
)

$Candidates = New-Object System.Collections.Generic.List[object]
foreach ($root in $SearchRoots) {
  if (-not (Test-Path $root)) { continue }
  try {
    Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        ($_.Extension -in '.geojson','.json','.csv') -and
        ($_.Name -match 'security|asayis|asayiş|crime|police|parcel_security|safety')
      } |
      Select-Object -First 300 |
      ForEach-Object {
        $item = $_
        $sha = $null
        try { $sha = (Get-FileHash $item.FullName -Algorithm SHA256).Hash } catch {}
        $Candidates.Add([ordered]@{
          path = $item.FullName
          name = $item.Name
          length = $item.Length
          last_write = $item.LastWriteTime.ToString('o')
          sha256 = $sha
        }) | Out-Null
      }
  } catch {}
}

$Exact = @()
foreach ($name in $WantedNames) {
  $match = @($Candidates | Where-Object { $_.name -eq $name })
  foreach ($m in $match) { $Exact += $m }
}

$RecommendedPoint = $null
$RecommendedPolygon = $null
$pointPref = @($Candidates | Where-Object { $_.name -match 'spatial|point|0_120m|parcel_security_scores_rechecked' } | Sort-Object length -Descending | Select-Object -First 1)
$polyPref = @($Candidates | Where-Object { $_.name -match 'polygon|polygons' } | Sort-Object length -Descending | Select-Object -First 1)
if ($pointPref.Count -gt 0) { $RecommendedPoint = $pointPref[0].path }
if ($polyPref.Count -gt 0) { $RecommendedPolygon = $polyPref[0].path }

$Result = [ordered]@{
  task_id = $TaskId
  started_at = $StartedAt
  completed_at = (Get-Date).ToString('o')
  repo_root = $RepoRoot
  f_work_root = $FWorkRoot
  search_roots = $SearchRoots
  candidate_count = $Candidates.Count
  exact_matches = $Exact
  recommended_point_input = $RecommendedPoint
  recommended_polygon_input = $RecommendedPolygon
  candidates = @($Candidates | Sort-Object length -Descending | Select-Object -First 100)
  next_step = 'Patch London pilot input paths only after reviewing recommended_point_input and recommended_polygon_input. Keep heavy outputs on F drive.'
}

$JsonPath = Join-Path $RepoOutDir 'security_london_input_inventory_latest.json'
$MdPath = Join-Path $RepoOutDir 'security_london_input_inventory_latest.md'
$StatusPath = Join-Path $RepoStatusDir 'security_london_input_inventory_status_20260609.md'
$Result | ConvertTo-Json -Depth 20 | Set-Content -Path $JsonPath -Encoding UTF8

$md = @()
$md += '# Security London Input Inventory'
$md += "Task: $TaskId"
$md += "Completed: $($Result.completed_at)"
$md += "Candidate count: $($Result.candidate_count)"
$md += "Recommended point input: $RecommendedPoint"
$md += "Recommended polygon input: $RecommendedPolygon"
$md += ''
$md += '## Top candidates'
foreach ($c in @($Result.candidates | Select-Object -First 30)) { $md += "- $($c.path) size=$($c.length)" }
$md += ''
$md += '## Next step'
$md += $Result.next_step
$mdText = $md -join [Environment]::NewLine
Set-Content -Path $MdPath -Value $mdText -Encoding UTF8
Set-Content -Path $StatusPath -Value $mdText -Encoding UTF8
Write-Host $mdText
exit 0
