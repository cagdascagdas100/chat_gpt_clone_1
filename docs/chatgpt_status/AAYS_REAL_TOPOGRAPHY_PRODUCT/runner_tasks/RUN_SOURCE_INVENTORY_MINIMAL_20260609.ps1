$B='aays-runner-v17-icon-work-20260603-232706'
$Page='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$W='F:\AAYS_GITHUB_WORK\AAYS'
$R=Join-Path $W "docs\chatgpt_status\$Page\reports"
New-Item -ItemType Directory -Force -Path $R | Out-Null
$Now=Get-Date -Format yyyyMMdd-HHmmss
$Out=Join-Path $R "real_topography_source_inventory_$Now.txt"
"PAGE_KEY=$Page" | Set-Content $Out -Encoding UTF8
"MODE=REAL_TOPOGRAPHY_SOURCE_INVENTORY_MINIMAL" | Add-Content $Out
"RUN_AT=$Now" | Add-Content $Out
"WORKTREE=$W" | Add-Content $Out
"FAKE_DATA_CREATED=False" | Add-Content $Out
if (!(Test-Path (Join-Path $W '.git'))) { "BLOCKER=F_WORKTREE_NOT_FOUND" | Add-Content $Out; exit 1 }
git -C $W checkout $B | Add-Content $Out
git -C $W pull --rebase --autostash origin $B | Add-Content $Out
"MATCHES:" | Add-Content $Out
$patterns=@('parcel_elevation_lookup_v2.json','*elevation*.json','*elevation*.csv','*elevation*.gpkg','*terrain*.tif','*terrain*.gpkg','*dtm*.tif','*dtm*.asc','*lidar*.tif','*lidar*.asc')
foreach($p in $patterns){ Get-ChildItem 'F:\','C:\Users\cagda\Documents\GitHub\AAYS' -Recurse -File -Filter $p -ErrorAction SilentlyContinue | Select-Object -First 100 | ForEach-Object { $_.FullName } | Add-Content $Out }
$matchCount=(Get-Content $Out | Select-String -Pattern 'elevation|terrain|dtm|lidar|parcel_elevation_lookup_v2' | Measure-Object).Count
"MATCH_COUNT=$matchCount" | Add-Content $Out
if($matchCount -gt 0){ "PRODUCT_PROGRESS_ESTIMATE=88" | Add-Content $Out; "PRODUCT_RESULT=REAL_ELEVATION_SOURCE_CANDIDATES_FOUND" | Add-Content $Out } else { "PRODUCT_PROGRESS_ESTIMATE=84" | Add-Content $Out; "PRODUCT_RESULT=BLOCKED_WAITING_FOR_REAL_ELEVATION_SOURCE" | Add-Content $Out }
git -C $W add "docs/chatgpt_status/$Page/reports"
git -C $W commit -m "Add real topography source inventory report $Now"
git -C $W pull --rebase --autostash origin $B
git -C $W push origin HEAD:$B
