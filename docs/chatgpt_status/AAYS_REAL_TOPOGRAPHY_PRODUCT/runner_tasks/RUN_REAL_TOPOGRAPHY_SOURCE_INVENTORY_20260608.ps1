$ErrorActionPreference='Continue'
$B='aays-runner-v17-icon-work-20260603-232706'
$Page='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Roots=@('F:\AAYS_GITHUB_WORK\AAYS','C:\Users\cagda\Documents\GitHub\AAYS')
$W=$Roots | Where-Object { Test-Path (Join-Path $_ '.git') } | Select-Object -First 1
if(!$W){ $W='F:\AAYS_GITHUB_WORK\AAYS' }
$Reports=Join-Path $W "docs\chatgpt_status\$Page\reports"
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
$Now=Get-Date -Format yyyyMMdd-HHmmss
$Out=Join-Path $Reports "real_topography_source_inventory_$Now.txt"
"PAGE_KEY=$Page" | Set-Content $Out -Encoding UTF8
"MODE=REAL_TOPOGRAPHY_SOURCE_INVENTORY" | Add-Content $Out
"RUN_AT=$Now" | Add-Content $Out
"WORKTREE=$W" | Add-Content $Out
"DB_WRITE=false" | Add-Content $Out
"MIGRATION=false" | Add-Content $Out
"DEPLOY=false" | Add-Content $Out
"FAKE_DATA=false" | Add-Content $Out
$Patterns=@('parcel_elevation_lookup_v2.json','*elevation*.json','*elevation*.csv','*elevation*.gpkg','*terrain*.zip','*terrain*.asc','*terrain*.gpkg','*dtm*.zip','*dtm*.asc','*lidar*.zip','*lidar*.tif','*lidar*.asc')
"SEARCH_ROOTS:" | Add-Content $Out
$Roots | ForEach-Object { $_ | Add-Content $Out }
"CANDIDATE_FILES:" | Add-Content $Out
$found=@()
foreach($root in $Roots){
  if(Test-Path $root){
    foreach($pat in $Patterns){
      $items=Get-ChildItem $root -Recurse -File -Filter $pat -ErrorAction SilentlyContinue | Select-Object -First 200
      foreach($i in $items){ $found += $i.FullName; $i.FullName | Add-Content $Out }
    }
  }
}
$artifact=$found | Where-Object { $_ -like '*parcel_elevation_lookup_v2.json' } | Select-Object -First 1
if($artifact){
  "ARTIFACT_FOUND=true" | Add-Content $Out
  "ARTIFACT_PATH=$artifact" | Add-Content $Out
  "PRODUCT_PROGRESS_ESTIMATE=88" | Add-Content $Out
  "PRODUCT_RESULT=REAL_ELEVATION_ARTIFACT_FOUND_NEEDS_SCHEMA_AND_API_SMOKE" | Add-Content $Out
}else{
  "ARTIFACT_FOUND=false" | Add-Content $Out
  "PRODUCT_PROGRESS_ESTIMATE=84" | Add-Content $Out
  "PRODUCT_RESULT=WAITING_FOR_REAL_ELEVATION_SOURCE_OR_ARTIFACT" | Add-Content $Out
  "BLOCKER=parcel_elevation_lookup_v2_json_not_found" | Add-Content $Out
}
git -C $W add "docs/chatgpt_status/$Page/reports" 2>&1 | Add-Content $Out
git -C $W commit -m "Add real topography source inventory $Now" 2>&1 | Add-Content $Out
git -C $W pull --rebase --autostash origin $B 2>&1 | Add-Content $Out
git -C $W push origin HEAD:$B 2>&1 | Add-Content $Out
Write-Host "Real topography source inventory complete: $Out"
