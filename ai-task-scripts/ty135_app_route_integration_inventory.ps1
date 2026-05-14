$TaskId='ty135-app-route-integration-inventory'
$Bridge='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$report=@('# TY135 App Route Integration Inventory','')
$targets=@('app\main.py','app\api','app\routers','app\routes','app\services','app\schemas')
$existing=@()
foreach($t in $targets){$p=Join-Path $Project $t;if(Test-Path $p){$existing += $p}}
$report += '## Existing integration locations'
$report += $existing
$patterns='FastAPI|APIRouter|include_router|@router|get\(|post\(|prefix=|contractor|runtime_ops|ops|dashboard'
$hits=@()
foreach($root in @('app')){
  $dir=Join-Path $Project $root
  if(Test-Path $dir){
    Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Extension -eq '.py'} | ForEach-Object {
      $m=Select-String -Path $_.FullName -Pattern $patterns -ErrorAction SilentlyContinue | Select-Object -First 12
      foreach($x in $m){$hits += ($_.FullName + ':' + $x.LineNumber + ': ' + $x.Line.Trim())}
    }
  }
}
$exports=@('E:\AAYS_DATA\contractor\exports\contractors_for_app.csv','E:\AAYS_DATA\contractor\exports\contractors_for_app.jsonl','E:\AAYS_DATA\contractor\exports\contractor_projects_for_app.csv','E:\AAYS_DATA\contractor\exports\contractor_parcel_matches_for_app.csv','E:\AAYS_DATA\contractor\exports\export_manifest.json')
$ready=0
$report += ''
$report += '## Export files'
foreach($e in $exports){$i=Get-Item $e -ErrorAction SilentlyContinue;if($i){$ready++;$report += ('- '+$e+' exists bytes='+$i.Length+' modified='+$i.LastWriteTime.ToString('s'))}else{$report += ('- '+$e+' MISSING')}}
$progress=55
if($hits.Count -gt 0){$progress=60}
$report += ''
$report += '## Route/service hits'
$report += $hits
$report += ''
$report += '## Recommended patch plan'
$report += '- Add a read-only contractor export service under app/services.'
$report += '- Add a read-only API router under the detected app API/router structure.'
$report += '- Return CSV/JSONL-backed summaries without exposing suppressed contact fields.'
$report += '- Keep DO_NOT_CONTACT gate unchanged; do not alter source export files.'
$report.Insert(2,('Plan completed: '+$progress+'%'))
$report.Insert(3,('Plan remaining: '+(100-$progress)+'%'))
$report | Set-Content -Encoding UTF8 (Join-Path $Out 'ty135-app-route-integration-inventory.report.md')
Write-Output ('PLAN_PROGRESS_PERCENT='+$progress)
Write-Output ('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
