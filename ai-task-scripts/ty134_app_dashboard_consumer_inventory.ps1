$TaskId='ty134-app-dashboard-consumer-inventory'
$Bridge='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$patterns='contractors_for_app|contractor_projects_for_app|contractor_parcel_matches_for_app|contractor|parcel|dashboard|route|export_manifest'
$hits=@()
foreach($root in @('app','scripts')){
  $dir=Join-Path $Project $root
  if(Test-Path $dir){
    Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Extension -in @('.py','.ts','.tsx','.js','.jsx','.json','.md')} | ForEach-Object {
      $m=Select-String -Path $_.FullName -Pattern $patterns -ErrorAction SilentlyContinue | Select-Object -First 5
      foreach($x in $m){$hits += ($_.FullName + ':' + $x.LineNumber + ': ' + $x.Line.Trim())}
    }
  }
}
$files=@()
foreach($p in @('E:\AAYS_DATA\contractor\exports\contractors_for_app.csv','E:\AAYS_DATA\contractor\exports\contractors_for_app.jsonl','E:\AAYS_DATA\contractor\exports\contractor_projects_for_app.csv','E:\AAYS_DATA\contractor\exports\contractor_parcel_matches_for_app.csv','E:\AAYS_DATA\contractor\exports\export_manifest.json')){ $i=Get-Item $p -ErrorAction SilentlyContinue; if($i){$files += ('- '+$p+' bytes='+$i.Length+' modified='+$i.LastWriteTime.ToString('s'))}else{$files += ('- '+$p+' MISSING')}}
$progress=40
if($hits.Count -gt 0){$progress=45}
$report=@('# TY134 App Dashboard Consumer Inventory','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),'','## Export readiness') + $files + @('','## Consumer/code hits') + $hits + @('','## Next Action','Patch app code to read contractor export files or expose them through a route.')
$report | Set-Content -Encoding UTF8 (Join-Path $Out 'ty134-app-dashboard-consumer-inventory.report.md')
Write-Output ('PLAN_PROGRESS_PERCENT='+$progress)
Write-Output ('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
