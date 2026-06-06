$repoCandidates = @('C:\Users\cagda\Documents\GitHub\AAYS','C:\AAYS_GITHUB_BRIDGE_CLEAN2')
$repo = $repoCandidates | Where-Object { Test-Path (Join-Path $_ '.git') } | Select-Object -First 1
if (-not $repo) { throw 'AAYS repo not found' }
$dir = Join-Path $repo 'docs\chatgpt_status'
New-Item -ItemType Directory -Force $dir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = Join-Path $dir "AAYS_MAPDATA_LIVE_EVIDENCE_$stamp.txt"
$api = 'http://127.0.0.1:8000'
$lines = @('AAYS_MAPDATA_LIVE_EVIDENCE','DONE_BEFORE=97','LEFT_BEFORE=3')
try {
  $openapi = Invoke-RestMethod -TimeoutSec 10 "$api/openapi.json"
  $paths = $openapi.paths.PSObject.Properties.Name | Where-Object { $_ -match 'map|parcel|geo|data|layer|site|planning|growth|score' } | Select-Object -First 60
  $lines += 'OPENAPI_OK'
  $lines += 'CANDIDATE_PATHS=' + ($paths -join ',')
} catch {
  $paths = @()
  $lines += 'OPENAPI_FAIL=' + $_.Exception.Message
}
foreach ($p in $paths) {
  if ($p -match '\{') { continue }
  $u = "$api$p"
  try {
    $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 $u
    $lines += "OK $($r.StatusCode) $u"
  } catch {
    $lines += "FAIL $u"
  }
}
if (-not $paths -or $paths.Count -eq 0) { $lines += 'NO_CANDIDATE_PATHS' }
$lines += 'FINISHED_AT=' + (Get-Date -Format s)
$lines | Set-Content -Encoding UTF8 $out
Set-Location $repo
git add docs/chatgpt_status
if (git status --porcelain) {
  git commit -m 'Add AAYS mapdata live evidence'
  git push
}
