$TaskId='rtsacc-002-smoke-20260518'
$Root=Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'ai-results'),(Join-Path $Root 'ai-heartbeat')|Out-Null
Set-Content -Encoding UTF8 -Path (Join-Path $Root 'ai-heartbeat\rtsacc_002_smoke_20260518.md') -Value @('# RTSACC 002 SMOKE','stage=COMPLETE','progress=100')
Set-Content -Encoding UTF8 -Path (Join-Path $Root 'ai-results\rtsacc-002-smoke-20260518.md') -Value @('# RTSACC 002 smoke','task_gate: COMPLETE','RTSACC_002_DONE=true')
Write-Output 'RTSACC_002_DONE=true'
