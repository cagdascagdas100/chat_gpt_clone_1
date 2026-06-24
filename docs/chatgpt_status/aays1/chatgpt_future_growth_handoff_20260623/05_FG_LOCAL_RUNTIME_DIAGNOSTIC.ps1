param(
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS",
  [string]$OutputRoot = ""
)

$ErrorActionPreference = "Continue"

function Resolve-OutputRoot {
  param([string]$Requested)
  if ($Requested -and (Split-Path -Path $Requested -Qualifier)) {
    return $Requested
  }
  if (Test-Path "F:\") { return "F:\chatgpt\AAYS_FG100" }
  if (Test-Path "D:\") { return "D:\chatgpt\AAYS_FG100" }
  return (Join-Path $RepoRoot "docs\chatgpt_status\aays1\local_fg100_reports_fallback")
}

function Add-Line {
  param(
    [System.Collections.Generic.List[string]]$Lines,
    [string]$Text
  )
  $Lines.Add($Text) | Out-Null
}

function Try-WebStatus {
  param(
    [string]$Url,
    [int]$TimeoutSec = 8
  )
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec $TimeoutSec
    return @{ status = [string]$resp.StatusCode; note = "OK" }
  } catch {
    $message = $_.Exception.Message
    return @{ status = "ERROR"; note = $message }
  }
}

$resolvedOutputRoot = Resolve-OutputRoot -Requested $OutputRoot
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportDir = Join-Path $resolvedOutputRoot "reports"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportPath = Join-Path $reportDir ("fg100_local_runtime_diagnostic_" + $timestamp + ".txt")

$lines = New-Object 'System.Collections.Generic.List[string]'
Add-Line $lines "FG100 local runtime diagnostic"
Add-Line $lines ("timestamp=" + $timestamp)
Add-Line $lines ("repo_root=" + $RepoRoot)
Add-Line $lines ("output_root=" + $resolvedOutputRoot)

try {
  $branch = git -C $RepoRoot branch --show-current 2>$null
  Add-Line $lines ("git_branch=" + ($branch -join " ").Trim())
} catch {
  Add-Line $lines "git_branch=ERROR"
}

try {
  $remote = git -C $RepoRoot remote -v 2>$null | Select-Object -First 1
  Add-Line $lines ("git_remote=" + ($remote -join " ").Trim())
} catch {
  Add-Line $lines "git_remote=ERROR"
}

try {
  $statusShort = git -C $RepoRoot status --short 2>$null
  if ($statusShort) {
    Add-Line $lines "git_status_short_begin"
    $statusShort | ForEach-Object { Add-Line $lines $_ }
    Add-Line $lines "git_status_short_end"
  } else {
    Add-Line $lines "git_status_short=CLEAN"
  }
} catch {
  Add-Line $lines "git_status_short=ERROR"
}

$rootCheck = Try-WebStatus -Url "http://127.0.0.1:8010/"
Add-Line $lines ("api_root_status=" + $rootCheck.status)
Add-Line $lines ("api_root_note=" + $rootCheck.note)

$webCheck = Try-WebStatus -Url "http://127.0.0.1:8010/england_map_web/"
Add-Line $lines ("england_map_web_status=" + $webCheck.status)
Add-Line $lines ("england_map_web_note=" + $webCheck.note)

$methodCheck = Try-WebStatus -Url "http://127.0.0.1:8010/api/future-growth/methodology"
Add-Line $lines ("future_growth_methodology_status=" + $methodCheck.status)
Add-Line $lines ("future_growth_methodology_note=" + $methodCheck.note)

$layerUrl = "http://127.0.0.1:8010/api/future-growth/layer?bbox=-0.6,51.25,0.3,51.75&zoom=12&limit=20"
$layerCheck = Try-WebStatus -Url $layerUrl
Add-Line $lines ("future_growth_layer_status=" + $layerCheck.status)
Add-Line $lines ("future_growth_layer_note=" + $layerCheck.note)

try {
  $docker = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1
  Add-Line $lines "docker_status_begin"
  $docker | ForEach-Object { Add-Line $lines $_ }
  Add-Line $lines "docker_status_end"
} catch {
  Add-Line $lines ("docker_status=ERROR " + $_.Exception.Message)
}

$finalWrapper = Join-Path $RepoRoot "docs\chatgpt_status\aays1\reports\aays1_sync_unblock_then_future_growth_wrapper_20260619_008.txt"
if (Test-Path $finalWrapper) {
  Add-Line $lines "final_wrapper_exists=true"
  Add-Line $lines ("final_wrapper_path=" + $finalWrapper)
} else {
  Add-Line $lines "final_wrapper_exists=false"
  Add-Line $lines ("final_wrapper_path=" + $finalWrapper)
}

$lines | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Output $reportPath
