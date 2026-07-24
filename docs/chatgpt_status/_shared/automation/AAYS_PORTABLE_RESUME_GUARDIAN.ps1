[CmdletBinding()]
param(
  [string]$ConfigPath = (Join-Path $env:ProgramData 'AAYS\portable_runner_guardian.json'),
  [string]$StatePath = (Join-Path $env:ProgramData 'AAYS\guardian_state.json'),
  [switch]$Loop,
  [switch]$Once,
  [switch]$NoStart,
  [switch]$SkipStabilityDelay,
  [switch]$SimulateDiskMissing,
  [switch]$SimulateNetworkDown,
  [switch]$SimulateResume
)

$ErrorActionPreference = 'Stop'
$programRoot = Split-Path -Parent $StatePath
$logPath = Join-Path $programRoot 'guardian.log'

function Now-Utc { [DateTimeOffset]::UtcNow.ToString('o') }
function Ensure-Dir([string]$Path) { if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
  try { Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $null }
}
function Write-Utf8Atomic([string]$Path,[string]$Text) {
  Ensure-Dir (Split-Path -Parent $Path)
  $tmp = "$Path.tmp.$PID"
  [IO.File]::WriteAllText($tmp,$Text,(New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Write-State([hashtable]$State) {
  $State.checked_at = Now-Utc
  Write-Utf8Atomic $StatePath (($State | ConvertTo-Json -Depth 30) + [Environment]::NewLine)
}
function Add-Log([string]$Message) {
  Ensure-Dir $programRoot
  Add-Content -LiteralPath $logPath -Value ("{0} {1}" -f (Now-Utc),$Message) -Encoding UTF8
}
function Get-Value($Object,[string[]]$Names,$Default=$null) {
  if ($null -eq $Object) { return $Default }
  foreach ($name in $Names) {
    $prop = $Object.PSObject.Properties[$name]
    if ($prop -and $null -ne $prop.Value -and [string]$prop.Value -ne '') { return $prop.Value }
  }
  return $Default
}
function Base-State {
  [ordered]@{
    checked_at = Now-Utc
    guardian_pid = $PID
    guardian_instance_id = $script:InstanceId
    portable_disk_present = $false
    portable_disk_stable = $false
    portable_root = ''
    resolved_drive_letter = ''
    portable_identity = ''
    disk_first_seen_at = ''
    internet_available = $false
    github_reachable = $false
    network_failure_count = 0
    next_retry_at = ''
    runner_active = $false
    runner_pid = 0
    runner_process_start_time = ''
    runner_lock_valid = $false
    current_task_id = ''
    current_page_key = ''
    current_stage = ''
    last_checkpoint_at = ''
    last_push_status = ''
    state = 'recoverable_blocked'
    restart_count = 0
    last_error = ''
    pages = @()
    five_pages_registry_verified = $false
    single_runner_only = $true
    parallel_runner = $false
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
}
function Test-Marker([string]$Root,$Config) {
  if (-not $Root) { return $false }
  $markerPath = Join-Path $Root ([string]$Config.marker_file)
  $marker = Read-Json $markerPath
  return ($marker -and [string]$marker.marker_id -eq [string]$Config.marker_id)
}
function Resolve-PortableRoot($Config) {
  if ($SimulateDiskMissing) { return $null }
  $candidates = New-Object Collections.Generic.List[string]
  if ($Config.fallback_root) { [void]$candidates.Add([string]$Config.fallback_root) }
  try {
    foreach ($volume in @(Get-Volume -ErrorAction SilentlyContinue)) {
      $identityMatch = ($Config.volume_unique_id -and [string]$volume.UniqueId -eq [string]$Config.volume_unique_id)
      $labelMatch = ($Config.volume_label -and [string]$volume.FileSystemLabel -eq [string]$Config.volume_label)
      if ($identityMatch -or $labelMatch) {
        if ($volume.Path) { [void]$candidates.Add([string]$volume.Path) }
        if ($volume.DriveLetter) { [void]$candidates.Add(([string]$volume.DriveLetter + ':\')) }
      }
    }
  } catch {}
  foreach ($drive in @(Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
    if ($drive.Root) { [void]$candidates.Add([string]$drive.Root) }
  }
  foreach ($candidate in @($candidates | Select-Object -Unique)) {
    try {
      $root = [IO.Path]::GetFullPath($candidate).TrimEnd('\')
      if (Test-Marker $root $Config) { return $root }
    } catch {}
  }
  return $null
}
function Test-GitHub {
  if ($SimulateNetworkDown) { return [pscustomobject]@{ internet=$false; github=$false } }
  $internet = [Net.NetworkInformation.NetworkInterface]::GetIsNetworkAvailable()
  $github = $false
  if ($internet) {
    $client = New-Object Net.Sockets.TcpClient
    try {
      $async = $client.BeginConnect('github.com',443,$null,$null)
      $github = $async.AsyncWaitHandle.WaitOne(2500,$false)
      if ($github) { $client.EndConnect($async) }
    } catch { $github = $false } finally { $client.Close() }
  }
  [pscustomobject]@{ internet=[bool]$internet; github=[bool]$github }
}
function Get-GitDir([string]$RepoRoot) {
  $dotGit = Join-Path $RepoRoot '.git'
  if (Test-Path -LiteralPath $dotGit -PathType Container) { return $dotGit }
  if (Test-Path -LiteralPath $dotGit -PathType Leaf) {
    $line = Get-Content -LiteralPath $dotGit -TotalCount 1
    if ($line -match '^gitdir:\s*(.+)$') {
      $path = $matches[1]
      if (-not [IO.Path]::IsPathRooted($path)) { $path = Join-Path $RepoRoot $path }
      return [IO.Path]::GetFullPath($path)
    }
  }
  return ''
}
function Test-CriticalGitWrite([string]$RepoRoot) {
  $gitDir = Get-GitDir $RepoRoot
  if (-not $gitDir) { return $true }
  foreach ($rel in @('index.lock','MERGE_HEAD','rebase-apply','rebase-merge')) {
    if (Test-Path -LiteralPath (Join-Path $gitDir $rel)) { return $true }
  }
  return $false
}
function Get-CommandLine([int]$ProcessId) {
  try { [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).CommandLine } catch { '' }
}
function Get-RunnerOwner([string]$RepoRoot) {
  $lockPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
  $lock = Read-Json $lockPath
  $ownerPid = [int](Get-Value $lock @('supervisor_pid','pid') 0)
  if ($ownerPid -le 0) { return [pscustomobject]@{ valid=$false; alive=$false; pid=0; start=''; reason='no_lock_pid' } }
  $proc = Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
  if (-not $proc) { return [pscustomobject]@{ valid=$false; alive=$false; pid=$ownerPid; start=''; reason='pid_dead' } }
  $command = Get-CommandLine $ownerPid
  $commandOk = ($command -like '*RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1*' -and $command -like "*$RepoRoot*")
  $start = $proc.StartTime.ToUniversalTime().ToString('o')
  $startOk = $true
  if ($lock.process_start_time) {
    try { $startOk = [math]::Abs(($proc.StartTime.ToUniversalTime() - ([datetime]$lock.process_start_time).ToUniversalTime()).TotalSeconds) -lt 2 } catch { $startOk=$false }
  }
  [pscustomobject]@{ valid=($commandOk -and $startOk); alive=$true; pid=$ownerPid; start=$start; reason=$(if($commandOk-and$startOk){'canonical_owner_verified'}else{'live_owner_identity_mismatch'}) }
}
function Stop-PortableProcesses([string]$PreviousRoot) {
  if (-not $PreviousRoot) { return 0 }
  $matches = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*$PreviousRoot*" -and
    ($_.CommandLine -like '*RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1*' -or $_.CommandLine -like '*RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1*')
  })
  foreach ($p in @($matches | Sort-Object { if($_.CommandLine-like'*RUN_SINGLE*'){0}else{1} })) {
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
  }
  return $matches.Count
}
function Get-FivePageState([string]$RepoRoot,$Config,$Current) {
  $result = @()
  foreach ($page in @($Config.page_registry)) {
    $checkpoint = $null
    $rel = [string]$page.checkpoint_path
    if ($rel) { $checkpoint = Read-Json (Join-Path $RepoRoot ($rel -replace '/', '\')) }
    $blocker = Get-Value $checkpoint @('blocker','blockers') $(if($checkpoint){''}else{'checkpoint_not_locally_available'})
    if ($blocker -is [array]) { $blocker = $blocker -join ';' }
    $result += [ordered]@{
      domain_key = [string]$page.domain_key
      page_key = [string]$page.page_key
      active_task_id = $(if($Current -and [string]$Current.task_id -like "*$([string]$page.task_hint)*"){[string]$Current.task_id}else{[string]$page.last_known_task_id})
      status = [string](Get-Value $checkpoint @('status','state') 'checkpoint_registry_ready')
      last_checkpoint = [string](Get-Value $checkpoint @('verified_at','updated_at','completed_at','heartbeat_at') '')
      verified_rows = [int](Get-Value $checkpoint @('verified_rows','verified_new_rows','served_row_count','row_count') 0)
      newly_published_rows = [int](Get-Value $checkpoint @('newly_published_rows','verified_new_rows','new_rows') 0)
      blocker = [string]$blocker
      remote_readback = [bool](Get-Value $checkpoint @('remote_readback_ok','PUSH_SYNC_OK','post_sync_ok') $false)
      final_ready = $false
    }
  }
  return $result
}
function Invoke-GuardianCheck($Config) {
  $previous = Read-Json $StatePath
  $state = Base-State
  $state.restart_count = [int](Get-Value $previous @('restart_count') 0)
  $root = Resolve-PortableRoot $Config
  if (-not $root) {
    if (-not $SimulateDiskMissing) { [void](Stop-PortableProcesses ([string](Get-Value $previous @('portable_root') ''))) }
    $state.state = 'waiting_for_portable_disk'
    $state.last_error = 'PORTABLE_DISK_NOT_PRESENT'
    Write-State $state
    return 60
  }
  $state.portable_disk_present = $true
  $state.portable_root = $root
  $state.resolved_drive_letter = [IO.Path]::GetPathRoot($root)
  $state.portable_identity = [string]$Config.marker_id
  $sameDisk = ([string](Get-Value $previous @('portable_identity') '') -eq [string]$Config.marker_id)
  $firstSeen = if ($sameDisk) { [string](Get-Value $previous @('disk_first_seen_at') '') } else { Now-Utc }
  $state.disk_first_seen_at = $firstSeen
  $stable = $SkipStabilityDelay
  if (-not $stable -and $firstSeen) {
    try { $stable = (([DateTimeOffset]::UtcNow - [DateTimeOffset]::Parse($firstSeen)).TotalSeconds -ge [int]$Config.stable_seconds) } catch {}
  }
  if (-not $stable) {
    $state.state = 'waiting_for_disk_stability'
    Write-State $state
    return [math]::Max(1,[int]$Config.stable_seconds)
  }
  $state.portable_disk_stable = $true
  $repoRoot = Join-Path $root ([string]$Config.repo_relative)
  $launcher = Join-Path $root ([string]$Config.launcher_relative)
  if (-not (Test-Path -LiteralPath $repoRoot) -or -not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    $state.state='recoverable_blocked';$state.last_error='PORTABLE_PREFLIGHT_PATH_MISSING';Write-State $state;return 60
  }
  $network = Test-GitHub
  $state.internet_available = $network.internet
  $state.github_reachable = $network.github
  $failureCount = if($network.github){0}else{[int](Get-Value $previous @('network_failure_count') 0)+1}
  $state.network_failure_count = $failureCount
  $backoff = @($Config.network_backoff_seconds)
  $delay = if($network.github){[int]$Config.interval_seconds}else{[int]$backoff[[math]::Min($failureCount-1,$backoff.Count-1)]}
  if(-not$network.github){$state.next_retry_at=[DateTimeOffset]::UtcNow.AddSeconds($delay).ToString('o')}
  $currentPath = Join-Path $repoRoot 'docs\chatgpt_status\aays1\queue\current.task.json'
  $current = Read-Json $currentPath
  $state.current_task_id = [string](Get-Value $current @('task_id') '')
  $state.current_page_key = [string](Get-Value $current @('page_key') '')
  $state.current_stage = [string](Get-Value $current @('state','status') '')
  $state.last_checkpoint_at = [string](Get-Value $current @('last_heartbeat_at','updated_at','completed_at') '')
  $state.last_push_status = [string](Get-Value $current @('PUSH_SYNC_OK','git_push_status') '')
  $state.pages = @(Get-FivePageState $repoRoot $Config $current)
  $keys = @($state.pages | ForEach-Object { $_.domain_key } | Select-Object -Unique)
  $state.five_pages_registry_verified = ($keys.Count -eq 5)
  $owner = Get-RunnerOwner $repoRoot
  $state.runner_active=$owner.valid;$state.runner_pid=$owner.pid;$state.runner_process_start_time=$owner.start;$state.runner_lock_valid=$owner.valid
  if ($owner.valid) {
    $state.state = if($network.github){'runner_healthy'}else{'waiting_for_network'}
    if($SimulateResume){$state.current_stage='resume_grace_owner_verified'}
    Write-State $state
    return $delay
  }
  if ($owner.alive) {
    $state.state='recoverable_blocked';$state.last_error='LIVE_RUNNER_IDENTITY_MISMATCH';Write-State $state;return 60
  }
  if (-not $network.github) {
    $state.state='waiting_for_network';$state.last_error='NETWORK_REQUIRED_BEFORE_RUNNER_RESTART';Write-State $state;return $delay
  }
  if (Test-CriticalGitWrite $repoRoot) {
    $state.state='recoverable_blocked';$state.last_error='CRITICAL_GIT_WRITE_IN_PROGRESS';Write-State $state;return 60
  }
  $probeDir = Join-Path $root '_portable_logs'
  Ensure-Dir $probeDir
  $probe = Join-Path $probeDir ('.guardian_write_probe_' + [guid]::NewGuid().ToString('N') + '.tmp')
  try { [IO.File]::WriteAllText($probe,'ok'); Remove-Item -LiteralPath $probe -Force } catch {
    $state.state='recoverable_blocked';$state.last_error='PORTABLE_ROOT_NOT_WRITABLE';Write-State $state;return 60
  }
  if ($NoStart) {
    $state.state='runner_restart_required';$state.last_error='NO_START_TEST_MODE';Write-State $state;return 60
  }
  $oldManaged = $env:AAYS_GUARDIAN_MANAGED
  $env:AAYS_GUARDIAN_MANAGED='1'
  try {
    $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"' + $launcher + '"')) -WorkingDirectory $root -WindowStyle Hidden -PassThru
    if (-not $proc.WaitForExit(75000)) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
  } finally { $env:AAYS_GUARDIAN_MANAGED=$oldManaged }
  $deadline=(Get-Date).AddSeconds(75)
  do { Start-Sleep -Seconds 2; $owner=Get-RunnerOwner $repoRoot; if($owner.valid){break} } while((Get-Date)-lt$deadline)
  if (-not $owner.valid) {
    $state.state='recoverable_blocked';$state.last_error='RUNNER_RESTART_FAILED';Write-State $state;return 60
  }
  $state.runner_active=$true;$state.runner_pid=$owner.pid;$state.runner_process_start_time=$owner.start;$state.runner_lock_valid=$true
  $state.restart_count++
  $state.state='runner_restarted'
  Write-State $state
  Add-Log "runner_restarted pid=$($owner.pid) root=$root"
  return [int]$Config.interval_seconds
}

Ensure-Dir $programRoot
$config = Read-Json $ConfigPath
if (-not $config) { throw "GUARDIAN_CONFIG_MISSING_OR_INVALID: $ConfigPath" }
$script:InstanceId = [guid]::NewGuid().ToString('N')
$mutex = $null
$lockTaken = $false
try {
  try { $mutex = New-Object Threading.Mutex($false,'Global\AAYS_Portable_Runner_Guardian') }
  catch { $mutex = New-Object Threading.Mutex($false,'Local\AAYS_Portable_Runner_Guardian') }
  $lockTaken = $mutex.WaitOne(0)
  if (-not $lockTaken) { exit 0 }
  do {
    $delay = 60
    try { $delay = Invoke-GuardianCheck $config }
    catch {
      $state=Base-State;$state.state='recoverable_blocked';$state.last_error=$_.Exception.Message;Write-State $state
      Add-Log ("error=" + $_.Exception.Message)
    }
    if ($Once -or -not $Loop) { break }
    Start-Sleep -Seconds ([math]::Max(5,[math]::Min(300,[int]$delay)))
  } while ($true)
} finally {
  if ($lockTaken -and $mutex) { try { $mutex.ReleaseMutex() } catch {} }
  if ($mutex) { $mutex.Dispose() }
}

