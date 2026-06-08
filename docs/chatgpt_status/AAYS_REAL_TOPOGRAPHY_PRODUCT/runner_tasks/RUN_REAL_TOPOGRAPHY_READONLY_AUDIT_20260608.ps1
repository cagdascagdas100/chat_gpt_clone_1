$ErrorActionPreference='Continue'
$Branch='aays-runner-v17-icon-work-20260603-232706'
$ProjectKey='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$RepoUrl='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$FRoot='F:\AAYS_GITHUB_WORK'
$W=Join-Path $FRoot 'AAYS_REAL_TOPOGRAPHY'
$Env:TEMP=Join-Path $FRoot 'tmp'
$Env:TMP=Join-Path $FRoot 'tmp'
New-Item -ItemType Directory -Force -Path $FRoot,$Env:TEMP | Out-Null
if(!(Test-Path (Join-Path $W '.git'))){
  if(Test-Path $W){ Remove-Item -Recurse -Force $W -ErrorAction SilentlyContinue }
  git clone --branch $Branch $RepoUrl $W
}else{
  git -C $W fetch origin
  git -C $W checkout $Branch
  git -C $W pull --rebase --autostash origin $Branch
}
$Reports=Join-Path $W "docs\chatgpt_status\$ProjectKey\reports"
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
$Now=Get-Date -Format yyyyMMdd-HHmmss
$Out=Join-Path $Reports "real_topography_product_readonly_audit_$Now.txt"
$Web=Join-Path $W 'england_map_web'
$App=Join-Path $Web 'app.js'
$Config=Join-Path $Web 'config\topography.overlay.json'
$Icon=Join-Path $Web 'assets\icons\terrayield_icons\hight_differance.png'
$LookupUrl='http://127.0.0.1:8765/lookup?parcel_id=61631825'
"PAGE_KEY=$ProjectKey" | Set-Content $Out -Encoding UTF8
"MODE=REAL_TOPOGRAPHY_PRODUCT_READONLY_AUDIT" | Add-Content $Out
"RUN_AT=$Now" | Add-Content $Out
"WORKTREE=$W" | Add-Content $Out
"TEMP=$Env:TEMP" | Add-Content $Out
"BRANCH=$Branch" | Add-Content $Out
"GIT_HEAD=$(git -C $W rev-parse --short HEAD 2>$null)" | Add-Content $Out
"CONFIG_EXISTS=$(Test-Path $Config)" | Add-Content $Out
"ICON_EXISTS=$(Test-Path $Icon)" | Add-Content $Out
"APP_EXISTS=$(Test-Path $App)" | Add-Content $Out
if(Test-Path $App){
  node --check $App >> $Out 2>&1
  $NodeExit=$LASTEXITCODE
}else{ $NodeExit=999 }
"NODE_CHECK_EXIT_CODE=$NodeExit" | Add-Content $Out
$Patterns=@(
  'fetchParcelElevationForPopup',
  'parcelElevationCache',
  'center_elevation_m',
  'region_average_elevation_m',
  'elevation_difference_from_region_average_m',
  'formatElevationDifferenceFromRegionAverage',
  'topography_lookup',
  'hight_differance.png',
  'worth-waves.svg',
  'MAP_WORTH_MENU_ITEMS'
)
foreach($Pattern in $Patterns){
  $Hit=$false
  if(Test-Path $App){ $Hit=(Select-String -Path $App -Pattern $Pattern -Quiet -SimpleMatch) }
  "APP_HAS_$($Pattern.Replace('.','_').Replace('-','_').Replace('(','').Replace(')',''))=$Hit" | Add-Content $Out
}
$RepoPatterns=@(
  'region_average_elevation_m',
  'elevation_difference_from_region_average_m',
  'source_dataset',
  'EA LIDAR',
  'OS Terrain',
  '127.0.0.1:8765',
  'lookup?parcel_id',
  'center_elevation_m'
)
foreach($Pattern in $RepoPatterns){
  $Hits=Get-ChildItem $W -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\.git\\|node_modules|__pycache__|\.venv|venv' } |
    Select-String -Pattern $Pattern -SimpleMatch -List -ErrorAction SilentlyContinue |
    Select-Object -First 30
  "REPO_HIT_COUNT_$($Pattern.Replace(' ','_').Replace(':','_').Replace('?','_').Replace('.','_').Replace('/','_'))=$(@($Hits).Count)" | Add-Content $Out
  $Hits | ForEach-Object { "REPO_HIT_$($Pattern.Replace(' ','_'))=$($_.Path):$($_.LineNumber)" } | Add-Content $Out
}
try{
  $Lookup=Invoke-WebRequest -UseBasicParsing $LookupUrl -TimeoutSec 5
  "LOOKUP_8765_STATUS=$($Lookup.StatusCode)" | Add-Content $Out
  $Body=$Lookup.Content
  "LOOKUP_8765_HAS_CENTER_ELEVATION=$($Body -match 'center_elevation_m')" | Add-Content $Out
  "LOOKUP_8765_HAS_REGION_AVERAGE=$($Body -match 'region_average_elevation_m')" | Add-Content $Out
  "LOOKUP_8765_HAS_ELEVATION_DIFF=$($Body -match 'elevation_difference_from_region_average_m')" | Add-Content $Out
}catch{
  "LOOKUP_8765_STATUS=CLOSED_OR_ERROR" | Add-Content $Out
  "LOOKUP_8765_ERROR=$($_.Exception.Message)" | Add-Content $Out
}
if(Test-Path $Config){
  "TOPOGRAPHY_CONFIG_SHA1=$((Get-FileHash $Config -Algorithm SHA1).Hash)" | Add-Content $Out
  $ConfigText=Get-Content $Config -Raw
  "CONFIG_HAS_TERRARIUM=$($ConfigText -match 'terrarium')" | Add-Content $Out
  "CONFIG_HAS_PM_TILES=$($ConfigText -match 'pmtiles|pbf|mbtiles')" | Add-Content $Out
}
$StaticOk=((Test-Path $Config) -and (Test-Path $Icon) -and (Test-Path $App) -and ($NodeExit -eq 0))
$HasObjectFields=$false
if(Test-Path $App){
  $HasObjectFields=((Select-String -Path $App -Pattern 'region_average_elevation_m' -Quiet -SimpleMatch) -and (Select-String -Path $App -Pattern 'elevation_difference_from_region_average_m' -Quiet -SimpleMatch))
}
if($StaticOk -and $HasObjectFields){
  "PROGRESS_ESTIMATE=70" | Add-Content $Out
  "PRODUCT_RESULT=PARTIAL_OBJECT_FIELDS_PRESENT_NEEDS_LOOKUP_PIPELINE_VERIFY" | Add-Content $Out
}else{
  "PROGRESS_ESTIMATE=65" | Add-Content $Out
  "PRODUCT_RESULT=REAL_PRODUCT_AUDIT_STARTED_NEEDS_PATCH" | Add-Content $Out
}
"NEXT_ACTION=Patch lookup v2 structured object, app.js object cache, all popup branches, icon binding, tile path evidence; no DB write/migration/deploy." | Add-Content $Out
git -C $W add "docs/chatgpt_status/$ProjectKey/reports"
git -C $W commit -m "Add real topography product readonly audit $Now"
git -C $W pull --rebase --autostash origin $Branch
git -C $W push origin HEAD:$Branch
Write-Host "REAL_TOPOGRAPHY_AUDIT_DONE"
Write-Host "Bekleme: 3-7 dakika"
