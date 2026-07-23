param([string]$Repo)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Slot = 'ready_to_sell_1'
$CanonicalBranch = 'codex/aays-single-runner-v5-20260706'
$ChannelBranch = 'recovery/ready_to_sell_1-command-channel'
$ReportPath = 'docs/chatgpt_status/_shared/recovery_inbox/ready_to_sell_1/latest.json'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$StartedUtc = (Get-Date).ToUniversalTime().ToString('o')
$script:Repair = [ordered]@{
  schema_version = 3
  protocol = 'AAYS_READY_TO_SELL_1_SAFE_REPAIR_V3'
  slot_id = $Slot
  started_at_utc = $StartedUtc
  completed_at_utc = $null
  state = 'RUNNING'
  error = $null
  safety = [ordered]@{
    reset_hard_used = $false
    git_clean_used = $false
    force_push_used = $false
    tracked_changes_preserved_in_stash = $false
    local_ahead_commits_preserved_by_normal_push = $false
    other_slot_files_deleted = $false
  }
  repository = [ordered]@{}
  runner = [ordered]@{ before = @(); stopped_duplicate_pids = @(); after = @() }
  git = [ordered]@{}
}

function Protect([AllowNull()][string]$Text) {
  if ($null -eq $Text) { return '' }
  $safe = $Text
  if ($script:RepoRoot) { $safe = $safe -replace [regex]::Escape($script:RepoRoot), '<REPO>' }
  if ($HOME) { $safe = $safe -replace [regex]::Escape($HOME), '<HOME>' }
  $safe = [regex]::Replace($safe, '(?i)https://[^\s/@]+(?::[^\s/@]*)?@github\.com', 'https://github.com')
  $safe = [regex]::Replace($safe, '(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b', '<REDACTED_TOKEN>')
  return $safe
}

function QuoteArg([string]$Value) {
  if ($Value -notmatch '[\s"]') { return $Value }
  return '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

function RunTimed {
  param([string]$FilePath,[string[]]$Arguments,[int]$TimeoutSeconds=60,[string]$WorkingDirectory)
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = $FilePath
  $psi.Arguments = (($Arguments | ForEach-Object { QuoteArg "$_" }) -join ' ')
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.CreateNoWindow = $true
  if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
  $p = [System.Diagnostics.Process]::new(); $p.StartInfo = $psi
  if (-not $p.Start()) { throw "Process baslatilamadi: $FilePath" }
  $outTask = $p.StandardOutput.ReadToEndAsync(); $errTask = $p.StandardError.ReadToEndAsync()
  $finished = $p.WaitForExit($TimeoutSeconds * 1000)
  $timedOut = -not $finished
  if ($timedOut) { try { $p.Kill() } catch {}; try { $p.WaitForExit(5000) | Out-Null } catch {} }
  try { $stdout = $outTask.Result } catch { $stdout = '' }
  try { $stderr = $errTask.Result } catch { $stderr = '' }
  $code = if ($timedOut) { 124 } else { $p.ExitCode }
  $p.Dispose()
  return [ordered]@{ exit_code=$code; timed_out=$timedOut; stdout=(Protect $stdout.Trim()); stderr=(Protect $stderr.Trim()) }
}

function Git {
  param([string[]]$Arguments,[int]$TimeoutSeconds=60,[string]$At)
  if (-not $At) { $At = $script:RepoRoot }
  return RunTimed -FilePath 'git.exe' -Arguments (@('-C',$At)+$Arguments) -TimeoutSeconds $TimeoutSeconds -WorkingDirectory $At
}

function MustGit {
  param([string[]]$Arguments,[string]$Label,[int]$TimeoutSeconds=60,[string]$At)
  $r = Git -Arguments $Arguments -TimeoutSeconds $TimeoutSeconds -At $At
  $script:Repair.git[$Label] = $r
  if ($r.exit_code -ne 0) { throw "$Label basarisiz. $($r.stderr) $($r.stdout)" }
  return $r
}

function FindRepo([string]$Preferred) {
  $candidates = @($Preferred,(Get-Location).Path,$env:AAYS_REPO,(Join-Path $HOME 'chat_gpt_clone_1'),(Join-Path $HOME 'Desktop\chat_gpt_clone_1'),(Join-Path $HOME 'Documents\chat_gpt_clone_1'),'C:\AAYS\chat_gpt_clone_1','D:\AAYS\chat_gpt_clone_1') | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
  foreach ($c in $candidates) {
    $r = RunTimed -FilePath 'git.exe' -Arguments @('-C',$c,'rev-parse','--show-toplevel') -TimeoutSeconds 15 -WorkingDirectory $c
    if ($r.exit_code -eq 0 -and $r.stdout) { return $r.stdout.Trim() }
  }
  $entered = Read-Host 'chat_gpt_clone_1 repo klasorunun tam yolunu yazin'
  $r = RunTimed -FilePath 'git.exe' -Arguments @('-C',$entered,'rev-parse','--show-toplevel') -TimeoutSeconds 15 -WorkingDirectory $entered
  if ($r.exit_code -ne 0 -or -not $r.stdout) { throw 'Gecerli Git deposu bulunamadi.' }
  return $r.stdout.Trim()
}

function GetRunnerProcesses {
  return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -and $_.Name -match '^(python|pythonw|node)(\.exe)?$' -and $_.CommandLine -match '(?i)(aays|terrayield)' -and $_.CommandLine -match '(?i)(single[-_]?runner|runner\.(py|js)|run[_-]?runner)'
  } | ForEach-Object {
    [ordered]@{ pid=$_.ProcessId; parent_pid=$_.ParentProcessId; name=$_.Name; created="$($_.CreationDate)"; command_line=(Protect $_.CommandLine); normalized=(($_.CommandLine -replace '\s+',' ').Trim().ToLowerInvariant()) }
  })
}

function PublishReport {
  $script:Repair.completed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  $json = $script:Repair | ConvertTo-Json -Depth 30
  if ([Text.Encoding]::UTF8.GetByteCount($json) -ge 45MB) { throw 'Recovery raporu 45 MiB sinirini asti.' }
  $temp = Join-Path ([IO.Path]::GetTempPath()) ('aays-rts1-repair-v3-' + [guid]::NewGuid().ToString('N'))
  try {
    $originUrl = $script:Repair.repository.origin
    $clone = RunTimed -FilePath 'git.exe' -Arguments @('clone','--depth','1','--branch',$ChannelBranch,$originUrl,$temp) -TimeoutSeconds 120
    if ($clone.exit_code -ne 0) { throw "Recovery channel clone basarisiz: $($clone.stderr)" }
    $full = Join-Path $temp ($ReportPath -replace '/','\')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $full) | Out-Null
    [IO.File]::WriteAllText($full,$json,[Text.UTF8Encoding]::new($false))
    foreach ($cfg in @(@('config','user.name','AAYS Recovery Channel'),@('config','user.email','aays-recovery@users.noreply.github.com'))) {
      $x = RunTimed -FilePath 'git.exe' -Arguments (@('-C',$temp)+$cfg) -TimeoutSeconds 15 -WorkingDirectory $temp
      if ($x.exit_code -ne 0) { throw 'Recovery git config basarisiz.' }
    }
    $add = RunTimed -FilePath 'git.exe' -Arguments @('-C',$temp,'add','--',$ReportPath) -TimeoutSeconds 30 -WorkingDirectory $temp
    if ($add.exit_code -ne 0) { throw "Recovery report add basarisiz: $($add.stderr)" }
    $commit = RunTimed -FilePath 'git.exe' -Arguments @('-C',$temp,'commit','-m',"recovery($Slot): publish safe repair result v3") -TimeoutSeconds 30 -WorkingDirectory $temp
    if ($commit.exit_code -ne 0) { throw "Recovery report commit basarisiz: $($commit.stderr)" }
    $pushed = $false
    for ($i=1; $i -le 5 -and -not $pushed; $i++) {
      $push = RunTimed -FilePath 'git.exe' -Arguments @('-C',$temp,'push','origin',"HEAD:refs/heads/$ChannelBranch") -TimeoutSeconds 90 -WorkingDirectory $temp
      if ($push.exit_code -eq 0) { $pushed=$true; break }
      $fetch = RunTimed -FilePath 'git.exe' -Arguments @('-C',$temp,'fetch','origin',$ChannelBranch) -TimeoutSeconds 60 -WorkingDirectory $temp
      if ($fetch.exit_code -ne 0) { continue }
      $rebase = RunTimed -FilePath 'git.exe' -Arguments @('-C',$temp,'rebase',"origin/$ChannelBranch") -TimeoutSeconds 30 -WorkingDirectory $temp
      if ($rebase.exit_code -ne 0) { break }
    }
    if (-not $pushed) { throw 'Recovery report normal push basarisiz.' }
  } finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue }
  }
}

$script:RepoRoot = $null
try {
  $script:RepoRoot = FindRepo $Repo
  $origin = MustGit -Arguments @('remote','get-url','origin') -Label 'origin' -TimeoutSeconds 15
  if (($origin.stdout + $origin.stderr) -notmatch 'cagdascagdas100[/:]chat_gpt_clone_1(?:\.git)?$') { throw "Beklenmeyen origin: $($origin.stdout)" }
  $script:Repair.repository.origin = $origin.stdout.Trim()
  $script:Repair.repository.repo_root = '<REPO>'

  $before = GetRunnerProcesses
  $script:Repair.runner.before = $before | ForEach-Object { $copy=[ordered]@{}; foreach($k in $_.Keys){if($k-ne'normalized'){$copy[$k]=$_.Item($k)}}; $copy }
  foreach ($group in ($before | Group-Object normalized | Where-Object Count -gt 1)) {
    $ordered = @($group.Group | Sort-Object created)
    foreach ($dup in ($ordered | Select-Object -Skip 1)) {
      try { Stop-Process -Id $dup.pid -ErrorAction Stop; $script:Repair.runner.stopped_duplicate_pids += $dup.pid } catch {}
    }
  }
  $after = GetRunnerProcesses
  $script:Repair.runner.after = $after | ForEach-Object { $copy=[ordered]@{}; foreach($k in $_.Keys){if($k-ne'normalized'){$copy[$k]=$_.Item($k)}}; $copy }

  $deadline = (Get-Date).AddSeconds(60)
  do {
    $activeGit = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^git(\.exe)?$' -and $_.CommandLine -and $_.CommandLine -match [regex]::Escape($script:RepoRoot) })
    if ($activeGit.Count -eq 0) { break }
    Start-Sleep -Seconds 3
  } while ((Get-Date) -lt $deadline)
  if ($activeGit.Count -gt 0) { throw 'Repo icin aktif Git islemi 60 saniye icinde bitmedi.' }

  $statusBefore = MustGit -Arguments @('status','--porcelain=v2','--branch','--untracked-files=no') -Label 'status_before' -TimeoutSeconds 60
  $trackedLines = @($statusBefore.stdout -split "`r?`n" | Where-Object { $_ -match '^[12u] ' })
  $script:Repair.repository.tracked_change_count_before = $trackedLines.Count

  if ($trackedLines.Count -gt 0) {
    $stashMessage = "AAYS SYSTEM preserve tracked publisher changes $Stamp"
    $stash = MustGit -Arguments @('stash','push','-m',$stashMessage) -Label 'stash_tracked_changes' -TimeoutSeconds 300
    $stashSha = MustGit -Arguments @('rev-parse','refs/stash') -Label 'stash_sha' -TimeoutSeconds 15
    $script:Repair.repository.stash = [ordered]@{ message=$stashMessage; sha=$stashSha.stdout.Trim() }
    $script:Repair.safety.tracked_changes_preserved_in_stash = $true
  }

  MustGit -Arguments @('fetch','--prune','origin',"+refs/heads/${CanonicalBranch}:refs/remotes/origin/${CanonicalBranch}") -Label 'fetch_canonical' -TimeoutSeconds 120 | Out-Null
  $current = MustGit -Arguments @('branch','--show-current') -Label 'current_branch' -TimeoutSeconds 15
  $script:Repair.repository.branch_before = $current.stdout.Trim()

  $canonicalLocal = Git -Arguments @('show-ref','--verify','--quiet',"refs/heads/$CanonicalBranch") -TimeoutSeconds 15
  if ($canonicalLocal.exit_code -eq 0) {
    $counts = MustGit -Arguments @('rev-list','--left-right','--count',"refs/heads/$CanonicalBranch...origin/$CanonicalBranch") -Label 'canonical_ahead_behind' -TimeoutSeconds 30
    $parts = $counts.stdout.Trim() -split '\s+'
    $ahead = [int]$parts[0]
    if ($ahead -gt 0) {
      $backupBranch = "recovery/system-canonical-ahead-$Stamp"
      MustGit -Arguments @('push','origin',"refs/heads/${CanonicalBranch}:refs/heads/${backupBranch}") -Label 'push_local_ahead_backup' -TimeoutSeconds 120 | Out-Null
      if ($current.stdout.Trim() -eq $CanonicalBranch) {
        MustGit -Arguments @('branch','-m',$backupBranch) -Label 'rename_current_canonical_to_backup' -TimeoutSeconds 30 | Out-Null
      } else {
        MustGit -Arguments @('branch','-m',$CanonicalBranch,$backupBranch) -Label 'rename_local_canonical_to_backup' -TimeoutSeconds 30 | Out-Null
      }
      $script:Repair.repository.backup_branch = $backupBranch
      $script:Repair.safety.local_ahead_commits_preserved_by_normal_push = $true
    }
  }

  if ((MustGit -Arguments @('branch','--show-current') -Label 'branch_before_switch' -TimeoutSeconds 15).stdout.Trim() -ne $CanonicalBranch) {
    $existsNow = Git -Arguments @('show-ref','--verify','--quiet',"refs/heads/$CanonicalBranch") -TimeoutSeconds 15
    if ($existsNow.exit_code -eq 0) {
      MustGit -Arguments @('switch',$CanonicalBranch) -Label 'switch_canonical' -TimeoutSeconds 60 | Out-Null
    } else {
      MustGit -Arguments @('switch','-c',$CanonicalBranch,'--track',"origin/$CanonicalBranch") -Label 'create_tracking_canonical' -TimeoutSeconds 60 | Out-Null
    }
  }

  MustGit -Arguments @('pull','--ff-only','origin',$CanonicalBranch) -Label 'pull_ff_only' -TimeoutSeconds 120 | Out-Null
  $localHead = MustGit -Arguments @('rev-parse','HEAD') -Label 'local_head_after' -TimeoutSeconds 15
  $remoteHead = MustGit -Arguments @('rev-parse',"origin/$CanonicalBranch") -Label 'remote_head_after' -TimeoutSeconds 15
  $statusAfter = MustGit -Arguments @('status','--porcelain=v2','--branch','--untracked-files=no') -Label 'status_after' -TimeoutSeconds 60
  $afterTracked = @($statusAfter.stdout -split "`r?`n" | Where-Object { $_ -match '^[12u] ' })
  $script:Repair.repository.tracked_change_count_after = $afterTracked.Count
  $script:Repair.repository.local_head_after = $localHead.stdout.Trim()
  $script:Repair.repository.remote_head_after = $remoteHead.stdout.Trim()
  if ($afterTracked.Count -ne 0) { throw "Tracked worktree temiz degil: $($afterTracked.Count)" }
  if ($localHead.stdout.Trim() -ne $remoteHead.stdout.Trim()) { throw 'Yerel ve uzak canonical HEAD eslesmiyor.' }

  $script:Repair.state = 'RESOLVED'
} catch {
  $script:Repair.state = 'BLOCKED'
  $script:Repair.error = Protect $_.Exception.Message
} finally {
  try { PublishReport } catch { Write-Error "Recovery sonucu GitHub'a yazilamadi: $($_.Exception.Message)"; exit 2 }
}

if ($script:Repair.state -eq 'RESOLVED') {
  Write-Host 'AAYS_READY_TO_SELL_1_REPAIR_RESOLVED' -ForegroundColor Green
  exit 0
}
Write-Error "AAYS_READY_TO_SELL_1_REPAIR_BLOCKED: $($script:Repair.error)"
exit 1
