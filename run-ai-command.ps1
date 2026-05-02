param(
    [Parameter(Mandatory = $true)]
    [string]$Command
)

$ErrorActionPreference = "Continue"

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logPath = "ai-logs/run-$timestamp.md"

New-Item -ItemType Directory -Force -Path "ai-logs" | Out-Null

$output = powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1 | Out-String
$status = git status | Out-String
$now = Get-Date
$path = Get-Location

$content = @"
# AI Command Log

## Time
$now

## Path
$path

## Command

$Command

## Output

$output

## Git Status

$status
"@

$content | Set-Content -Encoding UTF8 $logPath

git add $logPath
git commit -m "Add AI command log $timestamp"
git push
