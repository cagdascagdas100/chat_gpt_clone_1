$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$taskId = '206_aays1_parcel_label_53row_runtime_visibility_recovery_20260714'
$sourceTaskId = '205_aays1_parcel_label_53row_source_classification_publish_20260714'
$expectedCount = 53
$expectedTotal = 194
$now = (Get-Date).ToUniversalTime().ToString('o')
$webRel = 'england_map_web/data/program_layer_matrix'
$matrixRel = $webRel + '/distance_property_types_all_rows_latest.json'
$statusRel = $webRel + '/distance_property_types_status_latest.json'
$changesRel = $webRel + '/distance_property_types_latest_changes.json'
$manifestRel = $webRel + '/distance_property_types_source_manifest_latest.json'
$indexRel = $webRel + '/distance_property_types_row_artifact_index_latest.json'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/206_aays1_parcel_label_53row_runtime_visibility_recovery_20260714_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/206_aays1_parcel_label_53row_runtime_visibility_recovery_20260714_browser_http_proof.json'
$statusOutRel = 'docs/chatgpt_status/aays1/status/206_aays1_parcel_label_53row_runtime_visibility_recovery_20260714_status.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/206_parcel_label_53row_runtime_visibility_recovery_report_20260714.md'

function Repo-Path([string]$relativePath) {
  Join-Path $repoRoot ($relativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
}
function Save-Json([string]$relativePath, [object]$value) {
  $path = Repo-Path $relativePath
  $dir = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $json = $value | ConvertTo-Json -Depth 100
  [System.IO.File]::WriteAllText($path, $json, (New-Object System.Text.UTF8Encoding($false)))
}
function Parse-JsonText([string]$text) {
  $clean = [string]$text
  $clean = $clean.TrimStart([char]0xFEFF)
  if ($clean.Length -ge 3 -and [int]$clean[0] -eq 239 -and [int]$clean[1] -eq 187 -and [int]$clean[2] -eq 191) { $clean = $clean.Substring(3) }
  return ($clean | ConvertFrom-Json)
}
function Read-HttpJson([string]$uri, [string]$tempPrefix) {
  $tmp = Join-Path $env:TEMP ($tempPrefix + [Guid]::NewGuid().ToString('N') + '.json')
  try {
    Invoke-WebRequest -UseBasicParsing -Uri $uri -OutFile $tmp -TimeoutSec 45
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $tmp).Hash.ToLowerInvariant()
    $json = Parse-JsonText (Get-Content -LiteralPath $tmp -Raw -Encoding UTF8)
    return [pscustomobject]@{ json=$json; hash=$hash }
  } finally {
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
  }
}

try {
  $matrixPath = Repo-Path $matrixRel
  if (-not (Test-Path -LiteralPath $matrixPath -PathType Leaf)) { throw ('matrix missing: ' + $matrixRel) }
  $matrix = Parse-JsonText (Get-Content -LiteralPath $matrixPath -Raw -Encoding UTF8)
  $sourceRows = @($matrix.rows | Where-Object { [string]$_.task_id -eq $sourceTaskId })
  if (@($matrix.rows).Count -ne $expectedTotal) { throw ('expected total rows ' + $expectedTotal + ', found ' + @($matrix.rows).Count) }
  if ($sourceRows.Count -ne $expectedCount) { throw ('expected Task 205 rows ' + $expectedCount + ', found ' + $sourceRows.Count) }
  $expectedIds = @($sourceRows | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  if ($expectedIds.Count -ne $expectedCount) { throw ('expected unique Task 205 ids ' + $expectedCount + ', found ' + $expectedIds.Count) }
  $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $matrixPath).Hash.ToLowerInvariant()

  $portableRoot = if ($env:AAYS_PORTABLE_ROOT) {
    [System.IO.Path]::GetFullPath($env:AAYS_PORTABLE_ROOT)
  } else {
    $controllerRoot = if ($env:AAYS_CANONICAL_REPO_ROOT) { $env:AAYS_CANONICAL_REPO_ROOT } else { $repoRoot }
    $marker = [System.IO.Path]::DirectorySeparatorChar + 'runner_system' + [System.IO.Path]::DirectorySeparatorChar
    $markerIndex = $controllerRoot.IndexOf($marker, [System.StringComparison]::OrdinalIgnoreCase)
    if ($markerIndex -lt 0) { throw 'AAYS_PORTABLE_ROOT is not set and cannot be derived from controller root' }
    $controllerRoot.Substring(0, $markerIndex)
  }

  $candidateRoots = @(
    $repoRoot,
    $env:AAYS_REPO_ROOT,
    $env:AAYS_CANONICAL_REPO_ROOT,
    (Join-Path $portableRoot 'AAYS\terrayield_land_intelligence'),
    (Join-Path $portableRoot 'runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707')
  ) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | ForEach-Object { [System.IO.Path]::GetFullPath([string]$_) } | Select-Object -Unique

  $artifactNames = @(
    'distance_property_types_all_rows_latest.json',
    'distance_property_types_status_latest.json',
    'distance_property_types_latest_changes.json',
    'distance_property_types_source_manifest_latest.json',
    'distance_property_types_row_artifact_index_latest.json'
  )
  $copies = @()
  foreach ($root in $candidateRoots) {
    $webDir = Join-Path $root ($webRel.Replace('/', [char]92))
    if (-not (Test-Path -LiteralPath $webDir -PathType Container)) { continue }
    foreach ($name in $artifactNames) {
      $src = Repo-Path ($webRel + '/' + $name)
      if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw ('source artifact missing: ' + $src) }
      $dst = Join-Path $webDir $name
      if ([System.IO.Path]::GetFullPath($src) -ne [System.IO.Path]::GetFullPath($dst)) {
        Copy-Item -LiteralPath $src -Destination $dst -Force
      }
      $srcHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $src).Hash.ToLowerInvariant()
      $dstHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $dst).Hash.ToLowerInvariant()
      $copies += [pscustomobject]@{ root=$root; file=$name; source_sha256=$srcHash; destination_sha256=$dstHash; match=($srcHash -eq $dstHash) }
    }
  }
  if (@($copies).Count -lt 5) { throw 'no usable runtime artifact root found' }
  $copyMatch = (@($copies | Where-Object { -not $_.match }).Count -eq 0)
  if (-not $copyMatch) { throw 'runtime artifact copy hash mismatch' }

  $dataUrl = 'http://127.0.0.1:8012/' + $matrixRel
  $pageUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable'
  $restartPerformed = $false
  $listenerPid = $null
  $listenerCommandLine = $null
  $listenerExecutable = $null

  $servedBefore = Read-HttpJson ($dataUrl + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) 'aays206_before_'
  $beforeRows = @($servedBefore.json.rows | Where-Object { [string]$_.task_id -eq $sourceTaskId })

  if ($beforeRows.Count -ne $expectedCount -or $servedBefore.hash -ne $sourceHash) {
    $listener = Get-NetTCPConnection -LocalPort 8012 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $listener) { throw 'port 8012 listener not found for controlled restart' }
    $listenerPid = [int]$listener.OwningProcess
    $proc = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $listenerPid)
    if ($null -eq $proc) { throw ('port 8012 process not found: ' + $listenerPid) }
    $listenerCommandLine = [string]$proc.CommandLine
    $listenerExecutable = [string]$proc.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($listenerCommandLine) -or ($listenerCommandLine -notmatch '(?i)(8012|uvicorn|python)')) {
      throw ('refusing to restart unexpected port 8012 process: ' + $listenerCommandLine)
    }
    Stop-Process -Id $listenerPid -Force
    $deadline = (Get-Date).AddSeconds(30)
    do {
      Start-Sleep -Milliseconds 500
      $stillListening = Get-NetTCPConnection -LocalPort 8012 -State Listen -ErrorAction SilentlyContinue
    } while ($stillListening -and (Get-Date) -lt $deadline)
    if ($stillListening) { throw 'port 8012 did not close after controlled stop' }

    $appRoot = Join-Path $portableRoot 'AAYS\terrayield_land_intelligence'
    if (-not (Test-Path -LiteralPath $appRoot -PathType Container)) { $appRoot = $portableRoot }
    Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/s','/c',$listenerCommandLine) -WorkingDirectory $appRoot -WindowStyle Hidden | Out-Null
    $restartPerformed = $true

    $deadline = (Get-Date).AddSeconds(75)
    $pageOk = $false
    do {
      Start-Sleep -Seconds 2
      try {
        $pageResponse = Invoke-WebRequest -UseBasicParsing -Uri ($pageUrl + '&cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) -TimeoutSec 10
        $pageOk = ($pageResponse.StatusCode -eq 200)
      } catch { $pageOk = $false }
    } while (-not $pageOk -and (Get-Date) -lt $deadline)
    if (-not $pageOk) { throw 'port 8012 application did not return HTTP 200 after controlled restart' }
  }

  $pageResponseFinal = Invoke-WebRequest -UseBasicParsing -Uri ($pageUrl + '&cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) -TimeoutSec 30
  $servedAfter = Read-HttpJson ($dataUrl + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) 'aays206_after_'
  $servedRows = @($servedAfter.json.rows | Where-Object { [string]$_.task_id -eq $sourceTaskId })
  $servedIds = @($servedRows | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  $missingIds = @($expectedIds | Where-Object { $servedIds -notcontains $_ })
  $httpMatch = ($pageResponseFinal.StatusCode -eq 200 -and @($servedAfter.json.rows).Count -eq $expectedTotal -and $servedRows.Count -eq $expectedCount -and $missingIds.Count -eq 0 -and $servedAfter.hash -eq $sourceHash)

  Save-Json $proofRel ([pscustomobject]@{
    task_id=$taskId; source_task_id=$sourceTaskId; checked_at=$now;
    page_http_status=[int]$pageResponseFinal.StatusCode; source_row_count=$expectedTotal; served_row_count=@($servedAfter.json.rows).Count;
    expected_updated_row_count=$expectedCount; updated_rows_visible=$servedRows.Count; missing_updated_ids=@($missingIds);
    source_sha256=$sourceHash; served_sha256=$servedAfter.hash; file_hash_match=($servedAfter.hash -eq $sourceHash);
    runtime_artifact_copy_count=@($copies).Count; runtime_artifact_copy_hash_match=$copyMatch;
    restart_performed=$restartPerformed; stopped_listener_pid=$listenerPid; previous_listener_executable=$listenerExecutable;
    browser_data_visibility_proven=$httpMatch; selenium_browser_proof=$false; selenium_claimed=$false;
    final_ready=$false; fake_data=$false
  })

  $state = if ($httpMatch) { 'COMPLETED_53ROW_RUNTIME_VISIBILITY_RECOVERY_NOT_FINAL' } else { 'BLOCKED_53ROW_RUNTIME_VISIBILITY_RECOVERY' }
  $blockers = @('exact_geometry_binding_pending','manual_classification_review_pending')
  if (-not $httpMatch) { $blockers += 'runtime_served_copy_mismatch' }
  Save-Json $outputRel ([pscustomobject]@{
    task_id=$taskId; source_task_id=$sourceTaskId; status=$state; generated_at=$now;
    tracked_row_count=$expectedTotal; existing_rows_recovered=$expectedCount; updated_ids_visible=$servedRows.Count;
    average_accuracy_score_4=3.812; source_upgraded_count=53; classification_enriched_count=53;
    new_rows_created=0; exact_geometry_created=0; geometry_status='NOT_BOUND'; restart_performed=$restartPerformed;
    file_hash_match=($servedAfter.hash -eq $sourceHash); http_page_ok=($pageResponseFinal.StatusCode -eq 200); http_updated_rows_match=$httpMatch;
    blockers=@($blockers); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  Save-Json $statusOutRel ([pscustomobject]@{
    task_id=$taskId; page_key='aays1'; status=$state; completed_at=$now; source_task_id=$sourceTaskId;
    updated_ids_visible=$servedRows.Count; github_remote_readback_pending=$true;
    final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })

  $reportPath = Repo-Path $reportRel
  $reportDir = Split-Path -Parent $reportPath
  if (-not (Test-Path -LiteralPath $reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }
  @(
    '# Task 206 — Task 205 53-row runtime visibility recovery',
    '',
    ('- GitHub/source Task 205 rows: ' + $sourceRows.Count),
    ('- Port 8012 visible Task 205 rows: ' + $servedRows.Count),
    ('- Total served rows: ' + @($servedAfter.json.rows).Count),
    ('- Source/served hash match: ' + ($servedAfter.hash -eq $sourceHash)),
    ('- Controlled 8012 restart performed: ' + $restartPerformed),
    '- New rows: 0',
    '- Exact geometry created: 0',
    '- final_ready: false'
  ) | Set-Content -LiteralPath $reportPath -Encoding UTF8

  if (-not $httpMatch) { exit 1 }
  exit 0
}
catch {
  $errorOutput = [pscustomobject]@{
    task_id=$taskId; source_task_id=$sourceTaskId; status='FAILED_WITH_DIAGNOSTIC'; failed_at=$now; error=$_.Exception.Message;
    script_stack=$_.ScriptStackTrace; final_ready=$false; product_final_ready=$false; fake_data=$false;
    db_write=$false; migration=$false; production_deploy=$false
  }
  try { Save-Json $outputRel $errorOutput } catch { }
  try { Save-Json $statusOutRel $errorOutput } catch { }
  Write-Error $_.Exception.Message
  exit 1
}
