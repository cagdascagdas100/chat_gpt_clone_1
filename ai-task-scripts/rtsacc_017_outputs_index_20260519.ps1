$Root=Split-Path -Parent $PSScriptRoot
$Hb=Join-Path $Root 'ai-heartbeat\rtsacc_017_outputs_index_20260519.md'
$Res=Join-Path $Root 'ai-results\rtsacc-017-outputs-index-20260519.md'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb),(Split-Path $Res)|Out-Null
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 017 HEARTBEAT','stage=START','progress=1')
$lines=@('# RTSACC 017 outputs index',('generated: '+(Get-Date -Format s)),'')
foreach($d in @('ai-runner-outputs','ai-results','ai-heartbeat')){$p=Join-Path $Root $d;$lines+=('## '+$d);if(Test-Path $p){$files=Get-ChildItem $p -Recurse -File|Sort-Object LastWriteTime -Descending|Select-Object -First 80;$lines+=('file_count_seen: '+@($files).Count);foreach($f in $files){$lines+=('- '+$f.FullName+' size='+$f.Length+' updated='+$f.LastWriteTime.ToString('s'))}}else{$lines+='missing'};$lines+=''}
$lines+='task_gate: COMPLETE'
$lines+='RTSACC_017_DONE=true'
Set-Content -Encoding UTF8 -Path $Res -Value $lines
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 017 HEARTBEAT','stage=COMPLETE','progress=100')
Write-Output 'RTSACC_017_DONE=true'
