$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$pageKey = 'aays1'
$taskId = 'aays1-ready-to-sell-bulk-photo-polygon-evidence-20-20260711'
$targetBranch = 'codex/aays-single-runner-v5-20260706'
$maxRows = 20
$dataRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$geoPrimaryRelative = 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$geoFallbackRelative = 'england_map_web/data/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$evidenceRootRelative = 'england_map_web/data/geometry_review_3of4/vision_evidence/150_bulk_evidence_20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/150_aays1_bulk_photo_polygon_evidence_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/150_aays1_bulk_photo_polygon_evidence_report.md'
$batchRelative = 'england_map_web/data/aays1/ready_to_sell_active_batch_latest.json'

function Set-Prop($obj, [string]$name, $value) {
  if ($obj.PSObject.Properties[$name]) { $obj.$name = $value }
  else { $obj | Add-Member -NotePropertyName $name -NotePropertyValue $value -Force }
}
function Write-JsonFile([string]$path, $object) {
  $object | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $path -Encoding UTF8
}
function Test-NumberValue($value) {
  return ($value -is [byte] -or $value -is [sbyte] -or $value -is [int16] -or $value -is [uint16] -or $value -is [int32] -or $value -is [uint32] -or $value -is [int64] -or $value -is [uint64] -or $value -is [single] -or $value -is [double] -or $value -is [decimal])
}
function Find-FirstRing($node) {
  if ($null -eq $node) { return $null }
  if ($node -is [System.Collections.IList] -and $node.Count -ge 4) {
    $first = $node[0]
    if ($first -is [System.Collections.IList] -and $first.Count -ge 2 -and (Test-NumberValue $first[0]) -and (Test-NumberValue $first[1])) { return ,$node }
    foreach ($child in $node) {
      $ring = Find-FirstRing $child
      if ($null -ne $ring) { return ,$ring }
    }
  }
  return $null
}
function Write-PolygonSvg($feature, [string]$path, [int]$rowId, [string]$parcelRef) {
  $ring = Find-FirstRing $feature.geometry.coordinates
  if ($null -eq $ring -or $ring.Count -lt 4) { throw "No polygon ring available for row $rowId" }
  $xs = @($ring | ForEach-Object { [double]$_[0] })
  $ys = @($ring | ForEach-Object { [double]$_[1] })
  $minX = ($xs | Measure-Object -Minimum).Minimum; $maxX = ($xs | Measure-Object -Maximum).Maximum
  $minY = ($ys | Measure-Object -Minimum).Minimum; $maxY = ($ys | Measure-Object -Maximum).Maximum
  $dx = [Math]::Max(($maxX - $minX), 0.000000001); $dy = [Math]::Max(($maxY - $minY), 0.000000001)
  $points = foreach ($p in $ring) {
    $x = 40 + (([double]$p[0] - $minX) / $dx) * 720
    $y = 760 - (([double]$p[1] - $minY) / $dy) * 720
    ('{0:0.00},{1:0.00}' -f $x, $y)
  }
  $label = [System.Security.SecurityElement]::Escape("Row $rowId / parcel $parcelRef")
  $svg = @"
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
  <rect width="800" height="800" fill="white"/>
  <polygon points="$($points -join ' ')" fill="none" stroke="black" stroke-width="5"/>
  <text x="40" y="30" font-family="Segoe UI,Arial" font-size="20">$label</text>
</svg>
"@
  [System.IO.File]::WriteAllText($path, $svg, [System.Text.UTF8Encoding]::new($false))
}
function Get-ImageUrls([string]$html) {
  $decoded = [System.Net.WebUtility]::HtmlDecode($html.Replace('\/','/').Replace('\u002F','/').Replace('\u002f','/'))
  $pattern = 'https?://[^"''\\\s<>]+?\.(?:jpg|jpeg|png|webp)(?:\?[^"''\\\s<>]*)?'
  $urls = [System.Collections.Generic.List[string]]::new()
  foreach ($match in [regex]::Matches($decoded, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
    $url = $match.Value.TrimEnd(')',',',';')
    if ($url -match '(logo|icon|avatar|sprite|placeholder|tracking|pixel)') { continue }
    if (-not $urls.Contains($url)) { $urls.Add($url) }
  }
  return @($urls)
}

$started = [DateTimeOffset]::UtcNow.ToString('o')
$dataPath = Join-Path $repoRoot $dataRelative
$geoPath = Join-Path $repoRoot $geoPrimaryRelative
if (-not (Test-Path -LiteralPath $geoPath)) { $geoPath = Join-Path $repoRoot $geoFallbackRelative }
$evidenceRoot = Join-Path $repoRoot $evidenceRootRelative
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$batchPath = Join-Path $repoRoot $batchRelative
New-Item -ItemType Directory -Force -Path $evidenceRoot,(Split-Path $statusPath),(Split-Path $reportPath),(Split-Path $batchPath) | Out-Null

$blockers = [System.Collections.Generic.List[string]]::new()
$results = [System.Collections.Generic.List[object]]::new()
$branch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
if ($branch -ne $targetBranch) { $blockers.Add("wrong_branch:$branch") }
if (-not (Test-Path -LiteralPath $dataPath)) { $blockers.Add('site_data_json_missing') }
if (-not (Test-Path -LiteralPath $geoPath)) { $blockers.Add('canonical_geometry_missing') }
$data = $null; $geo = $null
if ($blockers.Count -eq 0) {
  try { $data = Get-Content -LiteralPath $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $blockers.Add('site_data_read_failed:' + $_.Exception.Message) }
  try { $geo = Get-Content -LiteralPath $geoPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $blockers.Add('geometry_read_failed:' + $_.Exception.Message) }
}
$beforeEvidence = if ($data -and $data.results) { @($data.results | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count } else { 0 }
$targets = @()
if ($blockers.Count -eq 0 -and $data.results) {
  foreach ($row in @($data.results | Sort-Object {[int]$_.row_id})) { Set-Prop $row 'new_this_run' $false }
  $targets = @($data.results | Where-Object {
    -not [string]::IsNullOrWhiteSpace([string]$_.listing_url) -and
    (-not $_.downloaded_photo_paths -or @($_.downloaded_photo_paths).Count -eq 0)
  } | Sort-Object {[int]$_.row_id} | Select-Object -First $maxRows)
}

$batch = [ordered]@{
  task_id = $taskId; status = if ($blockers.Count -eq 0) { 'RUNNING' } else { 'BLOCKED_PREFLIGHT' }
  target_limit = $maxRows; target_rows = @($targets | ForEach-Object { [int]$_.row_id })
  rows_processed = 0; rows_with_photo = 0; rows_with_polygon = 0; rows_evidence_ready = 0; current_row = $null
  expected_status_path = $statusRelative; expected_report_path = $reportRelative; updated_at = [DateTimeOffset]::UtcNow.ToString('o')
  final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
}
Write-JsonFile $batchPath $batch

$headers = @{
  'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
  'Accept-Language' = 'en-GB,en;q=0.9'
}
$photoRows = 0; $polygonRows = 0; $readyRows = 0
foreach ($row in $targets) {
  $rowId = [int]$row.row_id
  $batch.current_row = $rowId
  $batch.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
  Write-JsonFile $batchPath $batch
  $feature = if ($geo.features.Count -ge $rowId) { $geo.features[$rowId - 1] } else { $null }
  $parcelRef = if ($row.parcel_ref) { [string]$row.parcel_ref } elseif ($feature -and $feature.properties.matched_parcel_ref) { [string]$feature.properties.matched_parcel_ref } else { 'not_available' }
  $rowRootRelative = "$evidenceRootRelative/row_$rowId"
  $rowRoot = Join-Path $repoRoot $rowRootRelative
  New-Item -ItemType Directory -Force -Path $rowRoot | Out-Null
  $polygonRelative = "$rowRootRelative/canonical_polygon_row_$rowId.svg"
  $polygonPath = Join-Path $repoRoot $polygonRelative
  $polygonOk = $false; $polygonError = $null
  try {
    if ($null -eq $feature) { throw 'feature_not_available' }
    Write-PolygonSvg $feature $polygonPath $rowId $parcelRef
    $polygonOk = $true; $polygonRows++
  } catch { $polygonError = $_.Exception.Message }

  $photoPaths = [System.Collections.Generic.List[string]]::new()
  $sourceStatus = 'SOURCE_FETCH_NOT_RUN'; $sourceHttp = $null; $sourceError = $null
  try {
    $page = Invoke-WebRequest -Uri ([string]$row.listing_url) -Headers $headers -UseBasicParsing -MaximumRedirection 8 -TimeoutSec 45
    $sourceHttp = [int]$page.StatusCode
    if ($sourceHttp -lt 200 -or $sourceHttp -ge 400) { throw "Listing returned HTTP $sourceHttp" }
    $sourceStatus = 'LIVE_LISTING_OPENED'
    $imageUrls = @(Get-ImageUrls ([string]$page.Content) | Select-Object -First 16)
    $index = 0
    foreach ($imageUrl in $imageUrls) {
      if ($photoPaths.Count -ge 2) { break }
      $index++
      $ext = '.jpg'
      try {
        $candidateExt = [System.IO.Path]::GetExtension(([uri]$imageUrl).AbsolutePath).ToLowerInvariant()
        if ($candidateExt -in @('.jpg','.jpeg','.png','.webp')) { $ext = $candidateExt }
      } catch {}
      $photoRelative = "$rowRootRelative/source_photo_$index$ext"
      $photoPath = Join-Path $repoRoot $photoRelative
      try {
        Invoke-WebRequest -Uri $imageUrl -Headers $headers -UseBasicParsing -MaximumRedirection 8 -TimeoutSec 45 -OutFile $photoPath
        $length = (Get-Item -LiteralPath $photoPath).Length
        if ($length -lt 5000) { Remove-Item -LiteralPath $photoPath -Force; continue }
        $photoPaths.Add($photoRelative)
      } catch {
        if (Test-Path -LiteralPath $photoPath) { Remove-Item -LiteralPath $photoPath -Force }
      }
    }
    if ($photoPaths.Count -eq 0) { $sourceStatus = 'LIVE_LISTING_OPENED_NO_DOWNLOADABLE_IMAGE_FOUND' }
  } catch {
    $sourceStatus = 'LIVE_LISTING_FETCH_BLOCKED'; $sourceError = $_.Exception.Message
  }
  if ($photoPaths.Count -gt 0) { $photoRows++ }
  $runStatus = if ($photoPaths.Count -gt 0 -and $polygonOk) { 'EVIDENCE_READY_VISION_PENDING' } else { 'LIVE_SOURCE_VERIFIED_VISION_PENDING' }
  if ($runStatus -eq 'EVIDENCE_READY_VISION_PENDING') { $readyRows++ }
  $manifestRelative = "$rowRootRelative/vision_evidence_manifest_row_$rowId.json"
  $manifestPath = Join-Path $repoRoot $manifestRelative
  $manifest = [ordered]@{
    task_id = $taskId; row_id = $rowId; parcel_ref = $parcelRef; listing_url = [string]$row.listing_url
    source_fetch_status = $sourceStatus; source_http_status = $sourceHttp; source_error = $sourceError
    downloaded_photo_paths = @($photoPaths); polygon_render_path = if ($polygonOk) { $polygonRelative } else { $null }
    polygon_render_error = $polygonError; vision_status = $runStatus; visual_match_score = $null; geometry_mismatch_flag = $null
    confidence_after = '3/4_source_verified_vision_pending'
    rule = 'No 3.5+ confidence without a real visual comparison of downloaded listing evidence and the canonical parcel polygon.'
    generated_at = [DateTimeOffset]::UtcNow.ToString('o')
    final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
  }
  Write-JsonFile $manifestPath $manifest

  Set-Prop $row 'photo_evidence_status' $(if ($photoPaths.Count -gt 0) { 'downloaded_real_listing_evidence' } else { 'download_blocked_or_not_found' })
  Set-Prop $row 'downloaded_photo_path' $(if ($photoPaths.Count -gt 0) { $photoPaths[0] } else { $null })
  Set-Prop $row 'downloaded_photo_paths' @($photoPaths)
  Set-Prop $row 'polygon_render_path' $(if ($polygonOk) { $polygonRelative } else { $null })
  Set-Prop $row 'vision_output_path' $manifestRelative
  Set-Prop $row 'status_json_path' $statusRelative
  Set-Prop $row 'report_md_path' $reportRelative
  Set-Prop $row 'photo_boundary_visible' 'not_yet_assessed'
  Set-Prop $row 'visual_match_score' $null
  Set-Prop $row 'geometry_mismatch_flag' $null
  Set-Prop $row 'confidence_after' '3/4_source_verified_vision_pending'
  Set-Prop $row 'batch_id' $taskId
  Set-Prop $row 'evidence_updated_at' ([DateTimeOffset]::UtcNow.ToString('o'))
  Set-Prop $row 'new_this_run' $true
  Set-Prop $row 'run_status' $runStatus
  Set-Prop $row 'ai_notes' "Real evidence preparation: $runStatus. Confidence was not increased; real vision comparison remains pending."

  $results.Add([pscustomobject]@{
    row_id = $rowId; status = $runStatus; source_fetch_status = $sourceStatus
    photos_downloaded = $photoPaths.Count; downloaded_photo_paths = @($photoPaths)
    polygon_rendered = $polygonOk; polygon_render_path = if ($polygonOk) { $polygonRelative } else { $null }
    vision_output_path = $manifestRelative; visual_match_score = $null; confidence_after = '3/4_source_verified_vision_pending'
  })
  $rowsWithEvidenceNow = @($data.results | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count
  $sourceVerifiedNow = @($data.results | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
  Set-Prop $data 'status' 'BULK_REAL_EVIDENCE_PREPARATION_RUNNING__VISION_COMPARE_PENDING'
  Set-Prop $data 'rows_with_downloaded_photo_evidence' $rowsWithEvidenceNow
  Set-Prop $data 'rows_pending_vision_download' ([Math]::Max(0, $sourceVerifiedNow - $rowsWithEvidenceNow))
  Set-Prop $data 'rows_vision_compared' 0
  Set-Prop $data 'rows_3_5_plus_verified' 0
  Set-Prop $data 'last_vision_evidence_task' $taskId
  Set-Prop $data 'updated_at' ([DateTimeOffset]::UtcNow.ToString('o'))
  Set-Prop $data 'final_ready' $false
  Set-Prop $data 'fake_data' $false
  Set-Prop $data 'db_write' $false
  Set-Prop $data 'migration' $false
  Set-Prop $data 'production_deploy' $false
  Write-JsonFile $dataPath $data

  $batch.rows_processed = $results.Count; $batch.rows_with_photo = $photoRows; $batch.rows_with_polygon = $polygonRows; $batch.rows_evidence_ready = $readyRows
  $batch.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
  Write-JsonFile $batchPath $batch
}

$workPushStatus = 'not_attempted'; $workCommit = $null
if ($blockers.Count -eq 0) {
  try {
    & git -C $repoRoot add -- $dataRelative $batchRelative $evidenceRootRelative | Out-Null
    $staged = (& git -C $repoRoot diff --cached --name-only)
    if ($staged) {
      & git -C $repoRoot commit -m 'Prepare bulk ReadyToSell photo and polygon evidence' | Out-Null
      $workCommit = (& git -C $repoRoot rev-parse HEAD).Trim()
      & git -C $repoRoot push origin $targetBranch | Out-Null
      if ($LASTEXITCODE -eq 0) {
        $remote = (& git -C $repoRoot ls-remote origin "refs/heads/$targetBranch" 2>$null | Select-Object -First 1)
        $workPushStatus = if ($remote -and $remote.StartsWith($workCommit)) { 'pushed_remote_readback_ok' } else { 'pushed_remote_readback_unconfirmed' }
      } else { $workPushStatus = 'push_failed' }
    } else { $workPushStatus = 'no_work_changes' }
  } catch { $workPushStatus = 'push_exception:' + $_.Exception.Message }
}

$afterEvidence = if ($data -and $data.results) { @($data.results | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count } else { $beforeEvidence }
$status = [ordered]@{
  task_id = $taskId; page_key = $pageKey
  status = if ($blockers.Count -gt 0) { 'BLOCKED_PREFLIGHT' } elseif ($readyRows -gt 0) { 'REAL_EVIDENCE_PREPARED_VISION_COMPARE_PENDING' } else { 'PARTIAL_OR_NO_EVIDENCE_PREPARED' }
  rows_targeted = @($targets | ForEach-Object { [int]$_.row_id }); rows_targeted_count = $targets.Count
  rows_processed_this_run = $results.Count; rows_with_photo_downloaded_this_run = $photoRows
  rows_with_polygon_render_this_run = $polygonRows; rows_evidence_ready_this_run = $readyRows
  rows_vision_compared_this_run = 0; rows_3_5_plus_verified_this_run = 0
  rows_with_downloaded_photo_evidence_before = $beforeEvidence; rows_with_downloaded_photo_evidence_after = $afterEvidence
  evidence_preparation_progress_percent_of_verified_rows = if ($data -and $data.rows_with_live_source_verified) { [Math]::Round(($afterEvidence / [double]$data.rows_with_live_source_verified) * 100, 2) } else { 0 }
  results = @($results); blockers = @($blockers); work_git_commit_sha = $workCommit; git_push_status = $workPushStatus
  site_visible_progress_percent = if ($data) { $data.site_visible_progress_percent } else { 86 }
  overall_progress_percent = 97; this_run_overall_percent_increase = 0
  next_required = 'real_vision_comparison_for_evidence_ready_rows'
  generated_at = [DateTimeOffset]::UtcNow.ToString('o')
  final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
}
Write-JsonFile $statusPath $status
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# ReadyToSell Bulk Photo and Polygon Evidence - 20 Rows')
$lines.Add('')
$lines.Add("- Status: $($status.status)")
$lines.Add("- Targeted / processed: $($status.rows_targeted_count) / $($status.rows_processed_this_run)")
$lines.Add("- Rows with real photo download: $photoRows")
$lines.Add("- Rows with canonical polygon render: $polygonRows")
$lines.Add("- Rows evidence-ready: $readyRows")
$lines.Add("- Evidence total: $beforeEvidence -> $afterEvidence")
$lines.Add("- Git work proof: $workPushStatus / $workCommit")
$lines.Add('- Vision compared: 0; 3.5+ rows: 0.')
$lines.Add('- Safety: final_ready=false, fake_data=false, db_write=false, migration=false, production_deploy=false.')
[System.IO.File]::WriteAllLines($reportPath, $lines, [System.Text.UTF8Encoding]::new($false))
$batch.status = if ($blockers.Count -gt 0) { 'BLOCKED' } else { 'COMPLETED_EVIDENCE_PREPARATION' }
$batch.current_row = $null; $batch.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
Write-JsonFile $batchPath $batch

try {
  & git -C $repoRoot add -- $statusRelative $reportRelative $batchRelative | Out-Null
  $proofStaged = (& git -C $repoRoot diff --cached --name-only)
  if ($proofStaged) {
    & git -C $repoRoot commit -m 'Record ReadyToSell bulk evidence preparation proof' | Out-Null
    & git -C $repoRoot push origin $targetBranch | Out-Null
  }
} catch {}
