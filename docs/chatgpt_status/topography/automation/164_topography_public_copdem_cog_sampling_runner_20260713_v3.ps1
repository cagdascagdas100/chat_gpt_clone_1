[CmdletBinding()]
param()

$ErrorActionPreference='Stop'

$root=[System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not $root -or $root -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]'){
  throw 'TOPOGRAPHY_164_V3_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$marker='\runner_system\'
$markerIndex=$root.IndexOf($marker,[System.StringComparison]::OrdinalIgnoreCase)
if($markerIndex -lt 0){throw 'TOPOGRAPHY_164_V3_PORTABLE_ROOT_NOT_RESOLVED'}
$portableRoot=$root.Substring(0,$markerIndex)
$packageRoot=Join-Path $portableRoot 'data\topography\python_packages\task_164_rasterio'
if(-not(Test-Path -LiteralPath $packageRoot)){New-Item -ItemType Directory -Force -Path $packageRoot|Out-Null}

$pythonCommand=$null
$pythonPrefix=@()
$candidate=Get-Command python -ErrorAction SilentlyContinue
if($candidate){$pythonCommand=$candidate.Source}
if(-not $pythonCommand){$candidate=Get-Command py -ErrorAction SilentlyContinue;if($candidate){$pythonCommand=$candidate.Source;$pythonPrefix=@('-3')}}
if(-not $pythonCommand){$candidate=Get-Command python3 -ErrorAction SilentlyContinue;if($candidate){$pythonCommand=$candidate.Source}}
if(-not $pythonCommand){throw 'TOPOGRAPHY_164_V3_PYTHON_NOT_AVAILABLE'}

$previousPythonPath=[string]$env:PYTHONPATH
if($previousPythonPath){$env:PYTHONPATH="$packageRoot;$previousPythonPath"}else{$env:PYTHONPATH=$packageRoot}

& $pythonCommand @pythonPrefix -c "import rasterio; print(rasterio.__version__)"
if($LASTEXITCODE -ne 0){
  & $pythonCommand @pythonPrefix -m ensurepip --upgrade
  & $pythonCommand @pythonPrefix -m pip install --disable-pip-version-check --no-input --upgrade --target $packageRoot rasterio
  if($LASTEXITCODE -ne 0){throw 'TOPOGRAPHY_164_V3_RASTERIO_INSTALL_FAILED'}
  & $pythonCommand @pythonPrefix -c "import rasterio; print(rasterio.__version__)"
  if($LASTEXITCODE -ne 0){throw 'TOPOGRAPHY_164_V3_RASTERIO_IMPORT_FAILED'}
}

$base=Join-Path $root 'docs\chatgpt_status\topography\automation\164_topography_public_copdem_cog_sampling_runner_20260713.ps1'
if(-not(Test-Path -LiteralPath $base)){throw 'TOPOGRAPHY_164_V3_BASE_SCRIPT_NOT_FOUND'}
$text=Get-Content -LiteralPath $base -Raw -Encoding UTF8

$text=$text.Replace("  `$checksumStage='partial'","  `$checksumStage='partial'`r`n  `$checksum30Status='blocked';if(`$download30.downloaded){`$checksum30Status='verified'}`r`n  `$checksum90Status='blocked';if(`$download90.downloaded){`$checksum90Status='verified'}")
$text=$text.Replace("-Status (if(`$download30.downloaded){'verified'}else{'blocked'})","-Status `$checksum30Status")
$text=$text.Replace("-Status (if(`$download90.downloaded){'verified'}else{'blocked'})","-Status `$checksum90Status")
$text=$text.Replace("  `$blockers=@('real_parcel_boundary_required','ea_lidar_or_os_terrain_numeric_validation_required')","  `$blockers=@('real_parcel_boundary_required','ea_lidar_or_os_terrain_numeric_validation_required')`r`n  `$primaryLocalPathValue=`$null;if(`$download30.downloaded){`$primaryLocalPathValue=`$path30}`r`n  `$samplingEngineValue=`$null;if(`$samplePayload){`$samplingEngineValue=`$samplePayload.engine}")
$text=$text.Replace("(if(`$download30.downloaded){`$path30}else{`$null})","`$primaryLocalPathValue")
$text=$text.Replace("(if(`$samplePayload){`$samplePayload.engine}else{`$null})","`$samplingEngineValue")

$sampleRelLine="`$sampleRel='docs/chatgpt_status/topography/fixtures/topography_public_copdem_cog_samples_20260713.json'"
$sampleWebRelLine="`$sampleRel='docs/chatgpt_status/topography/fixtures/topography_public_copdem_cog_samples_20260713.json'`r`n`$sampleWebRel='england_map_web/data/program_layer_matrix/topography_public_copdem_cog_samples_latest.json'"
$text=$text.Replace($sampleRelLine,$sampleWebRelLine)
$text=$text.Replace("  `$samplePayload=Read-Json `$sampleOutput","  `$samplePayload=Read-Json `$sampleOutput`r`n  if(`$samplePayload){Set-Prop `$samplePayload 'task_id' `$taskId;Set-Prop `$samplePayload 'batch_id' `$batchId;Write-Json (Repo-Path `$sampleWebRel) `$samplePayload}")
$text=$text.Replace("`$publishPaths=@(`$visibleRowsRel,`$visibleStatusRel,`$operationsRel,`$sourceRel,`$sampleRel)-join'|'","`$publishPaths=@(`$visibleRowsRel,`$visibleStatusRel,`$operationsRel,`$sourceRel,`$sampleRel,`$sampleWebRel)-join'|'")
$text=$text.Replace("http://127.0.0.1:8012/docs/chatgpt_status/topography/fixtures/topography_public_copdem_cog_samples_20260713.json","http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_public_copdem_cog_samples_latest.json")

if($text.Contains('(if(')){throw 'TOPOGRAPHY_164_V3_INLINE_IF_REPAIR_INCOMPLETE'}
if(-not $text.Contains('topography_public_copdem_cog_samples_latest.json')){throw 'TOPOGRAPHY_164_V3_SAMPLE_WEB_PATCH_INCOMPLETE'}

$tempRoot=Join-Path ([System.IO.Path]::GetTempPath()) 'aays_topography_164_v3'
if(-not(Test-Path -LiteralPath $tempRoot)){New-Item -ItemType Directory -Force -Path $tempRoot|Out-Null}
$patched=Join-Path $tempRoot '164_topography_public_copdem_cog_sampling_runner_patched_v3.ps1'
[System.IO.File]::WriteAllText($patched,$text,[System.Text.UTF8Encoding]::new($false))

& powershell -NoProfile -ExecutionPolicy Bypass -File $patched
$code=$LASTEXITCODE
if($code -ne 0){throw "TOPOGRAPHY_164_V3_PATCHED_SCRIPT_EXIT_$code"}
