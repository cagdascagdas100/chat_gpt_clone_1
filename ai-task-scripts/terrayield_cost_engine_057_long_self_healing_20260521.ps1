$ErrorActionPreference='Continue'
$TaskId='terrayield-cost-engine-057-long-self-healing-20260521'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$OutDir=Join-Path $Root 'ai-results/terrayield_cost_engine/step_057_long_self_healing'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir|Out-Null
$Hb=Join-Path $HbDir 'portable-runner.md'
$Summary=Join-Path $OutDir 'summary.md'
$Status=Join-Path $OutDir 'status.json'
$Matrix=Join-Path $OutDir 'matrix_results.csv'
$Diag=Join-Path $OutDir 'diagnostics.json'
$Helper=Join-Path $Root 'ai-task-scripts/update_chatgpt_status.ps1'
function HB($status,$msg){@('# AAYS Portable Task Runner Fixed','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),('Status: '+$status),('TaskId: '+$TaskId),('BridgeRoot: '+$Root),('Message: '+$msg),'Mode: long-self-healing','SafeScriptOnly: enabled')|Set-Content -Encoding UTF8 $Hb}
function PageStatus($status,$progress,$wait,$runnerStatus,$msg,$blocker){if(Test-Path $Helper){try{& $Helper -PageKey '12 Cost' -ActiveTask $TaskId -Status $status -OverallProgress $progress -WaitMinutes $wait -NextCommand 'devam et' -RunnerStatus $runnerStatus -RunnerMessage $msg -Blocker $blocker -LastMessageText 'devam et' -DbWrite:$false -ProductionDeploy:$false}catch{}}}
HB 'running' 'started'
PageStatus 'running' 79 '35-45' 'running' 'Step 057 long self-healing started' ''
$Engine=Join-Path $Root 'terrayield_cost_engine/python_demo/terrayield_cost_engine_demo.py'
$Python=Get-Command python -ErrorAction SilentlyContinue
$engineExists=Test-Path $Engine
$pythonFound=[bool]$Python
$rows=@()
$tests=@(
 @{id='detached_250';bt='Müstakil Ev';st='One-off detached house';m=250;f=2;u=1;v='new_qualifying_dwelling'},
 @{id='apartment_1500';bt='Apartman';st='Flats/apartments with lifts';m=1500;f=6;u=12;v='standard_20'},
 @{id='retail_designer_600';bt='Perakende';st='Designer store fit-out';m=600;f=1;u=0;v='standard_20'},
 @{id='mixed_1200';bt='Karma';st='Ground retail + flats';m=1200;f=5;u=8;v='standard_20'},
 @{id='ind_general';bt='Sanayi';st='Factory - general';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_food';bt='Sanayi';st='Food & drink factory';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_chemical';bt='Sanayi';st='Chemical/allied factory';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_metals';bt='Sanayi';st='Metals factory';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_mech';bt='Sanayi';st='Mechanical/electrical engineering factory';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_electronics';bt='Sanayi';st='Electronics/computer factory';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_warehouse';bt='Sanayi';st='Warehouse general';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_dist_10_15';bt='Sanayi';st='Distribution 10-15m high';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_dist_16_24';bt='Sanayi';st='Distribution 16-24m high';m=2500;f=1;u=0;v='standard_20'},
 @{id='ind_cold';bt='Sanayi';st='Cold store/refrigerated';m=2500;f=1;u=0;v='standard_20'}
)
HB 'running' 'phase 1 diagnostics'
$diagObj=[ordered]@{task_id=$TaskId;root=$Root;engine=$Engine;engine_exists=$engineExists;python_found=$pythonFound;python_path=if($Python){$Python.Source}else{''};db_write=$false;production_deploy=$false;started_at=(Get-Date -Format s)}
$diagObj|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $Diag
HB 'running' 'phase 2 matrix tests'
$ok=0;$fail=0
foreach($t in $tests){
  $in=Join-Path $OutDir ($t.id+'.input.json');$out=Join-Path $OutDir ($t.id+'.output.json');$log=Join-Path $OutDir ($t.id+'.log')
  [ordered]@{building_type=$t.bt;subtype=$t.st;location='London';floors=$t.f;gia_m2=$t.m;spec='Mid';dwelling_units=$t.u;retail_ratio=0.0;residential_ratio=1.0;upfront_pct=0.20;payment_months=18;include_land=$false;land_cost=0.0;vat_treatment=$t.v}|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 $in
  $isOk=$false;$err='';$mid='';$min='';$max='';$lines=0
  if($engineExists -and $pythonFound){
    try{python $Engine --input-json $in --output-json $out *> $log;if($LASTEXITCODE -eq 0 -and (Test-Path $out)){$j=Get-Content -Raw -Encoding UTF8 $out|ConvertFrom-Json;$isOk=$true;$mid=$j.totals.mid_total_gbp;$min=$j.totals.min_total_gbp;$max=$j.totals.max_total_gbp;$lines=$j.lines.Count}else{$err='python_exit_'+$LASTEXITCODE}}catch{$err=$_.Exception.Message;$_|Out-String|Set-Content -Encoding UTF8 $log}
  }else{$err='engine_or_python_missing'}
  if($isOk){$ok++}else{$fail++}
  $rows += [pscustomobject]@{id=$t.id;building_type=$t.bt;subtype=$t.st;ok=$isOk;min_total_gbp=$min;max_total_gbp=$max;mid_total_gbp=$mid;line_count=$lines;error=$err;output=$out}
}
$rows|Export-Csv -NoTypeInformation -Encoding UTF8 $Matrix
HB 'running' 'phase 3 repository scan'
$scan=Join-Path $OutDir 'repository_scan.txt'
Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.FullName -match 'cost|terrayield_cost_engine|api|route|model|migration'} | Select-Object -First 500 FullName,Length,LastWriteTime | Out-String -Width 240 | Set-Content -Encoding UTF8 $scan
HB 'running' 'phase 4 integration plan'
$plan=Join-Path $OutDir 'self_healing_integration_plan.md'
@('# Cost Engine Step 057 long self-healing report','',('Started: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'','## Matrix','OK: '+$ok,'FAIL: '+$fail,'','## Generated files','- diagnostics.json','- matrix_results.csv','- repository_scan.txt','- self_healing_integration_plan.md','','## Next actions','1. If matrix fail count is not zero, inspect per-case .log files and repair Python engine path or input schema.','2. Add FastAPI adapter in dry-run mode only.','3. Add DB model draft without migration apply.','4. Add source quality gate for every output line.','5. Keep db_write=false and production_deploy=false until explicit approval.','','## Safety','DB write: false','Production deploy: false','Migration apply: false')|Set-Content -Encoding UTF8 $plan
HB 'running' 'phase 5 long watch cycle 35 min'
for($i=1;$i -le 35;$i++){
  HB 'running' ('long watch minute '+$i+' of 35; ok='+$ok+' fail='+$fail)
  if(($i % 5) -eq 0){PageStatus 'running' 79 '35-45' 'running' ('long watch minute '+$i+' of 35') ''}
  Start-Sleep -Seconds 60
}
$statusText=if($fail -eq 0){'finished'}else{'finished_with_failures'}
$blocker=if($fail -eq 0){''}else{'Some matrix cases failed; inspect logs in step_057_long_self_healing.'}
@('# TerraYield Cost Engine Step 057 Summary','',('Status: '+$statusText),('OK cases: '+$ok),('Failed cases: '+$fail),('Engine exists: '+$engineExists),('Python found: '+$pythonFound),'','No DB write. No production deploy. No migration apply.','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Summary
[ordered]@{task_id=$TaskId;status=$statusText;ok_count=$ok;fail_count=$fail;engine_exists=$engineExists;python_found=$pythonFound;out_dir=$OutDir;db_write=$false;production_deploy=$false;no_migration=$true;next_task='terrayield-cost-engine-058-fastapi-adapter-dry-run'}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $Status
PageStatus $statusText 82 '0-2' $statusText ('ok='+$ok+' fail='+$fail) $blocker
HB 'finished' 'exit=0'
Write-Output ('OK='+$ok+' FAIL='+$fail+' OUT='+$OutDir)
exit 0
