[CmdletBinding()]
param(
  [string]$CanonicalPoints='docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_canonical_points_latest.json',
  [string]$OfficialDiscovery='docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_official_discovery_latest.json',
  [string]$BoundaryManifest='docs/chatgpt_status/height_difference/runner_inputs/height_difference_3_hmlr_boundary_manifest_latest.json',
  [string]$RasterManifest='docs/chatgpt_status/height_difference/runner_inputs/height_difference_3_raster_manifest_latest.json',
  [string]$Output='docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_boundary_raster_sampling_latest.json',
  [string]$WebsiteOutput='england_map_web/data/height_difference/height_difference_3_boundary_raster_sampling_latest.json'
)
$ErrorActionPreference='Stop'
$root=[System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not $root){throw 'AAYS_REPO_ROOT_REQUIRED'}
$script=Join-Path $root 'docs\chatgpt_status\height_difference\automation\height_difference_3_boundary_raster_sampling_v1.py'
if(-not(Test-Path -LiteralPath $script)){throw 'HEIGHT_DIFFERENCE_3_BOUNDARY_RASTER_SCRIPT_NOT_FOUND'}
$python=$null;$prefix=@()
$c=Get-Command python -ErrorAction SilentlyContinue;if($c){$python=$c.Source}
if(-not $python){$c=Get-Command py -ErrorAction SilentlyContinue;if($c){$python=$c.Source;$prefix=@('-3')}}
if(-not $python){$c=Get-Command python3 -ErrorAction SilentlyContinue;if($c){$python=$c.Source}}
if(-not $python){throw 'PYTHON_NOT_AVAILABLE'}
$resolve={param([string]$p) if([System.IO.Path]::IsPathRooted($p)){$p}else{Join-Path $root ($p.Replace('/','\'))}}
$args=@(
  $script,
  '--canonical-points',(& $resolve $CanonicalPoints),
  '--official-discovery',(& $resolve $OfficialDiscovery),
  '--boundary-manifest',(& $resolve $BoundaryManifest),
  '--raster-manifest',(& $resolve $RasterManifest),
  '--output',(& $resolve $Output),
  '--website-output',(& $resolve $WebsiteOutput),
  '--expected-blob-sha','bb48164e7a0af78df875f30421a6a3068c43edb8'
)
& $python @prefix @args
exit $LASTEXITCODE