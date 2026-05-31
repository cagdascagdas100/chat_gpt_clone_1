param([string]$Repo='C:\Users\cagda\Documents\GitHub\AAYS')
$ErrorActionPreference='Continue'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
New-Item -ItemType Directory -Force -Path $out | Out-Null
function which($n){ try { (Get-Command $n -ErrorAction Stop).Source } catch { 'NOT_FOUND' } }
function wslwhich($n){ try { $v=(wsl bash -lc "command -v $n" 2>$null | Select-Object -First 1); if([string]::IsNullOrWhiteSpace($v)){'NOT_FOUND'}else{$v.Trim()} } catch { 'NOT_FOUND' } }
$tools=[ordered]@{
 tippecanoe=which 'tippecanoe'
 pmtiles=which 'pmtiles'
 ogr2ogr=which 'ogr2ogr'
 docker=which 'docker'
 python=which 'python'
 git=which 'git'
 wsl=which 'wsl'
 wsl_tippecanoe=wslwhich 'tippecanoe'
 wsl_pmtiles=wslwhich 'pmtiles'
 wsl_ogr2ogr=wslwhich 'ogr2ogr'
}
$dockerImages=''
try { $dockerImages=(docker image ls --format '{{.Repository}}:{{.Tag}}' | Select-Object -First 80) -join "`n" } catch { $dockerImages='DOCKER_IMAGE_LIST_FAILED' }
$regions=@('east','london','south_east','south_west','midlands','north','wales','scotland')
$assets=@()
foreach($r in $regions){
 $base=Join-Path $Repo "england_map_web\data\inspire\region_jobs\$r"
 $assets += [ordered]@{ region=$r; pmtiles=(Test-Path (Join-Path $base 'tiles\parcels.pmtiles')); gpkg=(Test-Path (Join-Path $base 'source\parcels_source.gpkg')); parquet=(Test-Path (Join-Path $base 'parcels_prepared_simplified.parquet')); path=$base }
}
$bedfordshireParquet=Join-Path $Repo 'regions\bedfordshire\parcels_prepared.parquet'
$bedfordshirePmtiles=Join-Path $Repo 'tiles\bedfordshire\parcels.pmtiles'
$assets += [ordered]@{ region='bedfordshire'; pmtiles=(Test-Path $bedfordshirePmtiles); gpkg=$false; parquet=(Test-Path $bedfordshireParquet); path=(Join-Path $Repo 'regions\bedfordshire') }
$winReady=($tools.tippecanoe -ne 'NOT_FOUND' -and $tools.pmtiles -ne 'NOT_FOUND' -and $tools.ogr2ogr -ne 'NOT_FOUND')
$wslReady=($tools.wsl_tippecanoe -ne 'NOT_FOUND' -and $tools.wsl_pmtiles -ne 'NOT_FOUND' -and $tools.wsl_ogr2ogr -ne 'NOT_FOUND')
$toolchainReady=($winReady -or $wslReady)
$sourceReady=@($assets | Where-Object { $_.gpkg -or $_.parquet }).Count -gt 0
$dryRunAllowed=($toolchainReady -and $sourceReady)
$progress=97
if($dryRunAllowed){$progress=98}
$result=[ordered]@{ timestamp=$stamp; progress=$progress; runner_recovered=$true; windows_toolchain_ready=$winReady; wsl_toolchain_ready=$wslReady; toolchain_ready=$toolchainReady; source_ready=$sourceReady; bedfordshire_source_ready=(Test-Path $bedfordshireParquet); tools=$tools; docker_images=$dockerImages; assets=$assets; dry_run_allowed=$dryRunAllowed; safety=[ordered]@{ db_write=$false; deploy=$false; fake_data=$false } }
$json=$result|ConvertTo-Json -Depth 8
$json|Set-Content (Join-Path $out 'aays-toolchain-evidence-probe-latest.json') -Encoding UTF8
"AAYS toolchain evidence probe $stamp`nprogress=$progress`nrunner_recovered=true`ntoolchain_ready=$toolchainReady`nsource_ready=$sourceReady`nbedfordshire_source_ready=$(Test-Path $bedfordshireParquet)`ndry_run_allowed=$dryRunAllowed"|Set-Content (Join-Path $out 'aays-toolchain-evidence-probe-latest.txt') -Encoding UTF8
Write-Host 'AAYS_TOOLCHAIN_EVIDENCE_PROBE_DONE'
