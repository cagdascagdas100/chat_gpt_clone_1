$ErrorActionPreference='Stop'
$PageKey='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch='aays-runner-v17-icon-work-20260603-232706'
$RepoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$ReportRel="docs/chatgpt_status/$PageKey/reports/pb_import_verified_planned_assets_data_20260621T000000Z.txt"
$StatusRel="docs/chatgpt_status/$PageKey/status/pb_import_verified_planned_assets_data_20260621T000000Z.txt"
$ReportPath=Join-Path $RepoRoot $ReportRel
$StatusPath=Join-Path $RepoRoot $StatusRel
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath),(Split-Path $StatusPath),(Join-Path $RepoRoot 'england_map_web\data') | Out-Null
function W($x){$x|Out-File $ReportPath -Append -Encoding utf8}
''|Out-File $ReportPath -Encoding utf8
W 'TASK=pb_import_verified_planned_assets_data_20260621T000000Z'
W "PAGE_KEY=$PageKey"
$accepted=@('TYLI_PLANNED_ASSETS_GEOJSON','AAYS_PLANNED_ASSETS_GEOJSON','PLANNED_ASSETS_PARCEL_LAYER_GEOJSON')
$candidates=@()
foreach($e in $accepted){$v=[Environment]::GetEnvironmentVariable($e); if($v){$candidates+=$v}}
$candidates+=(Join-Path $RepoRoot 'england_map_web\data\planned_assets_parcel_layer.geojson')
$candidates+=(Join-Path $RepoRoot 'england_map_web\data\planned_buildings_parcel_layer.geojson')
$candidates+=(Join-Path $RepoRoot 'terrayield_land_intelligence\data\planned_assets_parcel_layer.geojson')
$candidates+='F:\chatgpt\AAYS_RUNTIME\planned_buildings\sample_data\planned_assets_parcel_layer.geojson'
$candidates+='F:\chatgpt\AAYS_DATA\planned_assets_parcel_layer.geojson'
$candidates+='D:\AAYS_DATA\planned_assets_parcel_layer.geojson'
$required=@('parcel_id','planned_asset_count','planned_building_1_value','planned_building_1_probability','planned_building_1_completion_month','source_name','source_date','match_confidence_score','relation_type','calculation_explanation')
$source=$null
foreach($p in $candidates){
  if(-not $p -or -not (Test-Path -LiteralPath $p)){continue}
  try{
    $raw=Get-Content -LiteralPath $p -Raw -Encoding UTF8
    $json=$raw|ConvertFrom-Json
    if($json.type -ne 'FeatureCollection'){W "SKIP_NOT_FEATURE_COLLECTION=$p";continue}
    if(-not $json.features -or $json.features.Count -lt 1){W "SKIP_EMPTY_FEATURES=$p";continue}
    $ok=$true
    foreach($f in $json.features){
      if($f.type -ne 'Feature'){$ok=$false;break}
      foreach($k in $required){if(-not ($f.properties.PSObject.Properties.Name -contains $k)){$ok=$false;break}}
      if(-not $ok){break}
    }
    if($ok){$source=$p;break}else{W "SKIP_MISSING_REQUIRED_PROPERTIES=$p"}
  }catch{W "SKIP_PARSE_ERROR=$p ERROR=$($_.Exception.Message)"}
}
if($source){
  $dest=Join-Path $RepoRoot 'england_map_web\data\planned_assets_parcel_layer.geojson'
  Copy-Item -LiteralPath $source -Destination $dest -Force
  W "VERIFIED_DATA_IMPORTED=true"
  W "SOURCE=$source"
  W "DESTINATION=$dest"
  @('STATUS=VERIFIED_DATA_IMPORTED','FINAL_READY=false','REPORT='+$ReportRel)|Out-File $StatusPath -Encoding utf8
  git -C $RepoRoot add $ReportRel $StatusRel 'england_map_web/data/planned_assets_parcel_layer.geojson' | Out-Null
  git -C $RepoRoot commit -m 'Import verified planned assets data' | Out-Null
  git -C $RepoRoot push origin HEAD:$Branch | Out-Null
  exit 0
}
W 'VERIFIED_DATA_IMPORTED=false'
W 'FINAL_BLOCKER=NO_VERIFIED_FEATURE_COLLECTION_FOUND'
W 'NEXT_REQUIRED_ACTION=place verified planned_assets_parcel_layer.geojson in one accepted data path or set TYLI_PLANNED_ASSETS_GEOJSON'
@('STATUS=NO_VERIFIED_FEATURE_COLLECTION_FOUND','FINAL_READY=false','REPORT='+$ReportRel)|Out-File $StatusPath -Encoding utf8
git -C $RepoRoot add $ReportRel $StatusRel | Out-Null
$pending=git -C $RepoRoot status --porcelain -- $ReportRel $StatusRel
if($pending){git -C $RepoRoot commit -m 'Report missing verified planned assets data'|Out-Null;git -C $RepoRoot push origin HEAD:$Branch|Out-Null}
exit 1
