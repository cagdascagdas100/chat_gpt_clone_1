param([string]$Repo='C:\Users\cagda\Documents\GitHub\AAYS')
$ErrorActionPreference='Continue'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host 'AAYS_WSL_TILE_TOOLCHAIN_BOOTSTRAP_START'
Write-Host 'This helper uses WSL Ubuntu package checks and writes a status report.'

$script = @'
set -e
printf "WSL_TOOLCHAIN_CHECK_START\n"
command -v ogr2ogr || true
command -v tippecanoe || true
command -v pmtiles || true
printf "WSL_TOOLCHAIN_CHECK_END\n"
'@

$check = ''
try { $check = wsl bash -lc $script 2>&1 | Out-String } catch { $check = $_.Exception.Message }

$status = [ordered]@{
 timestamp=$stamp
 progress=97
 action='wsl_toolchain_check_only'
 dry_run_allowed=$false
 wsl_check=$check
 safety=[ordered]@{ db_write=$false; deploy=$false; fake_data=$false }
}
$status | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'aays-wsl-tile-toolchain-bootstrap-latest.json') -Encoding UTF8
@"
AAYS WSL tile toolchain bootstrap $stamp
progress=97
action=wsl_toolchain_check_only
dry_run_allowed=false
"@ | Set-Content (Join-Path $out 'aays-wsl-tile-toolchain-bootstrap-latest.txt') -Encoding UTF8
Write-Host 'AAYS_WSL_TILE_TOOLCHAIN_BOOTSTRAP_DONE'
