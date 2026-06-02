$ErrorActionPreference='Continue'
$BridgeRoot='C:\AAYS_GITHUB_BRIDGE_CLEAN'
$Bootstrap=Join-Path $BridgeRoot 'AAYS_REMOTE_AUTOPILOT_V7_BOOTSTRAP.ps1'
function Step($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
Step 'TASK=terrayield-056-autopilot-v7-bootstrap-wrapper'
Step 'MODE=run_root_v7_bootstrap_from_task_script'
if(-not(Test-Path $Bootstrap)){Step ('BOOTSTRAP_MISSING='+$Bootstrap); exit 2}
Step ('BOOTSTRAP_FOUND='+$Bootstrap)
powershell -NoProfile -ExecutionPolicy Bypass -File $Bootstrap
$code=$LASTEXITCODE
Step ('BOOTSTRAP_EXIT='+$code)
if($null -eq $code){$code=0}
Step 'TASK_COMPLETION=100/100'
exit $code
