$ErrorActionPreference='Continue'
$B='aays-runner-v17-icon-work-20260603-232706'
$PageKey='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$RepoUrl='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$FRoot='F:\AAYS_GITHUB_WORK'
$W=Join-Path $FRoot 'AAYS'
$Env:TEMP=Join-Path $FRoot 'tmp'
$Env:TMP=Join-Path $FRoot 'tmp'
New-Item -ItemType Directory -Force -Path $FRoot,$Env:TEMP | Out-Null
if(!(Test-Path (Join-Path $W '.git'))){
  if(Test-Path $W){ Remove-Item -Recurse -Force $W -ErrorAction SilentlyContinue }
  git clone --branch $B $RepoUrl $W
}else{
  git -C $W fetch origin
  git -C $W checkout $B
  git -C $W pull --rebase --autostash origin $B
}
$Reports=Join-Path $W "docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
$Now=Get-Date -Format yyyyMMdd-HHmmss
$Out=Join-Path $Reports "real_topography_static_audit_$Now.txt"
$Web=Join-Path $W 'england_map_web'
$App=Join-Path $Web 'app.js'
$Config=Join-Path $Web 'config\topography.overlay.json'
$Icon=Join-Path $Web 'assets\icons\terrayield_icons\hight_differance.png'
"PAGE_KEY=$PageKey" | Set-Content $Out -Encoding UTF8
"MODE=REAL_TOPOGRAPHY_STATIC_AUDIT" | Add-Content $Out
"RUN_AT=$Now" | Add-Content $Out
"WORKTREE=$W" | Add-Content $Out
"TEMP=$Env:TEMP" | Add-Content $Out
"NO_DB_WRITE=true" | Add-Content $Out
"NO_MIGRATION=true" | Add-Content $Out
"NO_DEPLOY=true" | Add-Content $Out
"APP_EXISTS=$(Test-Path $App)" | Add-Content $Out
"CONFIG_EXISTS=$(Test-Path $Config)" | Add-Content $Out
"ICON_EXISTS=$(Test-Path $Icon)" | Add-Content $Out
if(Test-Path $App){ node --check $App >> $Out 2>&1; $NodeExit=$LASTEXITCODE } else { $NodeExit=999 }
"NODE_CHECK_EXIT_CODE=$NodeExit" | Add-Content $Out
$Patterns=@('fetchParcelElevationForPopup','parcelElevationCache','center_elevation_m','region_average_elevation_m','elevation_difference_from_region_average_m','formatElevationDifferenceFromRegionAverage','hight_differance.png','worth-waves.svg','MAP_WORTH_MENU_ITEMS','Denizden','Bölge ortalamasından','Veri yok')
foreach($Ptn in $Patterns){
  $Count=0
  if(Test-Path $App){ $Count=@(Select-String -Path $App -Pattern $Ptn -SimpleMatch -ErrorAction SilentlyContinue).Count }
  "APP_PATTERN_COUNT_$($Ptn -replace '[^A-Za-z0-9]','_')=$Count" | Add-Content $Out
}
if(Test-Path $Config){
  $Cfg=Get-Content $Config -Raw -ErrorAction SilentlyContinue
  "CONFIG_HAS_TERRARIUM=$($Cfg -match 'terrarium')" | Add-Content $Out
  "CONFIG_HAS_TOPOGRAPHY=$($Cfg -match 'topography')" | Add-Content $Out
  "CONFIG_HAS_TILE=$($Cfg -match 'tile')" | Add-Content $Out
}
$PyHits=Get-ChildItem $W -Recurse -Include *.py -File -ErrorAction SilentlyContinue | Select-String -Pattern 'region_average_elevation_m|elevation_difference_from_region_average_m|center_elevation_m' -List
"BACKEND_RELEVANT_PY_FILES=$(@($PyHits).Count)" | Add-Content $Out
$PyHits | Select-Object -First 40 | ForEach-Object { "BACKEND_RELEVANT_PY_FILE=$($_.Path)" } | Add-Content $Out
$StaticPass=((Test-Path $App) -and (Test-Path $Config) -and (Test-Path $Icon) -and ($NodeExit -eq 0))
$HasRegionFields=$false
if(Test-Path $App){ $HasRegionFields=((Select-String -Path $App -Pattern 'region_average_elevation_m' -Quiet) -and (Select-String -Path $App -Pattern 'elevation_difference_from_region_average_m' -Quiet)) }
if($StaticPass -and $HasRegionFields){
  "PRODUCT_PROGRESS_ESTIMATE=72" | Add-Content $Out
  "PRODUCT_RESULT=FRONTEND_FIELDS_PRESENT_NEEDS_LOOKUP_V2_AND_POPUP_SMOKE" | Add-Content $Out
}elseif($StaticPass){
  "PRODUCT_PROGRESS_ESTIMATE=65" | Add-Content $Out
  "PRODUCT_RESULT=STATIC_READY_REAL_METRICS_MISSING" | Add-Content $Out
}else{
  "PRODUCT_PROGRESS_ESTIMATE=55" | Add-Content $Out
  "PRODUCT_RESULT=BLOCKED_BY_STATIC_FAILURE" | Add-Content $Out
}
"NEXT_ACTION=Patch lookup v2 structured object and app.js cache/popup behavior after reading this report." | Add-Content $Out
git -C $W add "docs/chatgpt_status/$PageKey/reports"
git -C $W commit -m "Add real topography static audit $Now"
git -C $W pull --rebase --autostash origin $B
git -C $W push origin HEAD:$B
Write-Host 'Real topography static audit done. Bekleme: 3-7 dakika'
