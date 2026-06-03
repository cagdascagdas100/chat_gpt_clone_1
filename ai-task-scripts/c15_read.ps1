$p = "C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\c15_read.result.json"
New-Item -ItemType Directory -Force -Path (Split-Path $p -Parent) | Out-Null
1..30 | ForEach-Object { Start-Sleep -Seconds 60 }
'{"task_id":"c15_read","status":"finished","plan_progress_percent":76}' | Set-Content -Encoding UTF8 $p
exit 0
