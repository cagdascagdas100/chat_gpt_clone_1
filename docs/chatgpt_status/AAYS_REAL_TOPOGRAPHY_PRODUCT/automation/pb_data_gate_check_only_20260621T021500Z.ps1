$ErrorActionPreference='Stop'
$page='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$target='england_map_web/data/planned_assets_parcel_layer.geojson'
$report="docs/chatgpt_status/$page/reports/pb_data_gate_check_only_20260621T021500Z.txt"
if(-not(Test-Path $target)){ 'STATUS=MISSING_DATA_FILE' | Set-Content $report; exit 1 }
$j=Get-Content $target -Raw | ConvertFrom-Json
$count=0
if($j.features){ $count=$j.features.Count }
if($count -lt 1){ @('STATUS=WAITING_FOR_VERIFIED_FEATURE','PROGRESS=99.999','DATA_PRESENT=false','FEATURE_COUNT=0','NEXT=Add one real verified planned asset feature') | Set-Content $report; exit 1 }
@('STATUS=DATA_PRESENT','FEATURE_COUNT='+$count,'NEXT=Run finalizer') | Set-Content $report
exit 0
