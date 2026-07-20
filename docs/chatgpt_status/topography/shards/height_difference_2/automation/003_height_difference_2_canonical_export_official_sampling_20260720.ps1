[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$branch = [string]$env:AAYS_TARGET_BRANCH
$root = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $root) { throw 'HEIGHT_DIFFERENCE_2_REPO_ROOT_MISSING' }
if ($branch -and $branch -ne 'codex/aays-single-runner-v5-20260706') { throw 'HEIGHT_DIFFERENCE_2_WRONG_BRANCH' }
if ([string]$env:AAYS_PAGE_KEY -and [string]$env:AAYS_PAGE_KEY -ne 'aays1') { throw 'HEIGHT_DIFFERENCE_2_WRONG_PAGE_KEY' }

$marker = '\runner_system\'
$markerIndex = $root.IndexOf($marker,[System.StringComparison]::OrdinalIgnoreCase)
if ($markerIndex -ge 0) { $portableRoot = $root.Substring(0,$markerIndex) } else { $portableRoot = Split-Path -Parent $root }
$packageRoot = Join-Path $portableRoot 'data\topography\python_packages\height_difference_2_official_sampling'
New-Item -ItemType Directory -Force -Path $packageRoot | Out-Null

$pythonCommand = $null
$pythonPrefix = @()
foreach($name in @('python','py','python3')) {
  $candidate = Get-Command $name -ErrorAction SilentlyContinue
  if($candidate){
    $pythonCommand = $candidate.Source
    if($name -eq 'py'){ $pythonPrefix = @('-3') }
    break
  }
}
if(-not $pythonCommand){ throw 'HEIGHT_DIFFERENCE_2_PYTHON_NOT_AVAILABLE' }

$previousPythonPath = [string]$env:PYTHONPATH
if($previousPythonPath){ $env:PYTHONPATH = "$packageRoot;$previousPythonPath" } else { $env:PYTHONPATH = $packageRoot }
$required = @('requests','numpy','rasterio','pyproj','shapely','lxml')
foreach($module in $required){
  & $pythonCommand @pythonPrefix -c "import $module" 2>$null
  if($LASTEXITCODE -ne 0){
    & $pythonCommand @pythonPrefix -m pip install --disable-pip-version-check --no-input --upgrade --target $packageRoot $module
    if($LASTEXITCODE -ne 0){ throw "HEIGHT_DIFFERENCE_2_PIP_INSTALL_FAILED_$module" }
  }
}

$env:AAYS_TASK_ID = $taskId
$env:AAYS_PORTABLE_ROOT = $portableRoot
$env:AAYS_HEIGHT_DIFFERENCE_2_PACKAGE_ROOT = $packageRoot
$payloadPath = Join-Path $root 'docs\chatgpt_status\topography\shards\height_difference_2\automation\003_height_difference_2_canonical_export_official_sampling_20260720.py.gz.b64'
if(-not(Test-Path -LiteralPath $payloadPath)){ throw 'HEIGHT_DIFFERENCE_2_PAYLOAD_NOT_FOUND' }
$payload = (Get-Content -LiteralPath $payloadPath -Raw -Encoding UTF8).Trim()
$compressedBytes = [Convert]::FromBase64String($payload)
$inputStream = New-Object System.IO.MemoryStream(,$compressedBytes)
$gzipStream = New-Object System.IO.Compression.GZipStream($inputStream,[System.IO.Compression.CompressionMode]::Decompress)
$reader = New-Object System.IO.StreamReader($gzipStream,[System.Text.Encoding]::UTF8)
$pythonSource = $reader.ReadToEnd()
$reader.Dispose(); $gzipStream.Dispose(); $inputStream.Dispose()

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_2'
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
$pythonPath = Join-Path $tempRoot '003_height_difference_2_canonical_export_official_sampling.py'
[System.IO.File]::WriteAllText($pythonPath,$pythonSource,[System.Text.UTF8Encoding]::new($false))
& $pythonCommand @pythonPrefix $pythonPath
$code = $LASTEXITCODE
if($code -ne 0){ throw "HEIGHT_DIFFERENCE_2_PYTHON_EXIT_$code" }
