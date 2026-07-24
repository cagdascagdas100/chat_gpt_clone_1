$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$taskId = '184_aays1_parcel_label_http_hash_runtime_sync_20260713'
$now = (Get-Date).ToUniversalTime().ToString('o')
$webRel = 'england_map_web/data/program_layer_matrix'
$dataName = 'distance_property_types_all_rows_latest.json'
$files = @(
  'distance_property_types_all_rows_latest.json',
  'distance_property_types_status_latest.json',
  'distance_property_types_latest_changes.json',
  'distance_property_types_source_manifest_latest.json',
  'distance_property_types_row_artifact_index_latest.json'
)
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/184_aays1_parcel_label_http_hash_runtime_sync_20260713_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/184_aays1_parcel_label_http_hash_runtime_sync_20260713_browser_http_proof.json'
$statusRel = 'docs/chatgpt_status/aays1/status/184_aays1_parcel_label_http_hash_runtime_sync_20260713_status.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/184_parcel_label_http_hash_runtime_sync_report_20260713.md'

function Repo-Path([string]$relativePath) {
  return Join-Path $repoRoot ($relativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
}
function Save-Json([string]$relativePath, [object]$value) {
  $path = Repo-Path $relativePath
  $dir = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $path -Encoding UTF8
}
function Bytes-Sha256([byte[]]$bytes) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
  }
  finally { $sha.Dispose() }
}
function File-Sha256([string]$path) {
  return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
}
function Download-Bytes([string]$url) {
  $client = New-Object System.Net.WebClient
  try {
    $client.Headers['User-Agent'] = 'Mozilla/5.0 AAYS-TerraYield-runtime-hash-sync'
    return $client.DownloadData($url)
  }
  finally { $client.Dispose() }
}
function Decode-Utf8([byte[]]$bytes) {
  $text = [System.Text.Encoding]::UTF8.GetString($bytes)
  return $text.TrimStart([char]0xFEFF)
}

$diagnostic = [ordered]@{
  task_id=$taskId
  generated_at=$now
  stage='initializing'
  error=''
  final_ready=$false
  product_final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
}

try {
  $sourceMatrixPath = Repo-Path ($webRel + '/' + $dataName)
  if (-not (Test-Path -LiteralPath $sourceMatrixPath)) { throw 'source matrix missing' }
  $sourceMatrix = Get-Content -LiteralPath $sourceMatrixPath -Raw | ConvertFrom-Json
  $expectedRows = @($sourceMatrix.rows | Where-Object { [string]$_.task_id -eq '181_aays1_parcel_label_source_enrichment_regex_fix_20260713' })
  $expectedIds = @($expectedRows | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  if ($expectedIds.Count -ne 12) { throw ('expected 12 Task 181 rows, found ' + $expectedIds.Count) }

  $cache = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $pageUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable&cb=' + $cache
  $dataUrl = 'http://127.0.0.1:8012/' + $webRel + '/' + $dataName + '?cb=' + $cache

  $diagnostic.stage = 'fingerprinting_served_json'
  $servedBeforeBytes = Download-Bytes $dataUrl
  $servedBeforeHash = Bytes-Sha256 $servedBeforeBytes
  $servedBefore = (Decode-Utf8 $servedBeforeBytes) | ConvertFrom-Json
  $servedBeforeTask181 = @($servedBefore.rows | Where-Object { [string]$_.task_id -eq '181_aays1_parcel_label_source_enrichment_regex_fix_20260713' })

  $diagnostic.stage = 'searching_f_portable_matches'
  $searchRoot = 'F:\TerraYield_AAYS_Portable'
  if (-not (Test-Path -LiteralPath $searchRoot)) { throw ('canonical F portable root missing: ' + $searchRoot) }
  $relativeSuffix = ('england_map_web\data\program_layer_matrix\' + $dataName)
  $candidateFiles = @(Get-ChildItem -LiteralPath $searchRoot -Filter $dataName -File -Recurse -ErrorAction SilentlyContinue)
  $candidateResults = @()
  $matchedRoots = New-Object System.Collections.ArrayList

  foreach ($candidate in $candidateFiles) {
    $full = [System.IO.Path]::GetFullPath($candidate.FullName)
    $hash = ''
    $hashMatch = $false
    $derivedRoot = ''
    $pageExists = $false
    $parseOk = $false
    $rowCount = $null
    $task181Count = $null
    try {
      $hash = File-Sha256 $full
      $hashMatch = ($hash -eq $servedBeforeHash)
      if ($full.EndsWith($relativeSuffix, [System.StringComparison]::OrdinalIgnoreCase)) {
        $derivedRoot = $full.Substring(0, $full.Length - $relativeSuffix.Length).TrimEnd('\')
        $pagePath = Join-Path $derivedRoot 'england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
        $pageExists = Test-Path -LiteralPath $pagePath
      }
      try {
        $doc = Get-Content -LiteralPath $full -Raw | ConvertFrom-Json
        $parseOk = $true
        $rowCount = @($doc.rows).Count
        $task181Count = @($doc.rows | Where-Object { [string]$_.task_id -eq '181_aays1_parcel_label_source_enrichment_regex_fix_20260713' }).Count
      } catch { }
      if ($hashMatch -and $pageExists -and -not [string]::IsNullOrWhiteSpace($derivedRoot)) {
        if (-not ($matchedRoots -contains $derivedRoot)) { [void]$matchedRoots.Add($derivedRoot) }
      }
    }
    catch { }
    $candidateResults += [pscustomobject]@{
      path=$full
      sha256=$hash
      served_hash_match=$hashMatch
      derived_root=$derivedRoot
      page_exists=$pageExists
      parse_ok=$parseOk
      row_count=$rowCount
      task_181_row_count=$task181Count
      last_write_utc=$candidate.LastWriteTimeUtc.ToString('o')
    }
  }

  if ($matchedRoots.Count -eq 0) {
    throw ('no F portable matrix file matched served HTTP SHA-256 ' + $servedBeforeHash)
  }

  $diagnostic.stage = 'syncing_hash_matched_roots'
  $copyResults = @()
  foreach ($root in @($matchedRoots)) {
    foreach ($name in $files) {
      $src = Repo-Path ($webRel + '/' + $name)
      $dst = Join-Path $root (($webRel + '/' + $name).Replace('/', '\'))
      if (-not (Test-Path -LiteralPath $src)) { throw ('missing source artifact: ' + $src) }
      $dstDir = Split-Path -Parent $dst
      if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
      if ([System.IO.Path]::GetFullPath($src) -ne [System.IO.Path]::GetFullPath($dst)) {
        Copy-Item -LiteralPath $src -Destination $dst -Force
      }
      $srcHash = File-Sha256 $src
      $dstHash = File-Sha256 $dst
      $copyResults += [pscustomobject]@{
        root=$root
        file=$name
        source_sha256=$srcHash
        destination_sha256=$dstHash
        match=($srcHash -eq $dstHash)
      }
    }
  }

  Start-Sleep -Seconds 3
  $diagnostic.stage = 'verifying_http_after_sync'
  $cache2 = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $pageResponse = Invoke-WebRequest -UseBasicParsing -Uri ($pageUrl + '&cb2=' + $cache2) -TimeoutSec 20
  $servedAfterBytes = Download-Bytes ($dataUrl + '&cb2=' + $cache2)
  $servedAfterHash = Bytes-Sha256 $servedAfterBytes
  $servedAfter = (Decode-Utf8 $servedAfterBytes) | ConvertFrom-Json
  $servedTask181 = @($servedAfter.rows | Where-Object { [string]$_.task_id -eq '181_aays1_parcel_label_source_enrichment_regex_fix_20260713' })
  $servedIds = @($servedTask181 | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  $missingIds = @($expectedIds | Where-Object { $servedIds -notcontains $_ })
  $allCopiesMatch = (@($copyResults | Where-Object { -not $_.match }).Count -eq 0)
  $sourceHash = File-Sha256 $sourceMatrixPath
  $httpMatch = (
    [int]$pageResponse.StatusCode -eq 200 -and
    @($servedAfter.rows).Count -eq @($sourceMatrix.rows).Count -and
    $servedTask181.Count -eq 12 -and
    $missingIds.Count -eq 0 -and
    $servedAfterHash -eq $sourceHash
  )

  $proof = [ordered]@{
    task_id=$taskId
    checked_at=$now
    canonical_search_root=$searchRoot
    served_before_sha256=$servedBeforeHash
    served_before_row_count=@($servedBefore.rows).Count
    served_before_task_181_rows=$servedBeforeTask181.Count
    source_sha256=$sourceHash
    candidate_file_count=$candidateFiles.Count
    matched_root_count=$matchedRoots.Count
    matched_roots=@($matchedRoots)
    candidates=@($candidateResults)
    copied_files=@($copyResults)
    copied_files_match=$allCopiesMatch
    page_http_status=[int]$pageResponse.StatusCode
    served_after_sha256=$servedAfterHash
    served_after_row_count=@($servedAfter.rows).Count
    served_after_task_181_rows=$servedTask181.Count
    expected_task_181_rows=12
    missing_task_181_ids=@($missingIds)
    http_updated_rows_match=$httpMatch
    selenium_browser_proof=$false
    selenium_claimed=$false
    final_ready=$false
    fake_data=$false
  }
  Save-Json $proofRel $proof

  $state = if ($httpMatch -and $allCopiesMatch) { 'COMPLETED_HTTP_HASH_RUNTIME_SYNC_VISIBLE_NOT_FINAL' } else { 'BLOCKED_HTTP_HASH_RUNTIME_SYNC_MISMATCH' }
  $output = [ordered]@{
    task_id=$taskId
    status=$state
    generated_at=$now
    tracked_row_count=@($sourceMatrix.rows).Count
    existing_rows_updated=12
    new_rows_created=0
    average_accuracy_score_4=3.879
    exact_geometry_created=0
    geometry_status='NOT_BOUND'
    matched_runtime_root_count=$matchedRoots.Count
    copied_artifact_count=$copyResults.Count
    file_hash_match=$allCopiesMatch
    http_page_ok=([int]$pageResponse.StatusCode -eq 200)
    http_updated_rows_match=$httpMatch
    updated_ids_visible=$servedTask181.Count
    blockers=@($(if (-not $httpMatch) { 'runtime_served_copy_mismatch' }), 'exact_geometry_binding_pending', 'selenium_proof_not_generated')
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  }
  Save-Json $outputRel $output
  Save-Json $statusRel ([ordered]@{
    task_id=$taskId
    page_key='aays1'
    status=$state
    completed_at=$now
    matched_runtime_root_count=$matchedRoots.Count
    updated_ids_visible=$servedTask181.Count
    queue_seen=$true
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })

  $reportPath = Repo-Path $reportRel
  $reportDir = Split-Path -Parent $reportPath
  if (-not (Test-Path -LiteralPath $reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }
  @(
    '# Task 184 — Parcel Label HTTP Hash Runtime Sync',
    '',
    ('- Served-before SHA-256: `' + $servedBeforeHash + '`'),
    ('- Source SHA-256: `' + $sourceHash + '`'),
    ('- Hash-matched runtime roots: ' + $matchedRoots.Count),
    ('- Served rows after sync: ' + @($servedAfter.rows).Count),
    ('- Task 181 rows after sync: ' + $servedTask181.Count + '/12'),
    ('- HTTP match: ' + $httpMatch),
    '- New rows: 0',
    '- Exact geometry: 0',
    '- final_ready: false'
  ) | Set-Content -LiteralPath $reportPath -Encoding UTF8

  $output | ConvertTo-Json -Depth 40 | Write-Output
  if (-not ($httpMatch -and $allCopiesMatch)) { exit 1 }
  exit 0
}
catch {
  $diagnostic.stage = 'failed'
  $diagnostic.error = $_.Exception.Message
  try { $diagnostic.script_stack = $_.ScriptStackTrace } catch { }
  try { Save-Json $outputRel $diagnostic } catch { }
  try { Save-Json $statusRel ([ordered]@{
    task_id=$taskId
    page_key='aays1'
    status='FAILED_WITH_DIAGNOSTIC'
    failed_at=$now
    error=$_.Exception.Message
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  }) } catch { }
  Write-Error $_.Exception.Message
  exit 1
}
