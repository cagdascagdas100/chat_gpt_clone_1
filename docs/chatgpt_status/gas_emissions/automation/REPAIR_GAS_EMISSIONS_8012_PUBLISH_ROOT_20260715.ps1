[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][ValidateSet(100,151,233,316)][int]$ExpectedRows
)

$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
$controllerRoot = [string]$env:AAYS_CONTROLLER_REPO_ROOT
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') { throw 'GAS_EMISSIONS_8012_REPAIR_WRONG_CONTEXT' }
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') { throw 'GAS_EMISSIONS_8012_REPAIR_WRONG_BRANCH' }

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}

function Copy-Atomic([string]$Source,[string]$Target) {
  Ensure-Dir (Split-Path -Parent $Target)
  $tmp = $Target + '.aays_tmp_' + [Guid]::NewGuid().ToString('N')
  Copy-Item -LiteralPath $Source -Destination $tmp -Force
  Move-Item -LiteralPath $tmp -Destination $Target -Force
}

function Get-RowCount([string]$Path) {
  try {
    $value = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    return @($value.rows).Count
  } catch { return -1 }
}

function Get-HttpRowCount {
  try {
    $url = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?root_repair=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $value = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 20 -Headers @{ 'Cache-Control'='no-cache' }
    return @($value.rows).Count
  } catch { return -1 }
}

function Add-Root([System.Collections.Generic.List[string]]$Roots,[string]$Candidate) {
  if ([string]::IsNullOrWhiteSpace($Candidate)) { return }
  try { $full = [System.IO.Path]::GetFullPath($Candidate).TrimEnd('\') } catch { return }
  if (-not (Test-Path -LiteralPath (Join-Path $full 'england_map_web') -PathType Container)) { return }
  if (-not $Roots.Contains($full)) { [void]$Roots.Add($full) }
}

function Add-RootFromPath([System.Collections.Generic.List[string]]$Roots,[string]$CandidatePath) {
  if ([string]::IsNullOrWhiteSpace($CandidatePath)) { return }
  $candidate = $CandidatePath.Trim().Trim('"').Trim("'").TrimEnd(',',';')
  try {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $candidate = Split-Path -Parent $candidate }
    for ($i=0; $i -lt 10 -and $candidate; $i++) {
      if (Test-Path -LiteralPath (Join-Path $candidate 'england_map_web') -PathType Container) {
        Add-Root $Roots $candidate
        return
      }
      $parent = Split-Path -Parent $candidate
      if (-not $parent -or $parent -eq $candidate) { break }
      $candidate = $parent
    }
  } catch {}
}

function Get-CandidateRoots {
  $roots = New-Object 'System.Collections.Generic.List[string]'

  try {
    $listener = Get-NetTCPConnection -LocalPort 8012 -State Listen -ErrorAction Stop | Select-Object -First 1
    $processId = [int]$listener.OwningProcess
    for ($depth=0; $depth -lt 5 -and $processId -gt 0; $depth++) {
      $process = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction Stop
      foreach ($text in @([string]$process.CommandLine,[string]$process.ExecutablePath)) {
        foreach ($match in [regex]::Matches($text,'(?i)"([A-Z]:\\[^\"]+)"|([A-Z]:\\\S+)')) {
          $path = if ($match.Groups[1].Success) { $match.Groups[1].Value } else { $match.Groups[2].Value }
          Add-RootFromPath $roots $path
        }
      }
      $processId = [int]$process.ParentProcessId
    }
  } catch {}

  try {
    $health = Invoke-WebRequest -Uri 'http://127.0.0.1:8012/health' -UseBasicParsing -TimeoutSec 10
    foreach ($match in [regex]::Matches([string]$health.Content,'(?i)[A-Z]:\\\\[^\",}]+')) {
      Add-RootFromPath $roots (($match.Value) -replace '\\\\','\')
    }
  } catch {}

  Add-Root $roots $controllerRoot
  Add-Root $roots $repoRoot

  $worktreeRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT'
  if (Test-Path -LiteralPath $worktreeRoot -PathType Container) {
    Get-ChildItem -LiteralPath $worktreeRoot -Directory -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 16 |
      ForEach-Object { Add-Root $roots $_.FullName }
  }

  return @($roots)
}

$rowsRel = 'england_map_web\data\program_layer_matrix\gas_emissions_visible_rows_latest.json'
$statusRel = 'england_map_web\data\program_layer_matrix\gas_emissions_status_latest.json'
$matrixRel = 'england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$sources = @(
  @{ Rel=$rowsRel; Path=(Join-Path $repoRoot $rowsRel) },
  @{ Rel=$statusRel; Path=(Join-Path $repoRoot $statusRel) },
  @{ Rel=$matrixRel; Path=(Join-Path $repoRoot $matrixRel) }
)
foreach ($source in $sources) {
  if (-not (Test-Path -LiteralPath $source.Path -PathType Leaf)) { throw "GAS_EMISSIONS_8012_REPAIR_SOURCE_MISSING: $($source.Path)" }
}
$canonicalCount = Get-RowCount (Join-Path $repoRoot $rowsRel)
if ($canonicalCount -ne $ExpectedRows) { throw "GAS_EMISSIONS_8012_REPAIR_CANONICAL_COUNT_MISMATCH: actual=$canonicalCount expected=$ExpectedRows" }

if ((Get-HttpRowCount) -eq $ExpectedRows) {
  Write-Output "GAS_EMISSIONS_8012_ALREADY_CURRENT: rows=$ExpectedRows"
  exit 0
}

$attempted = New-Object 'System.Collections.Generic.List[string]'
foreach ($publishRoot in @(Get-CandidateRoots)) {
  [void]$attempted.Add($publishRoot)
  foreach ($source in $sources) { Copy-Atomic $source.Path (Join-Path $publishRoot $source.Rel) }
  Start-Sleep -Milliseconds 750
  if ((Get-HttpRowCount) -eq $ExpectedRows) {
    Write-Output "GAS_EMISSIONS_8012_ROOT_REPAIRED: root=$publishRoot rows=$ExpectedRows"
    exit 0
  }
}
throw ('GAS_EMISSIONS_8012_ROOT_NOT_FOUND: expected=' + $ExpectedRows + ' attempted=' + ($attempted -join ';'))
