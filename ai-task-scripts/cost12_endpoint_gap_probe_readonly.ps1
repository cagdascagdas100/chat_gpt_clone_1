$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Report=Join-Path $Out ('cost12_endpoint_gap_probe_readonly_'+$Stamp+'.md')
$Json=Join-Path $Out 'cost12_endpoint_gap_probe_readonly.result.json'
$CallsLog=Join-Path $Out ('cost12_endpoint_gap_probe_calls_'+$Stamp+'.jsonl')
function Add-Line($s){ $s | Tee-Object -FilePath $Report -Append }
function Call-Api($Name,$Method,$Uri,$Body=$null){
  $entry=[ordered]@{name=$Name;method=$Method;uri=$Uri;ok=$false;status='';detail='';body=$null}
  try{
    if($Method -eq 'GET'){$resp=Invoke-RestMethod -Uri $Uri -Method Get -TimeoutSec 20}
    else{$json=$Body|ConvertTo-Json -Depth 10; $resp=Invoke-RestMethod -Uri $Uri -Method Post -ContentType 'application/json' -Body $json -TimeoutSec 30}
    $entry.ok=$true; $entry.status='PASS'; $entry.body=$resp
  }catch{
    $entry.status='FAIL'
    $entry.detail=$_.Exception.Message
    try{
      $stream=$_.Exception.Response.GetResponseStream(); if($stream){$reader=New-Object System.IO.StreamReader($stream); $entry.body=$reader.ReadToEnd()}
    }catch{}
  }
  ($entry|ConvertTo-Json -Depth 12 -Compress)|Add-Content -Encoding UTF8 $CallsLog
  return [pscustomobject]$entry
}
Add-Line '# COST12 Endpoint Gap Probe Read-only'
Add-Line ('time='+($Stamp))
Add-Line 'db_write=false'
Add-Line 'production_deploy=false'
Add-Line 'fake_data=false'
Add-Line ''
Add-Line '## Source snippets'
$patterns=@('/cost/building-types/options','/cost/estimate/preview','cost-latest','cost-history','cost_uk_v1','spec_grade','region','No cost rate row','rate row','retail')
$snippetRows=@()
if(Test-Path $Project){
  $files=Get-ChildItem $Project -Recurse -File -Include *.py,*.csv,*.json,*.yaml,*.yml -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\.git\|node_modules|__pycache__|venv|\.venv'}
  foreach($f in $files){
    foreach($p in $patterns){
      try{ $hits=Select-String -Path $f.FullName -Pattern $p -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 5; foreach($h in $hits){$snippetRows += [pscustomobject]@{path=$f.FullName;line=$h.LineNumber;pattern=$p;text=$h.Line.Trim()}} }catch{}
    }
  }
}
$snippetCsv=Join-Path $Out ('cost12_endpoint_gap_probe_snippets_'+$Stamp+'.csv')
$snippetRows|Export-Csv -NoTypeInformation -Encoding UTF8 $snippetCsv
Add-Line ('snippet_csv='+$snippetCsv)
Add-Line ('snippet_count='+@($snippetRows).Count)
Add-Line ''
Add-Line '## API calls'
$Base='http://127.0.0.1:8010'
$results=@()
$results += Call-Api 'options' 'GET' ($Base+'/cost/building-types/options')
$results += Call-Api 'history' 'GET' ($Base+'/parcels/1/cost-history')
$results += Call-Api 'latest' 'GET' ($Base+'/parcels/1/cost-latest')
$payloads=@()
$payloads += [ordered]@{name='retail_mid_full';body=[ordered]@{parcel_id=1;building_type='retail';building_subtype='restaurant';quality_level='mid';spec_grade='mid';region='UK';scenario='cost_uk_v1';retail_category='restaurant';floors=2;room_count=8;gross_internal_area_m2=250;db_write=$false;production_deploy=$false}}
$payloads += [ordered]@{name='retail_high_original';body=[ordered]@{parcel_id=1;building_type='retail';building_subtype='restaurant';quality_level='high';retail_category='restaurant';floors=2;room_count=8;gross_internal_area_m2=250;db_write=$false;production_deploy=$false}}
$payloads += [ordered]@{name='retail_mid_no_region';body=[ordered]@{parcel_id=1;building_type='retail';building_subtype='restaurant';quality_level='mid';retail_category='restaurant';floors=2;room_count=8;gross_internal_area_m2=250;db_write=$false;production_deploy=$false}}
$payloads += [ordered]@{name='residential_mid_baseline';body=[ordered]@{parcel_id=1;building_type='house';quality_level='mid';floors=2;room_count=4;gross_internal_area_m2=120;db_write=$false;production_deploy=$false}}
foreach($p in $payloads){$results += Call-Api ('preview_'+$p.name) 'POST' ($Base+'/cost/estimate/preview') $p.body}
foreach($r in $results){ Add-Line ('- '+$r.name+': ok='+$r.ok+' status='+$r.status+' detail='+$r.detail+' body='+($r.body|ConvertTo-Json -Depth 8 -Compress)) }
$latest404=@($results|Where-Object {$_.name -eq 'latest' -and -not $_.ok -and ($_.detail -match '404' -or ($_.body -as [string]) -match '404|Not Found|Bulunamad')}).Count -gt 0
$previewFailures=@($results|Where-Object {$_.name -like 'preview_*' -and -not $_.ok})
$previewPasses=@($results|Where-Object {$_.name -like 'preview_*' -and $_.ok})
$decision='COST12_ENDPOINT_GAP_BLOCKED'
$next='inspect failure bodies and route mapping'
if(@($previewPasses).Count -gt 0 -and ($latest404 -or @($previewFailures).Count -gt 0)){ $decision='COST12_ENDPOINT_PARTIAL_READY'; $next='use passing preview payload or add read-only latest fallback if latest is expected before persisted estimate' }
if(@($previewPasses).Count -gt 0 -and -not $latest404 -and @($previewFailures).Count -eq 0){ $decision='COST12_ENDPOINT_READY' ; $next='done'}
$res=[ordered]@{task_id='cost12-endpoint-gap-probe-readonly';decision=$decision;preview_pass_count=@($previewPasses).Count;preview_fail_count=@($previewFailures).Count;latest404=$latest404;calls_log=$CallsLog;snippet_csv=$snippetCsv;report=$Report;db_write=$false;production_deploy=$false;fake_data=$false;next_required_action=$next}
$res|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $Json
Add-Line ''
Add-Line ('decision='+$decision)
Add-Line ('result_json='+$Json)
Get-Content $Json -Raw
