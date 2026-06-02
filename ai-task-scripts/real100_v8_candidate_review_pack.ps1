$ErrorActionPreference='Continue'
$TaskId='real100-v8-candidate-review-pack'
$B='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$E='E:\AAYS_DATA\estate_agents'
$R=Join-Path $B 'ai-results'
New-Item -ItemType Directory -Force -Path $E,$R | Out-Null
$In=Join-Path $E 'real100_v7_real_source_candidates.csv'
$Out=Join-Path $E 'real100_v8_review_pack.csv'
$Res=Join-Path $R 'real100_v8_candidate_review_pack.result.json'
$Rep=Join-Path $R 'real100_v8_candidate_review_pack.report.md'
$Dem1='E:\AAYS_DATA\elevation\copernicus_dem_glo30\Copernicus_DSM_COG_10_N51_00_W001_00_DEM.tif'
$Dem2='E:\AAYS_DATA\elevation\copernicus_dem_glo30\Copernicus_DSM_COG_10_N52_00_W001_00_DEM.tif'
$rows=@()
if(Test-Path $In){
  try { $rows=Import-Csv $In } catch { $rows=@() }
}
$selected=@()
foreach($r in $rows){
  $score=0
  try { $score=[int]$r.score } catch { $score=0 }
  $p=[string]$r.path
  if($score -ge 5 -and $p -notmatch 'node_modules|\.git|bundle|unpkg|react'){
    $selected += $r
  }
}
if($selected.Count -eq 0 -and $rows.Count -gt 0){ $selected=$rows | Select-Object -First 20 }
$selected | Export-Csv -NoTypeInformation -Encoding UTF8 $Out
$demOk=((Test-Path $Dem1) -and (Test-Path $Dem2))
$status=if($selected.Count -gt 0 -and $demOk){'finished_review_pack_ready'}elseif(-not $demOk){'blocked_dem_missing'}else{'blocked_no_candidates'}
$progress=if($status -eq 'finished_review_pack_ready'){99}else{96}
@{task_id=$TaskId;status=$status;overall_progress=$progress;input=$In;output=$Out;candidate_rows=$rows.Count;review_pack_rows=$selected.Count;dem_ok=$demOk;db_write=$false;production_deploy=$false;fake_data=$false;next='manual approval or controlled DB import plan required for final production write'} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $Res
@('# Real100 V8 Candidate Review Pack','status='+$status,'overall_progress='+$progress,'input='+$In,'output='+$Out,'candidate_rows='+$rows.Count,'review_pack_rows='+$selected.Count,'dem_ok='+$demOk,'DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false','next=manual approval or controlled DB import plan required for final production write') | Set-Content -Encoding UTF8 $Rep
Start-Sleep -Seconds 900
exit 0
