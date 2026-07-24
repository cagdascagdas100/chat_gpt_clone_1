[CmdletBinding()]
param(
  [ValidateSet("Auto", "Docker", "Local")]
  [string]$Mode = "Auto",
  [int]$ApiPort = 8010,
  [int]$DbPort = 55460,
  [switch]$NoBrowser,
  [switch]$Rebuild
)

$ErrorActionPreference = "Stop"

function Import-PortableEnv {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$PortableRoot,
    [Parameter(Mandatory = $true)][string]$RepoRoot,
    [Parameter(Mandatory = $true)][string]$ProjectRoot
  )
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing portable env file: $Path"
  }
  foreach ($line in Get-Content -LiteralPath $Path) {
    $trimmed = $line.Trim()
    if ($trimmed -eq "" -or $trimmed.StartsWith("#")) { continue }
    $idx = $trimmed.IndexOf("=")
    if ($idx -lt 1) { continue }
    $key = $trimmed.Substring(0, $idx).Trim()
    $value = $trimmed.Substring($idx + 1).Trim()
    $value = $value.Trim('"').Trim("'")
    $value = $value.Replace("__PORTABLE_ROOT__", $PortableRoot)
    $value = $value.Replace("__REPO_ROOT__", $RepoRoot)
    $value = $value.Replace("__PROJECT_ROOT__", $ProjectRoot)
    [Environment]::SetEnvironmentVariable($key, $value, "Process")
  }
}

function Find-PortablePython {
  param(
    [string]$PortableRoot,
    [string]$ProjectRoot
  )
  $candidates = @(
    (Join-Path $PortableRoot "runtime\python312\python.exe"),
    (Join-Path $PortableRoot "runtime\python\python.exe")
  )
  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
  }
  throw "Portable Python not found under runtime\python312 or runtime\python."
}

function Wait-HttpOk {
  param(
    [string]$Url,
    [int]$TimeoutSeconds = 90
  )
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    try {
      $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
      if ($response.StatusCode -eq 200) {
        try {
          $payload = $response.Content | ConvertFrom-Json
          if ($payload.status -eq "ok" -and $payload.app -eq "TerraYield Land Intelligence") {
            return $true
          }
        } catch { }
      }
    } catch {
      Start-Sleep -Seconds 2
    }
  } while ((Get-Date) -lt $deadline)
  return $false
}

function Test-DockerUsable {
  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if ($null -eq $docker) { return $false }
  try {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & docker info *> $null
    return ($LASTEXITCODE -eq 0)
  } catch {
    return $false
  } finally {
    $ErrorActionPreference = $previousErrorAction
  }
}

$portableRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Join-Path $portableRoot "AAYS"
$projectRoot = Join-Path $repoRoot "terrayield_land_intelligence"
$runtimeRoot = Join-Path $portableRoot "runtime"
$logRoot = Join-Path $runtimeRoot "logs"
$tempRoot = Join-Path $runtimeRoot "tmp"
$cacheRoot = Join-Path $runtimeRoot "cache"
$homeRoot = Join-Path $runtimeRoot "home"
$pycacheRoot = Join-Path $runtimeRoot "pycache"
$pythonUserRoot = Join-Path $runtimeRoot "python-user"

# Keep TerraYield runtime output on the portable disk. These values are
# process-local and do not change the Windows user's global TEMP or HOME.
$env:AAYS_PORTABLE_ROOT = $portableRoot
$env:AAYS_REPO_ROOT = $repoRoot
$env:AAYS_PROJECT_ROOT = $projectRoot
$env:AAYS_RUNNER_MODE = "F_PORTABLE_SINGLE_COORDINATOR"
$env:TEMP = $tempRoot
$env:TMP = $tempRoot
$env:HOME = $homeRoot
$env:PYTHONNOUSERSITE = "1"
$env:PYTHONUSERBASE = $pythonUserRoot
$env:PYTHONPYCACHEPREFIX = $pycacheRoot
$env:PIP_CACHE_DIR = Join-Path $cacheRoot "pip"
$env:UV_CACHE_DIR = Join-Path $cacheRoot "uv"
$env:XDG_CACHE_HOME = Join-Path $cacheRoot "xdg"
$env:MPLCONFIGDIR = Join-Path $cacheRoot "matplotlib"
$env:NUMBA_CACHE_DIR = Join-Path $cacheRoot "numba"
$env:JOBLIB_TEMP_FOLDER = Join-Path $tempRoot "joblib"
$env:HF_HOME = Join-Path $cacheRoot "huggingface"
$env:TORCH_HOME = Join-Path $cacheRoot "torch"
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $runtimeRoot "playwright-browsers"

if (-not (Test-Path -LiteralPath $repoRoot)) {
  throw "Missing AAYS repo folder: $repoRoot"
}
if (-not (Test-Path -LiteralPath $projectRoot)) {
  throw "Missing TerraYield project folder: $projectRoot"
}

@(
  $runtimeRoot,
  $logRoot,
  (Join-Path $runtimeRoot "postgres-data"),
  (Join-Path $runtimeRoot "raw"),
  $tempRoot,
  $cacheRoot,
  $homeRoot,
  $pycacheRoot,
  $pythonUserRoot,
  $env:PIP_CACHE_DIR,
  $env:UV_CACHE_DIR,
  $env:XDG_CACHE_HOME,
  $env:MPLCONFIGDIR,
  $env:NUMBA_CACHE_DIR,
  $env:JOBLIB_TEMP_FOLDER,
  $env:HF_HOME,
  $env:TORCH_HOME,
  $env:PLAYWRIGHT_BROWSERS_PATH,
  (Join-Path $runtimeRoot "live-feeds-cache"),
  (Join-Path $runtimeRoot "live-feeds-exports")
) | ForEach-Object {
  New-Item -ItemType Directory -Force -Path $_ | Out-Null
}

$healthUrl = "http://127.0.0.1:$ApiPort/health"
$dockerAvailable = Test-DockerUsable
$useDocker = $false
if ($Mode -eq "Docker") { $useDocker = $true }
elseif ($Mode -eq "Auto" -and $dockerAvailable) { $useDocker = $true }

if ($useDocker) {
  if (-not $dockerAvailable) {
    throw "Docker is not available. Re-run with -Mode Local or install Docker Desktop."
  }
  $composeFile = Join-Path $projectRoot "docker-compose.portable.yml"
  if (-not (Test-Path -LiteralPath $composeFile)) {
    throw "Missing portable compose file: $composeFile"
  }
  $env:TYLI_API_PORT = "$ApiPort"
  $env:TYLI_DB_PORT = "$DbPort"
  Push-Location $projectRoot
  try {
    $args = @("compose", "-f", "docker-compose.portable.yml", "--project-name", "terrayield_aays_portable", "up", "-d")
    if ($Rebuild) { $args += "--build" }
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose failed with exit code $LASTEXITCODE" }
  } finally {
    Pop-Location
  }
  if (-not (Wait-HttpOk -Url $healthUrl -TimeoutSeconds 120)) {
    throw "TerraYield API did not become healthy at $healthUrl"
  }
  if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$ApiPort" | Out-Null }
  "mode=docker"
  "health=$healthUrl"
  exit 0
}

$envFile = Join-Path $projectRoot ".env.portable.local"
Import-PortableEnv -Path $envFile -PortableRoot $portableRoot -RepoRoot $repoRoot -ProjectRoot $projectRoot
$env:AAYS_PARCEL_PROXY_ALLOW_REMOTE = "true"
$env:TYLI_DB_PORT = "$DbPort"
if (-not $env:TYLI_DATABASE_URL) {
  $env:TYLI_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:$DbPort/terrayield_land"
}

$pythonExe = Find-PortablePython -PortableRoot $portableRoot -ProjectRoot $projectRoot
$stdoutLog = Join-Path $logRoot ("uvicorn-{0}.out.log" -f $ApiPort)
$stderrLog = Join-Path $logRoot ("uvicorn-{0}.err.log" -f $ApiPort)

Push-Location $projectRoot
try {
  & $pythonExe -c "import fastapi, uvicorn, sqlalchemy, psycopg" 2>$null
  if ($LASTEXITCODE -ne 0) {
    throw "Python dependencies are missing for $pythonExe. Run: python -m pip install -e ."
  }
  $existing = netstat -ano | Select-String ":$ApiPort\s+.*LISTENING" | Select-Object -First 1
  if ($existing -and -not (Wait-HttpOk -Url $healthUrl -TimeoutSeconds 4)) {
    throw "PORT_$ApiPort`_OCCUPIED_BY_NON_TERRAYIELD_PROCESS"
  }
  if (-not $existing) {
    $proc = Start-Process `
      -FilePath $pythonExe `
      -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
      -WorkingDirectory $projectRoot `
      -WindowStyle Hidden `
      -RedirectStandardOutput $stdoutLog `
      -RedirectStandardError $stderrLog `
      -PassThru
    "api_pid=$($proc.Id)"
  }
} finally {
  Pop-Location
}

if (-not (Wait-HttpOk -Url $healthUrl -TimeoutSeconds 90)) {
  throw "TerraYield API did not become healthy at $healthUrl. Check $stderrLog"
}
if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$ApiPort" | Out-Null }
"mode=local"
"health=$healthUrl"
