$Root=Split-Path -Parent $PSScriptRoot
$Hb=Join-Path $Root 'ai-heartbeat\rtsacc_016_visible_final_smoke_20260519.md'
$Res=Join-Path $Root 'ai-results\rtsacc-016-visible-final-smoke-20260519.md'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb),(Split-Path $Res)|Out-Null
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 016 HEARTBEAT','stage=START','progress=1')
$counts=@()
foreach($d in @('ai-results','ai-heartbeat','ready_to_sell_accuracy_runs','ai-runner-outputs')){$p=Join-Path $Root $d;$n=0;if(Test-Path $p){$n=@(Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue).Count};$counts+=($d+': '+$n)}
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 016 HEARTBEAT','stage=COMPLETE','progress=100')
Set-Content -Encoding UTF8 -Path $Res -Value (@('# RTSACC 016 visible final smoke','task_gate: COMPLETE','RTSACC_016_DONE=true')+$counts)
Write-Output 'RTSACC_016_DONE=true'
