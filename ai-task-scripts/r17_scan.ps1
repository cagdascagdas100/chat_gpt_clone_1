$Root = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$Out = Join-Path $Root "ai-results\r17_scan.txt"

New-Item -ItemType Directory -Force -Path (Split-Path $Out -Parent) | Out-Null

$End = (Get-Date).AddMinutes(30)

while ((Get-Date) -lt $End) {
  Get-ChildItem -Path (Join-Path $Root "ai-results") -File -ErrorAction SilentlyContinue |
    Select-Object Name, Length, LastWriteTime |
    Out-String |
    Out-File -FilePath $Out -Encoding utf8 -Append

  Start-Sleep -Seconds 60
}

"task_id=r17_scan;status=finished;plan_progress_percent=82" |
  Out-File -FilePath $Out -Encoding utf8 -Append

exit 0
