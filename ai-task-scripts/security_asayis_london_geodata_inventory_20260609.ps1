$ErrorActionPreference = 'Continue'

$TaskId = 'security-asayis-london-geodata-inventory-20260609'
$StartedAt = Get-Date
$RepoRoot = (Get-Location).Path
$FWorkRoot = 'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609'

$ReportDir = Join-Path $RepoRoot 'ai-results'
$StatusDir = Join-Path $RepoRoot 'docs\chatgpt_status'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null

$MdPath = Join-Path $ReportDir 'security_london_geodata_inventory_latest.md'
$JsonPath = Join-Path $ReportDir 'security_london_geodata_inventory_latest.json'
$StatusPath = Join-Path $StatusDir 'security_london_geodata_inventory_status_20260609.md'

$Roots = @(
  (Join-Path $RepoRoot 'england_map_web\data'),
  (Join-Path $RepoRoot 'data'),
  (Join-Path $RepoRoot 'ai-results'),
  $FWorkRoot,
  'F:\chatgpt\AAYS_WORK',
  'F:\sold_buildings',
  'F:\chatgpt'
) | Select-Object -Unique

$Extensions = @('.geojson','.json','.gpkg','.shp','.parquet','.csv','.ndjson','.jsonl')
$NamePattern = '(parcel|title|uprn|building|polygon|boundary|lsoa|borough|london|crime|police|security|asayis|safety|deprivation|imd|population)'

function Get-ShortHash($Path) {
  try {
    $item = Get-Item $Path -ErrorAction Stop
    if ($item.Length -le 200MB) {
      return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash
    }
    return 'SKIPPED_GT_200MB'
  } catch {
    return 'HASH_ERROR'
  }
}

$Candidates = New-Object System.Collections.Generic.List[object]
foreach ($Root in $Roots) {
  if (-not (Test-Path $Root)) { continue }
  try {
    Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $Extensions -contains $_.Extension.ToLowerInvariant() -and
        ($_.Name -match $NamePattern -or $_.FullName -match $NamePattern)
      } |
      Sort-Object Length -Descending |
      Select-Object -First 2000 |
      ForEach-Object {
        $full = $_.FullName
        $name = $_.Name
        $class = @()
        if ($full -match '(parcel|title|uprn|building)') { $class += 'parcel_or_building' }
        if ($full -match '(security|asayis|safety)') { $class += 'security' }
        if ($full -match '(crime|police)') { $class += 'crime_or_police' }
        if ($full -match '(lsoa|borough|boundary|london)') { $class += 'boundary_or_london' }
        if ($full -match '(imd|deprivation|population)') { $class += 'context' }
        if ($_.Extension.ToLowerInvariant() -in @('.geojson','.gpkg','.shp','.parquet')) { $class += 'geospatial' }
        if ($_.Length -gt 5MB) { $class += 'large' }
        $Candidates.Add([pscustomobject]@{
          path = $full
          name = $name
          extension = $_.Extension.ToLowerInvariant()
          length = $_.Length
          last_write = $_.LastWriteTime.ToString('o')
          classes = $class
          sha256 = Get-ShortHash $full
        })
      }
  } catch {
    $Candidates.Add([pscustomobject]@{
      path = $Root
      name = 'SCAN_ERROR'
      extension = ''
      length = 0
      last_write = (Get-Date).ToString('o')
      classes = @('scan_error')
      sha256 = $_.Exception.Message
    })
  }
}

$All = @($Candidates | Sort-Object length -Descending)
$Parcel = @($All | Where-Object { $_.classes -contains 'parcel_or_building' -and $_.classes -contains 'geospatial' } | Select-Object -First 100)
$Security = @($All | Where-Object { $_.classes -contains 'security' -and $_.classes -contains 'geospatial' } | Select-Object -First 100)
$Crime = @($All | Where-Object { $_.classes -contains 'crime_or_police' } | Select-Object -First 100)
$Boundary = @($All | Where-Object { $_.classes -contains 'boundary_or_london' -and $_.classes -contains 'geospatial' } | Select-Object -First 100)
$LargeGeo = @($All | Where-Object { $_.classes -contains 'geospatial' -and $_.classes -contains 'large' } | Select-Object -First 100)

$RecommendedParcel = $Parcel | Select-Object -First 1
$RecommendedSecurity = $Security | Select-Object -First 1
$RecommendedCrime = $Crime | Select-Object -First 1
$RecommendedBoundary = $Boundary | Select-Object -First 1

$Result = [ordered]@{
  task_id = $TaskId
  started_at = $StartedAt.ToString('o')
  completed_at = (Get-Date).ToString('o')
  repo_root = $RepoRoot
  f_work_root = $FWorkRoot
  search_roots = $Roots
  total_candidates = $All.Count
  parcel_geodata_count = $Parcel.Count
  security_geodata_count = $Security.Count
  crime_or_police_count = $Crime.Count
  boundary_geodata_count = $Boundary.Count
  large_geodata_count = $LargeGeo.Count
  recommended_parcel_input = if ($RecommendedParcel) { $RecommendedParcel.path } else { $null }
  recommended_security_input = if ($RecommendedSecurity) { $RecommendedSecurity.path } else { $null }
  recommended_crime_input = if ($RecommendedCrime) { $RecommendedCrime.path } else { $null }
  recommended_boundary_input = if ($RecommendedBoundary) { $RecommendedBoundary.path } else { $null }
  ready_for_london_build_task = [bool]($RecommendedParcel -and ($RecommendedSecurity -or $RecommendedCrime -or $RecommendedBoundary))
  parcel_candidates = $Parcel
  security_candidates = $Security
  crime_candidates = $Crime
  boundary_candidates = $Boundary
  large_geodata_candidates = $LargeGeo
}

$Result | ConvertTo-Json -Depth 8 | Set-Content -Path $JsonPath -Encoding UTF8

$Md = @()
$Md += '# Security/asayis London geodata inventory'
$Md += ''
$Md += "Task: $TaskId"
$Md += "Completed: $($Result.completed_at)"
$Md += "Repo root: $RepoRoot"
$Md += "F work root: $FWorkRoot"
$Md += ''
$Md += '## Counts'
$Md += "- Total candidates: $($Result.total_candidates)"
$Md += "- Parcel/building geodata candidates: $($Result.parcel_geodata_count)"
$Md += "- Security geodata candidates: $($Result.security_geodata_count)"
$Md += "- Crime/police candidates: $($Result.crime_or_police_count)"
$Md += "- Boundary/London geodata candidates: $($Result.boundary_geodata_count)"
$Md += "- Large geodata candidates: $($Result.large_geodata_count)"
$Md += ''
$Md += '## Recommended inputs'
$Md += "- Parcel input: $($Result.recommended_parcel_input)"
$Md += "- Security input: $($Result.recommended_security_input)"
$Md += "- Crime/police input: $($Result.recommended_crime_input)"
$Md += "- Boundary input: $($Result.recommended_boundary_input)"
$Md += "- Ready for London build task: $($Result.ready_for_london_build_task)"
$Md += ''
$Md += '## Top parcel/building geodata candidates'
$Parcel | Select-Object -First 20 | ForEach-Object { $Md += "- $($_.path) [$($_.length) bytes]" }
$Md += ''
$Md += '## Top security geodata candidates'
$Security | Select-Object -First 20 | ForEach-Object { $Md += "- $($_.path) [$($_.length) bytes]" }
$Md += ''
$Md += '## Top crime/police candidates'
$Crime | Select-Object -First 20 | ForEach-Object { $Md += "- $($_.path) [$($_.length) bytes]" }
$Md += ''
$Md += '## Top boundary/London geodata candidates'
$Boundary | Select-Object -First 20 | ForEach-Object { $Md += "- $($_.path) [$($_.length) bytes]" }
$Md -join "`r`n" | Set-Content -Path $MdPath -Encoding UTF8
Copy-Item $MdPath $StatusPath -Force

Write-Host "GEODATA_INVENTORY_COMPLETE"
Write-Host "JSON=$JsonPath"
Write-Host "MD=$MdPath"
