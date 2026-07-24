[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$taskId = 'aays1-165-topography-official-lidar-boundary-validation-20260713'
$root = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not $root -or $root -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]'){
  throw 'TOPOGRAPHY_165_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$marker = '\runner_system\'
$markerIndex = $root.IndexOf($marker,[System.StringComparison]::OrdinalIgnoreCase)
if($markerIndex -lt 0){ throw 'TOPOGRAPHY_165_PORTABLE_ROOT_NOT_RESOLVED' }
$portableRoot = $root.Substring(0,$markerIndex)
$packageRoot = Join-Path $portableRoot 'data\topography\python_packages\task_164_rasterio'
if(-not(Test-Path -LiteralPath $packageRoot)){ New-Item -ItemType Directory -Force -Path $packageRoot | Out-Null }

$pythonCommand = $null
$pythonPrefix = @()
$candidate = Get-Command python -ErrorAction SilentlyContinue
if($candidate){ $pythonCommand = $candidate.Source }
if(-not $pythonCommand){
  $candidate = Get-Command py -ErrorAction SilentlyContinue
  if($candidate){ $pythonCommand = $candidate.Source; $pythonPrefix = @('-3') }
}
if(-not $pythonCommand){
  $candidate = Get-Command python3 -ErrorAction SilentlyContinue
  if($candidate){ $pythonCommand = $candidate.Source }
}
if(-not $pythonCommand){ throw 'TOPOGRAPHY_165_PYTHON_NOT_AVAILABLE' }

$previousPythonPath = [string]$env:PYTHONPATH
if($previousPythonPath){ $env:PYTHONPATH = "$packageRoot;$previousPythonPath" } else { $env:PYTHONPATH = $packageRoot }

& $pythonCommand @pythonPrefix -c "import rasterio; print(rasterio.__version__)"
if($LASTEXITCODE -ne 0){
  & $pythonCommand @pythonPrefix -m ensurepip --upgrade
  & $pythonCommand @pythonPrefix -m pip install --disable-pip-version-check --no-input --upgrade --target $packageRoot rasterio
  if($LASTEXITCODE -ne 0){ throw 'TOPOGRAPHY_165_RASTERIO_INSTALL_FAILED' }
  & $pythonCommand @pythonPrefix -c "import rasterio; print(rasterio.__version__)"
  if($LASTEXITCODE -ne 0){ throw 'TOPOGRAPHY_165_RASTERIO_IMPORT_FAILED' }
}

$env:AAYS_PORTABLE_ROOT = $portableRoot
$env:AAYS_TASK_ID = $taskId
$env:AAYS_TASK_165_PACKAGE_ROOT = $packageRoot

$payloadPath = Join-Path $root 'docs\chatgpt_status\topography\automation\165_topography_official_lidar_boundary_validation_payload_20260713.b64'
if(-not(Test-Path -LiteralPath $payloadPath)){ throw 'TOPOGRAPHY_165_PAYLOAD_NOT_FOUND' }
$pythonSourceGzipBase64 = (Get-Content -LiteralPath $payloadPath -Raw -Encoding UTF8).Trim()
$compressedBytes = [Convert]::FromBase64String($pythonSourceGzipBase64)
$inputStream = New-Object System.IO.MemoryStream(,$compressedBytes)
$gzipStream = New-Object System.IO.Compression.GZipStream($inputStream,[System.IO.Compression.CompressionMode]::Decompress)
$reader = New-Object System.IO.StreamReader($gzipStream,[System.Text.Encoding]::UTF8)
$pythonSource = $reader.ReadToEnd()
$reader.Dispose(); $gzipStream.Dispose(); $inputStream.Dispose()

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_topography_165'
if(-not(Test-Path -LiteralPath $tempRoot)){ New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null }
$pythonPath = Join-Path $tempRoot '165_topography_official_lidar_boundary_validation.py'
[System.IO.File]::WriteAllText($pythonPath,$pythonSource,[System.Text.UTF8Encoding]::new($false))

& $pythonCommand @pythonPrefix $pythonPath
$code = $LASTEXITCODE
if($code -ne 0){ throw "TOPOGRAPHY_165_PYTHON_EXIT_$code" }
