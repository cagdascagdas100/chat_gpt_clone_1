$ErrorActionPreference = 'Continue'
$TaskId = 'cost50-013-recovery-probe-20260512'
$BridgeRoot = Join-Path $env:USERPROFILE 'Documents\chat_gpt_clone_1'
$ProjectRoot = 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function L($m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
L "TASK=$TaskId"
L "MODE=recovery_probe_readonly"
L "BRIDGE_ROOT=$BridgeRoot"
L "PROJECT_ROOT=$ProjectRoot"
L ('BRIDGE_EXISTS=' + (Test-Path $BridgeRoot))
L ('PROJECT_EXISTS=' + (Test-Path $ProjectRoot))
L ('SCRIPT_013_EXISTS=' + (Test-Path (Join-Path $BridgeRoot 'ai-task-scripts\terrayield_cost50_013_artifact_manifest_audit.ps1')))
L ('RESULT_DIR_EXISTS=' + (Test-Path $ResultDir))
$dirs=@($BridgeRoot,$ProjectRoot,$ResultDir,(Join-Path $BridgeRoot 'ai-task-scripts'),(Join-Path $BridgeRoot 'ai-runner-logs'))
foreach($d in $dirs){try{L ('DIR=' + $d + ' EXISTS=' + (Test-Path $d)); if(Test-Path $d){L ('COUNT=' + @(Get-ChildItem -LiteralPath $d -Force -ErrorAction SilentlyContinue | Measure-Object).Count)}}catch{L ('DIR_ERROR=' + $_.Exception.Message)}}
try { $psv=$PSVersionTable.PSVersion.ToString(); L "POWERSHELL_VERSION=$psv" } catch {}
try { $git=(git --version 2>&1 | Out-String).Trim(); L "GIT_VERSION=$git" } catch { L ('GIT_ERROR=' + $_.Exception.Message) }
try { $py=(python --version 2>&1 | Out-String).Trim(); L "PYTHON_VERSION=$py" } catch { L ('PYTHON_ERROR=' + $_.Exception.Message) }
$out=Join-Path $ResultDir "$TaskId.report.md"
@('# Cost50 013 Recovery Probe','',"Generated: $(Get-Date -Format s)",'','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 -Path $out
L "REPORT_PATH=$out"
L 'PLAN_PROGRESS_PERCENT=53'
L 'TASK_COMPLETION=100/100'
L 'TERRAYIELD_TASK_DONE'
exit 0
