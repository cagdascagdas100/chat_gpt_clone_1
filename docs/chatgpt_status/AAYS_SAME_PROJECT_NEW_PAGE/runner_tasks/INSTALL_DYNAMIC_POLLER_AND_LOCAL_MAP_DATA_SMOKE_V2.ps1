$ErrorActionPreference='Continue'
$PageKey='AAYS_SAME_PROJECT_NEW_PAGE'
$Branch='aays-runner-v17-icon-work-20260603-232706'
$BridgeRoot='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$ScriptDir=Join-Path $BridgeRoot 'ai-task-scripts'
$QueuePending=Join-Path $BridgeRoot 'ai-queue\pending'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$StateDir=Join-Path $BridgeRoot 'ai-state'
New-Item -ItemType Directory -Force -Path $ScriptDir,$QueuePending,$ResultDir,$StateDir | Out-Null
$Roots=@('F:\chatgpt','F:\','C:\Users\cagda\Documents\GitHub', "$env:USERPROFILE\Documents\GitHub", 'C:\AAYS_GITHUB_BRIDGE_CLEAN2') | Where-Object { $_ -and (Test-Path $_) }
$AppFile=$null
foreach($Root in $Roots){
  $AppFile=Get-ChildItem -Path $Root -Recurse -Filter app.js -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -like '*england_map_web\app.js' } | Select-Object -First 1
  if($AppFile){ break }
}
$Now=Get-Date -Format 'yyyyMMdd-HHmmss'
$InstallReport=Join-Path $ResultDir ("AAYS_DYNAMIC_POLLER_LOCAL_MAP_INSTALL_$Now.txt")
if(!$AppFile){
  "PAGE_KEY=$PageKey`nMODE=DYNAMIC_POLLER_INSTALL`nRESULT=BLOCKED`nBLOCKER=england_map_web_app_js_not_found`nPROGRESS_ESTIMATE=92" | Set-Content $InstallReport -Encoding UTF8
  Write-Host "REPORT=$InstallReport"
  exit 1
}
$WorktreePath=$AppFile.FullName -replace '\\england_map_web\\app\.js$',''
$ReportDir=Join-Path $WorktreePath "docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$SmokeReport=Join-Path $ReportDir ("local_map_data_final_smoke_$Now.txt")
$Web=Join-Path $WorktreePath 'england_map_web'
$Config=Join-Path $Web 'config\topography.overlay.json'
$Icon=Join-Path $Web 'assets\icons\terrayield_icons\hight_differance.png'
$App=Join-Path $Web 'app.js'
"PAGE_KEY=$PageKey`nMODE=LOCAL_MAP_DATA_FINAL_SMOKE`nRUN_AT=$Now`nFOUND_WORKTREE=$WorktreePath" | Set-Content $SmokeReport -Encoding UTF8
"CONFIG_EXISTS=$(Test-Path $Config)" | Add-Content $SmokeReport
"ICON_EXISTS=$(Test-Path $Icon)" | Add-Content $SmokeReport
"APP_EXISTS=$(Test-Path $App)" | Add-Content $SmokeReport
node --check $App >> $SmokeReport 2>&1
$NodeExit=$LASTEXITCODE
"NODE_CHECK_EXIT_CODE=$NodeExit" | Add-Content $SmokeReport
$HasShow=Select-String -Path $App -Pattern 'showTopographyOverlay' -Quiet
$HasIcon=Select-String -Path $App -Pattern 'hight_differance.png' -Quiet
$HasConfig=Select-String -Path $App -Pattern 'topography.overlay.json' -Quiet
"APP_HAS_SHOW_TOPOGRAPHY=$HasShow" | Add-Content $SmokeReport
"APP_HAS_ICON_BINDING=$HasIcon" | Add-Content $SmokeReport
"APP_HAS_CONFIG_FETCH=$HasConfig" | Add-Content $SmokeReport
$HtmlHits=Get-ChildItem $WorktreePath -Recurse -Include *.html,*.htm,*.ejs,*.jsx,*.tsx,*.vue -File -ErrorAction SilentlyContinue | Select-String -Pattern 'showTopographyOverlay|app.js|topography' -List
"UI_ENTRYPOINT_HITS=$($HtmlHits.Count)" | Add-Content $SmokeReport
$HtmlHits | ForEach-Object { "UI_ENTRYPOINT_FILE=$($_.Path)" } | Add-Content $SmokeReport
$StaticPass=((Test-Path $Config) -and (Test-Path $Icon) -and (Test-Path $App) -and ($NodeExit -eq 0) -and $HasShow -and $HasIcon -and $HasConfig)
if($StaticPass){
  "PRODUCT_PROGRESS_ESTIMATE=96" | Add-Content $SmokeReport
  "PRODUCT_RESULT=READY_FOR_FINAL_BROWSER_VISUAL_CONFIRMATION" | Add-Content $SmokeReport
}else{
  "PRODUCT_PROGRESS_ESTIMATE=92" | Add-Content $SmokeReport
  "PRODUCT_RESULT=BLOCKED_BY_STATIC_CHECK_FAILURE" | Add-Content $SmokeReport
}
git -C $WorktreePath add "docs/chatgpt_status/$PageKey/reports"
git -C $WorktreePath commit -m "Add local map data final smoke $Now"
git -C $WorktreePath pull --rebase --autostash origin $Branch
git -C $WorktreePath push origin HEAD:$Branch
"PAGE_KEY=$PageKey`nMODE=DYNAMIC_POLLER_INSTALL_AND_LOCAL_MAP_DATA_SMOKE`nRESULT=DONE`nWORKTREE_PATH=$WorktreePath`nSMOKE_REPORT=$SmokeReport" | Set-Content $InstallReport -Encoding UTF8
Write-Host "REPORT=$InstallReport"
Write-Host "Bekleme suresi: 5-10 dakika"
