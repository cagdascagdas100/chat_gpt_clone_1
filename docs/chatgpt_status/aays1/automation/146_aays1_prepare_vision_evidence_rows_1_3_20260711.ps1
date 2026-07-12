$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$TaskId = 'aays1-ready-to-sell-vision-evidence-rows-1-3-20260711'
$TargetRows = @(1, 2, 3)
$SiteBase = 'http://127.0.0.1:8012/england_map_web'
$AiRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$EvidenceRelative = 'england_map_web/data/geometry_review_3of4/vision_evidence/146_rows_1_3_20260711'
$StatusRelative = 'docs/chatgpt_status/aays1/status/146_aays1_prepare_vision_evidence_rows_1_3_latest.json'
$ReportRelative = 'docs/chatgpt_status/aays1/reports/146_aays1_prepare_vision_evidence_rows_1_3_report.md'
$StatusMirrorRelative = 'england_map_web/data/geometry_review_3of4/task_reports/146_aays1_prepare_vision_evidence_rows_1_3_latest.json'
$ReportMirrorRelative = 'england_map_web/data/geometry_review_3of4/task_reports/146_aays1_prepare_vision_evidence_rows_1_3_report.md'

function Get-RepoRoot {
    if ($env:AAYS_REPO_ROOT -and (Test-Path -LiteralPath $env:AAYS_REPO_ROOT)) {
        return (Resolve-Path -LiteralPath $env:AAYS_REPO_ROOT).Path
    }
    $root = (& git rev-parse --show-toplevel 2>$null)
    if (-not $root) { throw 'Repository root could not be resolved.' }
    return $root.Trim()
}

function Set-JsonField {
    param([Parameter(Mandatory=$true)]$Object, [Parameter(Mandatory=$true)][string]$Name, $Value)
    if ($Object.PSObject.Properties.Name -contains $Name) {
        $Object.$Name = $Value
    } else {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    }
}

function Test-NumberValue {
    param($Value)
    return ($Value -is [byte] -or $Value -is [sbyte] -or $Value -is [int16] -or $Value -is [uint16] -or $Value -is [int32] -or $Value -is [uint32] -or $Value -is [int64] -or $Value -is [uint64] -or $Value -is [single] -or $Value -is [double] -or $Value -is [decimal])
}

function Find-FirstRing {
    param($Node)
    if ($null -eq $Node) { return $null }
    if ($Node -is [System.Collections.IList] -and $Node.Count -ge 4) {
        $first = $Node[0]
        if ($first -is [System.Collections.IList] -and $first.Count -ge 2 -and (Test-NumberValue $first[0]) -and (Test-NumberValue $first[1])) {
            return ,$Node
        }
        foreach ($child in $Node) {
            $ring = Find-FirstRing $child
            if ($null -ne $ring) { return ,$ring }
        }
    }
    return $null
}

function Write-PolygonSvg {
    param([Parameter(Mandatory=$true)]$Feature, [Parameter(Mandatory=$true)][string]$Path, [Parameter(Mandatory=$true)][int]$RowId, [string]$ParcelRef)
    $ring = Find-FirstRing $Feature.geometry.coordinates
    if ($null -eq $ring -or $ring.Count -lt 4) { throw "No polygon ring available for row $RowId" }
    $xs = @($ring | ForEach-Object { [double]$_[0] })
    $ys = @($ring | ForEach-Object { [double]$_[1] })
    $minX = ($xs | Measure-Object -Minimum).Minimum
    $maxX = ($xs | Measure-Object -Maximum).Maximum
    $minY = ($ys | Measure-Object -Minimum).Minimum
    $maxY = ($ys | Measure-Object -Maximum).Maximum
    $dx = [Math]::Max(($maxX - $minX), 0.000000001)
    $dy = [Math]::Max(($maxY - $minY), 0.000000001)
    $points = foreach ($p in $ring) {
        $x = 40 + (([double]$p[0] - $minX) / $dx) * 720
        $y = 760 - (([double]$p[1] - $minY) / $dy) * 720
        ('{0:0.00},{1:0.00}' -f $x, $y)
    }
    $label = [System.Security.SecurityElement]::Escape("Row $RowId / parcel $ParcelRef")
    $svg = @"
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
  <rect width="800" height="800" fill="white"/>
  <polygon points="$($points -join ' ')" fill="none" stroke="black" stroke-width="5"/>
  <text x="40" y="30" font-family="Segoe UI,Arial" font-size="20">$label</text>
</svg>
"@
    [System.IO.File]::WriteAllText($Path, $svg, [System.Text.UTF8Encoding]::new($false))
}

function Get-ImageUrls {
    param([Parameter(Mandatory=$true)][string]$Html)
    $decoded = [System.Net.WebUtility]::HtmlDecode($Html.Replace('\/','/').Replace('\u002F','/').Replace('\u002f','/'))
    $pattern = 'https?://[^"''\\\s<>]+?\.(?:jpg|jpeg|png|webp)(?:\?[^"''\\\s<>]*)?'
    $urls = [System.Collections.Generic.List[string]]::new()
    foreach ($m in [regex]::Matches($decoded, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
        $u = $m.Value.TrimEnd(')',',',';')
        if ($u -match 'logo|icon|avatar|sprite|placeholder') { continue }
        if (-not $urls.Contains($u)) { $urls.Add($u) }
    }
    return @($urls)
}

$RepoRoot = Get-RepoRoot
$AiPath = Join-Path $RepoRoot $AiRelative
$EvidenceRoot = Join-Path $RepoRoot $EvidenceRelative
$StatusPath = Join-Path $RepoRoot $StatusRelative
$ReportPath = Join-Path $RepoRoot $ReportRelative
New-Item -ItemType Directory -Force -Path $EvidenceRoot, (Split-Path $StatusPath), (Split-Path $ReportPath) | Out-Null

if (-not (Test-Path -LiteralPath $AiPath)) { throw "AI JSON missing: $AiPath" }
$health = Invoke-WebRequest -Uri 'http://127.0.0.1:8012/health' -UseBasicParsing -TimeoutSec 20
if ($health.StatusCode -ne 200) { throw "Site health failed: HTTP $($health.StatusCode)" }
$portableRoot=$RepoRoot
while($portableRoot-and(Split-Path -Leaf $portableRoot)-ne'runner_system'){$parent=Split-Path -Parent $portableRoot;if($parent-eq$portableRoot){break};$portableRoot=$parent}
$geometryPath=$null
if((Split-Path -Leaf $portableRoot)-eq'runner_system'){$portableRoot=Split-Path -Parent $portableRoot;$candidate=Join-Path $portableRoot 'AAYS\england_map_web\data\geometry_review_3of4\all_1264_real_geometry_3of4.geojson';if(Test-Path -LiteralPath $candidate){$geometryPath=$candidate}}
$featureByRow=@{}
$featureCount=0
if($geometryPath){
    $pythonCandidates=@((Join-Path $portableRoot 'runtime\python312\python.exe'),(Join-Path $portableRoot 'runtime\python\python.exe'))
    $python=$pythonCandidates|Where-Object{Test-Path -LiteralPath $_}|Select-Object -First 1
    if($python){
        $tempRoot=Join-Path $portableRoot '_portable_logs\temp';New-Item -ItemType Directory -Path $tempRoot -Force|Out-Null
        $tempPython=Join-Path $tempRoot ("ready_geometry_subset_$PID.py")
        $pythonCode=@'
import json
import sys

rows = [int(value) for value in sys.argv[2].split(",")]
with open(sys.argv[1], encoding="utf-8-sig") as handle:
    data = json.load(handle)
features = data.get("features", [])
selected = {str(index): features[index - 1] for index in rows if 0 < index <= len(features)}
print(json.dumps({"feature_count": len(features), "selected": selected}))
'@
        [IO.File]::WriteAllText($tempPython,$pythonCode,[Text.UTF8Encoding]::new($false))
        try{$geometrySubsetText=& $python $tempPython $geometryPath ($TargetRows-join',');if($LASTEXITCODE-ne0){throw 'LOCAL_GEOMETRY_SUBSET_EXTRACTION_FAILED'}}finally{Remove-Item -LiteralPath $tempPython -Force -ErrorAction SilentlyContinue}
        $geometrySubset=($geometrySubsetText-join"`n")|ConvertFrom-Json
        $featureCount=[int]$geometrySubset.feature_count
        foreach($rowId in $TargetRows){$property=$geometrySubset.selected.PSObject.Properties[[string]$rowId];if($property){$featureByRow[[int]$rowId]=$property.Value}}
    }
}
if($featureCount-lt1264){
    $geometryResponse=Invoke-WebRequest -Uri "$SiteBase/data/geometry_review_3of4/all_1264_real_geometry_3of4.geojson?v=$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())" -UseBasicParsing -TimeoutSec 180
    $geometry=$geometryResponse.Content|ConvertFrom-Json
    $featuresProperty=$geometry.PSObject.Properties['features']
    $features=if($featuresProperty){@($featuresProperty.Value)}else{@()}
    $featureCount=$features.Count
    foreach($rowId in $TargetRows){if($rowId-le$featureCount){$featureByRow[[int]$rowId]=$features[$rowId-1]}}
}
if ($featureCount -lt 1264) { throw "Canonical geometry unavailable or incomplete: $featureCount features" }
$ai = Get-Content -LiteralPath $AiPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $ai.results) { throw 'AI results array is missing.' }

$headers = @{
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
    'Accept-Language' = 'en-GB,en;q=0.9'
}
$rowOutputs = [System.Collections.Generic.List[object]]::new()
$downloadedCount = 0
$renderedCount = 0

foreach ($rowId in $TargetRows) {
    $row = @($ai.results | Where-Object { [int]$_.row_id -eq $rowId }) | Select-Object -First 1
    if ($null -eq $row) {
        $rowOutputs.Add([pscustomobject]@{row_id=$rowId; status='BLOCKED_ROW_NOT_IN_AI_RESULTS'; photos_downloaded=0; polygon_rendered=$false; visual_match_score=$null})
        continue
    }
    $feature = $featureByRow[[int]$rowId]
    $rowDirRelative = "$EvidenceRelative/row_$rowId"
    $rowDir = Join-Path $RepoRoot $rowDirRelative
    New-Item -ItemType Directory -Force -Path $rowDir | Out-Null
    $parcelRef = if ($row.parcel_ref) { [string]$row.parcel_ref } elseif ($feature.properties.matched_parcel_ref) { [string]$feature.properties.matched_parcel_ref } else { 'not_available' }
    $polygonRelative = "$rowDirRelative/canonical_polygon_row_$rowId.svg"
    $polygonPath = Join-Path $RepoRoot $polygonRelative
    $polygonOk = $false
    try {
        Write-PolygonSvg -Feature $feature -Path $polygonPath -RowId $rowId -ParcelRef $parcelRef
        $polygonOk = $true
        $renderedCount++
    } catch {
        $polygonError = $_.Exception.Message
    }

    $photoRelatives = [System.Collections.Generic.List[string]]::new()
    $sourceStatus = 'SOURCE_FETCH_NOT_RUN'
    $sourceHttp = $null
    $sourceError = $null
    try {
        $page = Invoke-WebRequest -Uri ([string]$row.listing_url) -Headers $headers -UseBasicParsing -MaximumRedirection 6 -TimeoutSec 45
        $sourceHttp = [int]$page.StatusCode
        if ($sourceHttp -lt 200 -or $sourceHttp -ge 400) { throw "Listing returned HTTP $sourceHttp" }
        $sourceStatus = 'LIVE_LISTING_OPENED'
        $imageUrls = @(Get-ImageUrls -Html ([string]$page.Content) | Select-Object -First 12)
        $photoIndex = 0
        foreach ($imageUrl in $imageUrls) {
            if ($photoIndex -ge 3) { break }
            $photoIndex++
            $ext = [System.IO.Path]::GetExtension(([uri]$imageUrl).AbsolutePath).ToLowerInvariant()
            if ($ext -notin @('.jpg','.jpeg','.png','.webp')) { $ext = '.jpg' }
            $photoRelative = "$rowDirRelative/source_photo_$photoIndex$ext"
            $photoPath = Join-Path $RepoRoot $photoRelative
            try {
                Invoke-WebRequest -Uri $imageUrl -Headers $headers -UseBasicParsing -MaximumRedirection 6 -TimeoutSec 45 -OutFile $photoPath
                $length = (Get-Item -LiteralPath $photoPath).Length
                if ($length -lt 5000) { Remove-Item -LiteralPath $photoPath -Force; continue }
                $photoRelatives.Add($photoRelative)
            } catch {
                if (Test-Path -LiteralPath $photoPath) { Remove-Item -LiteralPath $photoPath -Force }
            }
        }
        if ($photoRelatives.Count -eq 0) { $sourceStatus = 'LIVE_LISTING_OPENED_NO_DOWNLOADABLE_IMAGE_FOUND' }
    } catch {
        $sourceStatus = 'LIVE_LISTING_FETCH_BLOCKED'
        $sourceError = $_.Exception.Message
    }

    if ($photoRelatives.Count -gt 0) { $downloadedCount++ }
    $visionRelative = "$rowDirRelative/vision_evidence_manifest_row_$rowId.json"
    $visionPath = Join-Path $RepoRoot $visionRelative
    $rowStatus = if ($photoRelatives.Count -gt 0 -and $polygonOk) { 'EVIDENCE_READY_FOR_VISION_COMPARE' } else { 'VISION_PENDING_EVIDENCE_INCOMPLETE' }
    $manifest = [ordered]@{
        task_id = $TaskId
        row_id = $rowId
        parcel_ref = $parcelRef
        listing_url = [string]$row.listing_url
        source_fetch_status = $sourceStatus
        source_http_status = $sourceHttp
        source_error = $sourceError
        downloaded_photo_paths = @($photoRelatives)
        polygon_render_path = if ($polygonOk) { $polygonRelative } else { $null }
        polygon_render_error = if ($polygonOk) { $null } else { $polygonError }
        vision_status = $rowStatus
        visual_match_score = $null
        geometry_mismatch_flag = $null
        confidence_after = '3/4_source_verified_vision_pending'
        rule = 'No 3.5+ confidence without real visual comparison of downloaded evidence and canonical polygon.'
        generated_at = [DateTimeOffset]::UtcNow.ToString('o')
        final_ready = $false
        fake_data = $false
        db_write = $false
        migration = $false
        production_deploy = $false
    }
    $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $visionPath -Encoding UTF8

    Set-JsonField $row 'photo_evidence_status' $(if ($photoRelatives.Count -gt 0) { 'downloaded_real_listing_evidence' } else { 'download_blocked_or_not_found' })
    Set-JsonField $row 'downloaded_photo_path' $(if ($photoRelatives.Count -gt 0) { $photoRelatives[0] } else { $null })
    Set-JsonField $row 'downloaded_photo_paths' @($photoRelatives)
    Set-JsonField $row 'polygon_render_path' $(if ($polygonOk) { $polygonRelative } else { $null })
    Set-JsonField $row 'vision_output_path' $visionRelative
    Set-JsonField $row 'status_json_path' $StatusMirrorRelative
    Set-JsonField $row 'report_md_path' $ReportMirrorRelative
    Set-JsonField $row 'photo_boundary_visible' 'not_yet_assessed'
    Set-JsonField $row 'visual_match_score' $null
    Set-JsonField $row 'geometry_mismatch_flag' $null
    Set-JsonField $row 'confidence_after' '3/4_source_verified_vision_pending'
    Set-JsonField $row 'ai_notes' "Real listing evidence preparation status: $rowStatus. Confidence was not increased; visual comparison remains pending."

    $rowOutputs.Add([pscustomobject]@{
        row_id = $rowId
        parcel_ref = $parcelRef
        listing_url = [string]$row.listing_url
        status = $rowStatus
        source_fetch_status = $sourceStatus
        photos_downloaded = $photoRelatives.Count
        downloaded_photo_paths = @($photoRelatives)
        polygon_rendered = $polygonOk
        polygon_render_path = if ($polygonOk) { $polygonRelative } else { $null }
        vision_output_path = $visionRelative
        visual_match_score = $null
        confidence_after = '3/4_source_verified_vision_pending'
    })
}

$rowsWithEvidence = @($ai.results | Where-Object { $_.downloaded_photo_path }).Count
Set-JsonField $ai 'status' 'ROWS_1_3_REAL_EVIDENCE_PREPARED__VISION_COMPARE_PENDING'
Set-JsonField $ai 'rows_with_downloaded_photo_evidence' $rowsWithEvidence
Set-JsonField $ai 'rows_pending_vision_download' ([Math]::Max(0, 30 - $rowsWithEvidence))
Set-JsonField $ai 'rows_vision_compared' 0
Set-JsonField $ai 'rows_3_5_plus_verified' 0
Set-JsonField $ai 'last_vision_evidence_task' $TaskId
Set-JsonField $ai 'updated_at' ([DateTimeOffset]::UtcNow.ToString('o'))
Set-JsonField $ai 'final_ready' $false
$ai | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $AiPath -Encoding UTF8

$status = [ordered]@{
    task_id = $TaskId
    status = if ($downloadedCount -gt 0 -and $renderedCount -gt 0) { 'REAL_EVIDENCE_PREPARED_VISION_COMPARE_PENDING' } else { 'PARTIAL_OR_BLOCKED_EVIDENCE_PREPARATION' }
    rows_targeted = $TargetRows
    rows_targeted_count = $TargetRows.Count
    rows_with_photo_downloaded_this_run = $downloadedCount
    rows_with_polygon_render_this_run = $renderedCount
    rows_vision_compared_this_run = 0
    rows_3_5_plus_verified_this_run = 0
    rows_with_downloaded_photo_evidence_total = $rowsWithEvidence
    initial_vision_batch_total = 30
    evidence_preparation_progress_percent_of_30 = [Math]::Round(($rowsWithEvidence / 30.0) * 100, 2)
    source_verified_rows_total = 30
    geometry_rows_total = 1264
    site_visible_progress_percent = 86
    confidence_increase_applied = $false
    results = @($rowOutputs)
    generated_at = [DateTimeOffset]::UtcNow.ToString('o')
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
}
$status | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $StatusPath -Encoding UTF8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Ready To Sell - Rows 1-3 Real Evidence Preparation')
$lines.Add('')
$lines.Add("- Task: $TaskId")
$lines.Add("- Targeted rows: $($TargetRows -join ', ')")
$lines.Add("- Rows with real listing photo download this run: $downloadedCount / $($TargetRows.Count)")
$lines.Add("- Rows with canonical polygon render this run: $renderedCount / $($TargetRows.Count)")
$lines.Add('- Real vision comparisons completed this run: 0')
$lines.Add('- 3.5+ rows added this run: 0')
$lines.Add('- Confidence was not increased. Evidence paths are exposed on the 8012 site for the next visual comparison step.')
$lines.Add('')
$lines.Add('## Row results')
foreach ($r in $rowOutputs) {
    $lines.Add("- Row $($r.row_id): $($r.status); photos=$($r.photos_downloaded); polygon=$($r.polygon_rendered); source=$($r.source_fetch_status)")
}
$lines.Add('')
$lines.Add('`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($ReportPath, $lines, [System.Text.UTF8Encoding]::new($false))
$statusMirrorPath=Join-Path $RepoRoot $StatusMirrorRelative;$reportMirrorPath=Join-Path $RepoRoot $ReportMirrorRelative;New-Item -ItemType Directory -Force -Path (Split-Path -Parent $statusMirrorPath)|Out-Null;Copy-Item -LiteralPath $StatusPath -Destination $statusMirrorPath -Force;Copy-Item -LiteralPath $ReportPath -Destination $reportMirrorPath -Force
if($env:AAYS_CONTROLLER_REPO_ROOT){$publishPaths=@($AiRelative,$StatusMirrorRelative,$ReportMirrorRelative);$publishPaths+=@(Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File|ForEach-Object{$_.FullName.Substring($RepoRoot.TrimEnd('\').Length).TrimStart('\')-replace'\','/'});$publisher=Join-Path $RepoRoot 'docs/chatgpt_status/_shared/automation/PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1';& powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $RepoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths ($publishPaths-join'|') -AllowGeneratedArtifacts -SyncPortableWeb;if($LASTEXITCODE-ne0){throw'READY_TO_SELL_LIVE_CONTROLLER_PUBLISH_BLOCKED'}}

$status | ConvertTo-Json -Depth 30
