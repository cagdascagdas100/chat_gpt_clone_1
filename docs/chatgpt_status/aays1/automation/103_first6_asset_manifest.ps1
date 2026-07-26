$Repo = $env:AAYS_REPO_ROOT
if (!$Repo) { $Repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$AiRoot = $env:AAYS_AI_READY_ROOT
if (!$AiRoot) { $AiRoot = 'F:\ai-ready-to-sell' }
$Base = Join-Path $Repo 'docs\chatgpt_status\aays1'
$Tasks = Join-Path $Base 'runner_tasks'
$Reports = Join-Path $Base 'reports'
$Status = Join-Path $Base 'status'
New-Item -ItemType Directory -Force $Tasks,$Reports,$Status | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$items = @(
  @{row=1; parcel='24008351'; url='https://media.onthemarket.com/properties/10225397/1608088842/image-0-1024x1024.jpg'},
  @{row=2; parcel='25897788'; url='https://media.onthemarket.com/properties/10693127/1598164700/image-0-1024x1024.jpg'},
  @{row=3; parcel='61306962'; url='https://media.onthemarket.com/properties/10905789/1606657534/image-0-1024x1024.jpg'},
  @{row=4; parcel='58687404'; url='https://media.onthemarket.com/properties/10935976/1611784280/image-0-1024x1024.jpg'},
  @{row=5; parcel='40686255'; url='https://media.onthemarket.com/properties/11110712/1601528497/image-0-1024x1024.jpg'},
  @{row=6; parcel='14799612'; url='https://media.onthemarket.com/properties/11567771/1606701648/image-0-1024x1024.jpg'}
)
$out = [ordered]@{ page_key='aays1'; task_id='103_first6_asset_manifest'; final_ready=$false; rows=$items }
$json = $out | ConvertTo-Json -Depth 6
$jsonPath = Join-Path $Tasks "first6_asset_manifest_$stamp.json"
$json | Set-Content -Encoding UTF8 $jsonPath
@"
# First6 AI Asset Manifest

rows: 1-6
photo_urls: 6
final_ready: false
next: download photos and render polygons locally
"@ | Set-Content -Encoding UTF8 (Join-Path $Reports "103_first6_asset_manifest_$stamp.md")
@"
PAGE_KEY=aays1
TASK_ID=103_first6_asset_manifest
STATUS=manifest_written
ROWS=6
FINAL_READY=false
"@ | Set-Content -Encoding UTF8 (Join-Path $Status "103_first6_asset_manifest_status_$stamp.txt")
Write-Host "first6 manifest written" $jsonPath
