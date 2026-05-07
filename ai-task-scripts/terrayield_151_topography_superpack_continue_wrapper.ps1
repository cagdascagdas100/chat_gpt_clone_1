$ErrorActionPreference='Continue'
Write-Output 'TASK_ID=terrayield-151-topography-superpack-continue-wrapper'
$script='C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_150_topography_superpack_continue.ps1'
if(!(Test-Path $script)){Write-Output "MISSING_CHAINED_SCRIPT=$script";exit 2}
& powershell -NoProfile -ExecutionPolicy Bypass -File $script
$code=$LASTEXITCODE
Write-Output "CHAINED_EXIT_CODE=$code"
Write-Output 'TERRAYIELD_TASK_DONE'
exit $code
