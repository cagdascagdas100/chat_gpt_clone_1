$ErrorActionPreference = 'Continue'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$statusDir = Join-Path $repo 'docs\chatgpt_status\aays1\status'
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
$out = Join-Path $statusDir 'pull_main_for_local_dashboard_latest.txt'
$log = @()
$log += 'started=' + (Get-Date -Format 'yyyyMMdd_HHmmss')
$log += 'repo=' + $repo
if (Test-Path $repo) {
  Push-Location $repo
  try {
    git stash push -u -m aays_local_dashboard_sync | Out-Null
    git fetch origin main | Out-Null
    git pull --ff-only origin main | Out-Null
    $log += 'pull=done'
  } catch {
    $log += 'pull=failed'
    $log += $_.Exception.Message
  }
  $page = Join-Path $repo 'england_map_web\geometry_review_2of4_20260629.html'
  if (Test-Path $page) {
    $text = Get-Content -Raw -LiteralPath $page
    if ($text -match 'Guncel 4 uzerinden dogruluk skalasi' -or $text -match 'Kanıt ve Geometri') { $log += 'dashboard=present' } else { $log += 'dashboard=missing' }
  } else { $log += 'page=missing' }
  Pop-Location
} else { $log += 'repo=missing' }
Set-Content -LiteralPath $out -Value ($log -join "`r`n") -Encoding UTF8
Push-Location $repo
try { git add docs/chatgpt_status/aays1/status/pull_main_for_local_dashboard_latest.txt; git commit -m 'Record dashboard pull sync'; git push origin main } catch {}
Pop-Location
