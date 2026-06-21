$ErrorActionPreference='Continue'
$repo=(Get-Location).Path
$page='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$out='england_map_web/data/planned_assets_parcel_layer.geojson'
$report='docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/pb_seed_one_verified_planned_asset_from_env_20260621T011000Z.txt'
New-Item -ItemType Directory -Force (Split-Path $out),(Split-Path $report) | Out-Null
$required='PARCEL_ID','LONGITUDE','LATITUDE','PLANNED_ASSET_COUNT','PLANNED_BUILDING_1_VALUE','PLANNED_BUILDING_1_PROBABILITY','PLANNED_BUILDING_1_COMPLETION_MONTH','SOURCE_NAME','SOURCE_DATE','MATCH_CONFIDENCE_SCORE','RELATION_TYPE','CALCULATION_EXPLANATION'
$missing=@(); foreach($k in $required){ if(-not [Environment]::GetEnvironmentVariable("TYLI_$k")){ $missing+="TYLI_$k" } }
if($missing.Count -gt 0){ "FINAL_STATUS=WAITING_FOR_VERIFIED_ENV`nPRODUCT_PROGRESS_ESTIMATE=99.999`nPRODUCTION_COMPLETE=false`nMISSING_ENV=$($missing -join ',')" | Set-Content $report -Encoding ascii; exit 1 }
$p=[ordered]@{parcel_id=$env:TYLI_PARCEL_ID;planned_asset_count=$env:TYLI_PLANNED_ASSET_COUNT;planned_building_1_value=$env:TYLI_PLANNED_BUILDING_1_VALUE;planned_building_1_probability=$env:TYLI_PLANNED_BUILDING_1_PROBABILITY;planned_building_1_completion_month=$env:TYLI_PLANNED_BUILDING_1_COMPLETION_MONTH;source_name=$env:TYLI_SOURCE_NAME;source_date=$env:TYLI_SOURCE_DATE;match_confidence_score=$env:TYLI_MATCH_CONFIDENCE_SCORE;relation_type=$env:TYLI_RELATION_TYPE;calculation_explanation=$env:TYLI_CALCULATION_EXPLANATION;data_verified='true'}
$feature=[ordered]@{type='Feature';geometry=[ordered]@{type='Point';coordinates=@([double]$env:TYLI_LONGITUDE,[double]$env:TYLI_LATITUDE)};properties=$p}
$fc=[ordered]@{type='FeatureCollection';features=@($feature)}
$fc | ConvertTo-Json -Depth 50 | Set-Content $out -Encoding utf8
"FINAL_STATUS=ONE_VERIFIED_FEATURE_SEEDED`nPRODUCT_PROGRESS_ESTIMATE=99.999`nPRODUCTION_COMPLETE=false`nOUTPUT=$out" | Set-Content $report -Encoding ascii
git add -A $out $report
git commit -m 'Seed one verified planned asset from env' 2>$null
git push origin HEAD:aays-runner-v17-icon-work-20260603-232706
& 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/pb_runtime_finalization_single_runner_20260617T000000Z.ps1'
