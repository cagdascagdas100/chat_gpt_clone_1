$root = Split-Path -Parent $PSScriptRoot
$status = Join-Path $root 'status/security_shared_runner_task_latest.md'
$reportDir = Join-Path $root 'reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$appRoot = Join-Path (Get-Location) 'england_map_web'
$overlay = Join-Path $appRoot 'security_overlay.js'
$data = Join-Path $appRoot 'data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
$summary = Join-Path $appRoot 'data/parcel_security_scores_rechecked_0_120m_spatial.summary.json'
$okOverlay = Test-Path $overlay
$okData = Test-Path $data
$okSummary = Test-Path $summary
$state = 'static_probe_done'
$percent = '99'
$final = 'false'
$reason = 'proof_missing'
$content = "state: $state`npercent: $percent`nfinal: $final`nreason: $reason`noverlay: $okOverlay`ndata: $okData`nsummary: $okSummary"
Set-Content -Path $status -Value $content -Encoding UTF8
Set-Content -Path (Join-Path $reportDir 'security_static_probe_latest.txt') -Value $content -Encoding UTF8
Write-Output $content
