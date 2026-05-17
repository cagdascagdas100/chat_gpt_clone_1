$ErrorActionPreference = "Continue"

$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Branch = "security-accuracy-expansion-20260508"
$QueueRoot = Join-Path $Repo "docs\chatgpt_handoff\local_runner_queue"
$Inbox = Join-Path $QueueRoot "inbox"
$Done = Join-Path $QueueRoot "done"
$Failed = Join-Path $QueueRoot "failed"
$Outputs = Join-Path $QueueRoot "outputs"
$Heartbeat = Join-Path $Outputs "WATCHDOG_HEARTBEAT.txt"

$AllowedTasks = @(
  "012A_STATIC_CLOUD_READY_VALIDATE_AND_PUBLISH.ps1",
  "012B_LOCAL_TEST_SMOKE_PERF_AND_PUBLISH.ps1"
)

New-Item -ItemType Directory -Force -Path $Inbox,$Done,$Failed,$Outputs | Out-Null

function Write-Heartbeat($status, $task) {
  @(
    "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
    "repo=$Repo",
    "branch=$Branch",
    "status=$status",
    "task=$task",
    "safe_mode=true",
    "db_write=none",
    "ddl=none",
    "migration_apply=none",
    "prod_deploy=none",
    "secret_values_printed=false"
  ) | Set-Content -LiteralPath $Heartbeat -Encoding UTF8
}

Set-Location $Repo
Write-Heartbeat "starting" "none"

git fetch origin $Branch | Out-Null
git checkout $Branch | Out-Null
git pull --ff-only origin $Branch | Out-Null

$tasks = Get-ChildItem -LiteralPath $Inbox -Filter "*.ps1" -File -ErrorAction SilentlyContinue | Sort-Object Name
foreach ($task in $tasks) {
  if ($AllowedTasks -notcontains $task.Name) {
    $target = Join-Path $Failed $task.Name
    Move-Item -LiteralPath $task.FullName -Destination $target -Force
    Write-Heartbeat "rejected_not_allowlisted" $task.Name
    continue
  }

  $runId = Get-Date -Format "yyyyMMdd_HHmmss"
  $taskOut = Join-Path $Outputs ($runId + "_" + [IO.Path]::GetFileNameWithoutExtension($task.Name))
  New-Item -ItemType Directory -Force -Path $taskOut | Out-Null
  $stdout = Join-Path $taskOut "stdout.log"
  $stderr = Join-Path $taskOut "stderr.log"

  Write-Heartbeat "started" $task.Name
  powershell -ExecutionPolicy Bypass -File $task.FullName 1> $stdout 2> $stderr
  $exitCode = $LASTEXITCODE

  if ($exitCode -eq 0) {
    Move-Item -LiteralPath $task.FullName -Destination (Join-Path $Done $task.Name) -Force
    Write-Heartbeat "done" $task.Name
  } else {
    Move-Item -LiteralPath $task.FullName -Destination (Join-Path $Failed $task.Name) -Force
    Write-Heartbeat "failed" $task.Name
  }

  git add "docs/chatgpt_handoff" "docs/cloud_ready" | Out-Null
  if (git diff --cached --name-only) {
    git commit -m "Publish watchdog evidence for $($task.Name)" | Out-Null
    if ($LASTEXITCODE -eq 0) {
      git push origin $Branch | Out-Null
    }
  }
}

Write-Heartbeat "idle" "none"
