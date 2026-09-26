param(
    [string]$InstallRoot = 'C:\AAYS_Producer',
    [string]$Repository = 'cagdascagdas100/chat_gpt_clone_1',
    [string]$Branch = 'main'
)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'aays_github_producer_uploader.py'
if (-not (Test-Path -LiteralPath $source)) {
    throw "Uploader not found: $source"
}

$python = (Get-Command python.exe -ErrorAction Stop).Source
$outbox = Join-Path $InstallRoot 'outbox'
$sent = Join-Path $InstallRoot 'sent'
$rejected = Join-Path $InstallRoot 'rejected'
$logs = Join-Path $InstallRoot 'logs'
$script = Join-Path $InstallRoot 'aays_github_producer_uploader.py'
foreach ($path in @($InstallRoot, $outbox, $sent, $rejected, $logs)) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
}
Copy-Item -LiteralPath $source -Destination $script -Force

$launcher = Join-Path $InstallRoot 'run-aays-producer.ps1'
$launcherText = @"
`$ErrorActionPreference = 'Stop'
& '$python' '$script' --outbox '$outbox' --sent '$sent' --rejected '$rejected' --repository '$Repository' --branch '$Branch' *>> '$(Join-Path $logs 'producer.log')'
"@
Set-Content -LiteralPath $launcher -Value $launcherText -Encoding UTF8

$taskName = 'AAYS Producer Uploader'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$launcher`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Validates AAYS packages and uploads them to GitHub.' -Force | Out-Null

$result = [ordered]@{
    installed = $true
    install_root = $InstallRoot
    outbox = $outbox
    task_name = $taskName
    credential_ready = [bool]((Get-Command gh.exe -ErrorAction SilentlyContinue) -and (& gh auth status 2>$null))
    next_action = 'Set the browser AAYS download directory to the outbox. Authenticate GitHub CLI once if credential_ready is false.'
}
$result | ConvertTo-Json -Depth 3
