[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$branch = [string]$env:AAYS_TARGET_BRANCH
$rootText = [string]$env:AAYS_REPO_ROOT
if (-not $rootText) { throw 'HEIGHT_DIFFERENCE_2_REPO_ROOT_MISSING' }
$root = [System.IO.Path]::GetFullPath($rootText)
if ($branch -and $branch -ne 'codex/aays-single-runner-v5-20260706') { throw 'HEIGHT_DIFFERENCE_2_WRONG_BRANCH' }
if ([string]$env:AAYS_PAGE_KEY -and [string]$env:AAYS_PAGE_KEY -ne 'aays1') { throw 'HEIGHT_DIFFERENCE_2_WRONG_PAGE_KEY' }

$pythonCommand = $null
$pythonPrefix = @()
foreach($name in @('python','py','python3')) {
  $candidate = Get-Command $name -ErrorAction SilentlyContinue
  if($candidate){
    $pythonCommand = $candidate.Source
    if($name -eq 'py'){ $pythonPrefix = @('-3') }
    break
  }
}
if(-not $pythonCommand){ throw 'HEIGHT_DIFFERENCE_2_PYTHON_NOT_AVAILABLE' }

$entrypoint = Join-Path $root 'docs\chatgpt_status\aays1\automation\height_difference_2_candidate_then_sampling_entry.py'
if(-not(Test-Path -LiteralPath $entrypoint)){ throw 'HEIGHT_DIFFERENCE_2_CANDIDATE_THEN_SAMPLING_ENTRYPOINT_NOT_FOUND' }

$env:AAYS_TASK_ID = $taskId
$env:AAYS_REPO_ROOT = $root
$env:AAYS_TARGET_BRANCH = 'codex/aays-single-runner-v5-20260706'
$env:AAYS_PAGE_KEY = 'aays1'

& $pythonCommand @pythonPrefix $entrypoint
$code = $LASTEXITCODE
if($code -ne 0){ throw "HEIGHT_DIFFERENCE_2_ENTRYPOINT_EXIT_$code" }
