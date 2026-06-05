$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Queue=Join-Path $Bridge 'ai-queue'
$Running=Join-Path $Queue 'running'
$Failed=Join-Path $Queue 'failed'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Quarantine=Join-Path $Failed "stale_running_unblock_$Stamp"
New-Item -ItemType Directory -Force -Path $Quarantine | Out-Null
$Cutoff=(Get-Date).AddHours(-6)
Get-ChildItem $Running -File -Filter '*.task.json' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $Cutoff } | ForEach-Object { Move-Item $_.FullName (Join-Path $Quarantine $_.Name) -Force }
$Runner=Join-Path $Bridge 'ai-task-scripts\portable_queue_runner.ps1'
$procs=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'portable_queue_runner.ps1' } | Sort-Object CreationDate)
if($procs.Count -gt 1){ $procs | Select-Object -Skip 1 | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }
if($procs.Count -eq 0 -and (Test-Path $Runner)){ Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" }
iwr -UseBasicParsing 'https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/main/ai-task-scripts/bootstrap_aays_v21_queue_status_report.ps1' | iex
