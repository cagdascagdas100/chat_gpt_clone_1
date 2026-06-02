$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
$HbDir=Join-Path $Bridge 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $Out,$HbDir | Out-Null
$Hb=Join-Path $HbDir 'v8_real100_parallel_plan.md'
$Rep=Join-Path $Out 'v8_real100_parallel_plan.report.md'
$Json=Join-Path $Out 'v8_real100_parallel_plan.result.json'
function H($s,$m){ @('# v8_real100_parallel_plan','status='+$s,'message='+$m,'time='+(Get-Date -Format s),'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb }
H 'running' 'start dependency-aware read-only final validation'
$jobs=@()
$jobs += Start-Job -Name 'handoff_hash' -ScriptBlock {
  $H='E:\AAYS_DATA\cost\handoff_zips'; $Z=Join-Path $H 'cost12_integration_apply_20260524_050921.zip'; $S=Join-Path $H 'cost12_integration_apply_20260524_050921.sha256.txt'
  $ok=$false; $msg='missing'
  if((Test-Path $Z) -and (Test-Path $S)){ $a=(Get-FileHash $Z -Algorithm SHA256).Hash.ToUpper(); $e=(Get-Content $S -Raw).ToUpper(); $ok=$e.Contains($a); $msg='actual='+$a }
  [pscustomobject]@{name='handoff_hash';ok=$ok;message=$msg}
}
$jobs += Start-Job -Name 'route_scan' -ArgumentList $Project -ScriptBlock { param($Project)
  $hits=@(); if(Test-Path $Project){ $hits=Get-ChildItem $Project -Recurse -File -Include *.py | Select-String -Pattern '/cost/building-types/options|/cost/estimate/preview|cost-latest|cost-history' -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 20 }
  [pscustomobject]@{name='route_scan';ok=(@($hits).Count -gt 0);message=('hits='+@($hits).Count)}
}
$jobs += Start-Job -Name 'pytest_readonly' -ArgumentList $Project,$Out -ScriptBlock { param($Project,$Out)
  $tmp=Join-Path $Out 'pytest_tmp_v8_real100'; New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  $log=Join-Path $Out 'v8_real100_pytest.log'
  if(Test-Path $Project){ Set-Location $Project; $env:TEMP=$tmp; $env:TMP=$tmp; pytest -q tests/test_cost_preview_readonly.py tests/test_cost50_handoff_integration.py --basetemp=$tmp 2>&1 | Tee-Object -FilePath $log | Out-Null; $code=$LASTEXITCODE } else { $code=999 }
  [pscustomobject]@{name='pytest_readonly';ok=($code -eq 0);message=('exit='+$code+' log='+$log)}
}
$jobs += Start-Job -Name 'api_smoke' -ArgumentList $Out -ScriptBlock { param($Out)
  $log=Join-Path $Out 'v8_real100_api_smoke.log'; $base='http://127.0.0.1:8010'; $pass=0; $fail=0
  foreach($u in @('/cost/building-types/options','/parcels/1/cost-latest','/parcels/1/cost-history')){ try{ Invoke-RestMethod -Uri ($base+$u) -TimeoutSec 10 | Out-File -Append $log; $pass++ }catch{ ('FAIL '+$u+' '+$_.Exception.Message) | Out-File -Append $log; $fail++ } }
  $body=@{parcel_id=1;building_type='retail';building_subtype='restaurant';quality_level='high';retail_category='restaurant';floors=2;room_count=8;gross_internal_area_m2=250;db_write=$false;production_deploy=$false}|ConvertTo-Json -Depth 8
  try{ Invoke-RestMethod -Method Post -Uri ($base+'/cost/estimate/preview') -ContentType 'application/json' -Body $body -TimeoutSec 15 | Out-File -Append $log; $pass++ }catch{ ('FAIL POST preview '+$_.Exception.Message) | Out-File -Append $log; $fail++ }
  [pscustomobject]@{name='api_smoke';ok=($fail -eq 0);message=('pass='+$pass+' fail='+$fail+' log='+$log)}
}
$jobs += Start-Job -Name 'source_review' -ArgumentList $Out -ScriptBlock { param($Out)
  $csv=Join-Path $Out 'v8_review_sources.csv'; $count=0; if(Test-Path $csv){ $count=@(Import-Csv $csv).Count }
  [pscustomobject]@{name='source_review';ok=($count -gt 0);message=('review_rows='+$count)}
}
H 'running' 'parallel read-only jobs launched'
Wait-Job -Job $jobs -Timeout 1700 | Out-Null
$results=@(); foreach($j in $jobs){ if($j.State -eq 'Running'){ Stop-Job $j -Force | Out-Null; $results += [pscustomobject]@{name=$j.Name;ok=$false;message='timeout'} } else { $results += Receive-Job $j } }
$passed=@($results | Where-Object {$_.ok}).Count; $failed=@($results | Where-Object {-not $_.ok}).Count
$status=if($failed -eq 0){'real_100_validated'}else{'real_100_blockers_found'}
$progress=if($failed -eq 0){100}else{97}
@('# V8 Real 100 Parallel Plan','status='+$status,'passed='+$passed,'failed='+$failed,'overall_progress='+$progress,'db_write=false','production_deploy=false','fake_data=false','','## Results') | Set-Content -Encoding UTF8 $Rep
foreach($r in $results){ ('- '+$r.name+': ok='+$r.ok+'; '+$r.message) | Add-Content -Encoding UTF8 $Rep }
@{task_id='v8_real100_parallel_plan';status=$status;overall_progress=$progress;passed=$passed;failed=$failed;results=$results;report=$Rep;db_write=$false;production_deploy=$false;fake_data=$false} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Json
H 'finished' $status
exit 0
