$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$targetBranch = 'codex/aays-single-runner-v5-20260706'
$taskId = 'aays1-ready-to-sell-site-row-visibility-verify-20260711'
$dataRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$htmlRelative = 'england_map_web/geometry_review_3of4_columns_1264.html'
$statusRelative = 'docs/chatgpt_status/aays1/status/154_aays1_ready_to_sell_site_row_visibility_verify_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/154_aays1_ready_to_sell_site_row_visibility_verify_report.md'
$dataPath = Join-Path $repoRoot $dataRelative
$htmlPath = Join-Path $repoRoot $htmlRelative
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath) | Out-Null

$blockers = [System.Collections.Generic.List[string]]::new()
$branch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
if ($branch -ne $targetBranch) { $blockers.Add("wrong_branch:$branch") }
if (-not (Test-Path -LiteralPath $dataPath)) { $blockers.Add('site_data_json_missing') }
if (-not (Test-Path -LiteralPath $htmlPath)) { $blockers.Add('ready_to_sell_html_missing') }
$data = $null
$html = $null
try { if (Test-Path -LiteralPath $dataPath) { $data = Get-Content -LiteralPath $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json } } catch { $blockers.Add('site_data_read_failed:' + $_.Exception.Message) }
try { if (Test-Path -LiteralPath $htmlPath) { $html = Get-Content -LiteralPath $htmlPath -Raw -Encoding UTF8 } } catch { $blockers.Add('html_read_failed:' + $_.Exception.Message) }

$healthOk = $false
$pageOk = $false
$jsonOk = $false
$healthStatus = $null
$pageStatus = $null
$jsonStatus = $null
try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8012/health' -UseBasicParsing -TimeoutSec 25; $healthStatus = [int]$r.StatusCode; $healthOk = $healthStatus -eq 200 } catch { $blockers.Add('health_probe_failed:' + $_.Exception.Message) }
try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html' -UseBasicParsing -TimeoutSec 35; $pageStatus = [int]$r.StatusCode; $pageOk = $pageStatus -eq 200 -and ([string]$r.Content -match 'newOnly') -and ([string]$r.Content -match 'NOT_PROCESSED') } catch { $blockers.Add('page_probe_failed:' + $_.Exception.Message) }
try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8012/england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json' -UseBasicParsing -TimeoutSec 35; $jsonStatus = [int]$r.StatusCode; $remoteData = ([string]$r.Content | ConvertFrom-Json); $jsonOk = $jsonStatus -eq 200 -and $remoteData.results } catch { $blockers.Add('json_probe_failed:' + $_.Exception.Message) }

$results = if ($data -and $data.results) { @($data.results) } else { @() }
$live = @($results | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
$newRows = @($results | Where-Object { $_.new_this_run -eq $true }).Count
$photoRows = @($results | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count
$polygonRows = @($results | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
$visionRows = @($results | Where-Object { $null -ne $_.visual_match_score }).Count
$rowsWithRequiredLinks = @($results | Where-Object {
  -not [string]::IsNullOrWhiteSpace([string]$_.listing_url) -and
  -not [string]::IsNullOrWhiteSpace([string]$_.status_json_path) -and
  -not [string]::IsNullOrWhiteSpace([string]$_.report_md_path)
}).Count
$htmlContractOk = $html -and $html.Contains('newOnly') -and $html.Contains('NOT_PROCESSED') -and $html.Contains('YENİ BU ÇALIŞMADA') -and $html.Contains('status_json_path') -and $html.Contains('report_md_path')
if (-not $htmlContractOk) { $blockers.Add('row_visibility_contract_incomplete') }

$status = [ordered]@{
  task_id = $taskId
  page_key = 'aays1'
  status = if ($blockers.Count -eq 0 -and $healthOk -and $pageOk -and $jsonOk -and $htmlContractOk) { 'SITE_ROW_VISIBILITY_VERIFIED' } else { 'SITE_ROW_VISIBILITY_PARTIAL_OR_BLOCKED' }
  health_http_status = $healthStatus
  page_http_status = $pageStatus
  json_http_status = $jsonStatus
  html_contract_ok = [bool]$htmlContractOk
  result_rows_total = $results.Count
  live_source_verified_rows = $live
  new_this_run_rows = $newRows
  rows_with_downloaded_photos = $photoRows
  rows_with_polygon_render = $polygonRows
  rows_with_real_vision_score = $visionRows
  rows_with_listing_status_report_links = $rowsWithRequiredLinks
  blockers = @($blockers)
  generated_at = [DateTimeOffset]::UtcNow.ToString('o')
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$status | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$lines = @(
  '# ReadyToSell Site Row Visibility Verification',
  '',
  "- Status: $($status.status)",
  "- Rows total in site data: $($status.result_rows_total)",
  "- Live source verified: $live",
  "- New this run: $newRows",
  "- Photo rows: $photoRows",
  "- Polygon rows: $polygonRows",
  "- Real vision rows: $visionRows",
  "- Rows with listing/status/report links: $rowsWithRequiredLinks",
  "- HTTP health/page/json: $healthStatus / $pageStatus / $jsonStatus",
  "- Blockers: $($blockers -join '; ')",
  '',
  '`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
)
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))
try {
  & git -C $repoRoot add -- $statusRelative $reportRelative | Out-Null
  $staged = (& git -C $repoRoot diff --cached --name-only)
  if ($staged) { & git -C $repoRoot commit -m 'Verify ReadyToSell row visibility on site' | Out-Null }
  & git -C $repoRoot push origin $targetBranch | Out-Null
} catch {}
