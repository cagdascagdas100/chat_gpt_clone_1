param(
  [string]$Repo = 'C:\Users\cagda\Documents\GitHub\AAYS',
  [int]$DelaySeconds = 60
)

$ErrorActionPreference = 'Continue'
Write-Host 'AAYS runner loop started'
Write-Host "Repo=$Repo"

while ($true) {
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  Write-Host "LOOP_START=$stamp"
  try {
    git -C $Repo pull
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo 'tools\chatgpt_local_sync.ps1') -Repo $Repo
  } catch {
    Write-Host "LOOP_ERROR=$($_.Exception.Message)"
  }
  Start-Sleep -Seconds $DelaySeconds
}
