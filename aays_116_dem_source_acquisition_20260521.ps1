$Root='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$Res=Join-Path $Root 'ai-results'
New-Item -ItemType Directory -Force -Path $Res | Out-Null
$Result=Join-Path $Res 'aays-116-dem-source-acquisition-20260521.result.json'
$Report=Join-Path $Res 'aays-116-dem-source-acquisition-20260521.report.md'
$data=[ordered]@{status='completed_dem_source_plan';db_write=$false;production_deploy=$false;fake_data=$false;next_command='devam et'}
$data | ConvertTo-Json -Depth 4 | Set-Content -Path $Result -Encoding UTF8
Set-Content -Path $Report -Encoding UTF8 -Value 'AAYS 116 DEM source acquisition completed as safe plan. db_write=false production_deploy=false fake_data=false'
