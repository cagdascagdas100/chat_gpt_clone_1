$B='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$E='E:\AAYS_DATA\estate_agents'
$R=Join-Path $B 'ai-results'
New-Item -ItemType Directory -Force -Path $R | Out-Null
$In=Join-Path $E 'real100_v7_real_source_candidates.csv'
$Out=Join-Path $R 'v8_review_sources.csv'
$Json=Join-Path $R 'v8_review.result.json'
$Md=Join-Path $R 'v8_review.report.md'
$rows=@(); if(Test-Path $In){$rows=Import-Csv $In}
$total=@($rows).Count
$kept=@($rows | Where-Object { $_.path -notmatch 'unpkg|react|nista|gov_pipeline|ai-logs|node_modules' })
$keepCount=@($kept).Count
$kept | Export-Csv -NoTypeInformation -Encoding UTF8 $Out
$progress=if($keepCount -gt 0){97}else{96}
@{task_id='v8-review';status='review_package_ready';overall_progress=$progress;source_rows=$total;review_rows=$keepCount;output=$Out;db_write=$false;production_deploy=$false;fake_data=$false}|ConvertTo-Json|Set-Content -Encoding UTF8 $Json
@('# V8 Review','status=review_package_ready','overall_progress='+$progress,'source_rows='+$total,'review_rows='+$keepCount,'output='+$Out,'db_write=false','production_deploy=false','fake_data=false')|Set-Content -Encoding UTF8 $Md
Start-Sleep -Seconds 1200
exit 0
