$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$Helper=Join-Path $PSScriptRoot 'update_chatgpt_status.ps1'
if(-not (Test-Path -LiteralPath $Helper)){ throw "missing helper: $Helper" }
& $Helper `
  -PageKey '2.1 Sold Buildings' `
  -ActiveTask 'terrayield-cost-engine-055-integration-fix-plan-20260520' `
  -Status 'finished' `
  -OverallProgress 90 `
  -WaitMinutes '0' `
  -NextCommand 'devam et' `
  -RunnerStatus 'finished' `
  -RunnerMessage 'exit=0' `
  -Blocker '' `
  -LastMessageText 'sayfa adı: 2.1 Sold Buildings status yönergesi' `
  -DbWrite:$false `
  -ProductionDeploy:$false
$StatusDir=Join-Path $Root 'docs/chatgpt_status'
$JsonPath=Join-Path $StatusDir 'multi_page_status.json'
$Standalone=Join-Path $StatusDir 'status_dashboard_standalone.html'
if((Test-Path -LiteralPath $JsonPath) -and (Test-Path -LiteralPath $Standalone)){
  $json=(Get-Content -LiteralPath $JsonPath -Raw -Encoding UTF8).Trim()
  $html=Get-Content -LiteralPath $Standalone -Raw -Encoding UTF8
  $pattern='const EMBEDDED=\{.*?\};function esc'
  $replacement='const EMBEDDED='+$json+';function esc'
  $new=[regex]::Replace($html,$pattern,$replacement,'Singleline')
  if($new -ne $html){ Set-Content -LiteralPath $Standalone -Encoding UTF8 -Value $new }
}
$ResultDir=Join-Path $Root 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir|Out-Null
$result=[ordered]@{
  task_id='status-update-2-1-sold-buildings-20260520'
  status='completed'
  page_key='2.1 Sold Buildings'
  db_write=$false
  production_deploy=$false
  updated_files=@('docs/chatgpt_status/multi_page_status.json','docs/chatgpt_status/status.md','docs/chatgpt_status/status_dashboard_standalone.html')
  updated_at=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
}
$result|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $ResultDir 'status-update-2-1-sold-buildings-20260520.result.json') -Encoding UTF8
Write-Output 'STATUS_UPDATE_2_1_SOLD_BUILDINGS_DONE'