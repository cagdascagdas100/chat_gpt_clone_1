$ErrorActionPreference = "Continue"
$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$WorktreePath = "F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706"
$PageKey = "AAYS_SAME_PROJECT_NEW_PAGE"
$BranchName = "aays-runner-v17-icon-work-20260603-232706"
$ArchiveRoot = "F:\chatgpt\AAYS_AUTO_RESULTS"
$Now = Get-Date -Format "yyyyMMdd-HHmmss"
$ReportDir = Join-Path $WorktreePath "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE\reports"
$BridgeResultDir = Join-Path $BridgeRoot "ai-results"
$RunArchiveDir = Join-Path $ArchiveRoot ("parallel_supervisor_" + $Now)
New-Item -ItemType Directory -Force -Path $ReportDir,$BridgeResultDir,$RunArchiveDir | Out-Null

function Save-Text($Path, $Lines) {
  ($Lines -join [Environment]::NewLine) | Set-Content $Path -Encoding UTF8
}

$common = @{
  PageKey = $PageKey
  BridgeRoot = $BridgeRoot
  WorktreePath = $WorktreePath
  BranchName = $BranchName
  ReportDir = $ReportDir
  BridgeResultDir = $BridgeResultDir
  RunArchiveDir = $RunArchiveDir
  Now = $Now
}

$jobs = @()
$jobs += Start-Job -Name "disk_check" -ArgumentList $common -ScriptBlock {
  param($c)
  $lines=@("JOB=disk_check","RUN_AT=$((Get-Date).ToString('o'))")
  foreach($d in @("C","F")){
    try { $psd=Get-PSDrive $d -ErrorAction Stop; $lines += ("drive_"+$d+"_free_gb="+[math]::Round($psd.Free/1GB,2)); $lines += ("drive_"+$d+"_used_gb="+[math]::Round($psd.Used/1GB,2)) } catch { $lines += ("drive_"+$d+"_error="+$_.Exception.Message) }
  }
  $p=Join-Path $c.RunArchiveDir "job_disk_check.txt"; ($lines -join [Environment]::NewLine) | Set-Content $p -Encoding UTF8; $p
}
$jobs += Start-Job -Name "queue_check" -ArgumentList $common -ScriptBlock {
  param($c)
  $q=Join-Path $c.BridgeRoot "ai-queue"
  $lines=@("JOB=queue_check","RUN_AT=$((Get-Date).ToString('o'))","queue_root_exists=$(Test-Path $q)")
  foreach($s in @("pending","running","done","failed")){
    $dir=Join-Path $q $s
    $count=@(Get-ChildItem $dir -File -ErrorAction SilentlyContinue).Count
    $lines += ("queue_"+$s+"_files="+$count)
  }
  $lines += "queue_lock_exists=$(Test-Path (Join-Path $q '.queue-lock'))"
  $p=Join-Path $c.RunArchiveDir "job_queue_check.txt"; ($lines -join [Environment]::NewLine) | Set-Content $p -Encoding UTF8; $p
}
$jobs += Start-Job -Name "git_check" -ArgumentList $common -ScriptBlock {
  param($c)
  $lines=@("JOB=git_check","RUN_AT=$((Get-Date).ToString('o'))","worktree_exists=$(Test-Path $c.WorktreePath)")
  if(Test-Path $c.WorktreePath){
    $lines += "branch=$((git -C $c.WorktreePath rev-parse --abbrev-ref HEAD) 2>&1)"
    $lines += "head=$((git -C $c.WorktreePath rev-parse --short HEAD) 2>&1)"
    $lines += "status_short_begin"
    $lines += (git -C $c.WorktreePath status --short 2>&1)
    $lines += "status_short_end"
    git -C $c.WorktreePath fetch origin $c.BranchName *> (Join-Path $c.RunArchiveDir "job_git_fetch.txt")
    $lines += "fetch_exit_code=$LASTEXITCODE"
  }
  $p=Join-Path $c.RunArchiveDir "job_git_check.txt"; ($lines -join [Environment]::NewLine) | Set-Content $p -Encoding UTF8; $p
}
$jobs += Start-Job -Name "app_check" -ArgumentList $common -ScriptBlock {
  param($c)
  $app=Join-Path $c.WorktreePath "england_map_web\app.js"
  $lines=@("JOB=app_check","RUN_AT=$((Get-Date).ToString('o'))","app_js_exists=$(Test-Path $app)")
  if(Test-Path $app){
    node --check $app *> (Join-Path $c.RunArchiveDir "job_app_node_check.txt")
    $lines += "node_check_exit_code=$LASTEXITCODE"
  }
  $p=Join-Path $c.RunArchiveDir "job_app_check.txt"; ($lines -join [Environment]::NewLine) | Set-Content $p -Encoding UTF8; $p
}
$jobs += Start-Job -Name "asset_check" -ArgumentList $common -ScriptBlock {
  param($c)
  $icon=Join-Path $c.WorktreePath "england_map_web\assets\icons\terrayield_icons\hight_differance.png"
  $cfg=Join-Path $c.WorktreePath "england_map_web\config\topography.overlay.json"
  $lines=@("JOB=asset_check","RUN_AT=$((Get-Date).ToString('o'))","target_icon_exists=$(Test-Path $icon)","topography_config_exists=$(Test-Path $cfg)")
  if(Test-Path $icon){ $lines += "target_icon_size_bytes=$((Get-Item $icon).Length)" }
  $p=Join-Path $c.RunArchiveDir "job_asset_check.txt"; ($lines -join [Environment]::NewLine) | Set-Content $p -Encoding UTF8; $p
}
$jobs += Start-Job -Name "result_sync" -ArgumentList $common -ScriptBlock {
  param($c)
  $lines=@("JOB=result_sync","RUN_AT=$((Get-Date).ToString('o'))")
  New-Item -ItemType Directory -Force -Path $c.ReportDir,$c.RunArchiveDir | Out-Null
  $files=@(Get-ChildItem $c.BridgeResultDir -Filter ($c.PageKey+"*.txt") -File -ErrorAction SilentlyContinue)
  $lines += "bridge_result_count=$($files.Count)"
  foreach($f in $files){ Copy-Item $f.FullName $c.ReportDir -Force -ErrorAction SilentlyContinue; Copy-Item $f.FullName $c.RunArchiveDir -Force -ErrorAction SilentlyContinue }
  $p=Join-Path $c.RunArchiveDir "job_result_sync.txt"; ($lines -join [Environment]::NewLine) | Set-Content $p -Encoding UTF8; $p
}

Wait-Job $jobs -Timeout 900 | Out-Null
$jobFiles=@()
foreach($j in $jobs){
  try { $jobFiles += Receive-Job $j -ErrorAction SilentlyContinue } catch {}
  Remove-Job $j -Force -ErrorAction SilentlyContinue
}

$summary=@()
$summary += "PAGE_KEY=$PageKey"
$summary += "RUN_AT=$((Get-Date).ToString('o'))"
$summary += "MODE=PARALLEL_SUPERVISOR_V1"
$summary += "WORKTREE_PATH=$WorktreePath"
$summary += "ARCHIVE_ROOT=$RunArchiveDir"
$summary += "PARALLEL_JOB_COUNT=6"
$summary += "OUTPUT_POLICY=github_reports_and_f_drive_archive"
$summary += "USER_OUTPUT_PASTE_REQUIRED=false"
$summary += "SAFETY=read_mostly_status_checks_no_db_write_no_prod_deploy"
foreach($jf in $jobFiles){ if(Test-Path $jf){ $summary += "JOB_REPORT=$jf"; $summary += (Get-Content $jf -Raw) } }
$summary += "PROGRESS_ESTIMATE=49"
$summary += "FINAL_LABEL=AAYS_PARALLEL_SUPERVISOR_READY"
$repoReport=Join-Path $ReportDir ("parallel_supervisor_"+$Now+".txt")
$bridgeReport=Join-Path $BridgeResultDir ($PageKey+"_parallel_supervisor_"+$Now+".txt")
Save-Text $repoReport $summary
Save-Text $bridgeReport $summary
Save-Text (Join-Path $RunArchiveDir "parallel_supervisor_summary.txt") $summary

Push-Location $WorktreePath
git add -- docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE/reports
$st=(git status --short)
if($st){ git commit -m "Add AAYS parallel supervisor report $Now" }
git pull --ff-only origin $BranchName *> (Join-Path $RunArchiveDir "git_pull_ff_only.txt")
if($LASTEXITCODE -eq 0){ git push origin HEAD:$BranchName *> (Join-Path $RunArchiveDir "git_push.txt") }
Pop-Location
Write-Host "PROGRESS_ESTIMATE=49"
Write-Host "REPORT=$repoReport"
Write-Host "Bekleme suresi: 8-15 dakika"
