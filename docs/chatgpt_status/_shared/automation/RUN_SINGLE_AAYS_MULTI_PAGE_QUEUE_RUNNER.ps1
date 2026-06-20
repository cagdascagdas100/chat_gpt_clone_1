$RepoRoot = "F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706"
$Branch = "aays-runner-v17-icon-work-20260603-232706"
$StatusRootRel = "docs\chatgpt_status"
$IntervalSeconds = 60
$StateRoot = "F:\chatgpt\AAYS_WORK\single_runner\state\MULTI_PAGE"
$RunnerName = "AAYS_SINGLE_MULTI_PAGE_RUNNER"
$MutexName = "Global\AAYS_SINGLE_MULTI_PAGE_RUNNER_aays_runner_v17_icon_work_20260603_232706"

New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
$LogFile = Join-Path $StateRoot "runner.log"
$LastTaskFile = Join-Path $StateRoot "last_task_keys.json"

$createdNew = $false
$mutex = New-Object System.Threading.Mutex($true, $MutexName, [ref]$createdNew)
if (-not $createdNew) {
  Write-Host "[$RunnerName] another runner instance is already active. Exiting."
  exit 0
}

function Write-RunnerLog([string]$Message) {
  $line = "[{0}] {1}" -f (Get-Date).ToString("s"), $Message
  Write-Host $line
  Add-Content -Path $LogFile -Value $line
}

function Invoke-GitChecked([string[]]$GitArgs) {
  if (-not $GitArgs -or $GitArgs.Count -eq 0) {
    throw "git failed: empty argument list"
  }
  & git @GitArgs
  if ($LASTEXITCODE -ne 0) {
    throw "git failed: $($GitArgs -join ' ') exit=$LASTEXITCODE"
  }
}

function Load-LastTasks {
  if (Test-Path $LastTaskFile) {
    try { return Get-Content $LastTaskFile -Raw | ConvertFrom-Json -AsHashtable } catch { return @{} }
  }
  return @{}
}

function Save-LastTasks($Map) {
  $Map | ConvertTo-Json -Depth 10 | Set-Content -Path $LastTaskFile
}

function Get-TaskCandidates {
  $root = Join-Path $RepoRoot $StatusRootRel
  if (-not (Test-Path $root)) { return @() }

  $candidates = @()
  Get-ChildItem $root -Directory | Where-Object { $_.Name -notlike "_*" } | ForEach-Object {
    $pageKey = $_.Name
    $pageRoot = $_.FullName
    foreach ($folder in @("current-task", "queue")) {
      $dir = Join-Path $pageRoot $folder
      if (Test-Path $dir) {
        Get-ChildItem $dir -File | ForEach-Object {
          $txt = Get-Content $_.FullName -Raw
          $pattern = "docs/chatgpt_status/$pageKey/automation/[A-Za-z0-9_.-]+\.ps1"
          $m = [regex]::Match($txt, $pattern)
          if ($m.Success -and $m.Value -notmatch "RUN_SINGLE_AAYS") {
            $scriptFull = Join-Path $RepoRoot ($m.Value -replace "/", "\")
            if (Test-Path $scriptFull) {
              $candidates += [pscustomobject]@{
                PageKey = $pageKey
                SourceFile = $_.FullName
                SourceRel = $_.FullName.Substring($RepoRoot.Length + 1)
                ScriptRel = $m.Value
                ScriptFull = $scriptFull
                ModifiedTicks = $_.LastWriteTimeUtc.Ticks
                Key = "$pageKey|$($m.Value)|$($_.FullName.Substring($RepoRoot.Length + 1))|$($_.LastWriteTimeUtc.Ticks)"
              }
            }
          }
        }
      }
    }
  }
  return $candidates | Sort-Object ModifiedTicks -Descending
}

try {
  Write-RunnerLog "$RunnerName started repo=$RepoRoot branch=$Branch"
  while ($true) {
    try {
      Set-Location $RepoRoot
      Invoke-GitChecked @("fetch", "origin", $Branch)
      Invoke-GitChecked @("pull", "--rebase", "--autostash", "origin", $Branch)

      $last = Load-LastTasks
      $tasks = Get-TaskCandidates
      foreach ($task in $tasks) {
        if (-not $last.ContainsKey($task.Key)) {
          Write-RunnerLog "running page=$($task.PageKey) script=$($task.ScriptRel) source=$($task.SourceRel)"
          & powershell -NoProfile -ExecutionPolicy Bypass -File $task.ScriptFull
          $exitCode = $LASTEXITCODE
          Write-RunnerLog "finished page=$($task.PageKey) exit=$exitCode script=$($task.ScriptRel)"
          $last[$task.Key] = (Get-Date).ToString("s")
          Save-LastTasks $last
          break
        }
      }

      $heartbeatRoot = Join-Path $RepoRoot "$StatusRootRel\_shared\heartbeat"
      New-Item -ItemType Directory -Force -Path $heartbeatRoot | Out-Null
      $heartbeat = Join-Path $heartbeatRoot "single_multi_page_runner_heartbeat.txt"
      Set-Content -Path $heartbeat -Value "runner=$RunnerName`nbranch=$Branch`nlast_heartbeat=$((Get-Date).ToString('s'))`nrepo=$RepoRoot"
      git add $heartbeat | Out-Null
      git commit -m "Update shared single runner heartbeat" | Out-Null
      git push origin "HEAD:$Branch" | Out-Null
    }
    catch {
      Write-RunnerLog "ERROR $($_.Exception.Message)"
    }
    Start-Sleep -Seconds $IntervalSeconds
  }
}
finally {
  if ($mutex) { $mutex.ReleaseMutex() | Out-Null; $mutex.Dispose() }
}
