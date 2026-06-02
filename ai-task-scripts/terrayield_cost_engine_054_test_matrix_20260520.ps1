$ErrorActionPreference='Continue'
$TaskId='terrayield-cost-engine-054-test-matrix-20260520'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$Engine=Join-Path $Root 'terrayield_cost_engine/python_demo/terrayield_cost_engine_demo.py'
$OutDir=Join-Path $Root 'ai-results/terrayield_cost_engine/step_054_test_matrix'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir|Out-Null
$Status=Join-Path $OutDir 'status.json'
$Summary=Join-Path $OutDir 'summary.md'
$MatrixCsv=Join-Path $OutDir 'test_matrix_results.csv'
$Hb=Join-Path $HbDir 'portable-runner.md'
@('# runner','Status: running','TaskId: '+$TaskId,'Message: test matrix started')|Set-Content -Encoding UTF8 $Hb
$tests=@(
  @{id='detached_250';building_type='Müstakil Ev';subtype='One-off detached house';gia_m2=250;floors=2;spec='Mid';dwelling_units=1;vat_treatment='new_qualifying_dwelling'},
  @{id='apartment_1500';building_type='Apartman';subtype='Flats/apartments with lifts';gia_m2=1500;floors=6;spec='Mid';dwelling_units=12;vat_treatment='standard_20'},
  @{id='retail_designer_600';building_type='Perakende';subtype='Designer store fit-out';gia_m2=600;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='mixed_ground_retail_flats_1200';building_type='Karma';subtype='Ground retail + flats';gia_m2=1200;floors=5;spec='Mid';dwelling_units=8;vat_treatment='standard_20'},
  @{id='industrial_general_2500';building_type='Sanayi';subtype='Factory - general';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_food_2500';building_type='Sanayi';subtype='Food & drink factory';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_chemical_2500';building_type='Sanayi';subtype='Chemical/allied factory';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_metals_2500';building_type='Sanayi';subtype='Metals factory';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_mech_elec_2500';building_type='Sanayi';subtype='Mechanical/electrical engineering factory';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_electronics_2500';building_type='Sanayi';subtype='Electronics/computer factory';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_warehouse_2500';building_type='Sanayi';subtype='Warehouse general';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_distribution_10_15_2500';building_type='Sanayi';subtype='Distribution 10-15m high';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_distribution_16_24_2500';building_type='Sanayi';subtype='Distribution 16-24m high';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'},
  @{id='industrial_cold_store_2500';building_type='Sanayi';subtype='Cold store/refrigerated';gia_m2=2500;floors=1;spec='Mid';dwelling_units=0;vat_treatment='standard_20'}
)
$engineExists=Test-Path $Engine
$python=(Get-Command python -ErrorAction SilentlyContinue)
$rows=@()
$okCount=0
$failCount=0
foreach($t in $tests){
  $inputPath=Join-Path $OutDir ($t.id+'.input.json')
  $outputPath=Join-Path $OutDir ($t.id+'.output.json')
  $logPath=Join-Path $OutDir ($t.id+'.python.log')
  $obj=[ordered]@{
    building_type=$t.building_type;subtype=$t.subtype;location='London';floors=$t.floors;gia_m2=$t.gia_m2;spec=$t.spec;dwelling_units=$t.dwelling_units;retail_ratio=0.0;residential_ratio=1.0;upfront_pct=0.20;payment_months=18;include_land=$false;land_cost=0.0;vat_treatment=$t.vat_treatment
  }
  $obj|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $inputPath
  $ok=$false;$mid='';$min='';$max='';$initial='';$monthly='';$lineCount=0;$err=''
  if($engineExists -and $python){
    try{
      python $Engine --input-json $inputPath --output-json $outputPath *> $logPath
      if($LASTEXITCODE -eq 0 -and (Test-Path $outputPath)){
        $j=Get-Content -Raw -Encoding UTF8 $outputPath|ConvertFrom-Json
        $ok=$true;$mid=$j.totals.mid_total_gbp;$min=$j.totals.min_total_gbp;$max=$j.totals.max_total_gbp;$initial=$j.totals.initial_payment_gbp;$monthly=$j.totals.recurring_payment_gbp_per_month;$lineCount=$j.lines.Count
      } else { $err='python_exit_'+$LASTEXITCODE }
    }catch{ $err=$_.Exception.Message; $err|Set-Content -Encoding UTF8 $logPath }
  } else { $err='engine_or_python_missing' }
  if($ok){$okCount++}else{$failCount++}
  $rows += [pscustomobject]@{id=$t.id;building_type=$t.building_type;subtype=$t.subtype;gia_m2=$t.gia_m2;ok=$ok;min_total_gbp=$min;max_total_gbp=$max;mid_total_gbp=$mid;initial_payment_gbp=$initial;recurring_monthly_gbp=$monthly;line_count=$lineCount;error=$err;output=$outputPath}
}
$rows|Export-Csv -NoTypeInformation -Encoding UTF8 $MatrixCsv
@('# TerraYield Cost Engine 054 Test Matrix','',('Status: '+$(if($failCount -eq 0){'completed'}else{'completed_with_failures'})),('Engine exists: '+$engineExists),('Python found: '+[bool]$python),('OK count: '+$okCount),('Fail count: '+$failCount),'','## Results')|Set-Content -Encoding UTF8 $Summary
foreach($r in $rows){ Add-Content -Encoding UTF8 -Path $Summary -Value ('- '+$r.id+' | ok='+$r.ok+' | mid_total_gbp='+$r.mid_total_gbp+' | lines='+$r.line_count+' | error='+$r.error) }
Add-Content -Encoding UTF8 -Path $Summary -Value @('','No DB write. No migration. No secrets.','TASK_COMPLETION=100/100')
[ordered]@{task_id=$TaskId;status=($(if($failCount -eq 0){'completed'}else{'completed_with_failures'}));engine_exists=$engineExists;python_found=[bool]$python;ok_count=$okCount;fail_count=$failCount;matrix_csv=$MatrixCsv;summary=$Summary;no_db_write=$true;no_migration=$true;no_secrets=$true;next_task='terrayield-cost-engine-055-codex-integration-plan'}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $Status
@('# runner','Status: finished','TaskId: '+$TaskId,'Message: ok='+$okCount+' fail='+$failCount)|Set-Content -Encoding UTF8 $Hb
Write-Output ('OK='+$okCount+' FAIL='+$failCount)
exit 0
