# AAYS shared runner task script
# Page: AAYS_REAL_TOPOGRAPHY_PRODUCT
# Purpose: persist planned buildings workflow status artifacts for current queue gates.
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$ArtifactPairs = @(
  @{
    Report = 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/pb_status_probe_20260614T052500Z.txt'
    Status = 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/pb_status_probe_20260614T052500Z.txt'
    Task = 'planned_buildings_status_probe'
  },
  @{
    Report = 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/pb_runner_pickup_readiness_gate_20260615T013000Z.txt'
    Status = 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/pb_runner_pickup_readiness_gate_20260615T013000Z.txt'
    Task = 'planned_buildings_runner_pickup_readiness_gate'
  }
)
foreach ($Pair in $ArtifactPairs) {
  New-Item -ItemType Directory -Force -Path (Split-Path $Pair.Report) | Out-Null
  New-Item -ItemType Directory -Force -Path (Split-Path $Pair.Status) | Out-Null
  $ReportText = @(
    ('TASK: ' + $Pair.Task),
    'PAGE_KEY: AAYS_REAL_TOPOGRAPHY_PRODUCT',
    'STATUS: ARTIFACT_WRITER_OK',
    'FINAL_READY: false',
    'NEXT: run planned buildings readiness audit'
  )
  $StatusText = @(
    'PAGE_KEY: AAYS_REAL_TOPOGRAPHY_PRODUCT',
    'STATUS: ARTIFACT_WRITER_OK',
    'FINAL_READY: false'
  )
  Set-Content -Encoding UTF8 -Path $Pair.Report -Value $ReportText
  Set-Content -Encoding UTF8 -Path $Pair.Status -Value $StatusText
}
Write-Output 'AAYS_REAL_TOPOGRAPHY_PRODUCT artifact writer completed'
