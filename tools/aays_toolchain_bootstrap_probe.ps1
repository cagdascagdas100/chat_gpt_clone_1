param([string]$Repo='C:\Users\cagda\Documents\GitHub\AAYS')
$ErrorActionPreference='Continue'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
New-Item -ItemType Directory -Force -Path $out | Out-Null
function cmdpath($n){ try { (Get-Command $n -ErrorAction Stop).Source } catch { 'NOT_FOUND' } }
$report=[ordered]@{
 timestamp=$stamp
 winget=cmdpath 'winget'
 docker=cmdpath 'docker'
 wsl=cmdpath 'wsl'
 tippecanoe=cmdpath 'tippecanoe'
 pmtiles=cmdpath 'pmtiles'
 ogr2ogr=cmdpath 'ogr2ogr'
 docker_version=''
 wsl_status=''
 decision='PROBE_ONLY_NO_INSTALL'
 progress=97
 dry_run_allowed=$false
 safety=[ordered]@{db_write=$false; deploy=$false; fake_data=$false}
}
try { $report.docker_version=(docker --version) } catch { $report.docker_version='DOCKER_VERSION_FAILED' }
try { $report.wsl_status=(wsl --status | Out-String).Trim() } catch { $report.wsl_status='WSL_STATUS_FAILED' }
$report | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'aays-toolchain-bootstrap-probe-latest.json') -Encoding UTF8
@"
AAYS toolchain bootstrap probe $stamp
progress=97
decision=PROBE_ONLY_NO_INSTALL
dry_run_allowed=false
"@ | Set-Content (Join-Path $out 'aays-toolchain-bootstrap-probe-latest.txt') -Encoding UTF8
Write-Host 'AAYS_TOOLCHAIN_BOOTSTRAP_PROBE_DONE'
