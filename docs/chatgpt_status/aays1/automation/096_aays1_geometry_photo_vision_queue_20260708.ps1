$ErrorActionPreference = 'Stop'

$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path
}

$PageKey = 'aays1'
$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { 'aays1-geometry-photo-vision-queue-20260708' } else { $env:AAYS_TASK_ID }
$Now = (Get-Date).ToUniversalTime().ToString('o')
function JP([string]$p) { Join-Path $RepoRoot ($p -replace '/', '\') }

$StatusDir = JP 'docs/chatgpt_status/aays1/status'
$ReportDir = JP 'docs/chatgpt_status/aays1/reports'
$HeartbeatDir = JP 'docs/chatgpt_status/aays1/heartbeat'
$GeomDataDir = JP 'england_map_web/data/geometry_review_3of4'
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir,$HeartbeatDir,$GeomDataDir | Out-Null

$aiPath = Join-Path $GeomDataDir 'photo_ai_boundary_review_results.json'
if (-not (Test-Path -LiteralPath $aiPath)) { throw 'PHOTO_AI_BOUNDARY_REVIEW_RESULTS_MISSING' }
$ai = Get-Content -Raw -LiteralPath $aiPath | ConvertFrom-Json -ErrorAction Stop
$rows = @($ai.results | Where-Object { $_.row_id -is [int] -or ([string]$_.row_id -match '^\d+$') })
$pending = @($rows | Where-Object { [string]$_.photo_shape_type -eq 'pending_vision_download' -or $null -eq $_.visual_match_score })

$downloadDirRel = 'england_map_web/data/geometry_review_3of4/downloaded_photo_candidates'
$downloadDir = JP $downloadDirRel
New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
$downloaded = @()
$failed = @()
foreach ($r in @($pending | Select-Object -First 6)) {
  $urls = @($r.photo_urls)
  if ($urls.Count -eq 0 -or [string]::IsNullOrWhiteSpace([string]$urls[0])) { $failed += [ordered]@{row_id=$r.row_id; reason='missing_photo_url'}; continue }
  $url = [string]$urls[0]
  $safe = ('row_' + [string]$r.row_id + '.jpg')
  $out = Join-Path $downloadDir $safe
  try {
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $out -TimeoutSec 30
    $downloaded += [ordered]@{ row_id=$r.row_id; source_url=$url; local_path=(($out.Substring($RepoRoot.Length).TrimStart('\')) -replace '\\','/'); downloaded=$true }
    $r.photo_evidence_status = ([string]$r.photo_evidence_status + '_local_download_ready')
    $r.photo_shape_type = 'downloaded_pending_vision_compare'
    $r.ai_notes = 'Photo candidate downloaded locally by runner. Polygon render + actual vision comparison still required before any 3.5/4 upgrade.'
  } catch {
    $failed += [ordered]@{row_id=$r.row_id; source_url=$url; reason=$_.Exception.Message}
  }
}

$ai.status = 'photo_candidates_downloaded_pending_vision_compare'
$ai.rows_downloaded_for_vision = $downloaded.Count
$ai.rows_failed_download = $failed.Count
$ai.updated_at = $Now
$ai | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $aiPath

$status = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  status = 'geometry_photo_candidates_downloaded_pending_vision_compare'
  rows_total = [int]$ai.rows_total
  rows_with_candidate_photo_urls = [int]$ai.rows_with_candidate_photo_urls
  rows_downloaded_for_vision = $downloaded.Count
  rows_failed_download = $failed.Count
  downloaded = $downloaded
  failed = $failed
  blocker = 'actual_vision_compare_required_before_confidence_upgrade'
  completion_percent = 60
  remaining_percent = 40
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  updated_at = $Now
}
$status | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $StatusDir '096_aays1_geometry_photo_vision_queue_latest.json')

@"
# 096 aays1 geometry photo vision queue

status: geometry_photo_candidates_downloaded_pending_vision_compare
rows_downloaded_for_vision: $($downloaded.Count)
rows_failed_download: $($failed.Count)
completion_percent: 60
remaining_percent: 40
blocker: actual_vision_compare_required_before_confidence_upgrade
final_ready: false
fake_data: false
db_write: false
migration: false
production_deploy: false

Notes:
- This step downloads candidate listing photos for the 3/4 geometry review page.
- It does not fabricate visual match scores.
- Rows remain below 3.5/4 until actual image/polygon vision comparison is completed.
"@ | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ReportDir '096_aays1_geometry_photo_vision_queue_latest.md')

"TASK_ID=$TaskId`nPAGE_KEY=$PageKey`nSTATUS=geometry_photo_candidates_downloaded_pending_vision_compare`nDOWNLOADED=$($downloaded.Count)`nFINAL_READY=false`nHEARTBEAT_AT=$Now`n" | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $HeartbeatDir '096_aays1_geometry_photo_vision_queue_latest.txt')
Write-Output "AAYS1_096_GEOMETRY_PHOTO_VISION_QUEUE downloaded=$($downloaded.Count) failed=$($failed.Count) final_ready=false fake_data=false"
exit 0
