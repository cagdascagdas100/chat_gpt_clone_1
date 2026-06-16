# PAGE_KEY: AAYS_REAL_TOPOGRAPHY_PRODUCT
# TASK: pb_patch_audit
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$ReportPath = 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/pb_patch_audit_20260615T032000Z.txt'
$StatusPath = 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/pb_patch_audit_20260615T032000Z.txt'
$Checks = @(
  'england_map_web/app.js',
  'england_map_web/static/planed_buildings.png',
  'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/pb_patch_audit_20260615T032000Z.ps1'
)
$Lines = @()
$Lines += 'PAGE_KEY: ' + $PageKey
$Lines += 'TASK: pb_patch_audit'
$Lines += 'STATUS: AUDIT_STARTED'
foreach ($p in $Checks) {
  if (Test-Path $p) { $Lines += 'FOUND: ' + $p } else { $Lines += 'MISSING: ' + $p }
}
$Lines += 'FINAL_READY: false'
$Lines += 'NEXT: apply planned buildings product patch, then run smoke and data proof'
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $StatusPath) | Out-Null
Set-Content -Path $ReportPath -Value ($Lines -join "`n") -Encoding UTF8
Set-Content -Path $StatusPath -Value "PAGE_KEY: $PageKey`nSTATUS: AUDIT_STARTED`nFINAL_READY: false" -Encoding UTF8
