$pageRoot = Split-Path -Parent $PSScriptRoot
$status = Join-Path $pageRoot 'status/security_shared_runner_task_latest.md'
$reportDir = Join-Path $pageRoot 'reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$candidates = @()
$candidates += (Join-Path (Get-Location) 'england_map_web')
$candidates += (Join-Path $repoRoot 'england_map_web')
$candidates += (Join-Path $repoRoot 'terrayield_land_intelligence\england_map_web')
$candidates += 'C:\Users\cagda\Documents\GitHub\AAYS\england_map_web'
$appRoot = $null
foreach ($c in $candidates) {
  if (Test-Path (Join-Path $c 'security_overlay.js')) { $appRoot = $c; break }
}
if ($null -eq $appRoot) { $appRoot = $candidates[0] }
$overlay = Join-Path $appRoot 'security_overlay.js'
$data = Join-Path $appRoot 'data\parcel_security_scores_rechecked_0_120m_spatial.geojson'
$summary = Join-Path $appRoot 'data\parcel_security_scores_rechecked_0_120m_spatial.summary.json'
$okOverlay = Test-Path $overlay
$okData = Test-Path $data
$createdSummary = $false
$featureCount = -1
if ((Test-Path $data) -and (-not (Test-Path $summary))) {
  try {
    $geo = Get-Content -Raw -Path $data | ConvertFrom-Json
    if ($null -ne $geo.features) { $featureCount = $geo.features.Count }
    $obj = [ordered]@{
      layer = 'security_public_safety'
      generated_by = 'security_static_probe'
      source_geojson = $data
      feature_count = $featureCount
      final = $false
      note = 'derived summary for runner static probe'
    }
    $obj | ConvertTo-Json -Depth 5 | Set-Content -Path $summary -Encoding UTF8
    $createdSummary = $true
  } catch {
    $createdSummary = $false
  }
}
$okSummary = Test-Path $summary
$state = 'static_probe_done'
$percent = '99'
$final = 'false'
$reason = 'proof_missing'
if (($okOverlay -eq $true) -and ($okData -eq $true) -and ($okSummary -eq $true)) { $reason = 'browser_proof_missing' }
$content = "state: $state`npercent: $percent`nfinal: $final`nreason: $reason`nappRoot: $appRoot`noverlay: $okOverlay`ndata: $okData`nsummary: $okSummary`ncreatedSummary: $createdSummary`nfeatureCount: $featureCount"
Set-Content -Path $status -Value $content -Encoding UTF8
Set-Content -Path (Join-Path $reportDir 'security_static_probe_latest.txt') -Value $content -Encoding UTF8
Write-Output $content