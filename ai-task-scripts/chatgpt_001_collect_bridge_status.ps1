$ErrorActionPreference = 'Continue'

$bridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$projectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$resultDir = Join-Path $bridgeRoot 'ai-results'
$resultPath = Join-Path $resultDir "chatgpt-001-collect-bridge-status-$timestamp.md"

New-Item -ItemType Directory -Force -Path $resultDir | Out-Null

function Add-Section {
    param(
        [string]$Title,
        [scriptblock]$Body
    )
    Add-Content -Encoding UTF8 -Path $resultPath -Value "`n## $Title`n"
    Add-Content -Encoding UTF8 -Path $resultPath -Value '```text'
    try {
        & $Body 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $resultPath
    } catch {
        $_ | Out-String | Add-Content -Encoding UTF8 -Path $resultPath
    }
    Add-Content -Encoding UTF8 -Path $resultPath -Value '```'
}

Set-Content -Encoding UTF8 -Path $resultPath -Value "# ChatGPT Task 001 - Bridge Status Collection`n`nTime: $timestamp`nBridgeRoot: $bridgeRoot`nProjectRoot: $projectRoot`nTaskType: read-only status collection"

Add-Section 'Bridge Git Status' { Set-Location $bridgeRoot; git status --short; git status -sb }
Add-Section 'Bridge Root Files' { Get-ChildItem -Force $bridgeRoot | Select-Object Mode, LastWriteTime, Length, Name | Format-Table -AutoSize }
Add-Section 'Related Processes' { Get-Process powershell,pwsh,git,node,npm,python -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, CPU, StartTime | Format-Table -AutoSize }
Add-Section 'Heartbeat Files' { Get-ChildItem -Force (Join-Path $bridgeRoot 'ai-heartbeat') -ErrorAction SilentlyContinue | Select-Object Mode, LastWriteTime, Length, Name | Format-Table -AutoSize }
Add-Section 'Recent Result Files' { Get-ChildItem -Force (Join-Path $bridgeRoot 'ai-results') -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Mode, LastWriteTime, Length, Name | Format-Table -AutoSize }
Add-Section 'Current Task File' { Get-Content -Raw (Join-Path $bridgeRoot 'ai-tasks\current-task.json') -ErrorAction SilentlyContinue }
Add-Section 'Project Git Status' { if (Test-Path $projectRoot) { Set-Location $projectRoot; git status -sb; git status --short } else { "ProjectRoot not found: $projectRoot" } }
Add-Section 'Project Root Files' { if (Test-Path $projectRoot) { Get-ChildItem -Force $projectRoot | Select-Object Mode, LastWriteTime, Length, Name | Format-Table -AutoSize } else { "ProjectRoot not found: $projectRoot" } }

Add-Content -Encoding UTF8 -Path $resultPath -Value "`nNEXT_COMMAND=devam et`n"

Set-Location $bridgeRoot

git add ai-results ai-heartbeat ai-tasks ai-task-scripts 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $resultPath
git add $resultPath 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $resultPath
git commit -m "Add ChatGPT bridge status collection result" 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $resultPath
git push 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $resultPath
