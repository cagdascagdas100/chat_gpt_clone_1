$ErrorActionPreference="Continue"

$RepoRoot="C:\Users\cagda\Documents\GitHub\AAYS"
$BridgeRoot="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$WorkBranch="aays-runner-v17-icon-work-20260603-232706"
$WorktreePath="F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706"
$Now=Get-Date -Format "yyyyMMdd-HHmmss"

$SourceIcon=Join-Path $RepoRoot "england_map_web\assets\icons\terrayield_icons\hight_differance.png"
$TargetIcon=Join-Path $WorktreePath "england_map_web\assets\icons\terrayield_icons\hight_differance.png"
$TargetIconDir=Split-Path $TargetIcon
$app=Join-Path $WorktreePath "england_map_web\app.js"
$backup=Join-Path $WorktreePath ("app.js.v17.icon.backup."+ $Now)

$ReportDir=Join-Path $WorktreePath "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE\reports"
$BridgeResultDir=Join-Path $BridgeRoot "ai-results"
New-Item -ItemType Directory -Force -Path $TargetIconDir,$ReportDir,$BridgeResultDir | Out-Null

$Report=Join-Path $ReportDir ("v17_icon_patch_with_asset_"+$Now+".txt")
$BridgeReport=Join-Path $BridgeResultDir ("AAYS_SAME_PROJECT_NEW_PAGE_v17_icon_patch_with_asset_"+$Now+".txt")

$lines=@()
$lines+="PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE"
$lines+="RUN_AT=$((Get-Date).ToString('o'))"
$lines+="MODE=V17_ICON_PATCH_WITH_LOCAL_ASSET_COPY_FROM_RUNNER_FILE"
$lines+="WORK_BRANCH=$WorkBranch"
$lines+="WORKTREE_PATH=$WorktreePath"
$lines+="SAFETY=no_delete_no_reset_hard_no_git_clean_no_force_push_no_db_write_no_prod_deploy"
$lines+="source_icon_exists=$(Test-Path $SourceIcon)"
$lines+="app_js_exists=$(Test-Path $app)"

$nodeOk=$false

if((Test-Path $SourceIcon) -and (Test-Path $app)){
  Copy-Item $SourceIcon $TargetIcon -Force
  $lines+="target_icon_exists_after_copy=$(Test-Path $TargetIcon)"

  Copy-Item $app $backup -Force
  $raw=Get-Content $app -Raw
  $lines+="before_has_hight_differance_png=$([bool]($raw -match 'hight_differance\.png'))"

  if($raw -notmatch 'hight_differance\.png'){
    $target='  const showTopographyOverlayEl = document.getElementById("showTopographyOverlay");'
    $insert=@'
  const TOPOGRAPHY_ICON_URL = "./assets/icons/terrayield_icons/hight_differance.png";
  if (showTopographyOverlayEl) {
    showTopographyOverlayEl.setAttribute("data-icon-src", TOPOGRAPHY_ICON_URL);
    showTopographyOverlayEl.style.backgroundImage = `url("${TOPOGRAPHY_ICON_URL}")`;
    showTopographyOverlayEl.style.backgroundRepeat = "no-repeat";
    showTopographyOverlayEl.style.backgroundPosition = "0.65rem center";
    showTopographyOverlayEl.style.backgroundSize = "1rem 1rem";
  }
'@

    if($raw.Contains($target)){
      $raw=$raw.Replace($target, $target + [Environment]::NewLine + $insert)
      Set-Content $app $raw -Encoding UTF8
      $lines+="patch_action=inserted_icon_constant_and_binding_after_showTopographyOverlayEl"
    } else {
      $lines+="patch_action=target_line_not_found_no_change"
    }
  } else {
    $lines+="patch_action=no_change_already_present"
  }

  Push-Location $WorktreePath
  node --check "england_map_web\app.js" *> "$env:TEMP\aays_v17_icon_asset_node_$Now.txt"
  $nodeExit=$LASTEXITCODE
  Pop-Location

  if($nodeExit -eq 0){
    $nodeOk=$true
    $lines+="node_check_app_js=true"
  } else {
    Copy-Item $backup $app -Force
    $lines+="node_check_app_js=false"
    $lines+="restore_action=app_js_restored_from_backup"
    Get-Content "$env:TEMP\aays_v17_icon_asset_node_$Now.txt" -ErrorAction SilentlyContinue | ForEach-Object { $lines+=("node_out="+$_) }
  }

  $after=Get-Content $app -Raw
  $lines+="after_has_hight_differance_png=$([bool]($after -match 'hight_differance\.png'))"
} else {
  $lines+="ERROR=missing_source_icon_or_app_js"
}

if($nodeOk -and (Test-Path $TargetIcon) -and ((Get-Content $app -Raw) -match 'hight_differance\.png')){
  $lines+="KICK_ACTION=executed_one_task_done"
  $lines+="PROGRESS_ESTIMATE=47"
  $lines+="FINAL_LABEL=AAYS_TerraYield_V17_ICON_PATCH_WITH_ASSET_APPLIED"
} else {
  $lines+="KICK_ACTION=executed_one_task_done_with_warnings"
  $lines+="PROGRESS_ESTIMATE=45"
  $lines+="FINAL_LABEL=AAYS_TerraYield_V17_ICON_PATCH_WITH_ASSET_REVIEW_REQUIRED"
}

$txt=$lines -join [Environment]::NewLine
$txt | Set-Content $Report -Encoding UTF8
$txt | Set-Content $BridgeReport -Encoding UTF8

Push-Location $WorktreePath
git add -- "england_map_web/app.js" "england_map_web/assets/icons/terrayield_icons/hight_differance.png" $Report
git commit -m "Apply AAYS V17 topography icon patch with asset $Now"
git push origin HEAD:$WorkBranch
Pop-Location

Write-Host "WORK_BRANCH=$WorkBranch"
Write-Host "REPORT=$Report"
Write-Host "PROGRESS_ESTIMATE_EXPECTED=47"
Write-Host "Bekleme suresi: 2-5 dakika"
