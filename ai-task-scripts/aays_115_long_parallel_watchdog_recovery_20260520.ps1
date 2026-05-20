$ErrorActionPreference='Continue'
$TaskId='aays-115-long-parallel-watchdog-recovery-20260520'
$Root=Split-Path -Parent $PSScriptRoot
$Start=Get-Date
$ResultDir=Join-Path $Root 'ai-results'
$ProgressDir=Join-Path $Root 'ai-progress'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir,$HbDir | Out-Null
$Progress=Join-Path $ProgressDir ($TaskId+'.progress.md')
$Result=Join-Path $ResultDir ($TaskId+'.result.json')
$Report=Join-Path $ResultDir ($TaskId+'.report.md')
function W($m){Add-Content -LiteralPath $Report -Encoding UTF8 -Value $m}
function P($pct,$phase){@('# '+$TaskId,'percent: '+$pct,'phase: '+$phase,'elapsed_minutes: '+[math]::Round(((Get-Date)-$Start).TotalMinutes,2))|Set-Content -Encoding UTF8 $Progress; @('# AAYS Portable Task Runner Fixed','Status: running','TaskId: '+$TaskId,'Message: '+$phase)|Set-Content -Encoding UTF8 (Join-Path $HbDir 'portable-runner.md')}
Set-Content -LiteralPath $Report -Encoding UTF8 -Value '# AAYS 115 Long Parallel Watchdog Recovery'
W "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
W 'mode=read_only_parallel_watchdog_no_db_no_deploy'
$checks=@(
 @{name='task_files';paths=@('ai-tasks/current-task.json','ai-tasks/.last-task-id','ai-heartbeat/portable-runner.md')},
 @{name='cost_engine';paths=@('ai-task-scripts/terrayield_cost_engine_051_smoke_test_20260520.ps1','terrayield_cost_engine/python_demo/terrayield_cost_engine_demo.py')},
 @{name='contractor';paths=@('ai-task-scripts/contractor_004_parcel_group_coverage_scoring_20260520.ps1','ai-task-scripts/terrayield_contractor_003_official_source_collector_and_normalizer.ps1')},
 @{name='dem';paths=@('ai-results/aays-113-dem-broad-inventory-20260519.result.json','ai-results/aays-114b-long-dem-classifier-watchdog-20260520.result.json')}
)
$summary=@()
for($cycle=1;$cycle -le 12;$cycle++){
 $pct=[int](5+$cycle*7)
 P $pct ('cycle_'+$cycle)
 W ""
 W "## cycle_$cycle $((Get-Date).ToUniversalTime().ToString('o'))"
 $jobs=@()
 foreach($c in $checks){
  $jobs+=Start-Job -ScriptBlock {
   param($Root,$Name,$Paths)
   $out=@()
   foreach($p in $Paths){$full=Join-Path $Root $p; $out += "$Name|$p|exists=$(Test-Path -LiteralPath $full)"}
   $out
  } -ArgumentList $Root,$c.name,(,$c.paths)
 }
 Wait-Job -Job $jobs -Timeout 120 | Out-Null
 foreach($j in $jobs){
  if($j.State -eq 'Running'){Stop-Job -Job $j -Force; W "job_timeout_stopped=$($j.Id)"; $summary += "timeout:$($j.Id)"}
  else {$data=Receive-Job -Job $j -ErrorAction SilentlyContinue; foreach($line in $data){W $line; $summary += $line}}
  Remove-Job -Job $j -Force -ErrorAction SilentlyContinue
 }
 if($cycle -lt 12){Start-Sleep -Seconds 180}
}
P 95 'writing_result'
$missing=@($summary | Where-Object {$_ -like '*exists=False*'})
$obj=[ordered]@{task_id=$TaskId;status='completed_read_only_watchdog';elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);missing_count=$missing.Count;missing_items=$missing;notes='Use missing items to choose next recovery task. No DB write, no deploy, no secrets.';next_recommended_task='If cost engine output still missing, run short result-only cost engine recovery. If contractor outputs missing, run contractor result-only recovery. If DEM still missing, wait for official DEM raster placement.'}
$obj|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $Result -Encoding UTF8
W ""
W '## final'
W "status=completed_read_only_watchdog"
W "result_json=$Result"
W "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
P 100 'completed'
Write-Host 'AAYS_115_DONE'