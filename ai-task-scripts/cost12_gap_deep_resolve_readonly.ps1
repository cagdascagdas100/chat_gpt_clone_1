$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
$HbDir=Join-Path $Bridge 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $Out,$HbDir | Out-Null
$Hb=Join-Path $HbDir 'cost12_gap_deep_resolve_readonly.md'
$Rep=Join-Path $Out 'cost12_gap_deep_resolve_readonly.report.md'
$Json=Join-Path $Out 'cost12_gap_deep_resolve_readonly.result.json'
$CandidateCsv=Join-Path $Out 'cost12_ratecard_deep_candidates.csv'
$LowExportCsv=Join-Path $Out 'cost12_low_items_deep_candidates.csv'
$EndpointLog=Join-Path $Out 'cost12_endpoint_deep_smoke.log'
function Write-Cost12Hb($s,$m){ @('# cost12_gap_deep_resolve_readonly','status='+$s,'message='+$m,'time='+(Get-Date -Format s),'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb }
Write-Cost12Hb 'running' 'start deep dependency-aware read-only resolve'
$jobs=@()
$jobs += Start-Job -Name 'ratecard_deep_scan' -ArgumentList $Project,$CandidateCsv -ScriptBlock { param($Project,$CandidateCsv)
  $rows=@()
  if(Test-Path $Project){
    $files=Get-ChildItem $Project -Recurse -File -Include *.csv,*.json,*.yaml,*.yml,*.py -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|node_modules|__pycache__|venv|\.venv' }
    foreach($f in $files){
      try{
        $txt=Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
        $score=0
        foreach($p in @('retail','mid','UK','cost_uk_v1','rate','card','building_type','spec_grade')){ if($txt -match [regex]::Escape($p)){ $score++ } }
        if($score -ge 3){ $rows += [pscustomobject]@{path=$f.FullName;score=$score;has_retail=($txt -match 'retail');has_mid=($txt -match 'mid');has_UK=($txt -match 'UK');has_cost_uk_v1=($txt -match 'cost_uk_v1')} }
      }catch{}
    }
  }
  $rows | Sort-Object score -Descending | Export-Csv -NoTypeInformation -Encoding UTF8 $CandidateCsv
  $exact=@($rows | Where-Object { $_.has_retail -and $_.has_mid -and $_.has_UK -and $_.has_cost_uk_v1 })
  [pscustomobject]@{name='ratecard_deep_scan';ok=(@($exact).Count -gt 0);exact_count=@($exact).Count;candidate_count=@($rows).Count;output=$CandidateCsv}
}
$jobs += Start-Job -Name 'low_items_deep_scan' -ArgumentList $Bridge,$Project,$LowExportCsv -ScriptBlock { param($Bridge,$Project,$LowExportCsv)
  $rows=@()
  foreach($root in @($Bridge,$Project)){
    if(Test-Path $root){
      $files=Get-ChildItem $root -Recurse -File -Include *.csv,*.json,*.md -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|node_modules|__pycache__|venv|\.venv' }
      foreach($f in $files){
        try{
          $txt=Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
          if($txt -match 'accuracy_score_4|LOW|low_reliability|source_url_or_path|PENDING_FROM_PREVIEW_EXPORT'){
            $rows += [pscustomobject]@{path=$f.FullName;has_accuracy=($txt -match 'accuracy_score_4');has_LOW=($txt -match 'LOW');has_source=($txt -match 'source_url_or_path');bytes=$txt.Length}
          }
        }catch{}
      }
    }
  }
  $rows | Sort-Object has_accuracy,has_LOW -Descending | Export-Csv -NoTypeInformation -Encoding UTF8 $LowExportCsv
  [pscustomobject]@{name='low_items_deep_scan';ok=(@($rows).Count -gt 0);candidate_count=@($rows).Count;output=$LowExportCsv}
}
$jobs += Start-Job -Name 'endpoint_deep_smoke' -ArgumentList $EndpointLog -ScriptBlock { param($EndpointLog)
  $base='http://127.0.0.1:8010'; $pass=0; $fail=0
  $payload=@{parcel_id=1;building_type='retail';building_subtype='restaurant';quality_level='mid';spec_grade='mid';region='UK';scenario='cost_uk_v1';retail_category='restaurant';floors=2;room_count=8;gross_internal_area_m2=250;db_write=$false;production_deploy=$false}|ConvertTo-Json -Depth 8
  foreach($u in @('/cost/building-types/options','/parcels/1/cost-latest','/parcels/1/cost-history')){ try{ $r=Invoke-RestMethod -Uri ($base+$u) -TimeoutSec 12; ('PASS GET '+$u) | Out-File -Append $EndpointLog; $pass++ }catch{ ('FAIL GET '+$u+' '+$_.Exception.Message) | Out-File -Append $EndpointLog; $fail++ } }
  try{ $r=Invoke-RestMethod -Method Post -Uri ($base+'/cost/estimate/preview') -ContentType 'application/json' -Body $payload -TimeoutSec 20; ('PASS POST preview') | Out-File -Append $EndpointLog; ($r|ConvertTo-Json -Depth 8)|Out-File -Append $EndpointLog; $pass++ }catch{ ('FAIL POST preview '+$_.Exception.Message) | Out-File -Append $EndpointLog; $fail++ }
  [pscustomobject]@{name='endpoint_deep_smoke';ok=($fail -eq 0);pass=$pass;fail=$fail;output=$EndpointLog}
}
$jobs += Start-Job -Name 'source_policy' -ScriptBlock {
  [pscustomobject]@{name='source_policy';ok=$true;message='No fake price inserted; verified source required: BCIS/RICS/official_fee_table/supplier_quote'}
}
Write-Cost12Hb 'running' 'parallel jobs launched'
Wait-Job -Job $jobs -Timeout 1500 | Out-Null
$results=@()
foreach($j in $jobs){ if($j.State -eq 'Running'){ Stop-Job $j -Force|Out-Null; $results += [pscustomobject]@{name=$j.Name;ok=$false;message='timeout'} } else { $results += Receive-Job $j } }
$rateOk=(@($results|Where-Object{$_.name -eq 'ratecard_deep_scan' -and $_.ok}).Count -gt 0)
$endpointOk=(@($results|Where-Object{$_.name -eq 'endpoint_deep_smoke' -and $_.ok}).Count -gt 0)
$decision=if($rateOk -and $endpointOk){'COST12_GAP_FIX_READY'}else{'COST12_GAP_FIX_BLOCKED'}
$progress=if($decision -eq 'COST12_GAP_FIX_READY'){100}else{98}
@('# COST12 GAP Deep Resolve Read-only Report','','decision='+$decision,'overall_progress='+$progress,'db_write=false','production_deploy=false','fake_data=false','','## Parallel results') | Set-Content -Encoding UTF8 $Rep
foreach($r in $results){ ($r | ConvertTo-Json -Compress -Depth 6) | Add-Content -Encoding UTF8 $Rep }
@{task_id='cost12-gap-deep-resolve-readonly';decision=$decision;overall_progress=$progress;results=$results;candidate_csv=$CandidateCsv;low_items_csv=$LowExportCsv;endpoint_log=$EndpointLog;report=$Rep;db_write=$false;production_deploy=$false;fake_data=$false;next_required_action=if($decision -eq 'COST12_GAP_FIX_READY'){'done'}else{'provide verified rate row source for retail/mid/UK/cost_uk_v1 or mount endpoint if smoke failed'}} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Json
Write-Cost12Hb 'finished' $decision
Start-Sleep -Seconds 600
exit 0
