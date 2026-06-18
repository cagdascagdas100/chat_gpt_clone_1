$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $here "security_public_safety_page6_4_single_runner_task.ps1"
if (-not (Test-Path $target)) {
  throw "Target script not found: $target"
}
& powershell -NoProfile -ExecutionPolicy Bypass -File $target
