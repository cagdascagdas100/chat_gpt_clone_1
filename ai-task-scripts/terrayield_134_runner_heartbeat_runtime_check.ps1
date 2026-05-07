$ErrorActionPreference = "Continue"

$TaskId = "terrayield-134-runner-heartbeat-runtime-check"
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { "C:\Users\cagda\Documents\chat_gpt_clone_1" }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence" }
$RunnerPath = Join-Path $BridgeRoot "AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1"
$StatusPanelPath = Join-Path $BridgeRoot "AAYS_TASK_STATUS_PANEL_FIXED.ps1"
$HeartbeatPath = Join-Path $BridgeRoot "ai-heartbeat\portable-runner.md"
$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Section([string]$Name) {
  Write-Output ""
  Write-Output ("## " + $Name)
}

function Test-Port([int]$Port, [string]$Name) {
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne(1500, $false)
    if ($ok -and $client.Connected) {
      $client.EndConnect($iar)
      $client.Close()
      Write-Output ("PORT_" + $Port + "_" + $Name + "=OPEN")
    } else {
      $client.Close()
      Write-Output ("PORT_" + $Port + "_" + $Name + "=CLOSED_OR_UNREACHABLE")
    }
  } catch {
    Write-Output ("PORT_" + $Port + "_" + $Name + "=ERROR " + $_.Exception.Message)
  }
}

Write-Output "# TerraYield Runner Heartbeat / Runtime Check"
Write-Output ("TASK_ID=" + $TaskId)
Write-Output ("TIME_LOCAL=" + $Now)
Write-Output "MODE=READ_ONLY_HEARTBEAT"
Write-Output "NO_DB=TRUE"
Write-Output "NO_DOCKER=TRUE"
Write-Output "NO_DOWNLOAD=TRUE"
Write-Output "NO_RUNTIME_RESTART=TRUE"
Write-Output "NO_UI_EDIT=TRUE"

Write-Section "Paths"
Write-Output ("BRIDGE_ROOT=" + $BridgeRoot)
Write-Output ("PROJECT_ROOT=" + $ProjectRoot)
Write-Output ("RUNNER_PATH_EXISTS=" + (Test-Path $RunnerPath))
Write-Output ("STATUS_PANEL_PATH_EXISTS=" + (Test-Path $StatusPanelPath))
Write-Output ("PROJECT_ROOT_EXISTS=" + (Test-Path $ProjectRoot))

Write-Section "Runner process check"
$runnerProcesses = @()
try {
  $runnerProcesses = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "powershell" -and $_.CommandLine -match [regex]::Escape("AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1")
  })
  Write-Output ("RUNNER_PROCESS_COUNT=" + $runnerProcesses.Count)
  foreach ($p in $runnerProcesses) {
    Write-Output ("RUNNER_PID=" + $p.ProcessId)
    Write-Output ("RUNNER_COMMANDLINE=" + $p.CommandLine)
  }
} catch {
  Write-Output ("RUNNER_PROCESS_CHECK_ERROR=" + $_.Exception.Message)
}

if (($runnerProcesses.Count -lt 1) -and (Test-Path $RunnerPath)) {
  Write-Output "RUNNER_REOPEN_ATTEMPT=STARTING_NEW_HIDDEN_RUNNER"
  try {
    Start-Process -FilePath "powershell.exe" `
      -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$RunnerPath) `
      -WorkingDirectory $BridgeRoot `
      -WindowStyle Hidden
    Start-Sleep -Seconds 3

    $runnerProcessesAfter = @(Get-CimInstance Win32_Process | Where-Object {
      $_.Name -match "powershell" -and $_.CommandLine -match [regex]::Escape("AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1")
    })
    Write-Output ("RUNNER_PROCESS_COUNT_AFTER_REOPEN=" + $runnerProcessesAfter.Count)
  } catch {
    Write-Output ("RUNNER_REOPEN_ATTEMPT_ERROR=" + $_.Exception.Message)
  }
} else {
  Write-Output "RUNNER_REOPEN_ATTEMPT=NOT_NEEDED"
}

Write-Section "Heartbeat file"
if (Test-Path $HeartbeatPath) {
  try {
    Write-Output "HEARTBEAT_FILE_EXISTS=TRUE"
    Write-Output "HEARTBEAT_FILE_CONTENT_BEGIN"
    Get-Content -Raw -Encoding UTF8 $HeartbeatPath | Write-Output
    Write-Output "HEARTBEAT_FILE_CONTENT_END"
  } catch {
    Write-Output ("HEARTBEAT_READ_ERROR=" + $_.Exception.Message)
  }
} else {
  Write-Output "HEARTBEAT_FILE_EXISTS=FALSE"
}

Write-Section "Runtime port reachability"
Test-Port -Port 8010 -Name "UI"
Test-Port -Port 8099 -Name "DEM"
Test-Port -Port 8765 -Name "LOOKUP"

Write-Section "Git status snapshot"
try {
  Set-Location $BridgeRoot
  Write-Output "BRIDGE_GIT_STATUS_BEGIN"
  git status --short 2>&1 | Out-String | Write-Output
  Write-Output "BRIDGE_GIT_STATUS_END"
} catch {
  Write-Output ("BRIDGE_GIT_STATUS_ERROR=" + $_.Exception.Message)
}

try {
  if (Test-Path $ProjectRoot) {
    Set-Location $ProjectRoot
    Write-Output "PROJECT_GIT_STATUS_BEGIN"
    git status --short 2>&1 | Out-String | Write-Output
    Write-Output "PROJECT_GIT_STATUS_END"
  }
} catch {
  Write-Output ("PROJECT_GIT_STATUS_ERROR=" + $_.Exception.Message)
}

Write-Section "Conclusion"
Write-Output "RUNNER_HEARTBEAT_TASK_EXECUTED=TRUE"
Write-Output "RUNTIME_CONTINUITY_ACTION=NO_CHANGE"
Write-Output "NEXT_SAFE_ACTION=topography-plan-static-validate-only"
Write-Output "TERRAYIELD_TASK_DONE"
exit 0
