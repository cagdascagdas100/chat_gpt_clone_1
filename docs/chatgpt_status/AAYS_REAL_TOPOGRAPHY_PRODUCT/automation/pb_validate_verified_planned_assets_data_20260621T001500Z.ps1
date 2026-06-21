$ErrorActionPreference='Continue'
$PageKey='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Repo=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$Base=Join-Path $Repo "docs\chatgpt_status\$PageKey"
$ReportDir=Join-Path $Base 'reports'
$StatusDir=Join-Path $Base 'status'
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Report=Join-Path $ReportDir 'pb_validate_verified_planned_assets_data_20260621T001500Z.txt'
$Status=Join-Path $StatusDir 'pb_validate_verified_planned_assets_data_20260621T001500Z.txt'
$Candidates=@('england_map_web\data\planned_assets_parcel_layer.geojson','terrayield_land_intelligence\data\planned_assets_parcel_layer.geojson','data\planned_assets_parcel_layer.geojson')|ForEach-Object{Join-Path $Repo $_}
$Required=@('parcel_id','planned_asset_count','planned_building_1_value','planned_building_1_probability','planned_building_1_completion_month','source_name','source_date','match_confidence_score','relation_type','calculation_explanation')
$found=$null;$missing=@()
foreach($f in $Candidates){if(Test-Path $f){try{$j=Get-Content $f -Raw|ConvertFrom-Json;if($j.type -eq 'FeatureCollection' -and $j.features.Count -gt 0){$p=$j.features[0].properties;$missing=@();foreach($r in $Required){if(-not($p.PSObject.Properties.Name -contains $r)){$missing+=$r}};if($missing.Count -eq 0){$found=$f;break}}}catch{}}}
if($found){@('FINAL_STATUS=VERIFIED_DATA_READY','DATA_PRESENT=true',"DATA_FILE=$found")|Set-Content $Report -Encoding utf8;@('FINAL_STATUS=VERIFIED_DATA_READY','DATA_PRESENT=true')|Set-Content $Status -Encoding utf8;exit 0}
@('FINAL_STATUS=WAITING_FOR_VERIFIED_DATA','DATA_PRESENT=false','MISSING_ITEMS=verified planned_assets_parcel_layer.geojson',('REQUIRED_PROPERTIES='+($Required -join ',')))|Set-Content $Report -Encoding utf8
@('FINAL_STATUS=WAITING_FOR_VERIFIED_DATA','DATA_PRESENT=false')|Set-Content $Status -Encoding utf8
exit 2
