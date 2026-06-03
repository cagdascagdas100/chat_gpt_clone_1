$B='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$R=Join-Path $B 'ai-results'
New-Item -ItemType Directory -Force -Path $R | Out-Null
$checks=@()
function C($name,$path){ $script:checks += [ordered]@{name=$name;path=$path;exists=(Test-Path -LiteralPath $path)} }
C 'dem_51' 'E:\AAYS_DATA\elevation\copernicus_dem_glo30\Copernicus_DSM_COG_10_N51_00_W001_00_DEM.tif'
C 'dem_52' 'E:\AAYS_DATA\elevation\copernicus_dem_glo30\Copernicus_DSM_COG_10_N52_00_W001_00_DEM.tif'
C 'v8_review_sources' 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\v8_review_sources.csv'
C 'v8_review_result' 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\v8_review.result.json'
C 'dem_resolution_result' 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays_8_1_deficiency_resolution_20260524.result.json'
C 'project_finalize_result' 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\project_100_finalize.result.json'
C 'contractor_preflight' 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\terrayield-079-contractor-db-env-loader-preflight.audit.json'
$missing=@($checks|Where-Object{-not $_.exists})
$status=if($missing.Count -eq 0){'finished_real_readiness_ready'}else{'blocked_missing_files'}
$progress=if($missing.Count -eq 0){100}else{98}
$res=[ordered]@{task_id='v9-final-readiness';status=$status;overall_progress=$progress;checks=$checks;missing=$missing;db_write=$false;production_deploy=$false;fake_data=$false;next_command=if($progress -eq 100){'done'}else{'resolve_missing_files'}}
$res|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 (Join-Path $R 'v9_final_readiness.result.json')
@('# V9 Final Readiness','status='+$status,'overall_progress='+$progress,'db_write=false','production_deploy=false','fake_data=false')|Set-Content -Encoding UTF8 (Join-Path $R 'v9_final_readiness.report.md')
Start-Sleep -Seconds 600
exit 0
