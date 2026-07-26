param()

$ErrorActionPreference = "Stop"
$TaskId = "terrayield-052-publish-2of4-geometry-review-to-f-site-20260629"
$PageKey = "aays1"
$Now = Get-Date -Format "yyyyMMdd-HHmmss"

$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } elseif (Test-Path "F:\chatgpt\chat_gpt_clone_1_main") { "F:\chatgpt\chat_gpt_clone_1_main" } else { (Get-Location).Path }
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } elseif (Test-Path "F:\AAYS_GITHUB_BRIDGE_CLEAN2") { "F:\AAYS_GITHUB_BRIDGE_CLEAN2" } else { $null }

$PageRoot = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$StatusDir = Join-Path $PageRoot "status"
$ReportDir = Join-Path $PageRoot "reports"
$RunnerOutputDir = Join-Path $PageRoot "runner_outputs\geometry_review_2of4_20260629"
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir,$RunnerOutputDir | Out-Null

$ReportPath = Join-Path $ReportDir "052_publish_2of4_geometry_review_to_f_site_$Now.md"
$StatusPath = Join-Path $StatusDir "052_publish_2of4_geometry_review_to_f_site_$Now.json"
$PublishLogPath = Join-Path $RunnerOutputDir "publish_2of4_geometry_review_to_f_site_$Now.log"

$LegacyAaysRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$LegacyOutputRoot = Join-Path $LegacyAaysRoot "outputs\terrayield_3110_20260629"
$SourceDir = Join-Path $LegacyOutputRoot "geometry_review_2of4_20260629"
$PublishPs1 = Join-Path $SourceDir "RUN_PUBLISH_TO_F_SITE_TR.ps1"
$PublishPy = Join-Path $LegacyOutputRoot "publish_2of4_geometry_review_to_f_site.py"

$RequiredSourceFiles = @(
  (Join-Path $SourceDir "TerraYield_2OF4_Geometry_Review_Queue_20260629.html"),
  (Join-Path $SourceDir "TerraYield_2OF4_Geometry_Review_Queue_20260629.csv"),
  (Join-Path $SourceDir "CHATGPT_2OF4_GEOMETRY_REVIEW_MASTER_PROMPT_TR.txt")
)

$SiteDir = Join-Path $RepoRoot "england_map_web"
$ExpectedHtml = Join-Path $SiteDir "geometry_review_2of4_20260629.html"
$ExpectedUrl = "http://127.0.0.1:8010/england_map_web/geometry_review_2of4_20260629.html"

function Write-TaskStatus {
  param([hashtable]$Data)
  $Data | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $StatusPath
}

function Write-ReportHeader {
@"
# 052 Publish 2/4 Geometry Review To F Site

task_id: $TaskId
page_key: $PageKey
started_at: $Now
repo_root: $RepoRoot
bridge_root: $BridgeRoot
legacy_source_dir: $SourceDir
expected_url: $ExpectedUrl

## Safety

- db_write: false
- ddl: false
- migration: false
- production_deploy: false
- fake_polygon: false
- new_runner_started: false

"@ | Set-Content -Encoding UTF8 $ReportPath
}

Write-ReportHeader

$BaseStatus = @{
  task_id = $TaskId
  page_key = $PageKey
  timestamp = $Now
  repo_root = $RepoRoot
  bridge_root = $BridgeRoot
  runner_contract = "single_shared_runner_only"
  new_runner_started = $false
  db_write = $false
  ddl = $false
  migration = $false
  production_deploy = $false
  fake_polygon = $false
  review_records_processed = 0
  review_upgraded_to_3of4 = 0
  review_upgraded_to_4of4 = 0
  review_kept_2of4 = 0
  final_ready = $false
}

try {
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "## Preflight`n"

  if (!(Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
  if (!(Test-Path $SourceDir)) { throw "Legacy source dir not found: $SourceDir" }

  $Missing = @()
  foreach ($File in $RequiredSourceFiles) {
    if (!(Test-Path $File)) { $Missing += $File }
  }
  if ($Missing.Count -gt 0) {
    Add-Content -Encoding UTF8 -Path $ReportPath -Value ("BLOCKED: missing required source files:`n" + (($Missing | ForEach-Object { "- $_" }) -join "`n"))
    $Status = $BaseStatus.Clone()
    $Status.status = "BLOCKED_MISSING_SOURCE_FILES"
    $Status.missing_source_files = $Missing
    $Status.expected_local_command = "powershell -ExecutionPolicy Bypass -File `"$PublishPs1`""
    Write-TaskStatus $Status
    exit 2
  }

  foreach ($File in $RequiredSourceFiles) {
    Copy-Item -Force -Path $File -Destination $RunnerOutputDir
    Add-Content -Encoding UTF8 -Path $ReportPath -Value "source_ok: $File"
  }
  if (Test-Path $PublishPy) { Copy-Item -Force -Path $PublishPy -Destination $RunnerOutputDir }
  if (Test-Path $PublishPs1) { Copy-Item -Force -Path $PublishPs1 -Destination $RunnerOutputDir }

  Set-Location $RepoRoot
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "`n## Git Sync`n"
  git status --short | Out-File -Encoding UTF8 -Append $ReportPath
  git fetch origin main 2>&1 | Out-File -Encoding UTF8 -Append $ReportPath
  git pull --ff-only origin main 2>&1 | Out-File -Encoding UTF8 -Append $ReportPath

  Add-Content -Encoding UTF8 -Path $ReportPath -Value "`n## Publish`n"
  if (Test-Path $PublishPs1) {
    Add-Content -Encoding UTF8 -Path $ReportPath -Value "running: $PublishPs1"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $PublishPs1 *> $PublishLogPath
    $PublishExit = $LASTEXITCODE
  } elseif (Test-Path $PublishPy) {
    Add-Content -Encoding UTF8 -Path $ReportPath -Value "running: python $PublishPy"
    & python $PublishPy *> $PublishLogPath
    $PublishExit = $LASTEXITCODE
  } else {
    throw "No publish script found. Expected $PublishPs1 or $PublishPy"
  }

  Add-Content -Encoding UTF8 -Path $ReportPath -Value "publish_exit_code: $PublishExit"
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "publish_log: $PublishLogPath"
  if ($PublishExit -ne 0) {
    $Status = $BaseStatus.Clone()
    $Status.status = "BLOCKED_PUBLISH_SCRIPT_FAILED"
    $Status.publish_exit_code = $PublishExit
    $Status.publish_log = $PublishLogPath
    Write-TaskStatus $Status
    exit 3
  }

  Add-Content -Encoding UTF8 -Path $ReportPath -Value "`n## Validation`n"
  $PublishedExists = Test-Path $ExpectedHtml
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "published_html_exists: $PublishedExists"
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "published_html_path: $ExpectedHtml"
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "published_url: $ExpectedUrl"

  if (!$PublishedExists) {
    $Status = $BaseStatus.Clone()
    $Status.status = "BLOCKED_PUBLISHED_HTML_NOT_FOUND"
    $Status.expected_html = $ExpectedHtml
    $Status.publish_log = $PublishLogPath
    Write-TaskStatus $Status
    exit 4
  }

  $Hash = (Get-FileHash -Algorithm SHA256 $ExpectedHtml).Hash
  $Size = (Get-Item $ExpectedHtml).Length
  Copy-Item -Force -Path $ExpectedHtml -Destination (Join-Path $RunnerOutputDir "published_geometry_review_2of4_20260629.html")
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "published_html_sha256: $Hash"
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "published_html_bytes: $Size"

  $AppJs = Join-Path $SiteDir "app.js"
  $LinkFound = $false
  if (Test-Path $AppJs) {
    $LinkFound = Select-String -Path $AppJs -Pattern "2/4 Geometri|geometry_review_2of4_20260629" -SimpleMatch -Quiet
  }
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "app_link_found: $LinkFound"

  Add-Content -Encoding UTF8 -Path $ReportPath -Value "`n## Git Commit And Push`n"
  $RelPaths = @(
    "england_map_web/geometry_review_2of4_20260629.html",
    "england_map_web/app.js",
    "docs/chatgpt_status/aays1/runner_outputs/geometry_review_2of4_20260629",
    "docs/chatgpt_status/aays1/reports",
    "docs/chatgpt_status/aays1/status"
  )
  foreach ($Rel in $RelPaths) {
    if (Test-Path (Join-Path $RepoRoot $Rel)) {
      git add -- $Rel 2>&1 | Out-File -Encoding UTF8 -Append $ReportPath
    }
  }

  $Changes = git status --porcelain
  if ($Changes) {
    Add-Content -Encoding UTF8 -Path $ReportPath -Value "changes_to_commit:`n$Changes"
    git commit -m "Publish 2of4 geometry review page" 2>&1 | Out-File -Encoding UTF8 -Append $ReportPath
    git push origin main 2>&1 | Out-File -Encoding UTF8 -Append $ReportPath
  } else {
    Add-Content -Encoding UTF8 -Path $ReportPath -Value "No changes to commit."
  }

  $Done = Get-Date -Format "yyyyMMdd-HHmmss"
  $Status = $BaseStatus.Clone()
  $Status.timestamp = $Done
  $Status.status = "PUBLISH_READY_FOR_REVIEW"
  $Status.publish_exit_code = 0
  $Status.published_html_path = $ExpectedHtml
  $Status.published_url = $ExpectedUrl
  $Status.published_html_sha256 = $Hash
  $Status.published_html_bytes = $Size
  $Status.app_link_found = $LinkFound
  $Status.output_dir = $RunnerOutputDir
  $Status.report_path = $ReportPath
  $Status.note = "This publishes the 2/4 review mechanism only. It does not complete the 1264-record evidence review."
  Write-TaskStatus $Status
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "`nSTATUS=PUBLISH_READY_FOR_REVIEW`nfinal_ready=false`n"
  exit 0
}
catch {
  $Err = $_.Exception.Message
  Add-Content -Encoding UTF8 -Path $ReportPath -Value "`n## ERROR`n$Err`n"
  $Status = $BaseStatus.Clone()
  $Status.status = "BLOCKED_AUTOMATION_EXCEPTION"
  $Status.error = $Err
  $Status.report_path = $ReportPath
  Write-TaskStatus $Status
  exit 9
}
