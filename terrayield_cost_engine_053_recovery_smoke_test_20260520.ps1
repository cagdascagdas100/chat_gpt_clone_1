$Root='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$Out=Join-Path $Root 'ai-results/terrayield_cost_engine'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$Summary=Join-Path $Out 'step_053_recovery_smoke_test_summary.json'
$Report=Join-Path $Out 'step_053_recovery_smoke_test_report.md'
$Cases=Join-Path $Out 'step_053_recovery_cases.json'
$Start=Get-Date
$caseRows=@(
  [ordered]@{case='detached_recovery';area_m2=180;base_cost_per_m2=1400;factor=1.08;status='demo_smoke_only'},
  [ordered]@{case='industrial_recovery';area_m2=1200;base_cost_per_m2=900;factor=1.15;status='demo_smoke_only'},
  [ordered]@{case='missing_input_guard';area_m2=0;base_cost_per_m2=0;factor=0;status='guard_only'}
)
$outRows=@()
foreach($c in $caseRows){
  $estimate=0
  if($c.area_m2 -gt 0){$estimate=[math]::Round(([decimal]$c.area_m2*[decimal]$c.base_cost_per_m2*[decimal]$c.factor),2)}
  $outRows += [ordered]@{case=$c.case;estimate=$estimate;status=$c.status;note='not_price_forecast'}
}
$outRows | ConvertTo-Json -Depth 6 | Set-Content -Path $Cases -Encoding UTF8
[ordered]@{status='completed_recovery_smoke_test';cases=$outRows.Count;outputs=@($Cases,$Report);safety=[ordered]@{db_write=$false;migration=$false;secret_output=$false;not_price_forecast=$true};started_at=$Start.ToString('s');finished_at=(Get-Date).ToString('s')} | ConvertTo-Json -Depth 8 | Set-Content -Path $Summary -Encoding UTF8
Set-Content -Path $Report -Encoding UTF8 -Value "# TerraYield Cost Engine Step 053 Recovery Smoke Test`nstatus=completed_recovery_smoke_test`ncases=$($outRows.Count)`nsummary=$Summary`nno_db_write=true`nno_migration=true`nnot_price_forecast=true`n"
