$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$StepId = "terrayield-051-step2-planned-parcel-layer"
$ParentTaskId = "terrayield-051-london-only-pilot"
$OutRel = "docs\chatgpt_status\runner_outputs"
$TxtName = "terrayield_051_step2_planned_parcel_layer_latest.txt"
$JsonName = "terrayield_051_step2_planned_parcel_layer_latest.json"
$LatestName = "terrayield_051_latest_output.json"
$PatchRel = "docs\chatgpt_status\runner_inputs\terrayield-051-step2-planned-parcel-layer.patch"

$Log = New-Object System.Collections.Generic.List[string]
function Add-Log([string]$s) {
  $line = "{0} {1}" -f (Get-Date -Format o), $s
  $script:Log.Add($line) | Out-Null
  Write-Host $line
}
function Exists([string]$p) { try { return (Test-Path -LiteralPath $p) } catch { return $false } }
function RunCmd([string]$cmd) {
  Add-Log "RUN $cmd"
  $out = cmd /c "$cmd 2>&1"
  foreach ($l in $out) { Add-Log "  $l" }
  return $LASTEXITCODE
}
function RepoRoot {
  try { $r = git rev-parse --show-toplevel 2>$null; if ($r) { return $r } } catch {}
  return "C:\Users\cagda\Documents\GitHub\AAYS"
}
function Write-Result([string]$status, [int]$progress, [string]$phase) {
  $obj = [ordered]@{
    task_id=$StepId
    parent_task_id=$ParentTaskId
    status=$status
    overall_progress_percent=$progress
    phase=$phase
    branch=$script:branch
    repo=$script:repo
    embedded_patch=$PatchRel
    embedded_patch_found=$script:patchFound
    patch_check_exit=$script:patchCheck
    patch_apply_exit=$script:patchApply
    node_check_exit=$script:nodeExit
    py_compile_exit=$script:pyExit
    pytest_exit=$script:pytestExit
    git_add_exit=$script:gitAdd
    commit_exit=$script:commitExit
    push_exit=$script:pushExit
    expected_next_report="docs/chatgpt_status/runner_outputs/terrayield_051_step2_planned_parcel_layer_latest.json"
    timestamp=(Get-Date -Format o)
  }
  $obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $script:json
  $obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $script:latest
  $script:Log | Set-Content -Encoding UTF8 -LiteralPath $script:txt
}

Add-Log "=== TERRAYIELD 051 EMBEDDED PATCH APPLY START ==="
$script:repo = RepoRoot
Set-Location $script:repo
$script:branch = "unknown"
try { $script:branch = (git rev-parse --abbrev-ref HEAD 2>$null) } catch {}
$outDir = Join-Path $script:repo $OutRel
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$script:txt = Join-Path $outDir $TxtName
$script:json = Join-Path $outDir $JsonName
$script:latest = Join-Path $outDir $LatestName
$patchPath = Join-Path $script:repo $PatchRel
$script:patchFound = Exists $patchPath
$script:patchCheck = 999
$script:patchApply = 999
$script:nodeExit = 999
$script:pyExit = 999
$script:pytestExit = 999
$script:gitAdd = 999
$script:commitExit = 999
$script:pushExit = 999

Add-Log "repo=$script:repo"
Add-Log "branch=$script:branch"
Add-Log "embedded_patch_path=$patchPath exists=$script:patchFound"

$targets = @(
  "terrayield_land_intelligence/app/api/routes/planned_assets.py",
  "terrayield_land_intelligence/app/services/planned_asset_service.py",
  "terrayield_land_intelligence/tests/test_planned_asset_parcel_layer_contract.py",
  "england_map_web/app.js"
)
foreach ($t in $targets) { Add-Log "target_exists $t=$(Exists (Join-Path $script:repo $t))" }

$applied = $false
if ($script:patchFound) {
  $script:patchCheck = RunCmd "git apply --check `"$patchPath`""
  if ($script:patchCheck -eq 0) {
    $script:patchApply = RunCmd "git apply --whitespace=nowarn `"$patchPath`""
    if ($script:patchApply -eq 0) { $applied = $true; Add-Log "patch_applied=true" }
  } else {
    Add-Log "patch_check_nonzero_try_apply_reject"
    $script:patchApply = RunCmd "git apply --reject --whitespace=nowarn `"$patchPath`""
    if ($script:patchApply -eq 0) { $applied = $true; Add-Log "patch_applied_reject_mode=true" }
  }
} else {
  Add-Log "embedded_patch_missing"
}

if (Exists (Join-Path $script:repo "england_map_web/app.js")) { $script:nodeExit = RunCmd "node --check england_map_web\app.js" }
if (Exists (Join-Path $script:repo "terrayield_land_intelligence/app/api/routes/planned_assets.py")) { $script:pyExit = RunCmd "cd terrayield_land_intelligence && python -m py_compile app\api\routes\planned_assets.py app\services\planned_asset_service.py" }
if (Exists (Join-Path $script:repo "terrayield_land_intelligence/tests/test_planned_asset_parcel_layer_contract.py")) { $script:pytestExit = RunCmd "cd terrayield_land_intelligence && python -m pytest tests\test_planned_asset_parcel_layer_contract.py -q" }

$status = "STEP2_EMBEDDED_PATCH_ATTEMPTED"
$progress = 40
if ($applied -and $script:nodeExit -eq 0 -and $script:pyExit -eq 0) { $status = "STEP2_PATCH_APPLIED_LOCAL_CHECKS_PASSED"; $progress = 60 }
elseif ($applied) { $status = "STEP2_PATCH_APPLIED_CHECKS_NEED_REVIEW"; $progress = 55 }
elseif (-not $script:patchFound) { $status = "STEP2_BLOCKED_EMBEDDED_PATCH_MISSING"; $progress = 49 }
else { $status = "STEP2_PATCH_NOT_APPLIED"; $progress = 49 }

Write-Result $status $progress "before_git"

$filesToAdd = @(
  "terrayield_land_intelligence/app/api/routes/planned_assets.py",
  "terrayield_land_intelligence/app/services/planned_asset_service.py",
  "terrayield_land_intelligence/tests/test_planned_asset_parcel_layer_contract.py",
  "england_map_web/app.js",
  "docs/chatgpt_status/runner_outputs/$TxtName",
  "docs/chatgpt_status/runner_outputs/$JsonName",
  "docs/chatgpt_status/runner_outputs/$LatestName"
)
$existing = @()
foreach ($f in $filesToAdd) { if (Exists (Join-Path $script:repo $f)) { $existing += $f } }
if ($existing.Count -gt 0) {
  $quoted = ($existing | ForEach-Object { '"' + $_ + '"' }) -join " "
  $script:gitAdd = RunCmd "git add -- $quoted"
}
$script:commitExit = RunCmd "git commit -m `"Apply TerraYield 051 embedded planned parcel layer patch`""
if ($script:branch -and $script:branch -ne "unknown" -and $script:branch -ne "HEAD") { $script:pushExit = RunCmd "git push origin $script:branch" }
Write-Result $status $progress "after_git"
Add-Log "=== TERRAYIELD 051 EMBEDDED PATCH APPLY END status=$status progress=$progress ==="
exit 0
