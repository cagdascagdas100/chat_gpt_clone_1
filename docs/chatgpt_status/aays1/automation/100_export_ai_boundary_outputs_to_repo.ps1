$ErrorActionPreference = 'Continue'
$Repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($Repo)) { $Repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$AiRoot = $env:AAYS_AI_READY_ROOT
if ([string]::IsNullOrWhiteSpace($AiRoot)) { $AiRoot = 'F:\ai-ready-to-sell' }
$Out = Join-Path $Repo 'docs\chatgpt_status\aays1\runner_outputs\ai_boundary_review'
$Status = Join-Path $Repo 'docs\chatgpt_status\aays1\status'
New-Item -ItemType Directory -Force $Out | Out-Null
New-Item -ItemType Directory -Force $Status | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$summaryPath = Join-Path $Out "ai_boundary_export_summary_$stamp.json"
$latestPath = Join-Path $Out 'ai_boundary_export_latest.json'
function CountFiles($p) { if (Test-Path $p) { @(Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue).Count } else { 0 } }
function ListRecent($p) { if (Test-Path $p) { @(Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 20 | ForEach-Object { $_.FullName }) } else { @() } }
$photoDir = Join-Path $AiRoot 'photos'
$polyDir = Join-Path $AiRoot 'polygon_renders'
$visionDir = Join-Path $AiRoot 'vision_outputs'
$runnerDir = Join-Path $AiRoot 'runner_outputs'
$manifestDir = Join-Path $AiRoot 'manifests'
$obj = [ordered]@{
  page_key='aays1'
  task_id='100_export_ai_boundary_outputs_to_repo'
  status='snapshot_written'
  final_ready=$false
  ai_root=$AiRoot
  repo_output=$Out
  counts=[ordered]@{
    photos=CountFiles $photoDir
    polygon_renders=CountFiles $polyDir
    vision_outputs=CountFiles $visionDir
    runner_outputs=CountFiles $runnerDir
    manifests=CountFiles $manifestDir
  }
  recent=[ordered]@{
    photos=ListRecent $photoDir
    polygon_renders=ListRecent $polyDir
    vision_outputs=ListRecent $visionDir
    runner_outputs=ListRecent $runnerDir
    manifests=ListRecent $manifestDir
  }
  blockers=@()
}
if ($obj.counts.photos -eq 0) { $obj.blockers += 'missing_downloaded_photos' }
if ($obj.counts.polygon_renders -eq 0) { $obj.blockers += 'missing_polygon_renders' }
if ($obj.counts.vision_outputs -eq 0) { $obj.blockers += 'missing_vision_outputs' }
$json = $obj | ConvertTo-Json -Depth 8
$json | Set-Content -Encoding UTF8 $summaryPath
$json | Set-Content -Encoding UTF8 $latestPath
$statusPath = Join-Path $Status "100_ai_boundary_export_status_$stamp.txt"
@"
PAGE_KEY=aays1
TASK_ID=100_export_ai_boundary_outputs_to_repo
STATUS=snapshot_written
FINAL_READY=false
REPO_OUTPUT=$Out
SUMMARY=$summaryPath
PHOTOS=$($obj.counts.photos)
POLYGON_RENDERS=$($obj.counts.polygon_renders)
VISION_OUTPUTS=$($obj.counts.vision_outputs)
BLOCKERS=$($obj.blockers -join ',')
"@ | Set-Content -Encoding UTF8 $statusPath
Write-Host "AI boundary export written:" $summaryPath
Write-Host "AI boundary latest:" $latestPath
Write-Host "Status:" $statusPath
