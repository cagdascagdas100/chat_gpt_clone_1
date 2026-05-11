param([switch]$Once)
$ErrorActionPreference = 'Continue'
$BridgeRoot = $PSScriptRoot
if (-not $BridgeRoot) { $BridgeRoot = Split-Path -Parent $MyInvocation.MyCommand.Path }
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
if (-not $env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT = $BridgeRoot }
$TaskFile = Join-Path $env:AAYS_BRIDGE_ROOT 'ai-tasks\current-task.json'
$ScriptsDir = Join-Path $env:AAYS_BRIDGE_ROOT 'ai-task-scripts'
$ResultsDir = Join-Path $env:AAYS_BRIDGE_ROOT 'ai-results'
$LogsDir = Join-Path $env:AAYS_BRIDGE_ROOT 'ai-runner-logs'
$HeartbeatFile = Join-Path $env:AAYS_BRIDGE_ROOT 'ai-heartbeat\portable-runner.md'
New-Item -ItemType Directory -Force -Path $ScriptsDir,$ResultsDir,$LogsDir,(Split-Path $HeartbeatFile) | Out-Null
function Write-Status($status,$taskId,$msg){ @("# TerraYield Portable Runner Heartbeat",'',"status: $status","task_id: $taskId","checked_at: $((Get-Date).ToString('s'))","bridge_root: $env:AAYS_BRIDGE_ROOT","message: $msg") | Set-Content -Path $HeartbeatFile -Encoding UTF8 }
function Write-Result($taskId,$status,$msg,$out='',$err=''){ $safe=($taskId -replace '[^a-zA-Z0-9._-]','_'); if(-not $safe){$safe='unknown-task'}; [ordered]@{task_id=$taskId;status=$status;message=$msg;output_path=$out;error_path=$err;bridge_root=$env:AAYS_BRIDGE_ROOT;written_at=(Get-Date).ToString('s')} | ConvertTo-Json -Depth 6 | Set-Content -Path (Join-Path $ResultsDir "$safe.result.json") -Encoding UTF8 }
try {
  if (-not (Test-Path $TaskFile)) { Write-Status 'waiting' '' 'Task file not found.'; exit 0 }
  $task = Get-Content $TaskFile -Raw | ConvertFrom-Json
  $taskId = [string]$task.id
  if (-not $taskId) { $taskId='unknown-task' }
  $candidate = [string]$task.script_path
  if (-not $candidate) { Write-Status 'idle' $taskId 'No script_path provided.'; Write-Result $taskId 'idle' 'No script_path provided.'; exit 0 }
  $scriptPath = [IO.Path]::GetFullPath((Join-Path $ScriptsDir $candidate))
  $allowed = [IO.Path]::GetFullPath($ScriptsDir)
  if (-not $scriptPath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw "Blocked script path: $scriptPath" }
  if (-not (Test-Path $scriptPath)) { throw "Task script not found: $scriptPath" }
  $wd = if ($task.working_directory) { [string]$task.working_directory } else { $env:AAYS_PROJECT_ROOT }
  if (-not (Test-Path $wd)) { throw "Working directory not found: $wd" }
  $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; $out=Join-Path $LogsDir "$taskId.$stamp.log"; $err=Join-Path $LogsDir "$taskId.$stamp.err.log"
  Write-Status 'running' $taskId "Running $scriptPath"
  Push-Location $wd; try { & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 1> $out 2> $err; $code=$LASTEXITCODE } finally { Pop-Location }
  if ($code -eq 0) { Write-Status 'completed' $taskId 'Task completed successfully.'; Write-Result $taskId 'completed' 'Task completed successfully.' $out $err } else { Write-Status 'failed' $taskId "Task failed with exit code $code."; Write-Result $taskId 'failed' "Task failed with exit code $code." $out $err }
} catch { Write-Status 'error' $taskId $_.Exception.Message; Write-Result $taskId 'error' $_.Exception.Message }


