$ErrorActionPreference='Continue'
$B='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$E='E:\AAYS_DATA\estate_agents'
$R=Join-Path $B 'ai-results'
New-Item -ItemType Directory -Force -Path $E,$R | Out-Null
$Out=Join-Path $E 'real100_v7_real_source_candidates.csv'
$Res=Join-Path $R 'real100_v7_real_source_filter.result.json'
$Rep=Join-Path $R 'real100_v7_real_source_filter.report.md'
$Roots=@('E:\AAYS_DATA','C:\AAYS_GITHUB_BRIDGE_CLEAN2','C:\Users\cagda\Documents\GitHub\AAYS')
'path,bytes,score,reason' | Set-Content -Encoding UTF8 $Out
$count=0
$good=0
foreach($root in $Roots){
 if(Test-Path $root){
  Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Extension -match 'csv|txt|md|html|json'} | Select-Object -First 4000 | ForEach-Object {
   $count++
   $p=$_.FullName
   if($p -match 'unpkg|react|bundle|\.js|gov_pipeline|nista|node_modules|\.git|ai-logs') { return }
   $s=0
   $name=$_.Name.ToLowerInvariant()
   if($name -match 'estate|agent|branch|property|contact|letting|sales'){$s+=2}
   try{$head=(Get-Content $p -TotalCount 80 -ErrorAction SilentlyContinue) -join ' '}catch{$head=''}
   if($head -match 'estate agent|property agent|letting agent|branch|office|contact us'){$s+=2}
   if($head -match '[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}'){$s++}
   if($head -match '@'){$s++}
   if($head -match 'https?://'){$s++}
   if($head -match '\+44|\b0[0-9]{10}\b'){$s++}
   if($s -ge 4){$good++; ('"'+$p+'",'+$_.Length+','+$s+',"filtered_real_source_candidate"') | Add-Content -Encoding UTF8 $Out}
  }
 }
}
$status=if($good -gt 0){'real_source_candidates_found_needs_review'}else{'blocked_no_real_source_candidates'}
$progress=if($good -gt 0){97}else{96}
@{task_id='real100-v7-real-source-filter';status=$status;overall_progress=$progress;files_scanned=$count;real_source_candidates=$good;output=$Out;db_write=$false;production_deploy=$false;fake_data=$false} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $Res
@('# Real100 V7 Real Source Filter','status='+$status,'overall_progress='+$progress,'files_scanned='+$count,'real_source_candidates='+$good,'output='+$Out,'DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false') | Set-Content -Encoding UTF8 $Rep
Start-Sleep -Seconds 1800
exit 0
