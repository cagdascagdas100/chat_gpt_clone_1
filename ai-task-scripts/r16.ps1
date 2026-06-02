$B='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$P=Join-Path $B 'ai-results\r16.result.txt'
New-Item -ItemType Directory -Force -Path (Split-Path $P -Parent) | Out-Null
1..30 | % { Start-Sleep -Seconds 60 }
Set-Content -Encoding UTF8 -Path $P -Value 'task_id=r16;status=finished;plan_progress_percent=79'
exit 0
