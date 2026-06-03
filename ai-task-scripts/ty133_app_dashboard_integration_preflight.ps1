$TaskId='ty133-app-dashboard-integration-preflight'
$Bridge='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Out=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$exports='E:\AAYS_DATA\contractor\exports'
$project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$files=@()
foreach($p in @('contractors_for_app.csv','contractors_for_app.jsonl','contractor_projects_for_app.csv','contractor_parcel_matches_for_app.csv','export_manifest.json')){ $f=Join-Path $exports $p; $i=Get-Item $f -ErrorAction SilentlyContinue; if($i){$files += "$p exists bytes=$($i.Length) modified=$($i.LastWriteTime.ToString('s'))"}else{$files += "$p missing"}}
$dirs=@()
foreach($d in @('app','api','backend','frontend','dashboard','src','pages','components','scripts')){ $p=Join-Path $project $d; if(Test-Path $p){$dirs += $d}}
$progress=10
if($files -notmatch 'missing'){$progress=25}
$report=@('# TY133 App Dashboard Integration Preflight','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),'','## Export files') + $files + @('','## Project dirs') + $dirs + @('','## Next Action','Map these exports into app/dashboard/API consumers.')
$report | Set-Content -Encoding UTF8 (Join-Path $Out 'ty133-app-dashboard-integration-preflight.report.md')
Write-Output ('PLAN_PROGRESS_PERCENT='+$progress)
Write-Output ('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
