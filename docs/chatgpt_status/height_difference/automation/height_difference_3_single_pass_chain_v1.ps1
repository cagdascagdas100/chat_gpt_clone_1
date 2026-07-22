[CmdletBinding()]
param(
  [string]$EpochPolicy = $env:AAYS_HD3_EPOCH_POLICY,
  [ValidateRange(30,900)][int]$GitFetchTimeoutSeconds = 180,
  [ValidateRange(30,3600)][int]$ExtractTimeoutSeconds = 1200,
  [ValidateRange(30,1800)][int]$ProbeTimeoutSeconds = 300,
  [ValidateRange(30,3600)][int]$DiscoveryTimeoutSeconds = 1200,
  [ValidateRange(30,3600)][int]$ManifestTimeoutSeconds = 1800,
  [ValidateRange(30,3600)][int]$SamplingTimeoutSeconds = 1800
)

$ErrorActionPreference = 'Stop'
$rawRoot = [string]$env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($rawRoot)) { throw 'AAYS_REPO_ROOT_REQUIRED' }
$root = [System.IO.Path]::GetFullPath($rawRoot)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'AAYS_REPO_ROOT_NOT_FOUND' }
if (-not (Test-Path -LiteralPath (Join-Path $root '.git'))) { throw 'AAYS_REPO_ROOT_NOT_GIT_WORKTREE' }

$sourceBranch = 'codex/aays-single-runner-v5-20260706'
$expectedBlob = 'bb48164e7a0af78df875f30421a6a3068c43edb8'
$epochEvidenceRel = 'docs/chatgpt_status/height_difference/runner_inputs/height_difference_3_epoch_policy_latest.json'
$epochProbeRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_epoch_provenance_probe_latest.json'
$chainReportRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_chain_orchestration_latest.json'
$websiteReportRel = 'england_map_web/data/height_difference/height_difference_3_chain_orchestration_latest.json'
$watchdogReportRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_execution_watchdog_latest.json'
$watchdogWebsiteRel = 'england_map_web/data/height_difference/height_difference_3_execution_watchdog_latest.json'
$canonicalRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_canonical_points_latest.json'
$discoveryRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_official_discovery_latest.json'
$manifestRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_official_input_manifest_latest.json'
$samplingRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_boundary_raster_sampling_latest.json'
$workRel = 'docs/chatgpt_status/height_difference/runner_work/height_difference_3_execution_watchdog'

function Resolve-RepoPath([string]$Rel) {
  return (Join-Path $root ($Rel.Replace('/','\')))
}
function Read-Json([string]$Rel) {
  $path = Resolve-RepoPath $Rel
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('INPUT_NOT_FOUND:' + $Rel) }
  return (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json)
}
function Write-JsonAtomic([string]$Rel, [object]$Payload) {
  $path = Resolve-RepoPath $Rel
  $dir = Split-Path -Parent $path
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $tmp = $path + '.tmp'
  [System.IO.File]::WriteAllText($tmp, ($Payload | ConvertTo-Json -Depth 100), [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $path -Force
}
function Read-TextBounded([string]$Path, [int]$MaxChars = 200000) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return '' }
  $text = [System.IO.File]::ReadAllText($Path)
  if ($text.Length -gt $MaxChars) { return $text.Substring(0,$MaxChars) + "`n[TRUNCATED]" }
  return $text
}
function Remove-StaleSlotTemps {
  $removed = @()
  $cutoff = (Get-Date).ToUniversalTime().AddMinutes(-10)
  $dirs = @(
    (Resolve-RepoPath 'docs/chatgpt_status/height_difference/runner_outputs'),
    (Resolve-RepoPath 'england_map_web/data/height_difference')
  )
  foreach ($dir in $dirs) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { continue }
    foreach ($file in @(Get-ChildItem -LiteralPath $dir -File -Filter 'height_difference_3_*.json.tmp' -ErrorAction SilentlyContinue)) {
      if ($file.LastWriteTimeUtc -lt $cutoff) {
        Remove-Item -LiteralPath $file.FullName -Force
        $removed += $file.FullName.Substring($root.Length).TrimStart('\').Replace('\','/')
      }
    }
  }
  return @($removed)
}
function Assert-FreshOutput([string]$Rel, [datetime]$StartedUtc, [string]$Code) {
  $path = Resolve-RepoPath $Rel
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ($Code + '_OUTPUT_NOT_FOUND') }
  $item = Get-Item -LiteralPath $path
  if ($item.Length -le 1) { throw ($Code + '_OUTPUT_EMPTY') }
  if ($item.LastWriteTimeUtc -lt $StartedUtc.AddSeconds(-2)) { throw ($Code + '_OUTPUT_STALE') }
}
function Resolve-Command([string]$Name) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $cmd) { throw ('COMMAND_NOT_AVAILABLE:' + $Name) }
  return $cmd.Source
}
function Invoke-BoundedProcess {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$FilePath,
    [Parameter(Mandatory=$true)][string[]]$Arguments,
    [Parameter(Mandatory=$true)][string]$WorkingDirectory,
    [Parameter(Mandatory=$true)][int]$TimeoutSeconds
  )
  $safe = ($Name -replace '[^A-Za-z0-9_.-]','_')
  $work = Resolve-RepoPath $workRel
  New-Item -ItemType Directory -Force -Path $work | Out-Null
  $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
  $stdoutPath = Join-Path $work ($stamp + '_' + $safe + '.stdout.log')
  $stderrPath = Join-Path $work ($stamp + '_' + $safe + '.stderr.log')
  $started = (Get-Date).ToUniversalTime()
  $proc = $null
  $timedOut = $false
  $killAttempted = $false
  $killSucceeded = $false
  $exitCode = $null
  try {
    $proc = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -NoNewWindow -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $completed = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $completed) {
      $timedOut = $true
      $killAttempted = $true
      $taskkill = Get-Command taskkill.exe -ErrorAction SilentlyContinue
      if ($null -ne $taskkill) {
        & $taskkill.Source /PID $proc.Id /T /F 2>&1 | Out-Null
        $killSucceeded = $true
      } else {
        try { $proc.Kill(); $killSucceeded = $true } catch { $killSucceeded = $false }
      }
      [void]$proc.WaitForExit(15000)
    }
    if ($proc.HasExited) { $exitCode = $proc.ExitCode }
  } finally {
    if ($null -ne $proc) { $proc.Dispose() }
  }
  $completedAt = (Get-Date).ToUniversalTime()
  $stdout = Read-TextBounded $stdoutPath
  $stderr = Read-TextBounded $stderrPath
  $row = [pscustomobject]@{
    name = $Name
    file = $FilePath
    arguments = @($Arguments)
    started_at = $started.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    completed_at = $completedAt.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    duration_seconds = [math]::Round(($completedAt - $started).TotalSeconds,3)
    timeout_seconds = $TimeoutSeconds
    timed_out = $timedOut
    kill_attempted = $killAttempted
    kill_succeeded = $killSucceeded
    exit_code = $exitCode
    stdout = $stdout
    stderr = $stderr
    passed = ((-not $timedOut) -and $exitCode -eq 0)
  }
  $script:watchdogRows += $row
  if ($timedOut) { throw ('STEP_TIMEOUT:' + $Name + ':' + $TimeoutSeconds) }
  return $row
}
function Invoke-Step([string]$Name, [string]$ScriptRel, [int]$TimeoutSeconds, [string[]]$Arguments = @()) {
  $script = Resolve-RepoPath $ScriptRel
  if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw ('STEP_SCRIPT_NOT_FOUND:' + $Name) }
  $powershell = Resolve-Command 'powershell'
  $args = @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$script) + @($Arguments)
  return Invoke-BoundedProcess -Name $Name -FilePath $powershell -Arguments $args -WorkingDirectory $root -TimeoutSeconds $TimeoutSeconds
}
function Assert-Canonical([object]$Doc) {
  if (-not $Doc.acceptance.passed) { throw 'CANONICAL_ACCEPTANCE_NOT_PASSED' }
  if ($Doc.source.git_blob_sha -ne $expectedBlob) { throw 'CANONICAL_BLOB_SHA_MISMATCH' }
  if ($Doc.canonical_point_row_count -ne 3) { throw 'CANONICAL_POINT_ROW_COUNT_NOT_3' }
  $ids = @($Doc.canonical_point_rows | ForEach-Object { [string]$_.parcel_id })
  if (($ids -join ',') -ne 'parcel_61523,parcel_61524,parcel_61525') { throw 'CANONICAL_POINT_ORDER_INVALID' }
}
function Accepted-EpochEvidence([string]$RequestedPolicy) {
  $accepted = @('ETRS89_EQUIVALENCE_PROVEN','WGS84_TO_ETRS89_TRANSFORM_PROVEN')
  if (-not ($accepted -contains $RequestedPolicy)) { return $null }
  $path = Resolve-RepoPath $epochEvidenceRel
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $null }
  $doc = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  if ($doc.slot_id -ne 'height_difference_3') { return $null }
  if (-not [bool]$doc.accepted) { return $null }
  if ($doc.policy -ne $RequestedPolicy) { return $null }
  if ($doc.canonical_blob_sha -ne $expectedBlob) { return $null }
  if ($null -eq $doc.evidence_sources -or @($doc.evidence_sources).Count -lt 1) { return $null }
  return $doc
}

$startedAt = (Get-Date).ToUniversalTime()
$watchdogRows = @()
$state = 'STARTED'
$blockers = @()
$staleTempsRemoved = @()
$preflight = [ordered]@{}
$oldGitPrompt = $env:GIT_TERMINAL_PROMPT
$oldGcmInteractive = $env:GCM_INTERACTIVE
$oldLowSpeedLimit = $env:GIT_HTTP_LOW_SPEED_LIMIT
$oldLowSpeedTime = $env:GIT_HTTP_LOW_SPEED_TIME

try {
  $staleTempsRemoved = @(Remove-StaleSlotTemps)
  $git = Resolve-Command 'git'
  $powershell = Resolve-Command 'powershell'
  $pythonAvailable = ($null -ne (Get-Command python -ErrorAction SilentlyContinue)) -or ($null -ne (Get-Command py -ErrorAction SilentlyContinue)) -or ($null -ne (Get-Command python3 -ErrorAction SilentlyContinue))
  if (-not $pythonAvailable) { throw 'PYTHON_COMMAND_NOT_AVAILABLE' }
  $driveRoot = [System.IO.Path]::GetPathRoot($root)
  $drive = New-Object System.IO.DriveInfo($driveRoot)
  if ($drive.AvailableFreeSpace -lt 2147483648) { throw 'FREE_DISK_SPACE_BELOW_2_GIB' }
  $preflight.repo_root = $root
  $preflight.git = $git
  $preflight.powershell = $powershell
  $preflight.python_available = $pythonAvailable
  $preflight.free_bytes = $drive.AvailableFreeSpace
  $preflight.stale_temp_files_removed = @($staleTempsRemoved)

  $env:GIT_TERMINAL_PROMPT = '0'
  $env:GCM_INTERACTIVE = 'Never'
  $env:GIT_HTTP_LOW_SPEED_LIMIT = '1'
  $env:GIT_HTTP_LOW_SPEED_TIME = '60'

  $fetch = Invoke-BoundedProcess -Name 'historical_branch_fetch' -FilePath $git -Arguments @('fetch','--no-tags','origin',("{0}:refs/heads/{0}" -f $sourceBranch)) -WorkingDirectory $root -TimeoutSeconds $GitFetchTimeoutSeconds
  if (-not $fetch.passed) { throw 'HISTORICAL_BRANCH_FETCH_FAILED' }
  $resolve = Invoke-BoundedProcess -Name 'historical_blob_resolve' -FilePath $git -Arguments @('rev-parse',($sourceBranch + ':england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson')) -WorkingDirectory $root -TimeoutSeconds 60
  if (-not $resolve.passed) { throw 'HISTORICAL_BRANCH_BLOB_RESOLVE_FAILED' }
  $resolved = ([string]$resolve.stdout).Trim()
  if ($resolved -ne $expectedBlob) { throw ('HISTORICAL_BRANCH_BLOB_MISMATCH:' + $resolved) }

  $stepStarted = (Get-Date).ToUniversalTime()
  $extract = Invoke-Step 'canonical_point_extract' 'docs/chatgpt_status/height_difference/automation/height_difference_3_extract_canonical_points_v1_1.ps1' $ExtractTimeoutSeconds
  if (-not $extract.passed) { throw 'CANONICAL_POINT_EXTRACT_FAILED' }
  Assert-FreshOutput $canonicalRel $stepStarted 'CANONICAL_POINT'
  $canonical = Read-Json $canonicalRel
  Assert-Canonical $canonical

  $stepStarted = (Get-Date).ToUniversalTime()
  $probe = Invoke-Step 'epoch_provenance_probe' 'docs/chatgpt_status/height_difference/automation/height_difference_3_epoch_provenance_probe_v1.ps1' $ProbeTimeoutSeconds
  if (-not $probe.passed) { throw 'EPOCH_PROVENANCE_PROBE_FAILED' }
  Assert-FreshOutput $epochProbeRel $stepStarted 'EPOCH_PROVENANCE_PROBE'

  $epochEvidence = Accepted-EpochEvidence $EpochPolicy
  if ($null -eq $epochEvidence) {
    $state = 'BLOCKED_EPOCH_PROVENANCE'
    $blockers += 'CANONICAL_POINT_CRS_EPOCH_PROVENANCE_NOT_CONFIRMED'
  } else {
    $stepStarted = (Get-Date).ToUniversalTime()
    $discovery = Invoke-Step 'official_discovery' 'docs/chatgpt_status/height_difference/automation/height_difference_3_post_point_official_discovery_v1.ps1' $DiscoveryTimeoutSeconds @('-EpochPolicy',$EpochPolicy)
    if (-not $discovery.passed) { throw 'OFFICIAL_DISCOVERY_FAILED' }
    Assert-FreshOutput $discoveryRel $stepStarted 'OFFICIAL_DISCOVERY'

    $stepStarted = (Get-Date).ToUniversalTime()
    $manifest = Invoke-Step 'official_input_manifest' 'docs/chatgpt_status/height_difference/automation/height_difference_3_official_input_manifest_v1.ps1' $ManifestTimeoutSeconds
    if (-not $manifest.passed) { throw 'OFFICIAL_INPUT_MANIFEST_FAILED' }
    Assert-FreshOutput $manifestRel $stepStarted 'OFFICIAL_INPUT_MANIFEST'

    $stepStarted = (Get-Date).ToUniversalTime()
    $sampling = Invoke-Step 'boundary_raster_sampling' 'docs/chatgpt_status/height_difference/automation/height_difference_3_boundary_raster_sampling_v1.ps1' $SamplingTimeoutSeconds
    if (-not $sampling.passed) { throw 'BOUNDARY_RASTER_SAMPLING_FAILED' }
    Assert-FreshOutput $samplingRel $stepStarted 'BOUNDARY_RASTER_SAMPLING'
    $state = 'CHAIN_EXECUTION_PASS_NONFINAL'
  }
} catch {
  $state = 'CHAIN_EXECUTION_BLOCKED'
  $blockers += $_.Exception.Message
} finally {
  $env:GIT_TERMINAL_PROMPT = $oldGitPrompt
  $env:GCM_INTERACTIVE = $oldGcmInteractive
  $env:GIT_HTTP_LOW_SPEED_LIMIT = $oldLowSpeedLimit
  $env:GIT_HTTP_LOW_SPEED_TIME = $oldLowSpeedTime
}

$completedAt = (Get-Date).ToUniversalTime()
$watchdog = [ordered]@{
  schema_version = 1
  slot_id = 'height_difference_3'
  task_id = 'height-difference-3-execution-watchdog-v1-20260722'
  started_at = $startedAt.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
  completed_at = $completedAt.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
  duration_seconds = [math]::Round(($completedAt - $startedAt).TotalSeconds,3)
  state = $state
  preflight = $preflight
  process_rows = @($watchdogRows)
  timeout_count = @($watchdogRows | Where-Object { $_.timed_out }).Count
  killed_process_tree_count = @($watchdogRows | Where-Object { $_.kill_succeeded }).Count
  stale_temp_files_removed = @($staleTempsRemoved)
  blockers = @($blockers | Select-Object -Unique)
  actual_business_data_rows_written = 0
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
}
$report = [ordered]@{
  schema_version = 3
  slot_id = 'height_difference_3'
  task_id = 'height-difference-3-single-pass-chain-v1-2-20260722'
  started_at = $startedAt.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
  completed_at = $completedAt.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
  state = $state
  source_branch = $sourceBranch
  expected_blob_sha = $expectedBlob
  epoch_policy_requested = $EpochPolicy
  epoch_evidence_path = $epochEvidenceRel
  epoch_provenance_probe_path = $epochProbeRel
  execution_watchdog_path = $watchdogReportRel
  steps = @($watchdogRows)
  blockers = @($blockers | Select-Object -Unique)
  canonical_point_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $canonicalRel))
  epoch_provenance_probe_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $epochProbeRel))
  official_discovery_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $discoveryRel))
  official_input_manifest_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $manifestRel))
  boundary_raster_sampling_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $samplingRel))
  output_semantics = 'SINGLE_SHARED_RUNNER_SEQUENTIAL_CHAIN_WITH_BOUNDED_PROCESS_WATCHDOG_AND_FRESH_OUTPUT_GATES_NONFINAL'
  actual_business_data_rows_written = 0
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
}
Write-JsonAtomic $watchdogReportRel $watchdog
Write-JsonAtomic $watchdogWebsiteRel $watchdog
Write-JsonAtomic $chainReportRel $report
Write-JsonAtomic $websiteReportRel $report
Write-Host ('HEIGHT_DIFFERENCE_3_CHAIN_STATE=' + $state)
Write-Host ('HEIGHT_DIFFERENCE_3_CHAIN_STEPS=' + @($watchdogRows).Count)
Write-Host ('HEIGHT_DIFFERENCE_3_TIMEOUT_COUNT=' + $watchdog.timeout_count)
Write-Host 'FINAL_READY=false'

if ($state -eq 'CHAIN_EXECUTION_BLOCKED') { exit 2 }
exit 0
