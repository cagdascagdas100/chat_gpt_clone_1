param(
  [string]$Repo = "C:\Users\cagda\Documents\GitHub\AAYS",
  [string]$SyncBranch = "chatgpt-local-sync"
)

$ErrorActionPreference = "Stop"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Worktree = Join-Path $env:TEMP "aays_chatgpt_sync_$Stamp"
$RelDir = "docs/chatgpt_status/local_sync"
$LatestRel = "$RelDir/latest_local_probe.json"
$SnapshotRel = "$RelDir/probe_$Stamp.json"

function Test-Cmd($name) {
  try { (Get-Command $name -ErrorAction Stop).Source } catch { "NOT_FOUND" }
}

function Test-FileSafe($p) {
  if ([string]::IsNullOrWhiteSpace($p)) { return $false }
  try { return (Test-Path $p) } catch { return $false }
}

function Run-GitOptional([string]$ArgsLine) {
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "cmd.exe"
  $psi.Arguments = "/c git $ArgsLine"
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $p = [System.Diagnostics.Process]::Start($psi)
  $p.WaitForExit()
  return $p.ExitCode
}

function Read-RegionConfig($path) {
  $rows = @()
  if (!(Test-Path $path)) {
    return @([ordered]@{ config = $path; status = "MISSING" })
  }
  try {
    $json = Get-Content $path -Raw | ConvertFrom-Json
    foreach ($prop in $json.PSObject.Properties) {
      $name = $prop.Name
      $row = $prop.Value
      if ($name -notmatch "london|south|east|midlands|north|wales|scotland") { continue }
      $paths = [ordered]@{}
      foreach ($key in @("prepared_path","prepared_simplified_path","source_gpkg_path","pmtiles_local_path","audit_report_path","poi_path")) {
        $value = ""
        try { $value = [string]$row.$key } catch {}
        if ($value) {
          $paths[$key] = [ordered]@{ path = $value; exists = Test-FileSafe $value }
        }
      }
      $rows += [ordered]@{ config = $path; region = $name; paths = $paths }
    }
  } catch {
    $rows += [ordered]@{ config = $path; status = "READ_FAIL"; error = $_.Exception.Message }
  }
  return $rows
}

if (!(Test-Path $Repo)) { throw "Repo path not found: $Repo" }

$toolStatus = [ordered]@{
  tippecanoe = Test-Cmd "tippecanoe"
  pmtiles    = Test-Cmd "pmtiles"
  ogr2ogr    = Test-Cmd "ogr2ogr"
  docker     = Test-Cmd "docker"
  python     = Test-Cmd "python"
  git        = Test-Cmd "git"
  wsl        = Test-Cmd "wsl"
}

$regionProbe = @()
foreach ($cf in @(
  "pmtiles_regions_england_generated_v2.json",
  "pmtiles_regions_britain_generated_v2.json",
  "england_map_web\config\regions.local.json"
)) {
  $regionProbe += Read-RegionConfig (Join-Path $Repo $cf)
}

$pmtilesFiles = @()
try {
  $pmtilesFiles = Get-ChildItem $Repo -Recurse -File -Filter "*.pmtiles" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\docs\\chatgpt_handoff\\" } |
    Select-Object FullName,Length,LastWriteTime
} catch {}

$wslStatus = "NOT_CHECKED"
try { $wslStatus = (wsl --list --verbose | Out-String) } catch { $wslStatus = "WSL_FAIL=$($_.Exception.Message)" }

$probe = [ordered]@{
  project = "AAYS_TerraYield"
  page_key = "AAYS_SAME_PROJECT_NEW_PAGE"
  timestamp = $Stamp
  repo = $Repo
  safety = [ordered]@{
    db_write = $false
    ddl = $false
    migration_apply = $false
    production_deploy = $false
    fake_demo_data = $false
    destructive_git = $false
  }
  tools = $toolStatus
  wsl_status = $wslStatus
  region_probe = $regionProbe
  pmtiles_files = $pmtilesFiles
  conclusion = [ordered]@{
    current_status = "LOCAL_PARTIAL_PARCEL_COVERAGE_READY_WITH_BLOCKER"
    blocker = "missing_region_pmtiles_files_or_missing_source_assets"
    next_needed = "install_or_use_containerized_tippecanoe_pmtiles_ogr2ogr_and_generate_missing_region_pmtiles"
  }
}

$ProbeJson = $probe | ConvertTo-Json -Depth 20
$LocalOut = Join-Path $Repo $RelDir
New-Item -ItemType Directory -Force -Path $LocalOut | Out-Null
$ProbeJson | Set-Content (Join-Path $Repo $LatestRel) -Encoding UTF8
$ProbeJson | Set-Content (Join-Path $Repo $SnapshotRel) -Encoding UTF8

# Branch ilk kez oluşuyorsa fetch hatası normaldir; bu hata akışı durdurmaz.
Run-GitOptional "-C `"$Repo`" fetch origin $SyncBranch" | Out-Null
$base = "HEAD"
$branchExists = Run-GitOptional "-C `"$Repo`" rev-parse --verify origin/$SyncBranch"
if ($branchExists -eq 0) { $base = "origin/$SyncBranch" }

if (Test-Path $Worktree) {
  git -C $Repo worktree remove $Worktree --force 2>$null
  Remove-Item $Worktree -Recurse -Force -ErrorAction SilentlyContinue
}

git -C $Repo worktree add -B $SyncBranch $Worktree $base
try {
  $TargetDir = Join-Path $Worktree $RelDir
  New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
  $ProbeJson | Set-Content (Join-Path $Worktree $LatestRel) -Encoding UTF8
  $ProbeJson | Set-Content (Join-Path $Worktree $SnapshotRel) -Encoding UTF8

  git -C $Worktree add $LatestRel $SnapshotRel
  git -C $Worktree commit -m "chatgpt local sync $Stamp" 2>$null
  git -C $Worktree push -u origin $SyncBranch
} finally {
  git -C $Repo worktree remove $Worktree --force 2>$null
}

Write-Host "SYNC_DONE"
Write-Host "BRANCH=$SyncBranch"
Write-Host "LATEST=$LatestRel"
Write-Host "SNAPSHOT=$SnapshotRel"
Write-Host "STAMP=$Stamp"
