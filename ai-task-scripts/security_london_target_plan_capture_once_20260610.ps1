$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportRel = "ai-results/security_london_target_plan_runner_$Stamp.txt"
$LatestRel = 'ai-results/security_london_target_plan_runner_latest.txt'
$Report = Join-Path $BridgeRoot ($ReportRel -replace '/', '\')
$Latest = Join-Path $BridgeRoot ($LatestRel -replace '/', '\')
$ScriptRel = 'ai-task-scripts/security_asayis_london_official_target_plan_20260610.ps1'
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
New-Item -ItemType Directory -Force -Path (Join-Path $BridgeRoot 'ai-results') | Out-Null
function Log($x){ [System.IO.File]::AppendAllText($Report, ([string]$x) + [Environment]::NewLine, $Utf8NoBom); Write-Host $x }
[System.IO.File]::WriteAllText($Report, "SECURITY_LONDON_TARGET_PLAN_CAPTURE_ONCE $Stamp" + [Environment]::NewLine, $Utf8NoBom)
Log "BridgeRoot=$BridgeRoot"
if (-not (Test-Path $BridgeRoot)) { Log "BRIDGE_ROOT_MISSING"; exit 2 }
Set-Location $BridgeRoot
Log '=== git sync ==='
git fetch origin main 2>&1 | ForEach-Object { Log $_ }
git reset --hard origin/main 2>&1 | ForEach-Object { Log $_ }
Log '=== run target plan script ==='
if (Test-Path $ScriptRel) {
  powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptRel 2>&1 | ForEach-Object { Log $_ }
  Log "TARGET_PLAN_EXIT_CODE=$LASTEXITCODE"
} else { Log "TARGET_PLAN_SCRIPT_MISSING=$ScriptRel" }
Log '=== expected outputs ==='
$Expected = @(
  'ai-results/security_london_official_target_plan_latest.json',
  'ai-results/security_london_official_target_plan_latest.md',
  'docs/chatgpt_status/security_london_official_target_plan_status_20260610.md'
)
$Add = @($ReportRel, $LatestRel)
foreach($p in $Expected){ if(Test-Path $p){ Log "EXISTS $p size=$((Get-Item $p).Length)"; $Add += $p } else { Log "MISSING $p" } }
Copy-Item $Report $Latest -Force
foreach($p in ($Add | Select-Object -Unique)){ if(Test-Path $p){ git add $p 2>&1 | ForEach-Object { Log $_ } } }
git commit -m "Add security London target plan output $Stamp" 2>&1 | ForEach-Object { Log $_ }
git push origin main 2>&1 | ForEach-Object { Log $_ }
Copy-Item $Report $Latest -Force
Log 'DONE security London target plan capture once'
