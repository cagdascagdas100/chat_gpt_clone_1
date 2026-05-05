$ErrorActionPreference='Continue'
$TaskId='terrayield-061-runner-canary-now'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Dir=Join-Path $Root ".aays_next_fix\061_runner_canary_now_$Run"
New-Item -ItemType Directory -Force -Path $Dir|Out-Null
$Out=Join-Path $Dir 'canary.txt'
@('TASK='+$TaskId,'RESULT=canary_ok','TIME='+(Get-Date -Format 's'),'BRIDGE='+$Bridge,'ROOT='+$Root)|Set-Content -Encoding UTF8 $Out
Write-Output "CANARY_FILE=$Out"
Write-Output 'TERRAYIELD_061_RUNNER_CANARY_NOW_DONE'
exit 0
