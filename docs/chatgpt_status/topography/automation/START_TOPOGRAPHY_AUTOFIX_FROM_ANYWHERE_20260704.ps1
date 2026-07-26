param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RepoUrl = 'https://github.com/cagdascagdas100/chat_gpt_clone_1.git',
  [string]$Branch = 'main',
  [int]$StaleMinutes = 20,
  [switch]$ForcePullWhenDirty
)

$ErrorActionPreference = 'Stop'
$mutexName = 'AAYS_TOPOGRAPHY_SINGLE_RUNNER_20260704'
$requiredCsvHeader = 'parcel_id,parcel_ref,elevation_sea_level_m,regional_average_elevation_m,elevation_difference_regional_average_m,elevation_class,color_category,confidence_rating,confidence_percent,source,source_url,source_date,matching_method,calculation_explanation,accuracy_score_4,needs_manual_review,changed_in_latest_run'

function Full-Path([string]$Path) { return [System.IO.Path]::GetFullPath($Path) }
function Is-FDrive([string]$Path) { return (Full-Path $Path).ToUpperInvariant().StartsWith('F:\') }
function Ensure-Dir([string]$Path) { if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Path, [string]$Content) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}
function To-Json([object]$Obj) { return ($Obj | ConvertTo-Json -Depth 16) }

$RepoRoot = Full-Path $RepoRoot
if (-not (Test-Path -LiteralPath 'F:\')) { throw 'F drive not found. Topography runner is F-disk only.' }
if (-not (Is-FDrive $RepoRoot)) { throw "Topography runner refused non-F repo root: $RepoRoot" }

$logDir = Join-Path $RepoRoot 'docs\chatgpt_status\topography\logs'
$logPath = Join-Path $logDir 'topography_autofix_latest_20260704.log'
$stateDir = Join-Path $RepoRoot 'docs\chatgpt_status\topography\runner_state'
$heartbeatDir = Join-Path $RepoRoot 'docs\chatgpt_status\topography\heartbeat'
$runnerStatePath = Join-Path $stateDir 'topography_single_runner_state_20260704.json'
$heartbeatPath = Join-Path $heartbeatDir 'topography_single_runner_heartbeat_latest_20260704.json'

function Log([string]$Message) {
  $line = ((Get-Date).ToString('s') + ' ' + $Message)
  Write-Host $line
  if (Test-Path -LiteralPath $logDir) { Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8 }
}
function Write-RunnerState([string]$State, [string[]]$Blockers = @(), [string]$Note = '') {
  if (Test-Path -LiteralPath $RepoRoot) {
    Ensure-Dir $stateDir
    Ensure-Dir $heartbeatDir
    $payload = [ordered]@{
      layer = 'Topography'
      runner = 'single_shared_topography_runner'
      state = $State
      pid = $PID
      repo_root = $RepoRoot
      branch = $Branch
      updated_at = (Get-Date).ToString('o')
      stale_after_minutes = $StaleMinutes
      blockers = @($Blockers)
      note = $Note
    }
    Write-Utf8 $runnerStatePath (To-Json $payload)
    Write-Utf8 $heartbeatPath (To-Json $payload)
  }
}

$mutex = New-Object System.Threading.Mutex($false, $mutexName)
$hasMutex = $false
try {
  $hasMutex = $mutex.WaitOne(0)
  if (-not $hasMutex) {
    Write-RunnerState 'already_running' @('single_runner_already_active') 'Another Topography runner owns the mutex; no duplicate runner was started.'
    Write-Host 'Topography runner already active; duplicate start refused.'
    exit 0
  }

  Ensure-Dir (Split-Path -Parent $RepoRoot)
  if (-not (Test-Path -LiteralPath $RepoRoot)) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git command not found.' }
    Log "clone_start repo=$RepoUrl root=$RepoRoot"
    git clone --branch $Branch $RepoUrl $RepoRoot | Out-Host
  }
  if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { throw "RepoRoot exists but is not a git repo: $RepoRoot" }

  Ensure-Dir $logDir
  Ensure-Dir $stateDir
  Ensure-Dir $heartbeatDir
  Set-Location -LiteralPath $RepoRoot
  $env:AAYS_REPO_ROOT = $RepoRoot
  Write-RunnerState 'started' @() 'Runner mutex acquired; repo root locked to F drive.'

  if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git command not found.' }
  Log 'git_sync_start'
  $dirty = (git status --porcelain | Out-String).Trim()
  if ($dirty -and -not $ForcePullWhenDirty) {
    Log 'git_dirty_local_changes_preserved; fetch only; pull skipped to avoid hiding local ChatGPT edits or runner fixes'
    git fetch origin $Branch | Out-Host
  } else {
    if ($dirty -and $ForcePullWhenDirty) {
      Log 'git_dirty_force_pull_requested; stashing before pull'
      git stash push -u -m ('topography-autofix-' + (Get-Date -Format yyyyMMdd_HHmmss)) | Out-Host
    }
    git fetch origin $Branch | Out-Host
    git checkout $Branch | Out-Host
    git pull --ff-only origin $Branch | Out-Host
  }

  $bridge = Join-Path $RepoRoot 'docs\chatgpt_status\topography\automation\topography_single_runner_bridge_20260703.ps1'
  if (-not (Test-Path -LiteralPath $bridge)) { throw "bridge script missing: $bridge" }

  $csv = Join-Path $RepoRoot 'docs\chatgpt_status\topography\fixtures\topography_verified_rows_template_20260703.csv'
  if (-not (Test-Path -LiteralPath $csv)) {
    Write-Utf8 $csv $requiredCsvHeader
    Log 'created verified rows CSV header only; no fake parcel row added'
  } else {
    $first = [System.IO.File]::ReadLines($csv) | Select-Object -First 1
    if ($first -ne $requiredCsvHeader) { Log 'verified rows CSV header differs from expected; bridge will report missing fields if needed' }
  }

  Write-RunnerState 'bridge_first_pass' @() 'Running local bridge before smoke.'
  & $bridge -RepoRoot $RepoRoot 2>&1 | Tee-Object -FilePath $logPath -Append | Out-Host

  Write-RunnerState 'browser_smoke' @() 'Running HTTP and Chrome headless smoke for 8010 and 8020 if available.'
  $smokeDir = Join-Path $RepoRoot 'docs\chatgpt_status\topography\browser_smoke'
  Ensure-Dir $smokeDir
  $smokePath = Join-Path $smokeDir 'topography_browser_smoke_latest_20260704.json'
  $urls = @(
    'http://127.0.0.1:8010/england_map_web/',
    'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=20260630-final'
  )
  $chromeCandidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles (x86)\Microsoft\Edge\Application\msedge.exe"
  )
  $browser = $chromeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  $results = @()
  foreach ($url in $urls) {
    $httpOk = $false
    $httpStatus = $null
    $httpError = $null
    try {
      $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
      $httpOk = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
      $httpStatus = [int]$r.StatusCode
    } catch { $httpError = $_.Exception.Message }

    $browserOk = $false
    $domBytes = 0
    $hasTitle = $false
    $hasTopography = $false
    $browserError = $null
    if ($browser) {
      $tmp = Join-Path $env:TEMP ('aays_topography_smoke_' + [guid]::NewGuid().ToString('N'))
      Ensure-Dir $tmp
      $outFile = Join-Path $tmp 'dom.txt'
      $errFile = Join-Path $tmp 'err.txt'
      try {
        $argLine = '--headless=new --disable-gpu --disable-extensions --no-first-run --user-data-dir="' + $tmp + '" --virtual-time-budget=5000 --dump-dom "' + $url + '"'
        $p = Start-Process -FilePath $browser -ArgumentList $argLine -NoNewWindow -Wait -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        $dom = if (Test-Path -LiteralPath $outFile) { [System.IO.File]::ReadAllText($outFile) } else { '' }
        $err = if (Test-Path -LiteralPath $errFile) { [System.IO.File]::ReadAllText($errFile) } else { '' }
        $domBytes = $dom.Length
        $hasTitle = ($dom -match 'Great Britain Parcel Map|TerraYield Program Parcel Layer Matrix')
        $hasTopography = ($dom -match 'Topography|topography')
        $browserOk = ($p.ExitCode -eq 0 -and $domBytes -gt 100 -and $hasTitle)
        if ($err) { $browserError = $err }
      } catch { $browserError = $_.Exception.Message }
      finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue } }
    } else {
      $browserError = 'chrome_or_edge_executable_not_found'
    }

    $results += [ordered]@{
      url = $url
      http_ok = $httpOk
      http_status = $httpStatus
      http_error = $httpError
      browser_ok = $browserOk
      dom_bytes = $domBytes
      has_title = $hasTitle
      has_topography = $hasTopography
      browser_error = $browserError
    }
  }
  $overall = (@($results | Where-Object { -not $_.http_ok -or -not $_.browser_ok }).Count -eq 0)
  $smokePayload = [ordered]@{
    layer = 'Topography'
    generated_at = (Get-Date).ToString('o')
    smoke_type = 'http_plus_chrome_headless_dump_dom'
    browser_path = $browser
    overall_ok = $overall
    results = $results
    note = 'Smoke proves local page render only. final_ready still requires real verified parcel rows and parcel popup/panel evidence.'
  }
  Write-Utf8 $smokePath (To-Json $smokePayload)

  Write-RunnerState 'bridge_final_pass' @() 'Running local bridge after smoke.'
  & $bridge -RepoRoot $RepoRoot 2>&1 | Tee-Object -FilePath $logPath -Append | Out-Host

  $latest = Join-Path $RepoRoot 'outputs\england_program_parcel_matrix_20260629\topography_updates\latest_changes.json'
  $siteMirror = Join-Path $env:USERPROFILE 'Documents\GitHub\AAYS\outputs\england_program_parcel_matrix_20260629\topography_updates\latest_changes.json'
  if ((Test-Path -LiteralPath $latest) -and (Test-Path -LiteralPath (Split-Path -Parent $siteMirror))) {
    Copy-Item -LiteralPath $latest -Destination $siteMirror -Force
    Log "site_8020_mirror_synced=$siteMirror"
  }

  $status = Join-Path $RepoRoot 'docs\chatgpt_status\topography\status\topography_current_status_20260703.txt'
  if (-not (Test-Path -LiteralPath $status)) { throw 'status file was not produced' }
  Write-RunnerState 'complete' @() 'Runner pass complete; read status file for final_ready and blockers.'
  Log 'final_status_begin'
  Get-Content -LiteralPath $status | Tee-Object -FilePath $logPath -Append | Out-Host
  Log 'final_status_end'
} catch {
  Write-RunnerState 'failed' @('runner_exception') $_.Exception.Message
  Log ('ERROR ' + $_.Exception.Message)
  throw
} finally {
  if ($hasMutex) { $mutex.ReleaseMutex() | Out-Null }
  $mutex.Dispose()
}