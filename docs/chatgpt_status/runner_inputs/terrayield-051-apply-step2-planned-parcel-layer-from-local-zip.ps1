$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# TerraYield 051 - Step 2 planned parcel layer local apply script
# Does NOT pull, checkout, switch branch, stash, write DB, or deploy.
# It uses the local planned_parcel_layer_low_credit_20260609.zip already present in the AAYS repo.
# v4 fix: explicit git add/commit/push commands; earlier script accidentally called add/commit/push without git.
# v4.1 fix: PowerShell elseif syntax corrected.

$TaskId = "terrayield-051-london-only-pilot"
$StepId = "terrayield-051-step2-planned-parcel-layer"
$StatusRootRel = "docs\chatgpt_status"
$OutRel = "docs\chatgpt_status\runner_outputs"
$TxtName = "terrayield_051_step2_planned_parcel_layer_latest.txt"
$JsonName = "terrayield_051_step2_planned_parcel_layer_latest.json"
$LatestName = "terrayield_051_latest_output.json"
$ZipRel = "terrayield_land_intelligence\docs\chatgpt_handoff\planned_parcel_layer_low_credit_20260609.zip"
$WorkRel = "docs\chatgpt_status\runner_work\terrayield_051_step2_planned_parcel_layer"

$Log = New-Object System.Collections.Generic.List[string]
function Log([string]$s) {
  $line = "{0} {1}" -f (Get-Date -Format o), $s
  $script:Log.Add($line) | Out-Null
  Write-Host $line
}
function Exists([string]$p) { try { return (Test-Path -LiteralPath $p) } catch { return $false } }
function Run([string]$cmd) {
  Log "RUN $cmd"
  $out = cmd /c "$cmd 2>&1"
  foreach ($l in $out) { Log "  $l" }
  return $LASTEXITCODE
}

function Write-Result([string]$status, [int]$progress, [string]$phase) {
  $obj = [ordered]@{
    task_id=$StepId
    parent_task_id=$TaskId
    status=$status
    overall_progress_percent=$progress
    phase=$phase
    branch=$script:currentBranch
    repo=$script:repo
    zip_found=$script:zipFound
    patch_check_exit=$script:patchCheckExit
    patch_apply_exit=$script:patchApplyExit
    node_check_exit=$script:nodeExit
    py_compile_exit=$script:pyExit
    pytest_exit=$script:pytestExit
    icon_fix_applied=$script:iconFixed
    git_add_exit=$script:gitAddExit
    commit_exit=$script:commitExit
    push_exit=$script:pushExit
    db_write=$false
    production_deploy=$false
    expected_next_report="docs/chatgpt_status/runner_outputs/terrayield_051_step2_planned_parcel_layer_latest.json"
    timestamp=(Get-Date -Format o)
  }
  $obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $script:json
  $obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $script:latest
  $script:Log | Set-Content -Encoding UTF8 -LiteralPath $script:txt
}

function FindRepoRoot {
  $candidates = @()
  try { $candidates += (git rev-parse --show-toplevel 2>$null) } catch {}
  try { $candidates += (Get-Location).Path } catch {}
  if ($PSScriptRoot) { $candidates += $PSScriptRoot }
  if ($PSCommandPath) { $candidates += (Split-Path -Parent $PSCommandPath) }
  $candidates += "C:\Users\cagda\Documents\GitHub\AAYS"
  foreach ($start in $candidates | Where-Object { $_ }) {
    try { $dir = (Resolve-Path -LiteralPath $start -ErrorAction Stop).Path } catch { continue }
    for ($i=0; $i -lt 12; $i++) {
      if ((Exists (Join-Path $dir ".git")) -and (Exists (Join-Path $dir "terrayield_land_intelligence")) -and (Exists (Join-Path $dir "england_map_web"))) { return $dir }
      $parent = Split-Path -Parent $dir
      if ($parent -eq $dir -or [string]::IsNullOrWhiteSpace($parent)) { break }
      $dir = $parent
    }
  }
  return $null
}

Log "=== TERRAYIELD 051 STEP2 PLANNED PARCEL LAYER APPLY START v4.1 ==="
$script:repo = FindRepoRoot
if (-not $script:repo) {
  Write-Host "REPO_ROOT_NOT_FOUND"
  exit 2
}
Set-Location $script:repo
$script:outDir = Join-Path $script:repo $OutRel
$script:workDir = Join-Path $script:repo $WorkRel
New-Item -ItemType Directory -Force -Path $script:outDir | Out-Null
New-Item -ItemType Directory -Force -Path $script:workDir | Out-Null
$script:txt = Join-Path $script:outDir $TxtName
$script:json = Join-Path $script:outDir $JsonName
$script:latest = Join-Path $script:outDir $LatestName

$script:currentBranch = "unknown"
try { $script:currentBranch = (git rev-parse --abbrev-ref HEAD 2>$null) } catch {}
Log "repo=$script:repo"
Log "current_branch=$script:currentBranch"
Log "NO_PULL_NO_CHECKOUT_NO_STASH=true"

$targets = @(
  "terrayield_land_intelligence\app\api\routes\planned_assets.py",
  "terrayield_land_intelligence\app\services\planned_asset_service.py",
  "terrayield_land_intelligence\tests\test_planned_asset_parcel_layer_contract.py",
  "england_map_web\app.js"
)
foreach ($t in $targets) { Log "target_exists $t=$(Exists (Join-Path $script:repo $t))" }

$zipPath = Join-Path $script:repo $ZipRel
$diffPath = Join-Path $script:workDir "STEP2_APPLY_PATCH_UNIFIED.diff"
$extractDir = Join-Path $script:workDir "zip_extract"
$script:zipFound = Exists $zipPath
$script:patchCheckExit = 999
$script:patchApplyExit = 999
$script:nodeExit = 999
$script:pyExit = 999
$script:pytestExit = 999
$script:gitAddExit = 999
$script:commitExit = 999
$script:pushExit = 999
$applied = $false
$script:iconFixed = $false

if (-not $script:zipFound) {
  Log "ZIP_NOT_FOUND path=$zipPath"
} else {
  Log "ZIP_FOUND path=$zipPath"
  try {
    Remove-Item -Recurse -Force $extractDir -ErrorAction SilentlyContinue
    Expand-Archive -LiteralPath $zipPath -DestinationPath $extractDir -Force
    $extractedDiff = Join-Path $extractDir "STEP2_APPLY_PATCH_UNIFIED.diff"
    if (Exists $extractedDiff) {
      Copy-Item -LiteralPath $extractedDiff -Destination $diffPath -Force
      Log "DIFF_EXTRACTED path=$diffPath"
    } else {
      Log "DIFF_NOT_FOUND_IN_ZIP"
    }
  } catch {
    Log "ZIP_EXTRACT_FAILED error=$($_.Exception.Message)"
  }
}

if (Exists $diffPath) {
  $script:patchCheckExit = Run "git apply --check `"$diffPath`""
  if ($script:patchCheckExit -eq 0) {
    $script:patchApplyExit = Run "git apply --whitespace=nowarn `"$diffPath`""
    if ($script:patchApplyExit -eq 0) { $applied = $true; Log "PATCH_APPLIED_CLEANLY=true" }
  } else {
    Log "PATCH_CHECK_FAILED_TRY_REJECT=true"
    $script:patchApplyExit = Run "git apply --reject --whitespace=nowarn `"$diffPath`""
    if ($script:patchApplyExit -eq 0) { $applied = $true; Log "PATCH_APPLIED_WITH_REJECT_MODE=true" }
  }
} else {
  Log "PATCH_DIFF_MISSING_SKIP_APPLY"
}

# Independent critical frontend icon fix, safe and idempotent.
$appJs = Join-Path $script:repo "england_map_web\app.js"
if (Exists $appJs) {
  try {
    $s = Get-Content -LiteralPath $appJs -Raw -Encoding UTF8
    $old = '{ id: "planned", label: "Planlanan", iconUrl: "./assets/icons/worth-factory.svg" }'
    $new = '{ id: "planned", label: "Planlanan", iconUrl: "./assets/icons/terrayield_icons/planed_buildings.png" }'
    if ($s.Contains($old)) {
      $s = $s.Replace($old, $new)
      Set-Content -LiteralPath $appJs -Value $s -Encoding UTF8
      $script:iconFixed = $true
      Log "ICON_FIX_APPLIED=true"
    } elseif ($s.Contains('planed_buildings.png')) {
      $script:iconFixed = $true
      Log "ICON_FIX_ALREADY_PRESENT=true"
    } else {
      Log "ICON_FIX_PATTERN_NOT_FOUND"
    }
  } catch { Log "ICON_FIX_FAILED error=$($_.Exception.Message)" }
}

if (Exists $appJs) { $script:nodeExit = Run "node --check england_map_web\app.js" }
if (Exists (Join-Path $script:repo "terrayield_land_intelligence\app\api\routes\planned_assets.py")) {
  $script:pyExit = Run "cd terrayield_land_intelligence && python -m py_compile app\api\routes\planned_assets.py app\services\planned_asset_service.py"
}
if (Exists (Join-Path $script:repo "terrayield_land_intelligence\tests\test_planned_asset_parcel_layer_contract.py")) {
  $script:pytestExit = Run "cd terrayield_land_intelligence && python -m pytest tests\test_planned_asset_parcel_layer_contract.py -q"
}

$changed = (git status --short 2>$null)
foreach ($c in $changed) { Log "GIT_STATUS $c" }

$status = "STEP2_ATTEMPTED"
$progress = 40
if ($applied -and ($script:nodeExit -eq 0) -and ($script:pyExit -eq 0)) { $status = "STEP2_PATCH_APPLIED_LOCAL_CHECKS_PASSED"; $progress = 60 }
elseif ($applied) { $status = "STEP2_PATCH_APPLIED_CHECKS_NEED_REVIEW"; $progress = 48 }
elseif ($script:iconFixed) { $status = "STEP2_PARTIAL_ICON_FIX_ONLY_PATCH_FAILED"; $progress = 36 }
else { $status = "STEP2_PATCH_FAILED_NO_PRODUCT_CHANGE"; $progress = 30 }

Write-Result $status $progress "before_git_commit"

# Commit only explicit Step 2 targets/reports. No cleaning unrelated untracked files.
$filesToAdd = @(
  "terrayield_land_intelligence/app/api/routes/planned_assets.py",
  "terrayield_land_intelligence/app/services/planned_asset_service.py",
  "terrayield_land_intelligence/tests/test_planned_asset_parcel_layer_contract.py",
  "england_map_web/app.js",
  "docs/chatgpt_status/runner_outputs/$TxtName",
  "docs/chatgpt_status/runner_outputs/$JsonName",
  "docs/chatgpt_status/runner_outputs/$LatestName",
  "docs/chatgpt_status/runner_work/terrayield_051_step2_planned_parcel_layer/STEP2_APPLY_PATCH_UNIFIED.diff"
)
$existingFilesToAdd = @()
foreach ($f in $filesToAdd) { if (Exists (Join-Path $script:repo $f)) { $existingFilesToAdd += $f } else { Log "GIT_ADD_SKIP_MISSING $f" } }
if ($existingFilesToAdd.Count -gt 0) {
  $quoted = ($existingFilesToAdd | ForEach-Object { '"' + $_ + '"' }) -join " "
  $script:gitAddExit = Run "git add -- $quoted"
} else {
  Log "GIT_ADD_SKIPPED_NO_EXISTING_TARGETS"
}
$script:commitExit = Run "git commit -m `"Apply TerraYield 051 planned parcel layer step2 local patch`""
if ($script:commitExit -ne 0) { Log "COMMIT_NONZERO exit=$script:commitExit maybe_no_changes_or_git_config_issue" }
if ($script:currentBranch -and $script:currentBranch -ne "unknown" -and $script:currentBranch -ne "HEAD") {
  $script:pushExit = Run "git push origin $script:currentBranch"
} else {
  Log "PUSH_SKIPPED_UNKNOWN_BRANCH"
}

Write-Result $status $progress "after_git_push"
Log "=== TERRAYIELD 051 STEP2 PLANNED PARCEL LAYER APPLY END status=$status progress=$progress ==="
exit 0
