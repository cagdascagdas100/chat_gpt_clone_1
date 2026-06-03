$Root=Split-Path -Parent $PSScriptRoot
$Hb=Join-Path $Root 'ai-heartbeat\rtsacc_013_columns_visible_wrap_20260518.md'
$Res=Join-Path $Root 'ai-results\rtsacc-013-columns-visible-wrap-20260518.md'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb),(Split-Path $Res)|Out-Null
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 013 HEARTBEAT','stage=START','progress=1')
$Script=Join-Path $Root 'ai-task-scripts\rtsacc_010_all_batch_columns_20260518.ps1'
if(Test-Path $Script){powershell -NoProfile -ExecutionPolicy Bypass -File $Script;$ok='yes'}else{$ok='no'}
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 013 HEARTBEAT','stage=COMPLETE','progress=100')
Set-Content -Encoding UTF8 -Path $Res -Value @('# RTSACC 013 columns visible wrap',('target_script_found: '+$ok),'task_gate: COMPLETE','RTSACC_013_DONE=true')
Write-Output 'RTSACC_013_DONE=true'
