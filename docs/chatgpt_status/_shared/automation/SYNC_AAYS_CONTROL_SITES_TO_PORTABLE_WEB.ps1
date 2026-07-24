[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$portableRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$publisherRepo = Join-Path $portableRoot "runner_system\adaptive_v2\publisher"
$legacyRunnerRepo = Join-Path $portableRoot "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
$runnerRepo = if (Test-Path -LiteralPath (Join-Path $publisherRepo ".git")) { $publisherRepo } else { $legacyRunnerRepo }
$webRoot = Join-Path $portableRoot "AAYS\england_map_web"
$manifestDir = Join-Path $webRoot "data\control_sites"
New-Item -ItemType Directory -Force -Path $manifestDir | Out-Null

function New-Result($id,$source,$destination,$ok,$errorText,$checked,$updated) {
  [ordered]@{ id=$id; source=$source; destination=$destination; ok=[bool]$ok; error=$errorText; files_checked=[int]$checked; files_updated=[int]$updated }
}
function Copy-FileIfChanged($Source,$Destination,$Id) {
  try {
    if (-not (Test-Path -LiteralPath $Source)) { return New-Result $Id $Source $Destination $false "Missing source file" 0 0 }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    $s=Get-Item -LiteralPath $Source; $copy=$true
    if(Test-Path -LiteralPath $Destination){$d=Get-Item -LiteralPath $Destination; $copy=($d.Length -ne $s.Length) -or ($d.LastWriteTimeUtc -lt $s.LastWriteTimeUtc.AddSeconds(-1))}
    if($copy){Copy-Item -LiteralPath $Source -Destination $Destination -Force}
    return New-Result $Id $Source $Destination $true $null 1 ($(if($copy){1}else{0}))
  } catch { return New-Result $Id $Source $Destination $false $_.Exception.Message 0 0 }
}
function Copy-DirectoryFilesIfChanged($SourceDir,$DestinationDir,$Id) {
  try {
    if (-not (Test-Path -LiteralPath $SourceDir)) { return New-Result $Id $SourceDir $DestinationDir $false "Missing source directory" 0 0 }
    New-Item -ItemType Directory -Force -Path $DestinationDir | Out-Null
    $args = @($SourceDir,$DestinationDir,"*.*","/E","/XO","/FFT","/R:1","/W:1","/COPY:DAT","/DCOPY:DAT","/NP","/NFL","/NDL","/NJH","/NJS")
    $proc = Start-Process -FilePath "$env:SystemRoot\System32\robocopy.exe" -ArgumentList $args -WindowStyle Hidden -Wait -PassThru
    if ($proc.ExitCode -gt 7) { return New-Result $Id $SourceDir $DestinationDir $false "ROBOCOPY_EXIT_$($proc.ExitCode)" 0 0 }
    return New-Result $Id $SourceDir $DestinationDir $true $null 0 ($(if($proc.ExitCode -ge 1){1}else{0}))
  } catch { return New-Result $Id $SourceDir $DestinationDir $false $_.Exception.Message 0 0 }
}function Expose-ChunkFiles($SourceDir,$DestinationDir,$Id) {
  try {
    if (-not (Test-Path -LiteralPath (Join-Path $SourceDir "manifest.json"))) { return New-Result $Id $SourceDir $DestinationDir $false "Missing source chunks" 0 0 }
    New-Item -ItemType Directory -Force -Path $DestinationDir | Out-Null
    $checked=0; $updated=0
    Get-ChildItem -LiteralPath $SourceDir -File | ForEach-Object {
      $checked++; $dest=Join-Path $DestinationDir $_.Name
      if(Test-Path -LiteralPath $dest){ return }
      try { New-Item -ItemType HardLink -Path $dest -Target $_.FullName | Out-Null }
      catch { Copy-Item -LiteralPath $_.FullName -Destination $dest -Force }
      $updated++
    }
    return New-Result $Id $SourceDir $DestinationDir $true $null $checked $updated
  } catch { return New-Result $Id $SourceDir $DestinationDir $false $_.Exception.Message 0 0 }
}

$results=@()
$matrixHtml=Join-Path $runnerRepo "england_map_web\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html"
if(-not(Test-Path -LiteralPath $matrixHtml)){$matrixHtml=Join-Path $runnerRepo "outputs\england_program_parcel_matrix_20260629\TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html"}
$results += Copy-FileIfChanged $matrixHtml (Join-Path $webRoot "TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html") "program_parcel_layer_matrix_html"
$results += Copy-FileIfChanged (Join-Path $runnerRepo "england_map_web\geometry_review_3of4_columns_1264.html") (Join-Path $webRoot "geometry_review_3of4_columns_1264.html") "geometry_review_html"
$results += Copy-FileIfChanged (Join-Path $runnerRepo "england_map_web\internet_access_overlay.js") (Join-Path $webRoot "internet_access_overlay.js") "internet_access_overlay"

foreach($dir in @("program_layer_matrix","distance_property_types","security_public_safety","geometry_review_3of4","aays1")){
  $results += Copy-DirectoryFilesIfChanged (Join-Path $runnerRepo "england_map_web\data\$dir") (Join-Path $webRoot "data\$dir") "data_$dir"
}
$chunkSource=Join-Path $runnerRepo "england_map_web\chunks"
if(-not(Test-Path -LiteralPath (Join-Path $chunkSource "manifest.json"))){$chunkSource=Join-Path $runnerRepo "outputs\england_program_parcel_matrix_20260629\chunks"}
if(-not(Test-Path -LiteralPath (Join-Path $chunkSource "manifest.json"))){$chunkSource=Join-Path $webRoot "chunks"}
$results += Expose-ChunkFiles $chunkSource (Join-Path $webRoot "chunks") "matrix_chunks"

$updateBase=Join-Path $runnerRepo "outputs\england_program_parcel_matrix_20260629"
$legacyUpdateBase=Join-Path $legacyRunnerRepo "outputs\england_program_parcel_matrix_20260629"
foreach($dir in @("security_public_safety_updates","gas_emissions_updates","internet_access_updates","topography_updates")){
  $updateSource = Join-Path $updateBase $dir
  if (-not (Test-Path -LiteralPath $updateSource)) { $updateSource = Join-Path $legacyUpdateBase $dir }
  $results += Copy-DirectoryFilesIfChanged $updateSource (Join-Path $webRoot $dir) $dir
}
$results += Copy-FileIfChanged (Join-Path $runnerRepo "docs\chatgpt_status\aays1\geometry_review_3of4\all_1264_real_geometry_3of4.geojson") (Join-Path $webRoot "data\geometry_review_3of4\all_1264_real_geometry_3of4.geojson") "geometry_review_geojson"

$runnerPanelData=Join-Path $webRoot "data\runner_panel"
$results += Copy-FileIfChanged (Join-Path $runnerRepo "docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json") (Join-Path $runnerPanelData "stable_runner_daemon_heartbeat_latest.json") "runner_heartbeat"
$results += Copy-FileIfChanged (Join-Path $runnerRepo "docs\chatgpt_status\_shared\locks\single_runner.lock") (Join-Path $runnerPanelData "single_runner.lock.json") "runner_lock"
$results += Copy-FileIfChanged (Join-Path $runnerRepo "docs\chatgpt_status\_shared\status\runner_bootstrap_latest.json") (Join-Path $runnerPanelData "runner_bootstrap_latest.json") "runner_bootstrap"
$results += Copy-FileIfChanged (Join-Path $runnerRepo "docs\chatgpt_status\_shared\runner_outputs\one_click_runner_self_test_latest.json") (Join-Path $runnerPanelData "one_click_runner_self_test_latest.json") "runner_self_test"

$manifest=[ordered]@{
  updated_at=(Get-Date).ToUniversalTime().ToString("o")
  portable_root=$portableRoot
  runner_repo=$runnerRepo
  web_root=$webRoot
  fixed_base_url="http://127.0.0.1:8012"
  control_sites=@(
    [ordered]@{id="program_parcel_layer_matrix";url="http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html"},
    [ordered]@{id="geometry_review_3of4_1264";url="http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html"}
  )
  sync_results=$results
}
$manifestPath=Join-Path $manifestDir "control_sites_manifest_latest.json"
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$manifest | ConvertTo-Json -Depth 8
