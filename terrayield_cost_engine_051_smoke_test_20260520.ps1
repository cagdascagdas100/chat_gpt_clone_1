$Root='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$Out=Join-Path $Root 'ai-results/terrayield_cost_engine'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$Summary=Join-Path $Out 'step_051_smoke_test_summary.json'
$Report=Join-Path $Out 'step_051_smoke_test_report.md'
$Detached=Join-Path $Out 'detached_example.json'
$Industrial=Join-Path $Out 'industrial_example.json'
$Start=Get-Date
$examples=@(
  @{name='detached';area_m2=180;build_type='detached';base_cost_per_m2=1400;site_factor=1.08},
  @{name='industrial';area_m2=1200;build_type='industrial';base_cost_per_m2=900;site_factor=1.15}
)
$results=@()
foreach($e in $examples){
  $base=[decimal]$e.area_m2*[decimal]$e.base_cost_per_m2
  $estimate=[math]::Round([decimal]$base*[decimal]$e.site_factor,2)
  $row=[ordered]@{name=$e.name;area_m2=$e.area_m2;build_type=$e.build_type;base_cost_per_m2=$e.base_cost_per_m2;site_factor=$e.site_factor;estimate=$estimate;status='demo_smoke_only'}
  $results += $row
  $path=if($e.name -eq 'detached'){$Detached}else{$Industrial}
  $row | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8
}
[ordered]@{status='completed_smoke_test';started_at=$Start.ToString('s');finished_at=(Get-Date).ToString('s');outputs=@($Detached,$Industrial,$Report);cases=$results;safety=[ordered]@{db_write=$false;migration=$false;secret_output=$false};note='demo smoke outputs only; not a price forecast'} | ConvertTo-Json -Depth 8 | Set-Content -Path $Summary -Encoding UTF8
Set-Content -Path $Report -Encoding UTF8 -Value "# TerraYield Cost Engine Step 051 Smoke Test`nstatus=completed_smoke_test`ncases=2`noutput_summary=$Summary`nno_db_write=true`nno_migration=true`nnot_price_forecast=true`n"
