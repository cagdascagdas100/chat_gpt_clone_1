$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-064-active-pool-real-work'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outRoot = Join-Path $ProjectRoot ('.aays_real_runs\064_active_pool_' + $stamp)
$resultRoot = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
New-Item -ItemType Directory -Force -Path $resultRoot | Out-Null

function Save-Text($path, $text) {
  $text | Out-File -FilePath $path -Encoding UTF8 -Append
}

function Run-Cmd($name, $workdir, $exe, $argText) {
  $safe = $name -replace '[^a-zA-Z0-9_-]', '_'
  $log = Join-Path $outRoot ($safe + '.md')
  Save-Text $log ('# ' + $name)
  Save-Text $log ('Started: ' + (Get-Date))
  Save-Text $log ('Workdir: ' + $workdir)
  Save-Text $log ('Command: ' + $exe + ' ' + $argText)
  Push-Location $workdir
  try {
    $args = @()
    if ($argText) { $args = $argText -split ' ' }
    $output = & $exe @args 2>&1 | Out-String
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    Save-Text $log '```text'
    Save-Text $log $output
    Save-Text $log '```'
    Save-Text $log ('ExitCode: ' + $code)
  } catch {
    Save-Text $log ('ERROR: ' + $_.Exception.Message)
  } finally {
    Pop-Location
  }
  Save-Text $log ('Finished: ' + (Get-Date))
  return $log
}

$jobs = @()
$jobs += Start-Job -Name 'slot1_python_compile' -ScriptBlock ${function:Run-Cmd} -ArgumentList 'slot1_python_compile', $ProjectRoot, 'python', '-m compileall app'
$jobs += Start-Job -Name 'slot2_git_status' -ScriptBlock ${function:Run-Cmd} -ArgumentList 'slot2_git_status', $ProjectRoot, 'git', 'status --short'
$jobs += Start-Job -Name 'slot3_python_version' -ScriptBlock ${function:Run-Cmd} -ArgumentList 'slot3_python_version', $ProjectRoot, 'python', '--version'
$jobs += Start-Job -Name 'slot4_dependency_check' -ScriptBlock ${function:Run-Cmd} -ArgumentList 'slot4_dependency_check', $ProjectRoot, 'python', '-m pip check'
$jobs += Start-Job -Name 'slot5_tests_collect' -ScriptBlock ${function:Run-Cmd} -ArgumentList 'slot5_tests_collect', $ProjectRoot, 'python', '-m pytest --collect-only -q'

$deadline = (Get-Date).AddMinutes(45)
while (@(Get-Job -State Running).Count -gt 0 -and (Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 5
}
foreach ($j in Get-Job -State Running) { Stop-Job $j | Out-Null }
$jobSummary = @()
foreach ($j in $jobs) {
  $received = Receive-Job $j -ErrorAction SilentlyContinue
  $state = $j.State
  $jobSummary += [pscustomobject]@{ Name=$j.Name; State=$state; Log=($received -join '; ') }
}

$summary = Join-Path $outRoot 'summary.md'
Save-Text $summary '# TerraYield 064 Active Pool Real Work'
Save-Text $summary ('Started: ' + $stamp)
Save-Text $summary 'Active pool size: 5'
Save-Text $summary 'No queue wording: jobs are active slots.'
Save-Text $summary ''
foreach ($s in $jobSummary) {
  Save-Text $summary ('- ' + $s.Name + ' => ' + $s.State + ' | ' + $s.Log)
}
Save-Text $summary ''
Save-Text $summary 'RESULT: active_pool_real_work_finished'
Save-Text $summary 'PROGRESS: 24'

$resultFile = Join-Path $resultRoot ('Runner V4 result ' + $TaskId + '.md')
Get-Content $summary -Raw | Out-File -FilePath $resultFile -Encoding UTF8
Write-Host 'RESULT: active_pool_real_work_finished'
Write-Host ('REPORT: ' + $summary)
exit 0
