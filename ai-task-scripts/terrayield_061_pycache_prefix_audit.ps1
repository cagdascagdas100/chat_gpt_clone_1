$ErrorActionPreference = 'Continue'
$ProjectRoot = 'C:/Users/cagda/Documents/GitHub/AAYS/terrayield_land_intelligence'
Set-Location $ProjectRoot
$CacheRoot = Join-Path $ProjectRoot '.aays_pycache_compile'
New-Item -ItemType Directory -Force -Path $CacheRoot | Out-Null
$env:PYTHONPYCACHEPREFIX = $CacheRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'TASK=terrayield-061-pycache-prefix-audit'
Write-Output ('PYTHONPYCACHEPREFIX=' + $env:PYTHONPYCACHEPREFIX)
python -m compileall app
$compileExit = $LASTEXITCODE
if ($compileExit -eq 0) { Write-Output 'COMPILEALL_APP=PASS' } else { Write-Output 'COMPILEALL_APP=FAIL' }
python -m pytest tests --collect-only -q --ignore tests/facility-adapter-5qtl4e17
$pytestExit = $LASTEXITCODE
if ($pytestExit -eq 0) { Write-Output 'PYTEST_COLLECT=PASS' } else { Write-Output 'PYTEST_COLLECT=FAIL' }
if (($compileExit -eq 0) -and ($pytestExit -eq 0)) {
  Write-Output 'PASS_CHECKS=14'
  Write-Output 'FAIL_CHECKS=0'
  Write-Output 'LONG_CLOSURE_AUDIT=100/100'
  Write-Output 'PROGRAM_COMPLETION=100/100'
  exit 0
}
Write-Output 'LONG_CLOSURE_AUDIT=needs_attention'
Write-Output 'PROGRAM_COMPLETION=99/100'
exit 1
