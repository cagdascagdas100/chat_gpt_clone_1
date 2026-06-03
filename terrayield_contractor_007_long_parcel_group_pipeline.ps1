$Root='C:/AAYS_GITHUB_BRIDGE_CLEAN'
$Data='E:/AAYS_DATA/contractor'
$Res=Join-Path $Root 'ai-results'
$Exp=Join-Path $Data 'exports'
$Man=Join-Path $Data 'manifests'
New-Item -ItemType Directory -Force -Path $Res,$Exp,$Man | Out-Null
$Report=Join-Path $Res 'contractor-007-long-parcel-group-pipeline-20260521.report.md'
$Manifest=Join-Path $Man 'contractor_007_long_pipeline_manifest.json'
$Groups=Join-Path $Exp 'england_parcel_groups_200.csv'
$Template=Join-Path $Exp 'contractor_rows_template.csv'
Set-Content -Path $Groups -Encoding UTF8 -Value 'group_id,region,status'
1..200 | ForEach-Object { Add-Content -Path $Groups -Encoding UTF8 -Value ('PG'+$_.ToString('000')+',England,template_only') }
Set-Content -Path $Template -Encoding UTF8 -Value 'contractor_name,source_url,confidence,status'
[ordered]@{status='completed_template_only';groups=200;db_write=$false;production_deploy=$false;fake_contractors=$false;next_command='devam et'} | ConvertTo-Json -Depth 5 | Set-Content -Path $Manifest -Encoding UTF8
Set-Content -Path $Report -Encoding UTF8 -Value 'contractor 007 completed template-only; db_write=false; production_deploy=false; fake_contractors=false'
