$ErrorActionPreference = 'Continue'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$statusDir = Join-Path $repo 'docs\chatgpt_status\aays1\status'
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
$out = Join-Path $statusDir 'local_8010_repair_latest.txt'
$log = @()
$log += 'started=' + (Get-Date -Format 'yyyyMMdd_HHmmss')
$log += 'repo=' + $repo
if (Test-Path $repo) {
  Push-Location $repo
  try {
    git pull --ff-only origin main | Out-Null
    $log += 'git_pull=done'
  } catch {
    $log += 'git_pull=failed'
  }
  Pop-Location
} else {
  $log += 'repo_missing=true'
}
$page = Join-Path $repo 'england_map_web\geometry_review_2of4_20260629.html'
if (Test-Path $page) { $log += 'page_exists=true' } else { $log += 'page_missing=true' }
try {
  $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8010/england_map_web/geometry_review_2of4_20260629.html' -UseBasicParsing -TimeoutSec 5
  $log += 'pre_status=' + $r.StatusCode
} catch {
  $log += 'pre_status=failed'
  try {
    Start-Process -FilePath 'python' -ArgumentList @('-m','http.server','8010','--bind','127.0.0.1') -WorkingDirectory $repo -WindowStyle Minimized | Out-Null
    Start-Sleep -Seconds 3
    $log += 'server_started=true'
  } catch {
    $log += 'server_started=false'
  }
}
try {
  $r2 = Invoke-WebRequest -Uri 'http://127.0.0.1:8010/england_map_web/geometry_review_2of4_20260629.html' -UseBasicParsing -TimeoutSec 8
  $log += 'final_status=' + $r2.StatusCode
} catch {
  $log += 'final_status=failed'
}
Set-Content -LiteralPath $out -Value ($log -join "`r`n") -Encoding UTF8
Push-Location $repo
try { git add docs/chatgpt_status/aays1/status/local_8010_repair_latest.txt; git commit -m 'Record local 8010 repair'; git push origin main } catch {}
Pop-Location
