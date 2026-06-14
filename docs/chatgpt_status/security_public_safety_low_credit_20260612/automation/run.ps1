$root = Split-Path -Parent $PSScriptRoot
$status = Join-Path $root 'status/security_shared_runner_task_latest.md'
$content = @'
state: script_reached
percent: 99
final: false
reason: needs final browser proof
'@
Set-Content -Path $status -Value $content -Encoding UTF8
Write-Output 'security runner wrapper reached'
