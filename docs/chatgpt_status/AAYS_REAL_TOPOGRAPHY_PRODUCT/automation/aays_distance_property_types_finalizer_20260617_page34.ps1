param(
  [string]$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT",
  [string]$PreferredWorktreeRoot = "F:\chatgpt\AAYS_WORK\distance_property_types_20260617_clean",
  [string]$FallbackWorktreeRoot = "D:\chatgpt\AAYS_WORK\distance_property_types_20260617_clean",
  [int]$ApiPort = 8010,
  [int]$DbPort = 55460
)

$ErrorActionPreference = "Continue"

function Get-RepoRoot {
  try {
    $root = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $root) { return $root.Trim() }
  } catch {}
  return (Get-Location).Path
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-Utf8([string]$Path, [string]$Text) {
  $dir = Split-Path -Parent $Path
  Ensure-Dir $dir
  $Text | Out-File -FilePath $Path -Encoding utf8 -Force
}

function Append-Utf8([string]$Path, [string]$Text) {
  $dir = Split-Path -Parent $Path
  Ensure-Dir $dir
  $Text | Out-File -FilePath $Path -Encoding utf8 -Append
}

function Add-Blocker([System.Collections.Generic.List[string]]$List, [string]$Item) {
  if (-not [string]::IsNullOrWhiteSpace($Item) -and -not $List.Contains($Item)) { [void]$List.Add($Item) }
}

function Run-Cmd([string]$Label, [scriptblock]$Block) {
  $result = [ordered]@{ label=$Label; ok=$false; output=""; error="" }
  try {
    $out = & $Block 2>&1 | Out-String
    $result.output = $out.Trim()
    $result.ok = $true
  } catch {
    $result.error = $_.Exception.Message
  }
  return $result
}

function Test-TextHasAny([string]$Path, [string[]]$Patterns) {
  if (-not (Test-Path -LiteralPath $Path)) { return $false }
  $txt = Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue
  foreach ($p in $Patterns) {
    if ($txt -match [regex]::Escape($p)) { return $true }
  }
  return $false
}

$repoRoot = Get-RepoRoot
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$pageRoot = Join-Path $repoRoot "docs\chatgpt_status\$PageKey"
$reportsDir = Join-Path $pageRoot "reports"
$statusDir = Join-Path $pageRoot "status"
$heartbeatDir = Join-Path $pageRoot "heartbeat"
$currentTaskDir = Join-Path $pageRoot "current-task"
$controlDir = Join-Path $pageRoot "control"
$queueDir = Join-Path $pageRoot "queue"
$runnerTasksDir = Join-Path $pageRoot "runner_tasks"
$automationDir = Join-Path $pageRoot "automation"
$runnerOutputsDir = Join-Path $pageRoot "runner_outputs"
$sharedDir = Join-Path $repoRoot "docs\chatgpt_status\_shared"

foreach ($d in @($reportsDir,$statusDir,$heartbeatDir,$currentTaskDir,$controlDir,$queueDir,$runnerTasksDir,$automationDir,$runnerOutputsDir)) { Ensure-Dir $d }

$applyReport = Join-Path $reportsDir "distance_property_types_df_worktree_apply_report_$timestamp.md"
$smokeReport = Join-Path $reportsDir "distance_property_types_df_worktree_smoke_report_$timestamp.md"
$blockerReport = Join-Path $reportsDir "distance_property_types_df_worktree_blockers_$timestamp.md"
$statusReport = Join-Path $statusDir "distance_property_types_status_$timestamp.md"
$heartbeatReport = Join-Path $heartbeatDir "distance_property_types_heartbeat_$timestamp.md"
$runnerOut = Join-Path $runnerOutputsDir "distance_property_types_runner_output_$timestamp.txt"

$blockers = New-Object 'System.Collections.Generic.List[string]'
$done = New-Object 'System.Collections.Generic.List[string]'
$observations = New-Object 'System.Collections.Generic.List[string]'

$branch = "unknown"
try { $branch = (git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim() } catch {}
if (-not $branch) { $branch = "unknown" }

Append-Utf8 $runnerOut "START timestamp=$timestamp`nrepo_root=$repoRoot`nbranch=$branch`npage_key=$PageKey`n"

# 1) Runner/page contract inspection. This is intentionally read-only except reports produced under this page key.
$contractLines = New-Object 'System.Collections.Generic.List[string]'
foreach ($folder in @($reportsDir,$statusDir,$heartbeatDir,$currentTaskDir,$controlDir,$queueDir,$runnerTasksDir,$automationDir,$runnerOutputsDir,$sharedDir)) {
  if (Test-Path -LiteralPath $folder) {
    $files = Get-ChildItem -LiteralPath $folder -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 80
    [void]$contractLines.Add("folder=$folder file_count=$($files.Count)")
    foreach ($f in $files) { [void]$contractLines.Add(" - $($f.FullName.Replace($repoRoot,'').TrimStart('\'))") }
  } else {
    [void]$contractLines.Add("folder=$folder missing=true")
  }
}
[void]$done.Add("page_key_folders_scanned_and_contract_snapshot_written")

# 2) Select worktree root. Prefer F, then D, then repo root only if it looks like the product repo.
$candidateRoots = @($PreferredWorktreeRoot, $FallbackWorktreeRoot, $repoRoot) | Where-Object { $_ -and $_.Trim() -ne "" } | Select-Object -Unique
$worktreeRoot = $null
foreach ($c in $candidateRoots) {
  if ((Test-Path -LiteralPath (Join-Path $c "terrayield_land_intelligence")) -or (Test-Path -LiteralPath (Join-Path $c "england_map_web"))) {
    $worktreeRoot = $c
    break
  }
}
if (-not $worktreeRoot) {
  $worktreeRoot = $PreferredWorktreeRoot
  Ensure-Dir $worktreeRoot
  Add-Blocker $blockers "target_worktree_product_structure_missing"
  [void]$observations.Add("Preferred worktree root was created if absent, but product folders were not found: $worktreeRoot")
}

# 3) Copy minimum C reference patch to D/F worktree when both sides are available.
$cRefRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$filePairs = @(
  @{name="app.js"; src=(Join-Path $cRefRoot "england_map_web\app.js"); dst=(Join-Path $worktreeRoot "england_map_web\app.js"); check="node"},
  @{name="map_layers.py"; src=(Join-Path $cRefRoot "terrayield_land_intelligence\app\api\routes\map_layers.py"); dst=(Join-Path $worktreeRoot "terrayield_land_intelligence\app\api\routes\map_layers.py"); check="python"},
  @{name="run_uvicorn_8010.ps1"; src=(Join-Path $cRefRoot "terrayield_land_intelligence\run_uvicorn_8010.ps1"); dst=(Join-Path $worktreeRoot "terrayield_land_intelligence\run_uvicorn_8010.ps1"); check="none"}
)

$fileApplyLines = New-Object 'System.Collections.Generic.List[string]'
foreach ($pair in $filePairs) {
  $src = $pair.src; $dst = $pair.dst; $name = $pair.name
  if (-not (Test-Path -LiteralPath $src)) {
    [void]$fileApplyLines.Add("$name source_missing=$src")
    Add-Blocker $blockers "source_reference_missing:$name"
    continue
  }
  $dstDir = Split-Path -Parent $dst
  Ensure-Dir $dstDir
  $srcHash = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
  $dstHash = $null
  if (Test-Path -LiteralPath $dst) { $dstHash = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash }
  if ($srcHash -ne $dstHash) {
    Copy-Item -LiteralPath $src -Destination $dst -Force
    [void]$fileApplyLines.Add("$name copied_from_C_reference src_sha256=$srcHash old_dst_sha256=$dstHash")
    [void]$done.Add("patched_$name")
  } else {
    [void]$fileApplyLines.Add("$name already_matching sha256=$srcHash")
    [void]$done.Add("verified_$name")
  }
}

# 4) Static syntax and integration-symbol checks.
$appPath = Join-Path $worktreeRoot "england_map_web\app.js"
$mapPath = Join-Path $worktreeRoot "terrayield_land_intelligence\app\api\routes\map_layers.py"
$apiRoot = Join-Path $worktreeRoot "terrayield_land_intelligence"
$staticLines = New-Object 'System.Collections.Generic.List[string]'

if (Test-Path -LiteralPath $appPath) {
  $bindingOk = Test-TextHasAny $appPath @("distance-property-types", "parcel_label", "parcel-use-parcels")
  [void]$staticLines.Add("app_binding_symbols_found=$bindingOk")
  if (-not $bindingOk) { Add-Blocker $blockers "frontend_binding_symbols_missing" }
  $node = Get-Command node -ErrorAction SilentlyContinue
  if ($node) {
    $nodeCheck = Run-Cmd "node_check_app_js" { node --check $appPath }
    [void]$staticLines.Add("node_check_ok=$($nodeCheck.ok) output=$($nodeCheck.output) error=$($nodeCheck.error)")
    if ($nodeCheck.ok) { [void]$done.Add("node_check_app_js_passed") } else { Add-Blocker $blockers "node_check_failed" }
  } else {
    [void]$staticLines.Add("node_check_skipped=node_not_found")
    Add-Blocker $blockers "node_not_found_static_check_skipped"
  }
} else {
  Add-Blocker $blockers "target_app_js_missing"
}

if (Test-Path -LiteralPath $mapPath) {
  $backendOk = Test-TextHasAny $mapPath @("distance-property-types", "distance_property", "parcel_context_metric_details")
  [void]$staticLines.Add("backend_route_symbols_found=$backendOk")
  if (-not $backendOk) { Add-Blocker $blockers "backend_route_symbols_missing" }
  $py = Get-Command python -ErrorAction SilentlyContinue
  if ($py) {
    $pyCheck = Run-Cmd "py_compile_map_layers" { python -m py_compile $mapPath }
    [void]$staticLines.Add("py_compile_ok=$($pyCheck.ok) output=$($pyCheck.output) error=$($pyCheck.error)")
    if ($pyCheck.ok) { [void]$done.Add("py_compile_map_layers_passed") } else { Add-Blocker $blockers "py_compile_map_layers_failed" }
  } else {
    [void]$staticLines.Add("py_compile_skipped=python_not_found")
    Add-Blocker $blockers "python_not_found_static_check_skipped"
  }
} else {
  Add-Blocker $blockers "target_map_layers_py_missing"
}

# 5) Runtime DB/API smoke. Do not kill unrelated processes. Use existing launcher if present.
$healthHttp = "not_run"
$healthBody = ""
$healthDatabase = "unknown"
$distanceHttp = "not_run"
$distanceBody = ""
$featureCount = 0
$popupContractOk = $false
$rightPanelContractOk = $false
$dbListenerFound = $false

if (Test-Path -LiteralPath $apiRoot) {
  Push-Location $apiRoot
  try {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($docker -and (Test-Path -LiteralPath (Join-Path $apiRoot "docker-compose.yml") -or Test-Path -LiteralPath (Join-Path $apiRoot "docker-compose.yaml"))) {
      $dockerStart = Run-Cmd "docker_compose_up_db" { docker compose up -d db }
      Append-Utf8 $runnerOut "docker_compose_up_db_ok=$($dockerStart.ok)`n$($dockerStart.output)`n$($dockerStart.error)`n"
      if ($dockerStart.ok) { [void]$done.Add("docker_compose_db_invoked") } else { Add-Blocker $blockers "docker_compose_db_failed" }
      Start-Sleep -Seconds 8
    } else {
      Add-Blocker $blockers "docker_or_compose_file_missing"
    }

    $dbListener = netstat -ano | Select-String (":" + $DbPort + "\s+.*LISTENING") | Select-Object -First 1
    if ($dbListener) { $dbListenerFound = $true; [void]$done.Add("db_listener_found_$DbPort") } else { Add-Blocker $blockers "db_listener_not_found_$DbPort" }

    $launcherCandidates = @("start_uvicorn_8010_bg.ps1", "run_uvicorn_8010.ps1")
    $launcher = $null
    foreach ($lc in $launcherCandidates) { if (Test-Path -LiteralPath (Join-Path $apiRoot $lc)) { $launcher = Join-Path $apiRoot $lc; break } }
    if ($launcher) {
      $apiStart = Run-Cmd "start_api_launcher" { powershell -NoProfile -ExecutionPolicy Bypass -File $launcher }
      Append-Utf8 $runnerOut "api_launcher=$launcher ok=$($apiStart.ok)`n$($apiStart.output)`n$($apiStart.error)`n"
      if ($apiStart.ok) { [void]$done.Add("api_launcher_invoked") } else { Add-Blocker $blockers "api_launcher_failed" }
      Start-Sleep -Seconds 8
    } else {
      Add-Blocker $blockers "api_launcher_missing"
    }

    try {
      $health = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/health" -TimeoutSec 15
      $healthHttp = [string]$health.StatusCode
      $healthBody = $health.Content
      if ($health.StatusCode -eq 200) { [void]$done.Add("health_http_200") }
      if ($healthBody -match '"database"\s*:\s*"?ok"?' -or $healthBody -match 'database\s*[=:]\s*ok') { $healthDatabase = "ok"; [void]$done.Add("health_database_ok") }
      elseif ($healthBody -match 'database') { $healthDatabase = "not_ok_or_degraded"; Add-Blocker $blockers "health_database_not_ok" }
    } catch {
      $healthHttp = "failed"
      $healthBody = $_.Exception.Message
      Add-Blocker $blockers "health_probe_failed"
    }

    try {
      $distance = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/map/distance-property-types?bbox=-0.55,51.28,0.35,51.75&limit=10" -TimeoutSec 25
      $distanceHttp = [string]$distance.StatusCode
      $distanceBody = $distance.Content
      if ($distance.StatusCode -eq 200) { [void]$done.Add("distance_endpoint_http_200") }
      try {
        $json = $distanceBody | ConvertFrom-Json
        if ($json.features) { $featureCount = @($json.features).Count }
        if ($featureCount -gt 0) { [void]$done.Add("distance_features_non_empty") } else { Add-Blocker $blockers "distance_features_empty" }
        $props = $null
        if ($featureCount -gt 0) { $props = $json.features[0].properties }
        if ($props) {
          $propNames = @($props.PSObject.Properties.Name)
          $requiredAny = @("parcel_id", "structure_type", "class", "level", "score", "source", "source_date", "confidence", "matching_method", "calculation_explanation")
          $present = @($requiredAny | Where-Object { $propNames -contains $_ })
          if ($present.Count -ge 6) { $popupContractOk = $true; $rightPanelContractOk = $true; [void]$done.Add("endpoint_contract_fields_present") }
          else { Add-Blocker $blockers "endpoint_contract_fields_insufficient" }
        }
      } catch { Add-Blocker $blockers "distance_json_parse_failed" }
    } catch {
      $distanceHttp = "failed"
      $distanceBody = $_.Exception.Message
      Add-Blocker $blockers "distance_endpoint_probe_failed"
    }
  } finally {
    Pop-Location
  }
} else {
  Add-Blocker $blockers "api_root_missing"
}

# 6) Optional UI smoke with Playwright if available. No separate runner is started; this is an in-script child process only.
$uiSmoke = "not_run"
$uiEvidence = ""
$playwrightSmokePath = Join-Path $runnerOutputsDir "distance_property_types_playwright_$timestamp.js"
$uiScreenshotPath = Join-Path $runnerOutputsDir "distance_property_types_ui_$timestamp.png"
$playwrightScript = @"
const fs = require('fs');
(async () => {
  let chromium;
  try { chromium = require('playwright').chromium; } catch (e) { console.log('playwright_missing'); process.exit(2); }
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
  let distanceResponse = null;
  page.on('response', async (resp) => {
    if (resp.url().includes('/map/distance-property-types')) {
      try { distanceResponse = { status: resp.status(), body: await resp.text() }; } catch(e) { distanceResponse = { status: resp.status(), body: String(e) }; }
    }
  });
  await page.goto('http://127.0.0.1:$ApiPort/england_map_web/', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  const selectors = [
    'img[src*="parcel_label"]',
    'button:has-text("Distance")',
    '[title*="Distance"]',
    '[aria-label*="Distance"]',
    'text=Distance to Nearby Property Types'
  ];
  let clicked = false;
  for (const sel of selectors) {
    try { const loc = page.locator(sel).first(); if (await loc.count()) { await loc.click({timeout: 5000}); clicked = true; break; } } catch(e) {}
  }
  await page.waitForTimeout(8000);
  await page.screenshot({ path: '$($uiScreenshotPath.Replace('\\','/'))', fullPage: true });
  console.log(JSON.stringify({ clicked, distanceResponse, screenshot: '$($uiScreenshotPath.Replace('\\','/'))' }));
  await browser.close();
  process.exit(clicked && distanceResponse && distanceResponse.status === 200 ? 0 : 3);
})();
"@
Write-Utf8 $playwrightSmokePath $playwrightScript
if (Get-Command node -ErrorAction SilentlyContinue) {
  $pw = Run-Cmd "playwright_ui_smoke" { node $playwrightSmokePath }
  $uiEvidence = ($pw.output + " " + $pw.error).Trim()
  if ($pw.ok -and $uiEvidence -notmatch "playwright_missing") {
    $uiSmoke = "attempted"
    if ($uiEvidence -match '"clicked"\s*:\s*true' -and $uiEvidence -match '"status"\s*:\s*200') {
      $uiSmoke = "passed_network_layer_click"
      [void]$done.Add("ui_smoke_layer_click_network_200")
    } else {
      Add-Blocker $blockers "ui_smoke_no_click_or_no_distance_network_response"
    }
  } else {
    $uiSmoke = "skipped_or_failed_playwright_missing"
    Add-Blocker $blockers "playwright_ui_smoke_not_available_or_failed"
  }
} else {
  $uiSmoke = "skipped_node_missing"
  Add-Blocker $blockers "node_missing_ui_smoke_skipped"
}

# 7) Score and final gate. No FINAL_READY unless live endpoint + data + UI smoke + contract pass.
$completion = 25
if ($done.Contains("page_key_folders_scanned_and_contract_snapshot_written")) { $completion += 10 }
if (($done | Where-Object { $_ -like "patched_*" -or $_ -like "verified_*" }).Count -ge 3) { $completion += 15 }
if ($done.Contains("node_check_app_js_passed") -and $done.Contains("py_compile_map_layers_passed")) { $completion += 10 }
if ($dbListenerFound -or $healthDatabase -eq "ok") { $completion += 10 }
if ($healthHttp -eq "200") { $completion += 5 }
if ($distanceHttp -eq "200") { $completion += 5 }
if ($featureCount -gt 0) { $completion += 10 }
if ($popupContractOk -and $rightPanelContractOk) { $completion += 5 }
if ($uiSmoke -eq "passed_network_layer_click") { $completion += 5 }
if ($completion -gt 99 -and -not ($healthDatabase -eq "ok" -and $featureCount -gt 0 -and $popupContractOk -and $rightPanelContractOk -and $uiSmoke -eq "passed_network_layer_click")) { $completion = 95 }
if ($completion -gt 100) { $completion = 100 }

$status = "BLOCKED"
$finalReady = "false"
if ($healthDatabase -eq "ok" -and $distanceHttp -eq "200" -and $featureCount -gt 0 -and $popupContractOk -and $rightPanelContractOk -and $uiSmoke -eq "passed_network_layer_click") {
  $status = "FINAL_READY"
  $finalReady = "true"
  $completion = 100
} elseif ($distanceHttp -eq "200" -and $featureCount -gt 0) {
  $status = "RUNTIME_PARTIAL_UI_EVIDENCE_MISSING"
} elseif ($healthHttp -eq "200") {
  $status = "RUNTIME_REACHED_DATA_OR_DB_BLOCKED"
}

$blockerListText = if ($blockers.Count -gt 0) { ($blockers | ForEach-Object { "- $_" }) -join "`n" } else { "- none" }
$doneText = if ($done.Count -gt 0) { ($done | Select-Object -Unique | ForEach-Object { "- $_" }) -join "`n" } else { "- none" }
$obsText = if ($observations.Count -gt 0) { ($observations | ForEach-Object { "- $_" }) -join "`n" } else { "- none" }
$contractText = ($contractLines -join "`n")
$fileApplyText = ($fileApplyLines -join "`n")
$staticText = ($staticLines -join "`n")

$commonHeader = @"
status: $status
FINAL_READY: $finalReady
completion_percent: $completion
page_key: $PageKey
worktree_root: $worktreeRoot
repo_root: $repoRoot
branch: $branch
timestamp: $timestamp
endpoint_health: $healthHttp
endpoint_distance_property_types: $distanceHttp
db_port_expected: $DbPort
db_listener_found: $dbListenerFound
parcel_count_visible: $featureCount
popup_contract_ok: $popupContractOk
right_panel_contract_ok: $rightPanelContractOk
ui_smoke: $uiSmoke
next_action: fix listed blockers, rerun same automation script through shared runner
"@

$applyBody = @"
# Distance Property Types D/F Worktree Apply Report

$commonHeader

## Runner/Page Contract Snapshot
```text
$contractText
```

## File Apply Result
```text
$fileApplyText
```

## Static Checks
```text
$staticText
```

## Done
$doneText

## Observations
$obsText

## Blockers
$blockerListText
"@

$smokeBody = @"
# Distance Property Types D/F Worktree Smoke Report

$commonHeader

## Health Body
```text
$healthBody
```

## Distance Endpoint Body
```json
$distanceBody
```

## UI Smoke Evidence
```text
$uiEvidence
```

## Runner Output
- $runnerOut
- $playwrightSmokePath
- $uiScreenshotPath
"@

$blockerBody = @"
# Distance Property Types D/F Worktree Blockers Report

$commonHeader

## Blocker List
$blockerListText

## Root Cause Routing
- If `target_worktree_product_structure_missing`: runner machine has not prepared the D/F clean product worktree.
- If `db_listener_not_found_$DbPort` or `health_database_not_ok`: start or repair local PostGIS/data chain before final.
- If `distance_features_empty`: inspect `parcels_inspire`, `parcel_context_summary`, `parcel_context_metric_details`, bbox coverage, and `parcel_use6_lookup.json`.
- If `playwright_ui_smoke_not_available_or_failed`: install/use existing UI smoke dependency or provide browser automation evidence in GitHub reports.

## Next Action
Run this same script again through the existing shared runner after blockers are addressed. Do not open a second runner.
"@

$statusBody = @"
page_key: $PageKey
branch: $branch
task_title: Distance to Nearby Property Types finalization via single shared runner
timestamp: $timestamp
status: $status
FINAL_READY: $finalReady
completion_percent: $completion

## Evidence
- report: docs/chatgpt_status/$PageKey/reports/$(Split-Path -Leaf $applyReport)
- smoke: docs/chatgpt_status/$PageKey/reports/$(Split-Path -Leaf $smokeReport)
- blockers: docs/chatgpt_status/$PageKey/reports/$(Split-Path -Leaf $blockerReport)
- runner_output: docs/chatgpt_status/$PageKey/runner_outputs/$(Split-Path -Leaf $runnerOut)

## Done
$doneText

## Blocked
$blockerListText

## Next
- Existing shared runner should continue with the same page-key task until FINAL_READY is proven.
"@

$heartbeatBody = "timestamp: $timestamp`npage_key: $PageKey`nstatus: $status`ncompletion_percent: $completion`nrunner_seen: true`n"

Write-Utf8 $applyReport $applyBody
Write-Utf8 $smokeReport $smokeBody
Write-Utf8 $blockerReport $blockerBody
Write-Utf8 $statusReport $statusBody
Write-Utf8 $heartbeatReport $heartbeatBody
Append-Utf8 $runnerOut "END status=$status completion=$completion final_ready=$finalReady`n"

# 8) Commit GitHub evidence if this is a git worktree. This keeps all evidence readable from GitHub reports/status.
try {
  git -C $repoRoot add "docs/chatgpt_status/$PageKey/reports" "docs/chatgpt_status/$PageKey/status" "docs/chatgpt_status/$PageKey/heartbeat" "docs/chatgpt_status/$PageKey/runner_outputs" 2>&1 | Out-Null
  $diffCheck = git -C $repoRoot diff --cached --name-only 2>$null
  if ($diffCheck) {
    git -C $repoRoot commit -m "AAYS page34 distance property types runner evidence $timestamp" 2>&1 | Out-Null
    git -C $repoRoot push 2>&1 | Out-Null
  }
} catch {
  Append-Utf8 $runnerOut "git_commit_push_failed=$($_.Exception.Message)`n"
}

Write-Output $statusBody
if ($status -eq "FINAL_READY") { exit 0 } else { exit 2 }
