$pageRoot = Split-Path -Parent $PSScriptRoot
$status = Join-Path $pageRoot 'status/security_shared_runner_task_latest.md'
$reportDir = Join-Path $pageRoot 'reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$candidates = @((Join-Path (Get-Location) 'england_map_web'), (Join-Path $repoRoot 'england_map_web'), (Join-Path $repoRoot 'terrayield_land_intelligence\england_map_web'), 'C:\Users\cagda\Documents\GitHub\AAYS\england_map_web')
$appRoot = $null
foreach ($c in $candidates) { if (Test-Path (Join-Path $c 'security_overlay.js')) { $appRoot = $c; break } }
if ($null -eq $appRoot) { $appRoot = $candidates[0] }
$index = Join-Path $appRoot 'index.html'
$appjs = Join-Path $appRoot 'app.js'
$overlay = Join-Path $appRoot 'security_overlay.js'
$data = Join-Path $appRoot 'data\parcel_security_scores_rechecked_0_120m_spatial.geojson'
$summary = Join-Path $appRoot 'data\parcel_security_scores_rechecked_0_120m_spatial.summary.json'
$okIndex = Test-Path $index
$okApp = Test-Path $appjs
$okOverlay = Test-Path $overlay
$okData = Test-Path $data
$okSummary = Test-Path $summary
$contract = $false
if ($okOverlay) {
  $txt = Get-Content -Raw -Path $overlay
  $contract = ($txt -match 'parcel_security_scores_rechecked_0_120m_spatial.geojson') -and ($txt -match 'safety_score') -and ($txt -match 'confidence_score')
}
$state = 'ui_probe_done'
$percent = '99'
$final = 'false'
$reason = 'ui_runtime_proof_missing'
if ($okIndex -and $okApp -and $okOverlay -and $okData -and $okSummary -and $contract) { $reason = 'static_contract_ready_ui_runtime_needed' }
$content = "state: $state`npercent: $percent`nfinal: $final`nreason: $reason`nappRoot: $appRoot`nindex: $okIndex`napp: $okApp`noverlay: $okOverlay`ndata: $okData`nsummary: $okSummary`ncontract: $contract"
Set-Content -Path $status -Value $content -Encoding UTF8
Set-Content -Path (Join-Path $reportDir 'security_ui_probe_latest.txt') -Value $content -Encoding UTF8
Write-Output $content
