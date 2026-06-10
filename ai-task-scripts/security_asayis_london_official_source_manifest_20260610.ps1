$ErrorActionPreference = 'Continue'

$TaskId = 'security-asayis-london-official-source-manifest-20260610'
$RepoRoot = (Get-Location).Path
$FRoot = 'F:\chatgpt\AAYS_WORK\security_asayis_london_official_sources_20260610'
$FallbackRoot = Join-Path $RepoRoot 'ai-results\security_london_official_sources_work_20260610'
$FDriveAvailable = Test-Path 'F:\'
if ($FDriveAvailable) { $WorkRoot = $FRoot } else { $WorkRoot = $FallbackRoot }

$OutDir = Join-Path $WorkRoot 'official_source_manifest'
$RawDir = Join-Path $OutDir 'raw_landing_pages'
$ManifestJson = Join-Path $RepoRoot 'ai-results\security_london_official_source_manifest_latest.json'
$ManifestMd = Join-Path $RepoRoot 'ai-results\security_london_official_source_manifest_latest.md'
$StatusMd = Join-Path $RepoRoot 'docs\chatgpt_status\security_london_official_source_manifest_status_20260610.md'

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $RawDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot 'ai-results') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot 'docs\chatgpt_status') | Out-Null

function Get-HeadProbe($Id, $Role, $Url) {
    $result = [ordered]@{ id=$Id; role=$Role; url=$Url; status='NOT_RUN'; http_status=$null; error=$null }
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -UseBasicParsing -TimeoutSec 30
        $result.status = 'HEAD_OK'
        $result.http_status = [int]$response.StatusCode
    } catch {
        $result.status = 'HEAD_FAILED'
        $result.error = $_.Exception.Message
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 30
            $result.status = 'GET_OK'
            $result.http_status = [int]$response.StatusCode
        } catch {
            if ($result.error) { $result.error = $result.error + ' | GET: ' + $_.Exception.Message } else { $result.error = $_.Exception.Message }
        }
    }
    return $result
}

function Get-LandingLinks($Id, $Url) {
    $links = @()
    $rawPath = Join-Path $RawDir ($Id + '.html')
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 45
        $html = [string]$response.Content
        [System.IO.File]::WriteAllText($rawPath, $html, [System.Text.UTF8Encoding]::new($false))
        $matches = [regex]::Matches($html, 'href=["'']([^"''#]+)')
        foreach ($m in $matches) {
            $href = $m.Groups[1].Value
            try {
                $abs = [System.Uri]::new([System.Uri]::new($Url), $href).AbsoluteUri
                if ($abs -match '(?i)(\.zip|\.csv|\.json|\.geojson|\.gpkg|\.shp|download|api|inspire|lsoa|crime|boundary)') {
                    $links += $abs
                }
            } catch {}
        }
    } catch {
        [System.IO.File]::WriteAllText($rawPath + '.error.txt', $_.Exception.Message, [System.Text.UTF8Encoding]::new($false))
    }
    return ($links | Sort-Object -Unique | Select-Object -First 50)
}

$sources = @(
    [ordered]@{ id='police_uk_bulk'; role='crime_or_police'; url='https://data.police.uk/data/' },
    [ordered]@{ id='police_uk_api_docs'; role='crime_or_police'; url='https://data.police.uk/docs/method/crime-street/' },
    [ordered]@{ id='ons_open_geography'; role='boundary_or_lsoa'; url='https://geoportal.statistics.gov.uk/' },
    [ordered]@{ id='hmlr_inspire'; role='parcel_or_title_polygon'; url='https://use-land-property-data.service.gov.uk/datasets/inspire' },
    [ordered]@{ id='london_datastore_recorded_crime'; role='borough_crime_crosscheck'; url='https://data.london.gov.uk/dataset/recorded_crime_summary' },
    [ordered]@{ id='gov_uk_imd'; role='imd_crime_domain_context'; url='https://www.gov.uk/government/collections/english-indices-of-deprivation' }
)

$probes = @()
$candidates = @()
foreach ($s in $sources) {
    $probe = Get-HeadProbe -Id $s.id -Role $s.role -Url $s.url
    $probes += $probe
    $links = Get-LandingLinks -Id $s.id -Url $s.url
    foreach ($ln in $links) {
        $kind = 'unknown'
        if ($ln -match '(?i)police|crime') { $kind='crime_or_police' }
        elseif ($ln -match '(?i)inspire|land-registry|title|parcel') { $kind='parcel_or_title_polygon' }
        elseif ($ln -match '(?i)lsoa|boundary|lookup|geography|shapefile|geojson|gpkg') { $kind='boundary_or_lsoa' }
        $candidates += [ordered]@{ source_id=$s.id; role=$s.role; candidate_kind=$kind; url=$ln }
    }
}

$localChecks = @(
    [ordered]@{ id='expected_point_input'; path=(Join-Path $RepoRoot 'england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson'); exists=(Test-Path (Join-Path $RepoRoot 'england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson')) },
    [ordered]@{ id='expected_polygon_input'; path=(Join-Path $RepoRoot 'england_map_web\data\parcel_security_scores_polygons.geojson'); exists=(Test-Path (Join-Path $RepoRoot 'england_map_web\data\parcel_security_scores_polygons.geojson')) }
)

$parcelCandidateCount = @($candidates | Where-Object { $_.candidate_kind -eq 'parcel_or_title_polygon' }).Count
$boundaryCandidateCount = @($candidates | Where-Object { $_.candidate_kind -eq 'boundary_or_lsoa' }).Count
$crimeCandidateCount = @($candidates | Where-Object { $_.candidate_kind -eq 'crime_or_police' }).Count
$decision = 'OFFICIAL_SOURCE_MANIFEST_READY_FOR_REVIEW'
$nextStep = 'Create targeted download task for parcel polygons, London boundaries, and crime records from validated candidates; do not mark FINAL_READY.'
if (($parcelCandidateCount -eq 0) -and ($boundaryCandidateCount -eq 0) -and ($crimeCandidateCount -eq 0)) {
    $decision = 'BLOCKED_NO_DOWNLOAD_CANDIDATES_FROM_LANDING_PAGES'
    $nextStep = 'Create targeted official source URL resolver task; landing pages did not expose enough direct download candidates.'
}

$result = [ordered]@{
    task_id=$TaskId
    started_at=(Get-Date).ToString('o')
    repo_root=$RepoRoot
    work_root=$WorkRoot
    f_drive_available=$FDriveAvailable
    probes=$probes
    candidate_count=@($candidates).Count
    parcel_candidate_count=$parcelCandidateCount
    boundary_candidate_count=$boundaryCandidateCount
    crime_candidate_count=$crimeCandidateCount
    candidates=$candidates
    local_checks=$localChecks
    ready_for_london_build_task=$false
    decision=$decision
    next_step=$nextStep
    safety=[ordered]@{ db_write=$false; production_deploy=$false; ddl=$false; london_only=$true; migration=$false; fake_data=$false }
}

$json = $result | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($ManifestJson, $json, [System.Text.UTF8Encoding]::new($false))

$md = @()
$md += '# Security London official source manifest status'
$md += ''
$md += '- task_id: ' + $TaskId
$md += '- repo_root: ' + $RepoRoot
$md += '- work_root: ' + $WorkRoot
$md += '- f_drive_available: ' + $FDriveAvailable
$md += '- candidate_count: ' + @($candidates).Count
$md += '- parcel_candidate_count: ' + $parcelCandidateCount
$md += '- boundary_candidate_count: ' + $boundaryCandidateCount
$md += '- crime_candidate_count: ' + $crimeCandidateCount
$md += '- decision: ' + $decision
$md += '- next_step: ' + $nextStep
$md += ''
$md += '## Probes'
foreach ($p in $probes) { $md += '- ' + $p.id + ': ' + $p.status + ' ' + $p.http_status + ' - ' + $p.url }
$md += ''
$md += '## Safety'
$md += '- db_write: false'
$md += '- production_deploy: false'
$md += '- ddl: false'
$md += '- migration: false'
$md += '- fake_data: false'
[System.IO.File]::WriteAllText($ManifestMd, ($md -join [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
Copy-Item $ManifestMd $StatusMd -Force

Write-Output ('OFFICIAL_SOURCE_MANIFEST_JSON=' + $ManifestJson)
Write-Output ('OFFICIAL_SOURCE_MANIFEST_DECISION=' + $decision)
exit 0
