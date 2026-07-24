[CmdletBinding()]
param()

$ErrorActionPreference='Stop'

$root=[System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not $root -or $root -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]'){
  throw 'TOPOGRAPHY_164_V4_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$marker='\runner_system\'
$markerIndex=$root.IndexOf($marker,[System.StringComparison]::OrdinalIgnoreCase)
if($markerIndex -lt 0){throw 'TOPOGRAPHY_164_V4_PORTABLE_ROOT_NOT_RESOLVED'}
$portableRoot=$root.Substring(0,$markerIndex)
$packageRoot=Join-Path $portableRoot 'data\topography\python_packages\task_164_rasterio'
if(-not(Test-Path -LiteralPath $packageRoot)){New-Item -ItemType Directory -Force -Path $packageRoot|Out-Null}

$pythonCommand=$null
$pythonPrefix=@()
$candidate=Get-Command python -ErrorAction SilentlyContinue
if($candidate){$pythonCommand=$candidate.Source}
if(-not $pythonCommand){$candidate=Get-Command py -ErrorAction SilentlyContinue;if($candidate){$pythonCommand=$candidate.Source;$pythonPrefix=@('-3')}}
if(-not $pythonCommand){$candidate=Get-Command python3 -ErrorAction SilentlyContinue;if($candidate){$pythonCommand=$candidate.Source}}
if(-not $pythonCommand){throw 'TOPOGRAPHY_164_V4_PYTHON_NOT_AVAILABLE'}

$previousPythonPath=[string]$env:PYTHONPATH
if($previousPythonPath){$env:PYTHONPATH="$packageRoot;$previousPythonPath"}else{$env:PYTHONPATH=$packageRoot}

& $pythonCommand @pythonPrefix -c "import rasterio; print(rasterio.__version__)"
if($LASTEXITCODE -ne 0){
  & $pythonCommand @pythonPrefix -m ensurepip --upgrade
  & $pythonCommand @pythonPrefix -m pip install --disable-pip-version-check --no-input --upgrade --target $packageRoot rasterio
  if($LASTEXITCODE -ne 0){throw 'TOPOGRAPHY_164_V4_RASTERIO_INSTALL_FAILED'}
  & $pythonCommand @pythonPrefix -c "import rasterio; print(rasterio.__version__)"
  if($LASTEXITCODE -ne 0){throw 'TOPOGRAPHY_164_V4_RASTERIO_IMPORT_FAILED'}
}

$base=Join-Path $root 'docs\chatgpt_status\topography\automation\164_topography_public_copdem_cog_sampling_runner_20260713.ps1'
if(-not(Test-Path -LiteralPath $base)){throw 'TOPOGRAPHY_164_V4_BASE_SCRIPT_NOT_FOUND'}
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

$readSampleLine="  `$samplePayload=Read-Json `$sampleOutput"
$readSampleReplacement=@'
  $samplePayload=Read-Json $sampleOutput
  if(-not $samplePayload){
    $samplePayload=[pscustomobject][ordered]@{ok=$false;engine=$null;error=$samplingError;datasets=[pscustomobject]@{};rows=@()}
  }
  Set-Prop $samplePayload 'task_id' $taskId
  Set-Prop $samplePayload 'batch_id' $batchId
  Set-Prop $samplePayload 'generated_at' (Now-Utc)
  Write-Json (Repo-Path $sampleWebRel) $samplePayload
'@
$text=$text.Replace($readSampleLine,$readSampleReplacement.TrimEnd())
$text=$text.Replace("`$publishPaths=@(`$visibleRowsRel,`$visibleStatusRel,`$operationsRel,`$sourceRel,`$sampleRel)-join'|'","`$publishPaths=@(`$visibleRowsRel,`$visibleStatusRel,`$operationsRel,`$sourceRel,`$sampleRel,`$sampleWebRel)-join'|'")

$oldReadback=@'
  $siteRows=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json' -TimeoutSec 60
  $siteOps=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json' -TimeoutSec 60
  $siteSamples=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/docs/chatgpt_status/topography/fixtures/topography_public_copdem_cog_samples_20260713.json' -TimeoutSec 60
  if($siteRows.StatusCode -ne 200 -or $siteOps.StatusCode -ne 200 -or $siteSamples.StatusCode -ne 200){throw 'TOPOGRAPHY_164_SITE_HTTP_READBACK_FAILED'}
  if($siteRows.Content -notmatch [regex]::Escape($taskId) -or $siteOps.Content -notmatch [regex]::Escape($taskId)){throw 'TOPOGRAPHY_164_TASK_ID_NOT_VISIBLE'}
'@
$newReadback=@'
  $sampleSourcePath=Repo-Path $sampleWebRel
  if(-not(Test-Path -LiteralPath $sampleSourcePath)){throw 'TOPOGRAPHY_164_SAMPLE_WEB_ARTIFACT_NOT_CREATED'}
  if($env:AAYS_CONTROLLER_REPO_ROOT){
    $controllerSamplePath=Join-Path ([string]$env:AAYS_CONTROLLER_REPO_ROOT) ($sampleWebRel-replace'/','\')
    if(-not(Test-Path -LiteralPath $controllerSamplePath)){
      $controllerParent=Split-Path -Parent $controllerSamplePath;if(-not(Test-Path -LiteralPath $controllerParent)){New-Item -ItemType Directory -Force -Path $controllerParent|Out-Null}
      Copy-Item -LiteralPath $sampleSourcePath -Destination $controllerSamplePath -Force
    }
  }
  $portableSamplePath=Join-Path $portableRoot ('AAYS\'+($sampleWebRel-replace'/','\'))
  if(Test-Path -LiteralPath (Join-Path $portableRoot 'AAYS\england_map_web')){
    if(-not(Test-Path -LiteralPath $portableSamplePath)){
      $portableParent=Split-Path -Parent $portableSamplePath;if(-not(Test-Path -LiteralPath $portableParent)){New-Item -ItemType Directory -Force -Path $portableParent|Out-Null}
      Copy-Item -LiteralPath $sampleSourcePath -Destination $portableSamplePath -Force
    }
  }
  $siteRows=$null;$siteOps=$null;$siteSamples=$null;$lastReadbackError=$null
  for($attempt=1;$attempt -le 12;$attempt++){
    try{
      $cache=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
      $siteRows=Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json?readback=$cache" -TimeoutSec 60
      $siteOps=Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json?readback=$cache" -TimeoutSec 60
      $siteSamples=Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_public_copdem_cog_samples_latest.json?readback=$cache" -TimeoutSec 60
      if($siteRows.StatusCode -eq 200 -and $siteOps.StatusCode -eq 200 -and $siteSamples.StatusCode -eq 200){break}
    }catch{$lastReadbackError=$_.Exception.Message}
    Start-Sleep -Seconds 5
  }
  if($null -eq $siteRows -or $null -eq $siteOps -or $null -eq $siteSamples -or $siteRows.StatusCode -ne 200 -or $siteOps.StatusCode -ne 200 -or $siteSamples.StatusCode -ne 200){throw ('TOPOGRAPHY_164_SITE_HTTP_READBACK_FAILED:'+([string]$lastReadbackError))}
  if($siteRows.Content -notmatch [regex]::Escape($taskId) -or $siteOps.Content -notmatch [regex]::Escape($taskId) -or $siteSamples.Content -notmatch [regex]::Escape($taskId)){throw 'TOPOGRAPHY_164_TASK_ID_NOT_VISIBLE'}
'@
$text=$text.Replace($oldReadback.Trim(),$newReadback.Trim())

if($text.Contains('(if(')){throw 'TOPOGRAPHY_164_V4_INLINE_IF_REPAIR_INCOMPLETE'}
if(-not $text.Contains('topography_public_copdem_cog_samples_latest.json')){throw 'TOPOGRAPHY_164_V4_SAMPLE_WEB_PATCH_INCOMPLETE'}
if(-not $text.Contains('TOPOGRAPHY_164_SAMPLE_WEB_ARTIFACT_NOT_CREATED')){throw 'TOPOGRAPHY_164_V4_READBACK_PATCH_INCOMPLETE'}

$tempRoot=Join-Path ([System.IO.Path]::GetTempPath()) 'aays_topography_164_v4'
if(-not(Test-Path -LiteralPath $tempRoot)){New-Item -ItemType Directory -Force -Path $tempRoot|Out-Null}
$patched=Join-Path $tempRoot '164_topography_public_copdem_cog_sampling_runner_patched_v4.ps1'
[System.IO.File]::WriteAllText($patched,$text,[System.Text.UTF8Encoding]::new($false))

& powershell -NoProfile -ExecutionPolicy Bypass -File $patched
$code=$LASTEXITCODE
if($code -ne 0){throw "TOPOGRAPHY_164_V4_PATCHED_SCRIPT_EXIT_$code"}
