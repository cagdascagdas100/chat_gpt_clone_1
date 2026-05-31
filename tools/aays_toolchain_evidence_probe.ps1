param([string]$Repo='C:\Users\cagda\Documents\GitHub\AAYS')
$ErrorActionPreference='Stop'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
New-Item -ItemType Directory -Force -Path $out | Out-Null
function which($n){ try { (Get-Command $n -ErrorAction Stop).Source } catch { 'NOT_FOUND' } }
$tools=[ordered]@{
 tippecanoe=which 'tippecanoe'
 pmtiles=which 'pmtiles'
 ogr2ogr=which 'ogr2ogr'
 docker=which 'docker'
 python=which 'python'
 git=which 'git'
 wsl=which 'wsl'
}
$dockerImages=''
try { $dockerImages=(docker image ls --format '{{.Repository}}:{{.Tag}}' | Select-Object -First 80) -join "`n" } catch { $dockerImages='DOCKER_IMAGE_LIST_FAILED' }
$regions=@('london','south_east','south_west','midlands','north','wales','scotland')
$assets=@()
foreach($r in $regions){
 $base=Join-Path $Repo "england_map_web\data\inspire\region_jobs\$r"
 $assets += [ordered]@{ region=$r; pmtiles=(Test-Path (Join-Path $base 'tiles\parcels.pmtiles')); gpkg=(Test-Path (Join-Path $base 'source\parcels_source.gpkg')); parquet=(Test-Path (Join-Path $base 'parcels_prepared_simplified.parquet')) }
}
$result=[ordered]@{ timestamp=$stamp; progress=96; tools=$tools; docker_images=$dockerImages; assets=$assets; dry_run_allowed=$false; safety=[ordered]@{ db_write=$false; deploy=$false; fake_data=$false } }
$json=$result|ConvertTo-Json -Depth 8
$json|Set-Content (Join-Path $out 'aays-toolchain-evidence-probe-latest.json') -Encoding UTF8
"AAYS toolchain evidence probe $stamp`nprogress=96`ndry_run_allowed=false"|Set-Content (Join-Path $out 'aays-toolchain-evidence-probe-latest.txt') -Encoding UTF8
Write-Host 'AAYS_TOOLCHAIN_EVIDENCE_PROBE_DONE'
