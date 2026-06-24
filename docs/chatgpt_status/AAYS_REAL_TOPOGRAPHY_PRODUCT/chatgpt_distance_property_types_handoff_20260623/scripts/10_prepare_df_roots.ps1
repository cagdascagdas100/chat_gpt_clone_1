$ErrorActionPreference = 'Stop'

param(
  [string]$WorkRoot = 'F:\chatgpt\AAYS_WORK\distance_property_types_page34_20260623',
  [string]$DataRoot = 'D:\AAYS_DATA\distance_property_types_page34_20260623',
  [string]$HandoffRoot = 'F:\chatgpt\handoffs\distance_property_types_page34_20260623'
)

$targets = @(
  $WorkRoot,
  $DataRoot,
  (Join-Path $DataRoot 'reports'),
  (Join-Path $DataRoot 'exports'),
  (Join-Path $DataRoot 'logs'),
  $HandoffRoot
)

foreach ($target in $targets) {
  New-Item -ItemType Directory -Force -Path $target | Out-Null
}

Write-Output "prepared_work_root=$WorkRoot"
Write-Output "prepared_data_root=$DataRoot"
Write-Output "prepared_handoff_root=$HandoffRoot"
