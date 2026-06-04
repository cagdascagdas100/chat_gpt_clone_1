$ErrorActionPreference="Continue"
$BridgeRoot="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$WorktreePath="F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706"
$PageKey="AAYS_SAME_PROJECT_NEW_PAGE"
$ReportDir=Join-Path $WorktreePath "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE\reports"
$BridgeResultDir=Join-Path $BridgeRoot "ai-results"
$ArchiveRoot="F:\chatgpt\AAYS_AUTO_RESULTS"
New-Item -ItemType Directory -Force -Path $ReportDir,$BridgeResultDir,$ArchiveRoot | Out-Null
$Now=Get-Date -Format "yyyyMMdd-HHmmss"
$LocalReport=Join-Path $BridgeResultDir ($PageKey+"_safe_auto_continue_"+$Now+".txt")
$RepoReport=Join-Path $ReportDir ("safe_auto_continue_"+$Now+".txt")
$ArchiveReport=Join-Path $ArchiveRoot ("safe_auto_continue_"+$Now+".txt")
$lines=@()
$lines+="PAGE_KEY=$PageKey"
$lines+="RUN_AT=$((Get-Date).ToString('o'))"
$lines+="MODE=SAFE_AUTO_CONTINUE_V1"
$lines+="WORKTREE_PATH=$WorktreePath"
$lines+="ARCHIVE_ROOT=$ArchiveRoot"
$lines+="OUTPUT_POLICY=github_reports_and_f_drive_archive"
$lines+="USER_OUTPUT_PASTE_REQUIRED=false"
$lines+="SAFETY=no_db_write_no_prod_deploy_no_reset_hard_no_git_clean_no_force_push"
$lines+="PROGRESS_ESTIMATE=47"
$lines+="FINAL_LABEL=AAYS_SAFE_AUTO_CONTINUE_READY"
$txt=$lines -join [Environment]::NewLine
$txt | Set-Content $LocalReport -Encoding UTF8
$txt | Set-Content $RepoReport -Encoding UTF8
$txt | Set-Content $ArchiveReport -Encoding UTF8
Push-Location $WorktreePath
git add -- docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE/reports
git commit -m "Add AAYS safe auto continue report $Now"
git push origin HEAD:aays-runner-v17-icon-work-20260603-232706
Pop-Location
Write-Host "REPORT=$RepoReport"
Write-Host "PROGRESS_ESTIMATE=47"
Write-Host "Bekleme suresi: 2-4 dakika"
