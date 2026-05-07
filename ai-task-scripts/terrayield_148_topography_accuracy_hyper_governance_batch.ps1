$ErrorActionPreference='Continue'
$TaskId='terrayield-148-topography-accuracy-hyper-governance-batch'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$BaseDir=Join-Path $ProjectRoot 'topography_accuracy_upgrade_plan'
$DeepDir=Join-Path $BaseDir 'phase_02_hyper_governance_batch'
$Report=Join-Path $DeepDir 'TERRAYIELD_TOPOGRAPHY_HYPER_BATCH_REPORT.md'
function W($p,$c){$d=Split-Path -Parent $p;if($d -and !(Test-Path $d)){New-Item -ItemType Directory -Force -Path $d|Out-Null};$e=New-Object Text.UTF8Encoding($false);[IO.File]::WriteAllText($p,$c,$e)}
function P($port){try{$c=New-Object Net.Sockets.TcpClient;$a=$c.BeginConnect('127.0.0.1',$port,$null,$null);$ok=$a.AsyncWaitHandle.WaitOne(1000,$false);if($ok -and $c.Connected){$c.EndConnect($a);$c.Close();return 'OPEN'};$c.Close();return 'CLOSED'}catch{return 'ERROR'}}
Write-Output "TASK_ID=$TaskId"
Write-Output 'MODE=HYPER_GOVERNANCE_BATCH_SCOPE_ONLY'
Write-Output 'GUARDS=NO_DB NO_DOCKER NO_DOWNLOAD NO_RESTART NO_UI_EDIT NO_ACTIVE_SCORE_CHANGE'
if(!(Test-Path $ProjectRoot)){Write-Output "PROJECT_ROOT_MISSING=$ProjectRoot";exit 2}
New-Item -ItemType Directory -Force -Path $DeepDir|Out-Null
$manifest=@()
$manifest+=@{file='00_MASTER_EXECUTION_MAP.md';role='one-map execution plan'}
$manifest+=@{file='01_SOURCE_EVIDENCE_BACKLOG.json';role='source evidence backlog'}
$manifest+=@{file='02_DATUM_NORMALIZATION_RULES.md';role='mAOD alias rules'}
$manifest+=@{file='03_CONFIDENCE_SCORING_CASES.json';role='confidence examples'}
$manifest+=@{file='04_PARCEL_ELEVATION_FIELD_MAPPING.csv';role='schema mapping'}
$manifest+=@{file='05_RUNTIME_COMPATIBILITY_GUARDS.md';role='runtime guardrails'}
$manifest+=@{file='06_DOWNLOAD_BLOCKLIST_AND_AOI_RULES.md';role='download safety'}
$manifest+=@{file='07_ACCEPTANCE_TEST_MATRIX.csv';role='test matrix'}
$manifest+=@{file='08_ROLLBACK_AND_FREEZE_PLAN.md';role='rollback plan'}
$manifest+=@{file='09_RISK_REGISTER.json';role='risk register'}
$manifest+=@{file='10_NEXT_IMPLEMENTABLE_TASKS.md';role='future tasks'}
$manifest+=@{file='11_EVIDENCE_RECORD_STUBS_INDEX.json';role='evidence stubs'}
W (Join-Path $DeepDir '00_MASTER_EXECUTION_MAP.md') @'
# TerraYield Topography Hyper Governance Batch

This batch remains scope-only. It expands the topography accuracy governance pack without touching current runtime, DB, Docker, UI, critical JS, active scores, or data downloads.

## Execution lanes

1. Datum contract: mAOD canonical, ODN/Newlyn aliases.
2. Geometry authority: HMLR INSPIRE / NPS first.
3. Elevation authority: EA LIDAR Composite DTM first.
4. Fallback: OS Terrain 5 then OS Terrain 50.
5. Current runtime: local Terrarium 8099 and lookup 8765 preserved as existing system sources only.
6. Evidence: every source needs datum, licence, coverage, resolution, limitation, and access evidence.
7. Confidence: no evidence means no HIGH; local runtime only is not authoritative HIGH.
8. Implementation: only additive, reviewed, AOI-scoped future changes.

## Non-negotiable guards

No DB rebuild. No SQL execution. No Docker build/recreate. No England-wide download. No service restart. No active UI edit. No critical topography JS or unified panel edit.
'@
$backlog=[ordered]@{phase='evidence_backlog';sources=@([ordered]@{slug='hmlr_inspire_or_national_polygon_service';need=@('geometry scope','licence','polygon limitations','parcel title matching')},[ordered]@{slug='environment_agency_lidar_composite_dtm';need=@('datum proof','coverage proof','resolution proof','vertical accuracy statement')},[ordered]@{slug='os_terrain_5';need=@('licence','resolution','fallback suitability')},[ordered]@{slug='os_terrain_50';need=@('open fallback role','resolution limitation')},[ordered]@{slug='local_terrarium_runtime_8099';need=@('current runtime only label','tile provenance audit')},[ordered]@{slug='local_lookup_runtime_8765';need=@('current lookup only label','lookup schema audit')})}
W (Join-Path $DeepDir '01_SOURCE_EVIDENCE_BACKLOG.json') ($backlog|ConvertTo-Json -Depth 10)
W (Join-Path $DeepDir '02_DATUM_NORMALIZATION_RULES.md') @'
# Datum Normalization Rules

Canonical label: `mAOD`.
Accepted aliases: `ODN`, `Ordnance Datum Newlyn`.

## Normalization

- Input `mAOD` => output `mAOD`.
- Input `ODN` => output `mAOD`, preserve alias in evidence.
- Input `Ordnance Datum Newlyn` => output `mAOD`, preserve alias in evidence.

## Rejection

Reject or downgrade any record using `sea level`, `local datum`, `unknown datum`, empty datum, or unverified vertical reference.
'@
$cases=[ordered]@{cases=@([ordered]@{name='EA DTM plus HMLR geometry with datum evidence';expected_band='HIGH_candidate';max_if_cross_check_missing='MEDIUM'},[ordered]@{name='Terrarium only';expected_band='LOW_or_MEDIUM_current_system';max='MEDIUM'},[ordered]@{name='Fallback OS Terrain 50 only';expected_band='LOW';fallback_used=$true},[ordered]@{name='Unknown datum';expected_band='WEAK';hard_gate='not_high'},[ordered]@{name='Geometry source unknown';expected_band='LOW';max='MEDIUM'})}
W (Join-Path $DeepDir '03_CONFIDENCE_SCORING_CASES.json') ($cases|ConvertTo-Json -Depth 10)
W (Join-Path $DeepDir '04_PARCEL_ELEVATION_FIELD_MAPPING.csv') @'
field,required,phase,notes
parcel_id,true,future_apply,Stable parcel identifier.
parcel_geometry_source_slug,true,future_apply,HMLR/NPS provenance.
elevation_source_slug,true,future_apply,EA DTM or fallback source.
datum_label,true,future_apply,Must equal mAOD.
datum_alias_accepted,false,future_apply,ODN or Ordnance Datum Newlyn where applicable.
mean_elevation_m,false,future_apply,Parcel mean elevation.
median_elevation_m,false,future_apply,Parcel median elevation.
fallback_used,true,future_apply,Required boolean.
confidence_score,false,future_apply,0-100 model score.
evidence_id,true,future_apply,Links to evidence record.
review_status,true,future_apply,draft/reviewed/accepted/rejected.
'@
W (Join-Path $DeepDir '05_RUNTIME_COMPATIBILITY_GUARDS.md') @'
# Runtime Compatibility Guards

- 8010 UI: observe only.
- 8099 DEM: observe only.
- 8765 lookup: observe only.
- Do not restart, rebuild, recreate, or replace services.
- Do not modify `aays_topography_mode_v1.js`.
- Do not modify `aays_topography_bulk_visible_parcels_v1.js`.
- Do not modify unified panel files.
- Additive future features must be isolated behind reviewed configuration and acceptance tests.
'@
W (Join-Path $DeepDir '06_DOWNLOAD_BLOCKLIST_AND_AOI_RULES.md') @'
# Download Blocklist and AOI Rules

## Blocked now

- England-wide downloads.
- Automatic bulk raster fetch.
- Any downloader with no AOI/tile whitelist.
- Any download job launched by current runner.

## Future AOI rule

A future download manifest must define source, tile id, AOI, expected size, licence, checksum plan, and rollback path before it can move out of `plan_only`.
'@
W (Join-Path $DeepDir '07_ACCEPTANCE_TEST_MATRIX.csv') @'
test_id,category,assertion,phase,status
TOPO-001,datum,canonical datum equals mAOD,governance,draft
TOPO-002,datum,ODN and Newlyn are aliases,governance,draft
TOPO-003,source,EA DTM primary elevation source,governance,draft
TOPO-004,source,HMLR/NPS primary geometry source,governance,draft
TOPO-005,runtime,8099 observe only,governance,draft
TOPO-006,runtime,8765 observe only,governance,draft
TOPO-007,runtime,8010 observe only,governance,draft
TOPO-008,safety,no Docker command,governance,draft
TOPO-009,safety,no SQL execution,governance,draft
TOPO-010,safety,no England-wide download,governance,draft
'@
W (Join-Path $DeepDir '08_ROLLBACK_AND_FREEZE_PLAN.md') @'
# Rollback and Freeze Plan

This batch writes only under `topography_accuracy_upgrade_plan/phase_02_hyper_governance_batch/`.

Rollback is file-only: remove that folder or revert the project commit. No runtime state, DB state, Docker image, service, or UI file is changed by this task.
'@
$risk=[ordered]@{risks=@([ordered]@{id='R1';risk='Datum ambiguity';mitigation='mAOD canonical with ODN/Newlyn aliases'},[ordered]@{id='R2';risk='Terrarium mistaken as authoritative';mitigation='current_system_source_only label'},[ordered]@{id='R3';risk='England-wide download accidentally triggered';mitigation='manifest no_download and blocklist'},[ordered]@{id='R4';risk='Critical JS/UI regression';mitigation='diff guard and no UI edit'},[ordered]@{id='R5';risk='Schema executed too early';mitigation='SQL draft only and no DB rule'})}
W (Join-Path $DeepDir '09_RISK_REGISTER.json') ($risk|ConvertTo-Json -Depth 10)
W (Join-Path $DeepDir '10_NEXT_IMPLEMENTABLE_TASKS.md') @'
# Next Implementable Tasks

1. Populate one evidence JSON for EA LIDAR Composite DTM.
2. Populate one evidence JSON for HMLR INSPIRE / NPS geometry.
3. Add a read-only parser test for `topography_source_registry.json`.
4. Convert acceptance matrix into static tests only.
5. Prepare AOI whitelist template without running downloads.
6. Review SQL draft and convert to migration only after approval.
'@
$stubs=[ordered]@{stubs=@('evidence_ea_lidar_composite_dtm.json','evidence_hmlr_inspire_or_nps.json','evidence_os_terrain_5.json','evidence_os_terrain_50.json','evidence_local_terrarium_8099.json','evidence_local_lookup_8765.json');status='index_only_no_source_records_populated'}
W (Join-Path $DeepDir '11_EVIDENCE_RECORD_STUBS_INDEX.json') ($stubs|ConvertTo-Json -Depth 10)
$ok=$true
$r="# TerraYield Topography Hyper Batch Report`n`nTask: $TaskId`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n`n## Files`n"
foreach($m in $manifest){$path=Join-Path $DeepDir $m.file;if(Test-Path $path){$r+="- PASS $($m.file) - $($m.role)`n"}else{$ok=$false;$r+="- FAIL missing $($m.file)`n"}}
$r+="`n## Observe-only runtime ports`n- 8010: $(P 8010)`n- 8099: $(P 8099)`n- 8765: $(P 8765)`n"
Set-Location $ProjectRoot
$st=git status --short 2>&1|Out-String
$r+="`n## Git status before guarded commit`n```text`n$st`n``` `n"
if($st -match 'aays_topography_mode_v1.js|aays_topography_bulk_visible_parcels_v1.js'){$ok=$false;$r+="- FAIL critical JS diff detected`n"}else{$r+="- PASS no critical topography JS diff detected`n"}
$r+="`nVALIDATION_OK=$ok`n"
W $Report $r
Write-Output 'HYPER_BATCH_FILES_BEGIN'
Get-ChildItem $DeepDir|Select Name,Length,LastWriteTime|Format-Table|Out-String|Write-Output
Write-Output 'HYPER_BATCH_FILES_END'
try{Set-Location $ProjectRoot;git add topography_accuracy_upgrade_plan 2>&1|Out-String|Write-Output;$cached=git diff --cached --name-only 2>&1|Out-String;Write-Output 'CACHED_DIFF_BEGIN';Write-Output $cached;Write-Output 'CACHED_DIFF_END';$unsafe=$false;foreach($line in ($cached -split "`n")){$t=$line.Trim();if($t -and !$t.StartsWith('topography_accuracy_upgrade_plan/')){$unsafe=$true}};if($unsafe){git reset 2>&1|Out-String|Write-Output;Write-Output 'PROJECT_COMMIT_SKIPPED_UNSAFE_CACHED_PATH'}elseif([string]::IsNullOrWhiteSpace($cached)){Write-Output 'PROJECT_COMMIT_SKIPPED_NO_CHANGES'}else{git commit -m 'Add TerraYield topography hyper governance batch' 2>&1|Out-String|Write-Output;git push 2>&1|Out-String|Write-Output;Write-Output 'PROJECT_COMMIT_PUSH_ATTEMPTED=TRUE'}}catch{Write-Output "PROJECT_COMMIT_ERROR=$($_.Exception.Message)"}
Write-Output "VALIDATION_OK=$ok"
Write-Output 'TERRAYIELD_TASK_DONE'
if($ok){exit 0}else{exit 1}
