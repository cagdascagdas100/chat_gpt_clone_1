$ErrorActionPreference = "Stop"
$TaskId = "terrayield-059-cross-platform-50step-bootstrap"
$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$StartedAt = Get-Date
$Stamp = $StartedAt.ToString("yyyyMMdd_HHmmss")
$OutRoot = Join-Path $ProjectRoot ".aays_50step_plan\step001_preflight_$Stamp"
$ResultRoot = Join-Path $BridgeRoot "ai-results"
$ResultFile = Join-Path $ResultRoot ("Runner V4 result " + $TaskId + ".md")

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Add-Line {
    param([System.Collections.Generic.List[string]]$Lines, [string]$Text)
    $Lines.Add($Text) | Out-Null
}

function Safe-Run {
    param([string]$Name, [scriptblock]$Block)
    $item = [ordered]@{
        name = $Name
        ok = $false
        output = ""
        error = ""
    }
    try {
        $out = & $Block 2>&1 | Out-String
        $item.ok = $true
        $item.output = $out.Trim()
    } catch {
        $item.ok = $false
        $item.error = $_.Exception.Message
    }
    return $item
}

function Test-Http {
    param([string]$Url)
    $row = [ordered]@{
        url = $Url
        ok = $false
        status = $null
        elapsed_ms = $null
        error = ""
    }
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 6
        $sw.Stop()
        $row.ok = $true
        $row.status = [int]$resp.StatusCode
        $row.elapsed_ms = [int]$sw.ElapsedMilliseconds
    } catch {
        $row.error = $_.Exception.Message
    }
    return $row
}

Ensure-Dir $OutRoot
Ensure-Dir $ResultRoot

$report = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$checks = @()

Add-Line $report "# TerraYield 50-Step Cross-Platform Bootstrap"
Add-Line $report ""
Add-Line $report ("Task: " + $TaskId)
Add-Line $report ("Started: " + $StartedAt.ToString("s"))
Add-Line $report ("BridgeRoot: " + $BridgeRoot)
Add-Line $report ("ProjectRoot: " + $ProjectRoot)
Add-Line $report ""
Add-Line $report "## Safety"
Add-Line $report "- Step 001 is report-only and preflight-only."
Add-Line $report "- No database writes were executed."
Add-Line $report "- No Docker build/recreate was executed."
Add-Line $report "- No external scraping was executed."
Add-Line $report "- No source file patch was applied in this step."
Add-Line $report ""

$checks += Safe-Run "project_root_exists" { Test-Path -LiteralPath $ProjectRoot }
$checks += Safe-Run "bridge_root_exists" { Test-Path -LiteralPath $BridgeRoot }
$checks += Safe-Run "powershell_version" { $PSVersionTable | Format-List | Out-String }

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    Add-Line $warnings ("Project root not found: " + $ProjectRoot)
} else {
    $totalFiles = 0
    try {
        $totalFiles = (Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    } catch {
        Add-Line $warnings ("Could not count all project files: " + $_.Exception.Message)
    }

    $importantPaths = @(
        "pyproject.toml",
        "package.json",
        "app\main.py",
        "app\core\ttl_cache.py",
        "app\middleware\map_listings_cache.py",
        "app\api\routes\aays_sales_layers.py",
        "docker-compose.yml",
        "docker-compose.aays-fast-start.yml",
        "docker-compose.aays-api-command.yml",
        "vite.config.ts",
        "vite.config.js",
        "next.config.js",
        "src",
        "frontend",
        "public"
    )

    $pathRows = @()
    foreach ($p in $importantPaths) {
        $full = Join-Path $ProjectRoot $p
        $pathRows += [ordered]@{
            path = $p
            exists = [bool](Test-Path -LiteralPath $full)
        }
    }

    $extensions = @(".py",".js",".jsx",".ts",".tsx",".css",".html",".yml",".yaml",".json",".md",".sql")
    $extRows = @()
    foreach ($ext in $extensions) {
        $count = 0
        try {
            $count = (Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -Filter ("*" + $ext) -ErrorAction SilentlyContinue | Measure-Object).Count
        } catch {
            $count = -1
        }
        $extRows += [ordered]@{ extension = $ext; count = $count }
    }

    $repoStatus = Safe-Run "project_git_status" {
        Push-Location $ProjectRoot
        try { git status --short 2>&1 | Out-String } finally { Pop-Location }
    }

    $bridgeStatus = Safe-Run "bridge_git_status" {
        Push-Location $BridgeRoot
        try { git status --short 2>&1 | Out-String } finally { Pop-Location }
    }

    $checks += $repoStatus
    $checks += $bridgeStatus

    Add-Line $report "## Inventory Summary"
    Add-Line $report ("Total files counted: " + $totalFiles)
    Add-Line $report ""
    Add-Line $report "### Important Paths"
    foreach ($row in $pathRows) {
        $mark = " "
        if ($row.exists) { $mark = "x" }
        Add-Line $report ("- [" + $mark + "] " + $row.path)
    }
    Add-Line $report ""
    Add-Line $report "### Extension Counts"
    foreach ($row in $extRows) {
        Add-Line $report ("- " + $row.extension + ": " + $row.count)
    }
    Add-Line $report ""
}

$httpTargets = @(
    "http://localhost:8010/health",
    "http://localhost:8010/openapi.json",
    "http://localhost:8010/map/listings?limit=1",
    "http://localhost:8010/map/sales-history/status",
    "http://localhost:8010/map/sales-history/combined"
)
$httpRows = @()
foreach ($u in $httpTargets) {
    $httpRows += Test-Http $u
}

Add-Line $report "## Local API Probe"
foreach ($row in $httpRows) {
    $statusText = "FAIL"
    if ($row.ok) { $statusText = "OK " + $row.status + " " + $row.elapsed_ms + "ms" }
    Add-Line $report ("- " + $row.url + " => " + $statusText)
    if (-not $row.ok -and $row.error) {
        Add-Line $report ("  - error: " + $row.error)
    }
}
Add-Line $report ""

$plan = @(
    [ordered]@{ step=1; title="Preflight and safety baseline"; action="Inventory project, bridge, API status, and create 50-step plan."; output=".aays_50step_plan step001 reports"; status="started" },
    [ordered]@{ step=2; title="Repository topology map"; action="Map backend, frontend, data, Docker, scripts, and generated report folders."; output="topology.json and topology.md"; status="queued" },
    [ordered]@{ step=3; title="Platform target matrix"; action="Define Web, PWA, Windows, macOS, Linux, mobile browser, and optional wrapper targets."; output="platform_matrix.md"; status="queued" },
    [ordered]@{ step=4; title="Runner queue v5 design"; action="Design queue-based bridge that avoids single current-task overwrite risk."; output="runner_queue_v5_design.md"; status="queued" },
    [ordered]@{ step=5; title="Atomic heartbeat design"; action="Specify temp-file rename heartbeat writes and lock-safe status reporting."; output="atomic_heartbeat_spec.md"; status="queued" },
    [ordered]@{ step=6; title="Backup and rollback policy"; action="Create per-file backup policy before source mutation."; output="rollback_policy.md"; status="queued" },
    [ordered]@{ step=7; title="Dependency baseline"; action="Inspect Python and Node dependency manifests and lockfiles."; output="dependency_baseline.json"; status="queued" },
    [ordered]@{ step=8; title="Backend boot health"; action="Validate FastAPI import, py_compile, Docker service names, and health endpoints."; output="backend_health_report.md"; status="queued" },
    [ordered]@{ step=9; title="API contract inventory"; action="Extract OpenAPI routes and classify map/listing/sales endpoints."; output="api_contract_inventory.json"; status="queued" },
    [ordered]@{ step=10; title="Regression baseline for map listings"; action="Record /map/listings behavior before patching."; output="map_listings_baseline.json"; status="queued" },
    [ordered]@{ step=11; title="Frontend boot baseline"; action="Identify frontend framework, build command, and dev server behavior."; output="frontend_baseline.md"; status="queued" },
    [ordered]@{ step=12; title="Performance trace baseline"; action="Capture safe endpoint timings and local bundle size proxies."; output="performance_baseline.json"; status="queued" },
    [ordered]@{ step=13; title="Route and screen map"; action="Map pages, components, menu transitions, and map interaction entry points."; output="ui_route_map.md"; status="queued" },
    [ordered]@{ step=14; title="Cache strategy"; action="Define TTL boundaries for listings, parcels, sales history, and static assets."; output="cache_strategy.md"; status="queued" },
    [ordered]@{ step=15; title="Backend endpoint cache implementation"; action="Patch safe TTL/cache middleware only after baseline confirms target files."; output="cache_patch_report.md"; status="queued" },
    [ordered]@{ step=16; title="Viewport-based data loading"; action="Implement zoom/bounds-aware map requests to avoid unnecessary fetches."; output="viewport_loading_patch.md"; status="queued" },
    [ordered]@{ step=17; title="Debounce and throttle"; action="Apply frontend debounce/throttle to map move, zoom, search, and filter events."; output="debounce_patch_report.md"; status="queued" },
    [ordered]@{ step=18; title="Lazy component loading"; action="Split heavy UI panels, map overlays, and evidence panels."; output="lazy_loading_patch_report.md"; status="queued" },
    [ordered]@{ step=19; title="Overlay and badge CSS fix"; action="Fix security/review labels overlapping buttons and map controls."; output="overlay_css_patch_report.md"; status="queued" },
    [ordered]@{ step=20; title="Parcel click workflow"; action="Defer heavy parcel details until explicit user action or visible panel open."; output="parcel_click_patch_report.md"; status="queued" },
    [ordered]@{ step=21; title="Responsive mobile layout"; action="Audit breakpoints and patch map/sidebar behavior for phone/tablet."; output="responsive_patch_report.md"; status="queued" },
    [ordered]@{ step=22; title="PWA manifest"; action="Add or verify manifest, icons, theme, and install behavior."; output="pwa_manifest_report.md"; status="queued" },
    [ordered]@{ step=23; title="Offline-safe shell"; action="Cache app shell and provide offline fallback without stale data claims."; output="offline_shell_report.md"; status="queued" },
    [ordered]@{ step=24; title="Desktop wrapper decision"; action="Evaluate Tauri/Electron/neutral browser wrapper based on project stack."; output="desktop_wrapper_decision.md"; status="queued" },
    [ordered]@{ step=25; title="Config and secrets hygiene"; action="Ensure env handling is platform-neutral and no secrets are committed."; output="config_hygiene_report.md"; status="queued" },
    [ordered]@{ step=26; title="Data source registry"; action="Create explicit registry for datasets, provenance, and invariant status."; output="data_source_registry.md"; status="queued" },
    [ordered]@{ step=27; title="Evidence-chain model"; action="Improve confidence scoring and visible provenance for listings/sales."; output="evidence_chain_report.md"; status="queued" },
    [ordered]@{ step=28; title="Geometry confidence model"; action="Normalize geometry/SRID handling and confidence flags."; output="geometry_confidence_report.md"; status="queued" },
    [ordered]@{ step=29; title="Manual review UI"; action="Design review queue and safe low-confidence labels."; output="manual_review_ui_plan.md"; status="queued" },
    [ordered]@{ step=30; title="Map tile optimization"; action="Minimize tile redraws, marker churn, and layer updates."; output="tile_optimization_report.md"; status="queued" },
    [ordered]@{ step=31; title="API pagination and limits"; action="Enforce bounded responses and clear pagination contracts."; output="pagination_report.md"; status="queued" },
    [ordered]@{ step=32; title="Background job model"; action="Move heavy calculations to bounded jobs or Web Workers where applicable."; output="background_jobs_plan.md"; status="queued" },
    [ordered]@{ step=33; title="Backend tests"; action="Add smoke/contract tests for health, listings, sales, and geometry routes."; output="backend_tests_report.md"; status="queued" },
    [ordered]@{ step=34; title="Frontend tests"; action="Add component/unit tests for filters, map controls, and badges."; output="frontend_tests_report.md"; status="queued" },
    [ordered]@{ step=35; title="End-to-end smoke"; action="Add one-command smoke flow for API plus UI boot."; output="e2e_smoke_report.md"; status="queued" },
    [ordered]@{ step=36; title="Docker compose hardening"; action="Standardize compose profiles without destructive rebuilds."; output="compose_hardening_report.md"; status="queued" },
    [ordered]@{ step=37; title="CI profile"; action="Create safe CI checks that do not require local secrets or heavy data."; output="ci_profile_report.md"; status="queued" },
    [ordered]@{ step=38; title="Logging and observability"; action="Normalize logs, request IDs, and performance counters."; output="observability_report.md"; status="queued" },
    [ordered]@{ step=39; title="Error handling"; action="Improve user-facing empty/error states for missing data and API failures."; output="error_handling_patch_report.md"; status="queued" },
    [ordered]@{ step=40; title="Release profiles"; action="Define dev, local-demo, production-like, and offline-demo modes."; output="release_profiles.md"; status="queued" },
    [ordered]@{ step=41; title="Windows one-click run"; action="Create a single PowerShell launcher with health checks."; output="windows_launcher_report.md"; status="queued" },
    [ordered]@{ step=42; title="macOS/Linux run scripts"; action="Create bash-compatible run script and documentation."; output="unix_launcher_report.md"; status="queued" },
    [ordered]@{ step=43; title="Data backup and restore"; action="Document and test safe backup/restore without overwriting real data."; output="backup_restore_report.md"; status="queued" },
    [ordered]@{ step=44; title="Operator runbook"; action="Write runbook for install, run, verify, troubleshoot."; output="operator_runbook.md"; status="queued" },
    [ordered]@{ step=45; title="Licensing and free stack review"; action="Confirm free/open-source runtime assumptions and constraints."; output="licensing_review.md"; status="queued" },
    [ordered]@{ step=46; title="Security scan"; action="Check exposed ports, unsafe defaults, and dependency warnings."; output="security_scan_report.md"; status="queued" },
    [ordered]@{ step=47; title="UX polish pass"; action="Tighten empty states, loading states, transitions, and map controls."; output="ux_polish_report.md"; status="queued" },
    [ordered]@{ step=48; title="Performance acceptance"; action="Compare after-patch timings against baseline and acceptance thresholds."; output="performance_acceptance.md"; status="queued" },
    [ordered]@{ step=49; title="Packaging"; action="Package local release artifacts and startup docs."; output="packaging_report.md"; status="queued" },
    [ordered]@{ step=50; title="Final verification"; action="Run final cross-platform checklist and produce release decision."; output="final_verification_report.md"; status="queued" }
)

$planPath = Join-Path $OutRoot "terrayield_50_step_plan.json"
$planMdPath = Join-Path $OutRoot "terrayield_50_step_plan.md"
$checksPath = Join-Path $OutRoot "step001_checks.json"
$httpPath = Join-Path $OutRoot "step001_http_probe.json"
$nextPath = Join-Path $OutRoot "next_task_recommendation.json"
$reportPath = Join-Path $OutRoot "step001_preflight_report.md"

$plan | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $planPath -Encoding UTF8
$checks | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $checksPath -Encoding UTF8
$httpRows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $httpPath -Encoding UTF8

$planMd = New-Object System.Collections.Generic.List[string]
Add-Line $planMd "# TerraYield 50-Step Implementation Plan"
Add-Line $planMd ""
foreach ($s in $plan) {
    Add-Line $planMd ("## " + $s.step + ". " + $s.title)
    Add-Line $planMd ("Action: " + $s.action)
    Add-Line $planMd ("Output: " + $s.output)
    Add-Line $planMd ("Status: " + $s.status)
    Add-Line $planMd ""
}
$planMd | Set-Content -LiteralPath $planMdPath -Encoding UTF8

$next = [ordered]@{
    id = "terrayield-060-cross-platform-topology-step002"
    title = "Step 002 - repository topology map and implementation target discovery"
    progress = 4
    working_directory = $ProjectRoot
    timeout_seconds = 1800
    created_by = "ChatGPT"
    note = "Run after reading result of 059. Generate topology and decide first safe code patch target. Wait 10-15 minutes before writing devam et."
    command = "powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_060_cross_platform_topology_step002.ps1"
}
$next | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $nextPath -Encoding UTF8

Add-Line $report "## 50-Step Plan Created"
Add-Line $report ("- JSON: " + $planPath)
Add-Line $report ("- Markdown: " + $planMdPath)
Add-Line $report ("- Checks: " + $checksPath)
Add-Line $report ("- HTTP probe: " + $httpPath)
Add-Line $report ("- Next recommendation: " + $nextPath)
Add-Line $report ""
if ($warnings.Count -gt 0) {
    Add-Line $report "## Warnings"
    foreach ($w in $warnings) { Add-Line $report ("- " + $w) }
    Add-Line $report ""
}
Add-Line $report "## RESULT"
Add-Line $report "RESULT: step001_preflight_complete"
Add-Line $report "NEXT: terrayield-060-cross-platform-topology-step002"
Add-Line $report "PROGRESS: 3"
Add-Line $report "WAIT: 10-15 minutes then write devam et"

$report | Set-Content -LiteralPath $reportPath -Encoding UTF8
$report | Set-Content -LiteralPath $ResultFile -Encoding UTF8

Write-Host ("RESULT: step001_preflight_complete")
Write-Host ("Task: " + $TaskId)
Write-Host ("Report: " + $reportPath)
Write-Host ("Plan: " + $planPath)
Write-Host ("Next: terrayield-060-cross-platform-topology-step002")
exit 0