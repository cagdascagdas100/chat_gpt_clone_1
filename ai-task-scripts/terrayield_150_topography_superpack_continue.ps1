$ErrorActionPreference='Continue'
$TaskId='terrayield-150-topography-superpack-continue'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Root=Join-Path $ProjectRoot 'topography_accuracy_upgrade_plan'
$Dir=Join-Path $Root 'phase_03_superpack_continue'
$Report=Join-Path $Dir 'TERRAYIELD_TOPOGRAPHY_SUPERPACK_REPORT.md'
function W($p,$c){$d=Split-Path -Parent $p;if($d -and !(Test-Path $d)){New-Item -ItemType Directory -Force -Path $d|Out-Null};$e=New-Object Text.UTF8Encoding($false);[IO.File]::WriteAllText($p,$c,$e)}
function Port($x){try{$c=New-Object Net.Sockets.TcpClient;$a=$c.BeginConnect('127.0.0.1',$x,$null,$null);$ok=$a.AsyncWaitHandle.WaitOne(900,$false);if($ok -and $c.Connected){$c.EndConnect($a);$c.Close();'OPEN'}else{$c.Close();'CLOSED'}}catch{'ERROR'}}
Write-Output "TASK_ID=$TaskId"
Write-Output 'MODE=SUPERPACK_SCOPE_ONLY_SINGLE_RUNNER'
Write-Output 'GUARDS=NO_DB NO_DOCKER NO_DOWNLOAD NO_RESTART NO_UI_EDIT NO_ACTIVE_SCORE_CHANGE'
if(!(Test-Path $ProjectRoot)){Write-Output "PROJECT_ROOT_MISSING=$ProjectRoot";exit 2}
New-Item -ItemType Directory -Force -Path $Dir|Out-Null
$files=@{}
$files['00_SUPERPACK_MASTER_INDEX.json']=(@{task=$TaskId;phase='phase_03_superpack_continue';runtime_impact='none';blocked=@('db_rebuild','sql_execute','docker_build','docker_recreate','england_wide_download','runtime_restart','ui_edit','critical_js_edit','active_score_change');outputs=@('evidence_specs','qa_matrix','confidence_cases','source_contracts','future_apply_tasks')}|ConvertTo-Json -Depth 8)
$files['01_EVIDENCE_REQUIREMENTS_MATRIX.csv']=@'
source,requirement,required_before_apply,notes
HMLR/NPS,geometry licence,true,parcel geometry authority
HMLR/NPS,polygon limitation statement,true,indicative extent caveat
EA LIDAR Composite DTM,datum evidence,true,mAOD/ODN/Newlyn proof
EA LIDAR Composite DTM,coverage evidence,true,AOI coverage only
EA LIDAR Composite DTM,resolution evidence,true,raster resolution
OS Terrain 5,licence evidence,true,fallback/cross-check
OS Terrain 50,open fallback evidence,true,low-resolution fallback
Local Terrarium 8099,current runtime label,true,not authoritative upgrade source
Local lookup 8765,current lookup label,true,not authoritative upgrade source
'@
$files['02_SOURCE_CONTRACTS.md']=@'
# Source Contracts

Canonical datum: mAOD. Aliases: ODN and Ordnance Datum Newlyn.

Primary geometry: HMLR INSPIRE / National Polygon Service. Primary elevation: EA LIDAR Composite DTM. Fallback/cross-check: OS Terrain 5 then OS Terrain 50. Existing local Terrarium 8099 and lookup 8765 remain current runtime sources only.

No source becomes accepted until evidence covers datum, licence, coverage, resolution, limitation and access date.
'@
$files['03_CONFIDENCE_TEST_VECTORS.json']=(@{vectors=@(@{id='CV1';scenario='EA DTM + HMLR geometry + datum evidence + cross-check';expected='HIGH_candidate'},@{id='CV2';scenario='EA DTM + HMLR geometry but no cross-check';expected='MEDIUM_until_cross_checked'},@{id='CV3';scenario='Terrarium only';expected='not_authoritative_high'},@{id='CV4';scenario='OS Terrain 50 fallback only';expected='LOW_fallback_used'},@{id='CV5';scenario='unknown datum';expected='WEAK_or_reject'},@{id='CV6';scenario='unknown geometry source';expected='max_MEDIUM'})}|ConvertTo-Json -Depth 8)
$files['04_STATIC_GUARD_MATRIX.csv']=@'
check_id,guard,expected
G001,no docker build,true
G002,no docker compose up,true
G003,no docker compose down,true
G004,no SQL execution,true
G005,no DB rebuild,true
G006,no England-wide download,true
G007,no service restart,true
G008,no UI edit,true
G009,no aays_topography_mode_v1.js edit,true
G010,no aays_topography_bulk_visible_parcels_v1.js edit,true
G011,no unified panel edit,true
G012,manifest no_download only,true
G013,datum mAOD canonical,true
G014,ODN alias present,true
G015,Ordnance Datum Newlyn alias present,true
'@
$files['05_AOI_WHITELIST_TEMPLATE.csv']=@'
aoi_id,source_slug,tile_or_product_id,bbox_or_geometry_ref,expected_size_mb,licence_checked,checksum_plan,status
AOI_DRAFT_001,environment_agency_lidar_composite_dtm,TBD,TBD,TBD,false,TBD,not_approved
AOI_DRAFT_002,os_terrain_5,TBD,TBD,TBD,false,TBD,not_approved
AOI_DRAFT_003,os_terrain_50,TBD,TBD,TBD,false,TBD,not_approved
'@
$files['06_FUTURE_IMPLEMENTATION_BACKLOG.md']=@'
# Future Implementation Backlog

1. Populate EA LIDAR evidence JSON.
2. Populate HMLR/NPS geometry evidence JSON.
3. Add read-only JSON parser tests.
4. Convert confidence vectors into unit tests.
5. Review SQL draft as additive migration only.
6. Build AOI/tile whitelist after manual evidence approval.
7. Prototype staging-only parcel elevation extractor.
8. Create read-only elevation report endpoint after staging approval.
'@
$files['07_RELEASE_FREEZE_CHECKLIST.md']=@'
# Release Freeze Checklist

- Confirm no DB migration executed.
- Confirm no Docker command executed.
- Confirm no bulk download started.
- Confirm no runtime restart occurred.
- Confirm no critical topography JS modified.
- Confirm no unified panel file modified.
- Confirm all outputs live under topography_accuracy_upgrade_plan.
'@
$files['08_EVIDENCE_STUB_EA_LIDAR.json']=(@{source='environment_agency_lidar_composite_dtm';status='stub_only';datum='mAOD';required_evidence=@('publisher datum statement','coverage statement','resolution statement','licence/access statement');download_status='not_downloaded'}|ConvertTo-Json -Depth 8)
$files['09_EVIDENCE_STUB_HMLR_NPS.json']=(@{source='hmlr_inspire_or_national_polygon_service';status='stub_only';role='parcel_geometry_primary';required_evidence=@('licence/access','geometry limitations','coverage','matching method');download_status='not_downloaded'}|ConvertTo-Json -Depth 8)
$files['10_EVIDENCE_STUB_OS_TERRAIN.json']=(@{sources=@('os_terrain_5','os_terrain_50');status='stub_only';role='fallback_cross_check';required_evidence=@('licence','resolution','coverage','datum relationship');download_status='not_downloaded'}|ConvertTo-Json -Depth 8)
foreach($k in $files.Keys){W (Join-Path $Dir $k) $files[$k]}
$ok=$true
$r="# TerraYield Topography Superpack Report`n`nTask: $TaskId`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n`n## Outputs`n"
foreach($k in $files.Keys){if(Test-Path (Join-Path $Dir $k)){$r+="- PASS $k`n"}else{$ok=$false;$r+="- FAIL missing $k`n"}}
$r+="`n## Runtime observe-only ports`n- 8010: $(Port 8010)`n- 8099: $(Port 8099)`n- 8765: $(Port 8765)`n"
Set-Location $ProjectRoot
$st=git status --short 2>&1|Out-String
$r+="`n## Git status before guarded commit`n```text`n$st`n``` `n"
if($st -match 'aays_topography_mode_v1.js|aays_topography_bulk_visible_parcels_v1.js|england_map_web'){$ok=$false;$r+="- FAIL unsafe active file diff detected`n"}else{$r+="- PASS no unsafe active file diff detected in status scan`n"}
$r+="`nVALIDATION_OK=$ok`n"
W $Report $r
Write-Output 'SUPERPACK_FILES_BEGIN'
Get-ChildItem $Dir|Select Name,Length,LastWriteTime|Format-Table|Out-String|Write-Output
Write-Output 'SUPERPACK_FILES_END'
try{Set-Location $ProjectRoot;git add topography_accuracy_upgrade_plan 2>&1|Out-String|Write-Output;$cached=git diff --cached --name-only 2>&1|Out-String;Write-Output 'CACHED_DIFF_BEGIN';Write-Output $cached;Write-Output 'CACHED_DIFF_END';$unsafe=$false;foreach($line in ($cached -split "`n")){$t=$line.Trim();if($t -and !$t.StartsWith('topography_accuracy_upgrade_plan/')){$unsafe=$true}};if($unsafe){git reset 2>&1|Out-String|Write-Output;Write-Output 'PROJECT_COMMIT_SKIPPED_UNSAFE_CACHED_PATH'}elseif([string]::IsNullOrWhiteSpace($cached)){Write-Output 'PROJECT_COMMIT_SKIPPED_NO_CHANGES'}else{git commit -m 'Add TerraYield topography superpack continuation' 2>&1|Out-String|Write-Output;git push 2>&1|Out-String|Write-Output;Write-Output 'PROJECT_COMMIT_PUSH_ATTEMPTED=TRUE'}}catch{Write-Output "PROJECT_COMMIT_ERROR=$($_.Exception.Message)"}
Write-Output "VALIDATION_OK=$ok"
Write-Output 'TERRAYIELD_TASK_DONE'
if($ok){exit 0}else{exit 1}
