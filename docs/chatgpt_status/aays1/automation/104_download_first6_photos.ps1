$Repo = $env:AAYS_REPO_ROOT
if (!$Repo) { $Repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$PhotoRoot = Join-Path $Repo 'england_map_web\data\geometry_review_3of4\first6_assets'
$Base = Join-Path $Repo 'docs\chatgpt_status\aays1'
$Tasks = Join-Path $Base 'runner_tasks'
$Reports = Join-Path $Base 'reports'
$Status = Join-Path $Base 'status'
New-Item -ItemType Directory -Force $PhotoRoot,$Tasks,$Reports,$Status | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$manifest = Get-ChildItem $Tasks -Filter 'first6_asset_manifest_*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$data = Get-Content $manifest.FullName -Raw | ConvertFrom-Json
$items = @()
foreach ($r in $data.rows) {
  $target = Join-Path $PhotoRoot ("row_{0}_candidate.jpg" -f $r.row)
  $st = 'pending'
  try {
    Invoke-WebRequest -Uri $r.url -OutFile $target -UseBasicParsing -TimeoutSec 45
    if (Test-Path $target) { $st = 'downloaded' } else { $st = 'missing_after_download' }
  } catch { $st = 'download_error' }
  $items += [ordered]@{ row=$r.row; parcel=$r.parcel; target=$target; status=$st }
}
$downloaded = @($items | Where-Object { $_.status -eq 'downloaded' }).Count
$out = [ordered]@{ page_key='aays1'; task_id='104_download_first6_photos'; final_ready=$false; downloaded=$downloaded; rows=$items; web_asset_folder=$PhotoRoot }
$json = $out | ConvertTo-Json -Depth 6
$json | Set-Content -Encoding UTF8 (Join-Path $Tasks "first6_photo_download_$stamp.json")
@"
# First6 Photo Download

downloaded: $downloaded
final_ready: false
"@ | Set-Content -Encoding UTF8 (Join-Path $Reports "104_first6_photo_download_$stamp.md")
@"
PAGE_KEY=aays1
TASK_ID=104_download_first6_photos
STATUS=done
DOWNLOADED=$downloaded
FINAL_READY=false
"@ | Set-Content -Encoding UTF8 (Join-Path $Status "104_first6_photo_download_status_$stamp.txt")
Write-Host "first6 photo download complete" $downloaded
