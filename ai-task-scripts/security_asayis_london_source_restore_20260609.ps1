$ErrorActionPreference = 'Continue'
$RepoRoot = (Get-Location).Path
$WorkRoot = 'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609'
$OutDir = Join-Path $WorkRoot 'source_restore'
$AiResults = Join-Path $RepoRoot 'ai-results'
$StatusDir = Join-Path $RepoRoot 'docs\chatgpt_status'
New-Item -ItemType Directory -Force -Path $OutDir,$AiResults,$StatusDir | Out-Null
$Started = Get-Date

$Sources = @(
  [pscustomobject]@{ id='police_uk_api'; role='crime_or_police'; url='https://data.police.uk/docs/method/crime-street/'; note='Official Police.uk street-level API documentation; anonymised/approximate locations only' },
  [pscustomobject]@{ id='police_uk_bulk'; role='crime_or_police'; url='https://data.police.uk/data/'; note='Official Police.uk bulk download landing page' },
  [pscustomobject]@{ id='ons_open_geography'; role='boundary_or_lsoa'; url='https://geoportal.statistics.gov.uk/'; note='ONS Open Geography Portal landing page for boundaries/lookups' },
  [pscustomobject]@{ id='hmlr_inspire'; role='parcel_or_title_polygon'; url='https://use-land-property-data.service.gov.uk/datasets/inspire'; note='HM Land Registry INSPIRE Index Polygons landing page; required for parcel/title polygons if available' },
  [pscustomobject]@{ id='london_datastore_recorded_crime'; role='borough_crime_crosscheck'; url='https://data.london.gov.uk/dataset/recorded_crime_summary'; note='London Datastore MPS recorded crime summary for London cross-checking' },
  [pscustomobject]@{ id='gov_uk_imd'; role='imd_crime_domain_context'; url='https://www.gov.uk/government/collections/english-indices-of-deprivation'; note='English Indices of Deprivation collection for contextual confidence only' }
)

$ProbeResults = @()
foreach ($s in $Sources) {
  $status = 'UNKNOWN'
  $code = $null
  $err = $null
  try {
    $resp = Invoke-WebRequest -Uri $s.url -Method Head -MaximumRedirection 5 -TimeoutSec 20 -UseBasicParsing
    $code = [int]$resp.StatusCode
    $status = 'HEAD_OK'
  } catch {
    try {
      $resp = Invoke-WebRequest -Uri $s.url -Method Get -MaximumRedirection 5 -TimeoutSec 30 -UseBasicParsing
      $code = [int]$resp.StatusCode
      $status = 'GET_OK'
    } catch {
      $status = 'FAILED'
      $err = $_.Exception.Message
    }
  }
  $ProbeResults += [pscustomobject]@{
    id=$s.id; role=$s.role; url=$s.url; status=$status; http_status=$code; error=$err; note=$s.note
  }
}

# Check whether any existing local data can satisfy the minimum London parcel/security build inputs.
$LocalChecks = @(
  [pscustomobject]@{ id='expected_point_input'; path=(Join-Path $RepoRoot 'england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson') },
  [pscustomobject]@{ id='expected_polygon_input'; path=(Join-Path $RepoRoot 'england_map_web\data\parcel_security_scores_polygons.geojson') },
  [pscustomobject]@{ id='f_point_output'; path=(Join-Path $WorkRoot 'data\parcel_security_scores_london_pilot_points.geojson') },
  [pscustomobject]@{ id='f_polygon_output'; path=(Join-Path $WorkRoot 'data\parcel_security_scores_london_pilot_polygons.geojson') },
  [pscustomobject]@{ id='f_summary'; path=(Join-Path $WorkRoot 'data\parcel_security_london_pilot_summary.json') }
) | ForEach-Object {
  $exists = Test-Path $_.path
  [pscustomobject]@{ id=$_.id; path=$_.path; exists=$exists; length=($(if($exists){(Get-Item $_.path).Length}else{$null})) }
}

$ReadyForBuild = $false
$Decision = 'BLOCKED_NO_LOCAL_PARCEL_OR_SECURITY_GEODATA'
if (($LocalChecks | Where-Object { $_.id -eq 'expected_point_input' -and $_.exists }).Count -gt 0 -and ($LocalChecks | Where-Object { $_.id -eq 'expected_polygon_input' -and $_.exists }).Count -gt 0) {
  $ReadyForBuild = $true
  $Decision = 'READY_EXISTING_INPUTS_FOUND'
}

$Report = [pscustomobject]@{
  task_id='security-asayis-london-source-restore-20260609'
  started_at=$Started.ToString('o')
  completed_at=(Get-Date).ToString('o')
  repo_root=$RepoRoot
  work_root=$WorkRoot
  probe_results=$ProbeResults
  local_checks=$LocalChecks
  ready_for_london_build_task=$ReadyForBuild
  decision=$Decision
  next_step=($(if($ReadyForBuild){'Run London pilot build again'}else{'Create official-source download/restore task for parcel polygons, boundaries, and crime data; do not mark FINAL_READY'}))
  safety=@{ db_write=$false; ddl=$false; migration=$false; production_deploy=$false; fake_data=$false; london_only=$true }
}

$JsonPath = Join-Path $AiResults 'security_london_source_restore_latest.json'
$MdPath = Join-Path $AiResults 'security_london_source_restore_latest.md'
$StatusPath = Join-Path $StatusDir 'security_london_source_restore_status_20260609.md'
$Report | ConvertTo-Json -Depth 8 | Set-Content -Path $JsonPath -Encoding UTF8

$md = @()
$md += '# Security London Source Restore Audit'
$md += ''
$md += "Completed: $((Get-Date).ToString('o'))"
$md += "Decision: $Decision"
$md += "Ready for London build: $ReadyForBuild"
$md += ''
$md += '## Source probes'
foreach($p in $ProbeResults){ $md += "- $($p.id): $($p.status) $($p.http_status) - $($p.url)" }
$md += ''
$md += '## Local checks'
foreach($c in $LocalChecks){ $md += "- $($c.id): exists=$($c.exists) length=$($c.length) path=$($c.path)" }
$md += ''
$md += '## Safety'
$md += '- DB write: false'
$md += '- DDL/migration: false'
$md += '- Production deploy: false'
$md += '- Fake data: false'
$md += '- Scope: London only'
$md -join "`r`n" | Set-Content -Path $MdPath -Encoding UTF8
Copy-Item $MdPath $StatusPath -Force

Write-Host "SOURCE_RESTORE_REPORT=$JsonPath"
Write-Host "SOURCE_RESTORE_DECISION=$Decision"
exit 0
