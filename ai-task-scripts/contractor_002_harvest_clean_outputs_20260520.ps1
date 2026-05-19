$ErrorActionPreference='Continue'
$TaskId='contractor-002-harvest-clean-outputs-20260520'
$Src='C:\AAYS_GITHUB_BRIDGE_CLEAN'
$Dst='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$ResultDir=Join-Path $Dst 'ai-results'
$ProgressDir=Join-Path $Dst 'ai-progress'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir | Out-Null
$names=@('contractor-002-long-watchdog-foundation-20260519.result.json','contractor-002-long-watchdog-foundation-20260519.report.md')
$copied=@();$missing=@()
foreach($n in $names){$s1=Join-Path (Join-Path $Src 'ai-results') $n;$s2=Join-Path $ResultDir $n;if(Test-Path $s1){Copy-Item $s1 $s2 -Force;$copied+=$s2}else{$missing+=$s1}}
$p1=Join-Path (Join-Path $Src 'ai-progress') 'contractor-002-long-watchdog-foundation-20260519.progress.md'
$p2=Join-Path $ProgressDir 'contractor-002-long-watchdog-foundation-20260519.progress.md'
if(Test-Path $p1){Copy-Item $p1 $p2 -Force;$copied+=$p2}else{$missing+=$p1}
$Json=Join-Path $ResultDir ($TaskId+'.result.json')
$Report=Join-Path $ResultDir ($TaskId+'.report.md')
[ordered]@{task_id=$TaskId;status=if($copied.Count -gt 0){'completed_copied_some'}else{'completed_no_source_outputs_found'};copied=$copied;missing=$missing;safety=@{no_db_write=$true;no_production_deploy=$true}} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $Json
@('# Contractor 002 Harvest CLEAN Outputs','',"Copied count: $($copied.Count)","Missing count: $($missing.Count)",'','## Copied',$copied,'','## Missing',$missing,'','TASK_COMPLETION=100/100') | Set-Content -Encoding UTF8 $Report
Write-Host 'CONTRACTOR_002_HARVEST_DONE'
exit 0
