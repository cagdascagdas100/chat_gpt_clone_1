$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path ".").Path
$PageKey = "aays1"
$TaskId = "future-growth-anchor-probe-20260614-0001"
$Root = Join-Path $Repo "docs/chatgpt_status/$PageKey"
$Reports = Join-Path $Root "reports"
$Status = Join-Path $Root "status"
$Heartbeat = Join-Path $Root "heartbeat"
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat | Out-Null

$appJs = Join-Path $Repo "england_map_web/app.js"
$content = ""
if (Test-Path $appJs) { $content = Get-Content $appJs -Raw -Encoding UTF8 }

$result = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  product = "Future Growth"
  status = "anchor_probe_complete"
  app_js_exists = (Test-Path $appJs)
  has_future_growth_toggle = ($content -match "futureGrowthToggle")
  has_future_growth_layer_function = ($content -match "setFutureGrowthLayerVisibility")
  has_future_growth_text = ($content -match "Future Growth|future growth|future_growth")
  final_ready = $false
  completion_percent = 62
  next_expected = "apply validated Future Growth patch through shared runner"
  generated_at = (Get-Date).ToString("s")
}

$result | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $Reports "future_growth_anchor_probe_20260614_0001.result.json") -Encoding UTF8
@"
status=anchor_probe_complete
completion=62
final_ready=false
task_id=$TaskId
expected_report=docs/chatgpt_status/$PageKey/reports/future_growth_anchor_probe_20260614_0001.result.json
generated_at=$($result.generated_at)
"@ | Set-Content -Path (Join-Path $Status "future_growth_anchor_probe_20260614_0001.status.txt") -Encoding UTF8
@"
status=finished
task_id=$TaskId
generated_at=$($result.generated_at)
"@ | Set-Content -Path (Join-Path $Heartbeat "latest.txt") -Encoding UTF8
