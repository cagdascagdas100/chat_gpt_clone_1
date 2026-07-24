[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$PortableRoot,
  [Parameter(Mandatory = $true)]
  [string]$PayloadRoot,
  [string]$RemoteUrl = "https://github.com/cagdascagdas100/chat_gpt_clone_1.git",
  [string]$Branch = "codex/aays-single-runner-v5-20260706"
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($PortableRoot).TrimEnd("\")
$payload = [System.IO.Path]::GetFullPath($PayloadRoot).TrimEnd("\")
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "PORTABLE_ROOT_MISSING: $root" }
if (-not (Test-Path -LiteralPath $payload -PathType Container)) { throw "PAYLOAD_ROOT_MISSING: $payload" }
if ($root.StartsWith("C:\", [StringComparison]::OrdinalIgnoreCase) -or $root.StartsWith("D:\", [StringComparison]::OrdinalIgnoreCase)) {
  throw "PORTABLE_ROOT_MUST_REMAIN_ON_F_FOR_THIS_INSTALL: $root"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $root "_portable_backups\adaptive_v2_$stamp"
$stageRoot = Join-Path $root "_v2_staging\$stamp"
$adaptiveStage = Join-Path $root "runner_system\adaptive_v2.staging.$stamp"
$adaptiveFinal = Join-Path $root "runner_system\adaptive_v2"
$manifestPath = Join-Path $stageRoot "staging_sha256_manifest.json"
New-Item -ItemType Directory -Force -Path $backupRoot,$stageRoot,$adaptiveStage | Out-Null

function Write-JsonAtomic([string]$Path, [object]$Value) {
  $directory = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
  $temporary = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
  [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 20) + [Environment]::NewLine, (New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $temporary -Destination $Path -Force
}
function Invoke-Git([string]$WorkingRoot, [string[]]$Arguments) {
  & git -c "safe.directory=$WorkingRoot" -C $WorkingRoot @Arguments
  if ($LASTEXITCODE -ne 0) { throw "GIT_FAILED: root=$WorkingRoot args=$($Arguments -join ' ')" }
}
function Configure-Sparse([string]$Repo, [string[]]$Paths) {
  Invoke-Git $Repo @("sparse-checkout", "init", "--cone", "--sparse-index")
  Invoke-Git $Repo (@("sparse-checkout", "set") + $Paths)
}

$payloadFiles = @(
  "AAYS_ADAPTIVE_5_WORKER_COORDINATOR.py",
  "AAYS_PORTABLE_CONTROL_PANEL.py",
  "RUN_AAYS_ADAPTIVE_5_WORKER.ps1",
  "RUN_AAYS_ADAPTIVE_5_WORKER.cmd",
  "RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.ps1"
)
foreach ($name in $payloadFiles) {
  $source = Join-Path $payload $name
  if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "PAYLOAD_FILE_MISSING: $source" }
  Copy-Item -LiteralPath $source -Destination (Join-Path $stageRoot $name) -Force
}

$manifest = @()
foreach ($file in Get-ChildItem -LiteralPath $stageRoot -File) {
  $manifest += [ordered]@{ path = $file.Name; size = $file.Length; sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash }
}
Write-JsonAtomic $manifestPath ([ordered]@{ generated_at = (Get-Date).ToUniversalTime().ToString("o"); files = $manifest; final_ready = $false })

$publisher = Join-Path $adaptiveStage "publisher"
& git clone --depth=1 --filter=blob:none --no-checkout --branch $Branch $RemoteUrl $publisher
if ($LASTEXITCODE -ne 0) { throw "PUBLISHER_CLONE_FAILED" }
Configure-Sparse $publisher @("docs/chatgpt_status", "terrayield_land_intelligence", "england_map_web")
Invoke-Git $publisher @("checkout", "--detach", "origin/$Branch")
Invoke-Git $publisher @("config", "user.name", "AAYS Adaptive Publisher")
Invoke-Git $publisher @("config", "user.email", "aays-adaptive@local.invalid")

$slotPaths = [ordered]@{
  ready_to_sell = @("docs/chatgpt_status/_shared/slots", "docs/chatgpt_status/aays1")
  gas_emissions = @("docs/chatgpt_status/_shared/slots", "docs/chatgpt_status/gas_emissions")
  height_difference = @("docs/chatgpt_status/_shared/slots", "docs/chatgpt_status/topography")
  security_public_safety = @("docs/chatgpt_status/_shared/slots", "docs/chatgpt_status/aays1")
  parcel_label = @("docs/chatgpt_status/_shared/slots", "docs/chatgpt_status/aays1")
}
$worktreeRoot = Join-Path $adaptiveStage "worktrees\slots"
New-Item -ItemType Directory -Force -Path $worktreeRoot | Out-Null
foreach ($slotId in $slotPaths.Keys) {
  $slotRepo = Join-Path $worktreeRoot $slotId
  & git clone --depth=1 --filter=blob:none --no-checkout --branch $Branch $RemoteUrl $slotRepo
  if ($LASTEXITCODE -ne 0) { throw "SLOT_CLONE_FAILED: $slotId" }
  Invoke-Git $slotRepo @("remote", "set-url", "--push", "origin", "DISABLED_CHILD_DIRECT_PUSH")
  Configure-Sparse $slotRepo $slotPaths[$slotId]
  Invoke-Git $slotRepo @("checkout", "--detach", "origin/$Branch")
}

$identity = [ordered]@{
  schema_version = 2
  portable_product = "AAYS_TerraYield"
  portable_instance_id = [guid]::NewGuid().ToString("N")
  repository = "cagdascagdas100/chat_gpt_clone_1"
  branch = $Branch
  architecture_version = 2
  created_at = (Get-Date).ToUniversalTime().ToString("o")
  relative_launcher_path = "RUN_AAYS_ADAPTIVE_5_WORKER.cmd"
  relative_repo_path = "runner_system\adaptive_v2\publisher"
  relative_worktree_root = "runner_system\adaptive_v2\worktrees"
  relative_runtime_path = "runtime\adaptive_v2"
  expected_markers = @("AAYS_ADAPTIVE_5_WORKER_COORDINATOR.py", "AAYS_PORTABLE_CONTROL_PANEL.py", "runner_system\adaptive_v2\publisher")
  canonical_drive_letter_persisted = $false
  final_ready = $false
}
Write-JsonAtomic (Join-Path $stageRoot ".aays_portable_identity.json") $identity

if (Test-Path -LiteralPath $adaptiveFinal) {
  throw "ADAPTIVE_V2_ALREADY_EXISTS_NO_DESTRUCTIVE_OVERWRITE: $adaptiveFinal"
}
Move-Item -LiteralPath $adaptiveStage -Destination $adaptiveFinal

foreach ($name in @($payloadFiles + ".aays_portable_identity.json")) {
  $target = Join-Path $root $name
  if (Test-Path -LiteralPath $target -PathType Leaf) { Copy-Item -LiteralPath $target -Destination (Join-Path $backupRoot $name) -Force }
  $temporary = "$target.tmp.$([guid]::NewGuid().ToString('N'))"
  Copy-Item -LiteralPath (Join-Path $stageRoot $name) -Destination $temporary -Force
  Move-Item -LiteralPath $temporary -Destination $target -Force
}

[ordered]@{
  status = "STAGED_AND_CUTOVER_READY"
  portable_root = $root
  backup_root = $backupRoot
  staging_manifest = $manifestPath
  publisher = $publisher.Replace($adaptiveStage, $adaptiveFinal)
  slot_count = 5
  child_direct_push_forbidden = $true
  f_source_preserved = $true
  d_drive_written = $false
  final_ready = $false
} | ConvertTo-Json -Depth 10
