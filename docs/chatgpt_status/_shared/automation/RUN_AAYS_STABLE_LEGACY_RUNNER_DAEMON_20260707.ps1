[CmdletBinding()]
param(
  [string]$RepoRoot = "F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "codex/aays-single-runner-v5-20260706",
  [string]$WorkRoot = "F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES",
  [int]$IntervalSeconds = 60,
  [int]$HeartbeatSeconds = 15,
  [int]$MaxTasks = 8,
  [int]$StaleMinutes = 20,
  [int]$MaxLoops = 0,
  [int]$RefreshIntervalSeconds = 43200,
  [int]$SiteCheckIntervalSeconds = 60,
  [int]$SiteFailureThreshold = 3,
  [int]$MaxBackoffSeconds = 300,
  [switch]$NoPush,
  [switch]$SelfTestMode,
  [switch]$SelfTestFailFirstWorker
)

$ErrorActionPreference = "Stop"
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd("\")
$WorkRoot = [System.IO.Path]::GetFullPath($WorkRoot).TrimEnd("\")
if ($RepoRoot.StartsWith("C:\", [System.StringComparison]::OrdinalIgnoreCase)) { throw "C_DRIVE_NOT_CANONICAL: $RepoRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) { throw "REPO_ROOT_INVALID: $RepoRoot" }

$sharedRoot = Join-Path $RepoRoot "docs\chatgpt_status\_shared"
$automationRoot = Join-Path $sharedRoot "automation"
$runner = Join-Path $automationRoot "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1"
$statusDir = Join-Path $sharedRoot "status"
$heartbeatDir = Join-Path $sharedRoot "heartbeat"
$lockDir = Join-Path $sharedRoot "locks"
$logDir = Join-Path $sharedRoot "logs"
foreach ($dir in @($statusDir,$heartbeatDir,$lockDir,$logDir,$WorkRoot)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
if (-not (Test-Path -LiteralPath $runner)) { throw "SCAN_RUNNER_MISSING: $runner" }

$lockPath = Join-Path $lockDir "single_runner.lock"
$statusPath = Join-Path $statusDir "stable_runner_daemon_latest.json"
$bootstrapPath = Join-Path $statusDir "runner_bootstrap_latest.json"
$heartbeatPath = Join-Path $heartbeatDir "stable_runner_daemon_heartbeat_latest.json"
$instanceId = [guid]::NewGuid().ToString("N")
$process = Get-Process -Id $PID -ErrorAction Stop
$processStartUtc = $process.StartTime.ToUniversalTime().ToString("o")
$executablePath = [string]$process.Path
$scriptPath = $MyInvocation.MyCommand.Path
$portableRoot = $RepoRoot
while ($portableRoot -and (Split-Path -Leaf $portableRoot) -ne "runner_system") { $parent = Split-Path -Parent $portableRoot; if ($parent -eq $portableRoot) { break }; $portableRoot = $parent }
if ((Split-Path -Leaf $portableRoot) -eq "runner_system") { $portableRoot = Split-Path -Parent $portableRoot } else { throw "PORTABLE_ROOT_NOT_RESOLVED_FROM_REPO: $RepoRoot" }
$appLauncher = Join-Path $portableRoot "START_TERRAYIELD_PORTABLE_8012.ps1"
$logPath = Join-Path $logDir ("persistent_runner_daemon_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

$script:Loop = 0
$script:WorkerPid = $null
$script:CurrentTaskId = $null
$script:LastQueueScanAt = $null
$script:LastWorkerExitCode = $null
$script:ConsecutiveFailures = 0
$script:LastSuccessAt = $null
$script:State = "starting"
$script:SiteFailureCount = 0
$script:Site8012Ok = $false
$script:ReadySiteOk = $false
$script:AppPid = $null
$script:AppCommandVerified = $false
$script:LastSiteCheckAt = [datetime]::MinValue
$script:LastRefreshAt = $null
$script:RefreshResult = "not_run"
$script:NextRefreshAt = (Get-Date).ToUniversalTime().AddSeconds($RefreshIntervalSeconds)
$script:DummyFailureUsed = $false

function Now-Utc { (Get-Date).ToUniversalTime().ToString("o") }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8Atomic([string]$Path, [string]$Text) {
  Ensure-Dir (Split-Path -Parent $Path)
  $temp = "$Path.tmp.$PID.$([guid]::NewGuid().ToString('N'))"
  [System.IO.File]::WriteAllText($temp, $Text, [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temp -Destination $Path -Force
}
function Write-JsonAtomic([string]$Path, [object]$Payload) { Write-Utf8Atomic $Path (($Payload | ConvertTo-Json -Depth 50) + "`n") }
function Read-Json([string]$Path) { try { if (Test-Path -LiteralPath $Path) { return Get-Content -Raw -LiteralPath $Path -Encoding UTF8 | ConvertFrom-Json } } catch {}; return $null }
function Get-CommandLine([int]$ProcessId) { try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).CommandLine } catch { return "" } }
function Get-TextHash([string]$Text) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes([string]$Text)))).Replace("-","").ToLowerInvariant() } finally { $sha.Dispose() }
}
function Rotate-Log {
  if ((Test-Path -LiteralPath $logPath) -and (Get-Item -LiteralPath $logPath).Length -gt 5242880) {
    $archive = "$logPath.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Move-Item -LiteralPath $logPath -Destination $archive -Force
    @(Get-ChildItem -LiteralPath $logDir -File -Filter "persistent_runner_daemon_*.log.*" | Sort-Object LastWriteTime -Descending | Select-Object -Skip 5) | Remove-Item -Force -ErrorAction SilentlyContinue
  }
}
function Add-Log([string]$Message) { Rotate-Log; Add-Content -LiteralPath $logPath -Encoding UTF8 -Value ("[{0}] {1}" -f (Now-Utc),$Message) }
function Test-ProcessAlive([int]$ProcessId) { if ($ProcessId -le 0) { return $false }; return $null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) }
function Test-CanonicalDaemonLock([object]$Lock) {
  if (-not $Lock) { return [pscustomobject]@{ valid=$false; alive=$false; pid=$null; reason="lock_missing_or_invalid" } }
  $existingPid = if ($Lock.supervisor_pid) { [int]$Lock.supervisor_pid } elseif ($Lock.pid) { [int]$Lock.pid } else { 0 }
  if (-not (Test-ProcessAlive $existingPid)) { return [pscustomobject]@{ valid=$false; alive=$false; pid=$existingPid; reason="pid_not_alive" } }
  $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
  if (-not $existingProcess) { return [pscustomobject]@{ valid=$false; alive=$false; pid=$existingPid; reason="process_unavailable" } }
  $startMatches = $true
  if ($Lock.process_start_time) {
    try { $startMatches = [math]::Abs(($existingProcess.StartTime.ToUniversalTime() - ([datetime]$Lock.process_start_time).ToUniversalTime()).TotalSeconds) -lt 2 } catch { $startMatches = $false }
  }
  $commandLine = Get-CommandLine $existingPid
  $commandMatches = if ($commandLine) { $commandLine -like "*$([System.IO.Path]::GetFileName($scriptPath))*" -and $commandLine -like "*$RepoRoot*" } else { $existingProcess.ProcessName -like "powershell*" }
  $scopeMatches = -not $Lock.lock_scope -or [string]$Lock.lock_scope -eq "single_shared_runner_daemon"
  [pscustomobject]@{ valid=($startMatches -and $commandMatches -and $scopeMatches); alive=$true; pid=$existingPid; reason=if($startMatches -and $commandMatches -and $scopeMatches){"validated_process_identity"}else{"process_identity_mismatch"}; command_line=$commandLine }
}
function New-LockPayload {
  $commandLine = Get-CommandLine $PID
  [ordered]@{
    instance_id = $instanceId
    pid = $PID
    supervisor_pid = $PID
    process_start_time = $processStartUtc
    executable_path = $executablePath
    command_line_hash = Get-TextHash $(if($commandLine){$commandLine}else{"$scriptPath|$RepoRoot|$MainBranch"})
    repo_root = $RepoRoot
    branch = $MainBranch
    created_at = $processStartUtc
    updated_at = Now-Utc
    lock_scope = "single_shared_runner_daemon"
    final_ready = $false
  }
}
function Update-Lock {
  $lock = Read-Json $lockPath
  if ($lock -and [string]$lock.instance_id -eq $instanceId -and [int]$lock.supervisor_pid -eq $PID) {
    $lock.updated_at = Now-Utc
    Write-JsonAtomic $lockPath $lock
  }
}
function Get-PortProcess {
  $portPid = 0
  try { $connection = Get-NetTCPConnection -LocalPort 8012 -State Listen -ErrorAction Stop | Select-Object -First 1; if ($connection) { $portPid = [int]$connection.OwningProcess } } catch {}
  if ($portPid -le 0) { return [pscustomobject]@{ pid=$null; alive=$false; canonical=$false; command_line="" } }
  $alive = Test-ProcessAlive $portPid
  $command = if ($alive) { Get-CommandLine $portPid } else { "" }
  $canonical = $alive -and $command -like "*uvicorn*" -and $command -like "*$portableRoot*"
  [pscustomobject]@{ pid=$portPid; alive=$alive; canonical=$canonical; command_line=$command }
}
function Test-Http([string]$Url) { try { $response=Invoke-WebRequest -UseBasicParsing -Uri ("$Url`?watchdog=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())") -TimeoutSec 10; return $response.StatusCode -eq 200 } catch { return $false } }
function Update-SiteState([switch]$AllowRecovery) {
  $script:Site8012Ok = Test-Http "http://127.0.0.1:8012/health"
  $script:ReadySiteOk = Test-Http "http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html"
  $port = Get-PortProcess
  $script:AppPid = $port.pid
  $script:AppCommandVerified = $port.canonical
  $script:LastSiteCheckAt = (Get-Date).ToUniversalTime()
  if ($script:Site8012Ok -and $script:ReadySiteOk) { $script:SiteFailureCount = 0; return }
  $script:SiteFailureCount++
  if ($AllowRecovery -and $script:SiteFailureCount -ge $SiteFailureThreshold) {
    if ($port.alive) { Add-Log "site_degraded_existing_port_process_preserved pid=$($port.pid) canonical=$($port.canonical)"; return }
    if (-not (Test-Path -LiteralPath $appLauncher)) { Add-Log "site_recovery_blocked_launcher_missing=$appLauncher"; return }
    Add-Log "site_recovery_start launcher=$appLauncher"
    Start-Process -FilePath powershell -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$appLauncher,"-NoBrowser") -WorkingDirectory $portableRoot -WindowStyle Hidden | Out-Null
    for ($i=0;$i-lt 12;$i++) { Start-Sleep -Seconds 5; if (Test-Http "http://127.0.0.1:8012/health") { break } }
    $script:Site8012Ok = Test-Http "http://127.0.0.1:8012/health"
    $script:ReadySiteOk = Test-Http "http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html"
    if ($script:Site8012Ok -and $script:ReadySiteOk) { $script:SiteFailureCount=0; Add-Log "site_recovery_pass" } else { Add-Log "site_recovery_failed" }
  }
}
function Write-Heartbeat {
  Update-Lock
  $payload = [ordered]@{
    heartbeat_at = Now-Utc
    instance_id = $instanceId
    supervisor_pid = $PID
    daemon_pid = $PID
    worker_pid = $script:WorkerPid
    app_pid = $script:AppPid
    loop = $script:Loop
    state = $script:State
    current_task_id = $script:CurrentTaskId
    last_queue_scan_at = $script:LastQueueScanAt
    last_worker_exit_code = $script:LastWorkerExitCode
    consecutive_failures = $script:ConsecutiveFailures
    last_success_at = $script:LastSuccessAt
    last_refresh_at = $script:LastRefreshAt
    next_refresh_at = $script:NextRefreshAt.ToString("o")
    refresh_result = $script:RefreshResult
    site_8012_ok = $script:Site8012Ok
    ready_to_sell_site_ok = $script:ReadySiteOk
    site_failure_count = $script:SiteFailureCount
    app_command_verified = $script:AppCommandVerified
    runner_active = $true
    single_runner_only = $true
    parallel_runner = $false
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Write-JsonAtomic $heartbeatPath $payload
}
function Write-DaemonStatus([string]$Status) {
  Write-JsonAtomic $statusPath ([ordered]@{ checked_at=Now-Utc; status=$Status; instance_id=$instanceId; supervisor_pid=$PID; worker_pid=$script:WorkerPid; loop=$script:Loop; state=$script:State; last_worker_exit_code=$script:LastWorkerExitCode; consecutive_failures=$script:ConsecutiveFailures; last_success_at=$script:LastSuccessAt; last_refresh_at=$script:LastRefreshAt; next_refresh_at=$script:NextRefreshAt.ToString("o"); refresh_result=$script:RefreshResult; site_8012_ok=$script:Site8012Ok; CONTINUE_RUNNER_READY=$true; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  Write-JsonAtomic $bootstrapPath ([ordered]@{ updated_at=Now-Utc; repo_root=$RepoRoot; repo_full_name=$RepoFullName; runner_branch=$MainBranch; runner_status=$Status; runner_engine="persistent_stable_supervisor_20260711"; scan_runner="RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707"; runner_pid=$PID; supervisor_pid=$PID; instance_id=$instanceId; runner_lock_active=(Test-Path -LiteralPath $lockPath); lock_file="docs/chatgpt_status/_shared/locks/single_runner.lock"; CONTINUE_RUNNER_READY=$true; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
}
function Invoke-Git([string[]]$Args) {
  $old=$ErrorActionPreference
  try { $ErrorActionPreference="Continue"; $output=& git -c "safe.directory=$RepoRoot" -C $RepoRoot @Args 2>&1; $code=$LASTEXITCODE } finally { $ErrorActionPreference=$old }
  [pscustomobject]@{ code=$code; output=(($output|Out-String).Trim()) }
}
function Test-RuntimePath([string]$Path) {
  $p=$Path.Replace("\","/")
  return $p -like "docs/chatgpt_status/_shared/heartbeat/*" -or $p -like "docs/chatgpt_status/_shared/status/*" -or $p -like "docs/chatgpt_status/_shared/logs/*" -or $p -like "docs/chatgpt_status/_shared/locks/*" -or $p -like "docs/chatgpt_status/_shared/runner_lock/*" -or $p -like "docs/chatgpt_status/*/heartbeat/*" -or $p -like "docs/chatgpt_status/*/runner_outputs/*"
}
function Invoke-SafeRefresh {
  $script:State="refreshing"
  Write-Heartbeat
  try {
    $status=Invoke-Git @("status","--porcelain")
    if($status.code -ne 0){$script:RefreshResult="git_status_failed";return}
    $dirty=@($status.output -split "`r?`n" | Where-Object {$_} | ForEach-Object {if($_.Length -gt 3){$_.Substring(3).Trim()}else{""}})
    $nonRuntime=@($dirty | Where-Object {-not(Test-RuntimePath $_)})
    if($nonRuntime.Count -gt 0){$script:RefreshResult="blocked_dirty_repo";Add-Log ("refresh_blocked_dirty_repo="+($nonRuntime -join ","));return}
    $fetch=Invoke-Git @("fetch","--no-tags","origin",$MainBranch)
    if($fetch.code -ne 0){$script:RefreshResult="fetch_failed";Add-Log "refresh_fetch_failed=$($fetch.output)";return}
    if($dirty.Count -gt 0){$script:RefreshResult="fetch_only_runtime_changes_preserved"}else{
      $pull=Invoke-Git @("pull","--ff-only","origin",$MainBranch)
      $script:RefreshResult=if($pull.code -eq 0){"pull_ff_ok"}else{"pull_ff_failed"}
    }
    Update-SiteState -AllowRecovery
  } finally {
    $script:LastRefreshAt=Now-Utc
    $script:NextRefreshAt=(Get-Date).ToUniversalTime().AddSeconds($RefreshIntervalSeconds)
    Add-Log "refresh_result=$($script:RefreshResult) next=$($script:NextRefreshAt.ToString('o'))"
  }
}
function Wait-WithHeartbeat([int]$Seconds,[switch]$AllowSiteRecovery) {
  $deadline=(Get-Date).AddSeconds([math]::Max(0,$Seconds))
  do {
    if(((Get-Date).ToUniversalTime()-$script:LastSiteCheckAt).TotalSeconds -ge $SiteCheckIntervalSeconds){Update-SiteState -AllowRecovery:$AllowSiteRecovery}
    Write-Heartbeat
    $remaining=($deadline-(Get-Date)).TotalSeconds
    if($remaining -le 0){break}
    Start-Sleep -Seconds ([math]::Min($HeartbeatSeconds,[math]::Max(1,[int][math]::Ceiling($remaining))))
  } while((Get-Date)-lt $deadline)
}

$existing = Test-CanonicalDaemonLock (Read-Json $lockPath)
if ($existing.valid) {
  Write-JsonAtomic $statusPath ([ordered]@{ checked_at=Now-Utc; status="already_running"; active_pid=$existing.pid; reason=$existing.reason; lock_path="docs/chatgpt_status/_shared/locks/single_runner.lock"; parallel_runner=$false; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  Write-Output ((Read-Json $statusPath) | ConvertTo-Json -Depth 20)
  exit 0
}
if ($existing.alive) {
  Write-JsonAtomic $statusPath ([ordered]@{ checked_at=Now-Utc; status="live_lock_owner_unverified"; active_pid=$existing.pid; reason=$existing.reason; lock_path="docs/chatgpt_status/_shared/locks/single_runner.lock"; second_instance_blocked=$true; parallel_runner=$false; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  Write-Output ((Read-Json $statusPath) | ConvertTo-Json -Depth 20)
  exit 2
}
if (Test-Path -LiteralPath $lockPath) { Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue }
Write-JsonAtomic $lockPath (New-LockPayload)
Update-SiteState -AllowRecovery
Write-Heartbeat
Write-DaemonStatus "runner_started"
Add-Log "persistent_daemon_started pid=$PID instance=$instanceId repo=$RepoRoot"

try {
  while ($true) {
    try {
    if ((Get-Date).ToUniversalTime() -ge $script:NextRefreshAt) { Invoke-SafeRefresh }
    $script:Loop++
    $script:State="starting_worker"
    $stdout=Join-Path $logDir ("worker_{0}_{1}.out.log" -f $PID,$script:Loop)
    $stderr=Join-Path $logDir ("worker_{0}_{1}.err.log" -f $PID,$script:Loop)
    if($SelfTestFailFirstWorker -and -not $script:DummyFailureUsed){
      $script:DummyFailureUsed=$true
      $worker=Start-Process -FilePath powershell -ArgumentList @("-NoProfile","-Command","exit 7") -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
      Add-Log "self_test_dummy_worker_started pid=$($worker.Id)"
    }elseif($SelfTestMode){
      $worker=Start-Process -FilePath powershell -ArgumentList @("-NoProfile","-Command","Start-Sleep -Seconds 2; exit 0") -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
      Add-Log "self_test_success_worker_started pid=$($worker.Id)"
    }else{
      $args=@("-NoProfile","-ExecutionPolicy","Bypass","-File",$runner,"-RepoRoot",$RepoRoot,"-RepoFullName",$RepoFullName,"-MainBranch",$MainBranch,"-WorkRoot",$WorkRoot,"-MaxTasks","$MaxTasks","-StaleMinutes","$StaleMinutes")
      if($NoPush){$args+="-NoPush"}
      $worker=Start-Process -FilePath powershell -ArgumentList $args -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    }
    $script:WorkerPid=$worker.Id
    $script:State="worker_running"
    $script:LastQueueScanAt=Now-Utc
    Write-Heartbeat
    while(-not $worker.HasExited){Wait-WithHeartbeat -Seconds $HeartbeatSeconds -AllowSiteRecovery; $worker.Refresh()}
    $script:LastWorkerExitCode=$worker.ExitCode
    $script:WorkerPid=$null
    if($worker.ExitCode -eq 0){$script:ConsecutiveFailures=0;$script:LastSuccessAt=Now-Utc;$script:State="idle";Add-Log "worker_completed loop=$($script:Loop) exit=0"}else{$script:ConsecutiveFailures++;$script:State=if($script:ConsecutiveFailures-ge5){"degraded"}else{"worker_backoff"};Add-Log "worker_failed loop=$($script:Loop) exit=$($worker.ExitCode) failures=$($script:ConsecutiveFailures)"}
    Write-Heartbeat
    Write-DaemonStatus $(if($script:ConsecutiveFailures-ge5){"degraded"}else{"runner_active"})
    if($MaxLoops -gt 0 -and $script:Loop -ge $MaxLoops){break}
    $delay=if($script:ConsecutiveFailures-gt0){[math]::Min($MaxBackoffSeconds,15*[math]::Pow(2,[math]::Min(5,$script:ConsecutiveFailures-1)))}else{$IntervalSeconds}
      Wait-WithHeartbeat -Seconds ([int]$delay) -AllowSiteRecovery
    } catch {
      $script:WorkerPid=$null
      $script:State="degraded"
      $script:ConsecutiveFailures++
      Add-Log "supervisor_loop_error=$($_.Exception.Message) failures=$($script:ConsecutiveFailures)"
      Write-Heartbeat
      Write-DaemonStatus "degraded"
      if($MaxLoops -gt 0 -and $script:Loop -ge $MaxLoops){break}
      Wait-WithHeartbeat -Seconds ([math]::Min($MaxBackoffSeconds,300)) -AllowSiteRecovery
    }
  }
}finally{
  $current=Read-Json $lockPath
  if($current -and [string]$current.instance_id -eq $instanceId -and [int]$current.supervisor_pid -eq $PID){Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue}
  Add-Log "persistent_daemon_exit pid=$PID instance=$instanceId"
}
