$ErrorActionPreference='Continue'
$TaskId='terrayield-143-topography-accuracy-governance-pack-wide'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$OutDir=Join-Path $ProjectRoot 'topography_accuracy_upgrade_plan'
$Report=Join-Path $OutDir 'TERRAYIELD_TOPOGRAPHY_STATIC_VALIDATION_REPORT.md'
function W($p,$c){$d=Split-Path -Parent $p;if($d -and !(Test-Path $d)){New-Item -ItemType Directory -Force -Path $d|Out-Null};$e=New-Object System.Text.UTF8Encoding($false);[IO.File]::WriteAllText($p,$c,$e)}
function P($port){try{$c=New-Object Net.Sockets.TcpClient;$a=$c.BeginConnect('127.0.0.1',$port,$null,$null);$ok=$a.AsyncWaitHandle.WaitOne(1200,$false);if($ok -and $c.Connected){$c.EndConnect($a);$c.Close();return 'OPEN'};$c.Close();return 'CLOSED_OR_UNREACHABLE'}catch{return 'ERROR '+$_.Exception.Message}}
Write-Output "TASK_ID=$TaskId"
Write-Output 'MODE=TOPOGRAPHY_GOVERNANCE_PACK_ONLY'
Write-Output 'NO_DB=TRUE NO_DOCKER=TRUE NO_DOWNLOAD=TRUE NO_RESTART=TRUE NO_UI_EDIT=TRUE'
if(!(Test-Path $ProjectRoot)){Write-Output "PROJECT_ROOT_MISSING=$ProjectRoot";exit 2}
New-Item -ItemType Directory -Force -Path $OutDir|Out-Null
$registry=[ordered]@{schema_version='1.0.0';phase='governance_only';runtime_policy=[ordered]@{keep_8099_dem_runtime=$true;keep_8765_lookup_runtime=$true;keep_8010_ui=$true;no_db_rebuild=$true;no_docker_build_or_recreate=$true;no_england_wide_download=$true;critical_files_read_only=@('aays_topography_mode_v1.js','aays_topography_bulk_visible_parcels_v1.js','unified panel files')};vertical_datum_standard=[ordered]@{canonical_label='mAOD';meaning='metres Above Ordnance Datum';accepted_aliases=@('ODN','Ordnance Datum Newlyn');normalization_rule='Normalize ODN and Ordnance Datum Newlyn to mAOD.'};source_chain=@([ordered]@{rank=1;source_slug='hmlr_inspire_or_national_polygon_service';role='parcel_geometry_primary';runtime_role='not_current_runtime_dependency'},[ordered]@{rank=2;source_slug='environment_agency_lidar_composite_dtm';role='elevation_primary';datum_required='mAOD';runtime_role='not_current_runtime_dependency'},[ordered]@{rank=3;source_slug='os_terrain_5';role='fallback_or_cross_check_high_resolution';runtime_role='not_current_runtime_dependency'},[ordered]@{rank=4;source_slug='os_terrain_50';role='fallback_or_cross_check_low_resolution';runtime_role='not_current_runtime_dependency'},[ordered]@{rank=5;source_slug='local_terrarium_runtime_8099';role='current_system_source_only';runtime_role='current_dem_runtime'},[ordered]@{rank=6;source_slug='local_lookup_runtime_8765';role='current_system_lookup_only';runtime_role='current_lookup_runtime'})}
W (Join-Path $OutDir 'topography_source_registry.json') ($registry|ConvertTo-Json -Depth 10)
$evidence=[ordered]@{schema_version='1.0.0';evidence_id='topography_dataset_evidence__SOURCE__YYYYMMDD';source_slug='SOURCE_SLUG';source_role='parcel_geometry_primary | elevation_primary | fallback | cross_check | current_runtime_only';vertical_datum=[ordered]@{canonical_label='mAOD';accepted_aliases=@('ODN','Ordnance Datum Newlyn');datum_checked=$false};resolution=[ordered]@{horizontal_resolution_m=$null;vertical_accuracy_statement='';resolution_checked=$false};access=[ordered]@{accessed_at='YYYY-MM-DD';download_status='not_downloaded_in_this_phase';local_path=$null};confidence=[ordered]@{band='DRAFT';score=$null};status='template_only'}
W (Join-Path $OutDir 'topography_dataset_evidence.template.json') ($evidence|ConvertTo-Json -Depth 10)
$csv=@'
source_slug,source_role,publisher,datum_required,planned_action,status,local_target_path,notes
hmlr_inspire_or_national_polygon_service,parcel_geometry_primary,HM Land Registry,mAOD,plan_only,no_download,,Geometry source to be evidenced before extraction.
environment_agency_lidar_composite_dtm,elevation_primary,Environment Agency,mAOD,plan_only,no_download,,Primary DTM source; no England-wide download.
os_terrain_5,fallback_cross_check_high_resolution,Ordnance Survey,mAOD,plan_only,no_download,,Fallback/cross-check only.
os_terrain_50,fallback_cross_check_low_resolution,Ordnance Survey,mAOD,plan_only,no_download,,Lower-resolution fallback only.
local_terrarium_runtime_8099,current_system_source_only,Local runtime,mAOD_alias_or_unknown,observe_only,preserve_runtime,,Existing DEM runtime retained.
local_lookup_runtime_8765,current_system_lookup_only,Local runtime,mAOD_alias_or_unknown,observe_only,preserve_runtime,,Existing lookup runtime retained.
'@
W (Join-Path $OutDir 'topography_download_manifest.csv') $csv
$sql=@'
-- DRAFT ONLY. DO NOT EXECUTE IN THIS PHASE. No DB rebuild, no Docker, no migration.
create table if not exists parcel_elevation_observations (
  id bigserial primary key,
  parcel_id text not null,
  parcel_geometry_source_slug text not null,
  elevation_source_slug text not null,
  datum_label text not null default 'mAOD',
  min_elevation_m numeric null,
  max_elevation_m numeric null,
  mean_elevation_m numeric null,
  median_elevation_m numeric null,
  sample_count integer null,
  fallback_used boolean not null default false,
  cross_check_delta_mean_m numeric null,
  confidence_score numeric null,
  confidence_band text null,
  evidence_id text null,
  review_status text not null default 'draft',
  created_at timestamptz not null default now(),
  constraint parcel_elevation_datum_mAOD_chk check (datum_label = 'mAOD')
);
'@
W (Join-Path $OutDir 'parcel_elevation_schema.sql') $sql
$conf=[ordered]@{schema_version='1.0.0';model_name='terrayield_topography_confidence_model_v1';phase='draft_governance_only';max_score=100;components=@([ordered]@{name='source_authority';max_points=25},[ordered]@{name='parcel_geometry_quality';max_points=20},[ordered]@{name='coverage_completeness';max_points=15},[ordered]@{name='resolution_quality';max_points=15},[ordered]@{name='cross_check_agreement';max_points=15},[ordered]@{name='runtime_operational_health';max_points=10});bands=@([ordered]@{band='HIGH';min=80;max=100},[ordered]@{band='MEDIUM';min=60;max=79.99},[ordered]@{band='LOW';min=40;max=59.99},[ordered]@{band='WEAK';min=0;max=39.99});hard_gates=@('No explicit mAOD/ODN/Newlyn datum evidence means not HIGH.','Only local Terrarium/lookup evidence cannot be authoritative HIGH.','Fallback-only extraction must set fallback_used=true.','Unknown geometry provenance cannot exceed MEDIUM.')}
W (Join-Path $OutDir 'topography_confidence_model.json') ($conf|ConvertTo-Json -Depth 10)
$plan=@'# TerraYield Topography Accuracy Upgrade Pipeline Plan

Status: draft governance pack only.

## Source chain
1. HMLR INSPIRE / National Polygon Service geometry.
2. EA LIDAR Composite DTM primary elevation.
3. OS Terrain 5/50 fallback and cross-check.
4. Local Terrarium 8099 and lookup 8765 preserved as current runtime only.

## Non-goals
No DB rebuild, SQL execution, Docker build/recreate, runtime restart, England-wide download, UI edit, or critical JS/unified panel edit.

## Next safe phase
Populate evidence JSON records one source at a time; AOI/tile whitelist only after review.
'@
W (Join-Path $OutDir 'TERRAYIELD_TOPOGRAPHY_PIPELINE_PLAN.md') $plan
$tests=@'# TerraYield Topography Acceptance Tests

- JSON files parse.
- CSV imports and contains no download_ready status.
- Canonical datum is exactly mAOD.
- Aliases include ODN and Ordnance Datum Newlyn.
- Local Terrarium/lookup are current runtime only.
- No DB, Docker, download, runtime restart, UI edit, critical JS edit, or unified panel edit.
- SQL exists but is not executed.
'@
W (Join-Path $OutDir 'TERRAYIELD_TOPOGRAPHY_ACCEPTANCE_TESTS.md') $tests
$index=[ordered]@{schema_version='1.0.0';pack_name='TERRAYIELD_TOPOGRAPHY_EVIDENCE_PACK_INDEX';phase='governance_only';runtime_impact='none';files=@('topography_source_registry.json','topography_dataset_evidence.template.json','topography_download_manifest.csv','parcel_elevation_schema.sql','topography_confidence_model.json','TERRAYIELD_TOPOGRAPHY_PIPELINE_PLAN.md','TERRAYIELD_TOPOGRAPHY_ACCEPTANCE_TESTS.md','TERRAYIELD_TOPOGRAPHY_STATIC_VALIDATION_REPORT.md');blocked_actions=@('db_rebuild','sql_execute','docker_build','docker_recreate','england_wide_download','runtime_restart','critical_ui_js_edit')}
W (Join-Path $OutDir 'TERRAYIELD_TOPOGRAPHY_EVIDENCE_PACK_INDEX.json') ($index|ConvertTo-Json -Depth 10)
$ok=$true;$r="# TerraYield Topography Static Validation Report`n`nTask: $TaskId`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n`n## Assertions`n- NO_DB TRUE`n- NO_DOCKER TRUE`n- NO_DOWNLOAD TRUE`n- NO_RESTART TRUE`n- NO_UI_EDIT TRUE`n"
foreach($jf in @('topography_source_registry.json','topography_dataset_evidence.template.json','topography_confidence_model.json','TERRAYIELD_TOPOGRAPHY_EVIDENCE_PACK_INDEX.json')){try{Get-Content -Raw (Join-Path $OutDir $jf)|ConvertFrom-Json|Out-Null;$r+="- PASS JSON $jf`n"}catch{$ok=$false;$r+="- FAIL JSON $jf $($_.Exception.Message)`n"}}
try{$rows=Import-Csv (Join-Path $OutDir 'topography_download_manifest.csv');$bad=@($rows|?{$_.status -match 'download_ready'});if($bad.Count -eq 0){$r+="- PASS manifest no download_ready`n"}else{$ok=$false;$r+="- FAIL manifest has download_ready`n"}}catch{$ok=$false;$r+="- FAIL manifest import $($_.Exception.Message)`n"}
$reg=Get-Content -Raw (Join-Path $OutDir 'topography_source_registry.json')|ConvertFrom-Json;if($reg.vertical_datum_standard.canonical_label -eq 'mAOD'){$r+="- PASS canonical datum mAOD`n"}else{$ok=$false;$r+="- FAIL canonical datum`n"}
$r+="`n## Runtime observe-only ports`n- 8010: $(P 8010)`n- 8099: $(P 8099)`n- 8765: $(P 8765)`n"
Set-Location $ProjectRoot;$st=git status --short 2>&1|Out-String;$r+="`n## Git status before commit`n```text`n$st`n````n"
if($st -match 'aays_topography_mode_v1.js|aays_topography_bulk_visible_parcels_v1.js'){$ok=$false;$r+="- FAIL critical topography JS diff detected`n"}else{$r+="- PASS no critical topography JS diff detected`n"}
$r+="`nVALIDATION_OK=$ok`n"
W $Report $r
Write-Output 'FILES_WRITTEN_BEGIN';Get-ChildItem $OutDir|Select Name,Length,LastWriteTime|Format-Table|Out-String|Write-Output;Write-Output 'FILES_WRITTEN_END'
try{Set-Location $ProjectRoot;git add topography_accuracy_upgrade_plan 2>&1|Out-String|Write-Output;$cached=git diff --cached --name-only 2>&1|Out-String;Write-Output 'CACHED_DIFF_BEGIN';Write-Output $cached;Write-Output 'CACHED_DIFF_END';$unsafe=$false;foreach($line in ($cached -split "`n")){$t=$line.Trim();if($t -and !$t.StartsWith('topography_accuracy_upgrade_plan/')){$unsafe=$true}};if($unsafe){git reset 2>&1|Out-String|Write-Output;Write-Output 'PROJECT_COMMIT_SKIPPED_UNSAFE_CACHED_PATH'}elseif([string]::IsNullOrWhiteSpace($cached)){Write-Output 'PROJECT_COMMIT_SKIPPED_NO_CHANGES'}else{git commit -m 'Add TerraYield topography accuracy governance pack' 2>&1|Out-String|Write-Output;git push 2>&1|Out-String|Write-Output;Write-Output 'PROJECT_COMMIT_PUSH_ATTEMPTED=TRUE'}}catch{Write-Output "PROJECT_COMMIT_ERROR=$($_.Exception.Message)"}
Write-Output "VALIDATION_OK=$ok"
Write-Output 'TERRAYIELD_TASK_DONE'
if($ok){exit 0}else{exit 1}
